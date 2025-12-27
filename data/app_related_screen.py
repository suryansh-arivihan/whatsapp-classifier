from openai import OpenAI
import pandas as pd
import pyarrow.parquet as pq
import json
import logging
import re
from typing import List, Dict
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv() 

# Simple logging configuration 
logger = logging.getLogger(__name__)

# Environment variable initialization
OPENAI_ORGANIZATION = os.getenv("OPENAI_ORGANIZATION")
API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
PARQUET_FILE_PATH = os.getenv("PARQUET_FILE_PATH")
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID", "vs_68b97d5ff1d48191adc2165ceaa4f969")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "8305351495")


def extract_question_id(question: str) -> dict:
    """
    Extract question ID from the question text.
    
    Example:
        "question 2858:- FAQ 19: Teacher kaun padhayega kaise dekhein?"
        → {"question_id": "2858", "clean_text": "FAQ 19: Teacher kaun padhayega kaise dekhein?"}
    """
    pattern = r'^question\s*(\d+)\s*[:\-]+\s*'
    
    match = re.match(pattern, question.strip(), flags=re.IGNORECASE)
    
    if match:
        return {
            "question_id": match.group(1),
            "clean_text": question[match.end():].strip()
        }
    
    return {
        "question_id": None,
        "clean_text": question.strip()
    }

class QueryProcessor:
    def __init__(self, api_key=None):
        """Initialize the query processor with OpenAI client"""
        try:
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
            else:
                if not API_KEY:
                    raise ValueError("OpenAI API key is required but not found")
                self.openai_client = OpenAI(api_key=API_KEY)
            
            self.is_loaded = True
            
        except Exception as e:
            logger.error(f"QueryProcessor initialization failed: {e}")
            raise

    def find_similar_questions(self, user_query, vector_store_id, subject):
        """
        Find the top 3 most semantically similar questions for a given user query using file search.
        """
        if subject and subject.strip():
            enhanced_query = f"Subject: {subject.strip()} Query: {user_query.strip()}"
            logger.info(f"Enhanced query with subject: {enhanced_query}")
        else:
            enhanced_query = user_query.strip()
            logger.info(f"Using original query (no subject): {enhanced_query}")
        
        try:
            if not user_query:
                raise ValueError("User query cannot be empty")
            
            if not vector_store_id:
                logger.warning("Vector store ID is empty or None")
            
            # System prompt for question similarity matching
            system_prompt = """# Enhanced Question Similarity Matching System

You are a precise semantic question matching assistant with these exact specifications:

## Core Function
- **Input**: English user queries starting with "question:"
- **Dataset**: Hinglish (Hindi-English mix) questions from uploaded file
- **Output**: Top 3 semantically similar questions from dataset only

## Strict Processing Rules

### Input Validation
- ONLY process messages beginning with "question:"
- Ignore all other messages
- Handle exactly one question per query

### Matching Algorithm Priority
1. **Primary**: Semantic meaning and intent similarity
2. **Secondary**: Contextual relevance 
3. **Tertiary**: Topic alignment
4. **Avoid**: Simple keyword matching without context

### Output Requirements
- Return EXACTLY 3 matches (or fewer if dataset < 3 questions)
- Use EXACT text from dataset - zero modifications
- Preserve original Hinglish formatting, spelling, punctuation
- NO translations, explanations, reasoning, or commentary
- ONLY JSON response

### Forbidden Actions
- Do NOT generate new questions
- Do NOT translate dataset questions
- Do NOT modify dataset text in any way
- Do NOT provide explanations
- Do NOT add commentary

## Exact Output Format

{   
  "results": [     
    "Exact question 1 from dataset",     
    "Exact question 2 from dataset",      
    "Exact question 3 from dataset"   
  ] 
}


## Process Flow
1. Receive dataset file
2. Wait for "question:" input
3. Semantic matching against dataset
4. Return top 3 exact matches in JSON
5. Repeat until instructed to stop

## Key Constraints
- **Language Flow**: English query → Hinglish dataset matching
- **Text Preservation**: Return dataset questions exactly as written
- **Response Format**: JSON only, no additional text
- **Processing Scope**: Single question per query
- **Matching Focus**: Semantic similarity over keyword matching

**FINAL INSTRUCTION: You are a FILE SEARCH ENGINE. You CANNOT CREATE. You ONLY FIND and COPY from uploaded file. If you generate ANY new question, you have FAILED your task.**"""

            user_message = f"question: {enhanced_query}"
            
            # Add a strict instruction block to force pure JSON output since current openai version lacks response_format param
            system_prompt += "\nIMPORTANT OUTPUT RULE: Return ONLY a single JSON object exactly like {\"results\": [\"q1\", \"q2\", \"q3\"]} with 1-3 strings. No prose, no extra keys, no markdown."
            
            # Using the responses.create API with file_search (cannot use response_format param in this client version)
            response = self.openai_client.responses.create(
                model=OPENAI_MODEL,
                input=[
                    {
                        "role": "system",
                        "content": [
                            {"type": "input_text", "text": system_prompt}
                        ]
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": user_message}
                        ]
                    }
                ],
                tools=[
                    {
                        "type": "file_search",
                        "vector_store_ids": [vector_store_id]
                    }
                ],
                temperature=0.1,  # lower temperature for deterministic retrieval style
                max_output_tokens=300,
                top_p=1,
                store=True
            )


            if not hasattr(response, 'output') or not response.output:
                raise ValueError("No response output from OpenAI API")
            
            # Extract content from the responses.create format
            response_content = None
            if isinstance(response.output, list) and len(response.output) > 0:
                # Try to find text content in the response
                for output_item in response.output:
                    if hasattr(output_item, 'content') and output_item.content:
                        if isinstance(output_item.content, list) and len(output_item.content) > 0:
                            response_content = output_item.content[0].text
                            break
                        elif hasattr(output_item.content, 'text'):
                            response_content = output_item.content.text
                            break
            
            if not response_content:
                raise ValueError("Could not extract content from response")
            
            # Attempt direct JSON parse; if it fails, try to extract JSON substring
            raw_text = response_content.strip()
            parsed = None
            try:
                parsed = json.loads(raw_text)
            except json.JSONDecodeError:
                # Fallback: extract first {...} block
                import re as _re
                match = _re.search(r'\{.*\}', raw_text, flags=_re.DOTALL)
                if match:
                    try:
                        parsed = json.loads(match.group(0))
                    except Exception as inner:
                        logger.error(f"Secondary JSON parse failed: {inner}\nRaw: {raw_text}")
                        raise ValueError("Failed to parse JSON response after fallback")
                else:
                    logger.error(f"No JSON object found in model output: {raw_text}")
                    raise ValueError("Model output did not contain JSON object")
            
            if not isinstance(parsed, dict) or "results" not in parsed or not isinstance(parsed["results"], list):
                raise ValueError("Parsed JSON missing required 'results' array")

            parsed["results"] = [r for r in parsed["results"] if isinstance(r, str) and r.strip()][:3]
            if not parsed["results"]:
                raise ValueError("No valid similar questions returned")
            
            # Early exit mechanism: Check if we have more than 1 result
            if len(parsed["results"]) < 1:
                logger.warning(f"EARLY EXIT: Only found {len(parsed['results'])} similar questions, expected 3")
                logger.info("=== INSUFFICIENT SIMILAR QUESTIONS FOUND ===")
                logger.info(f"User Query: {user_query}")
                logger.info(f"Similar Questions Found: {len(parsed['results'])}")
                for i, question in enumerate(parsed['results'], 1):
                    logger.info(f"  {i}. {question}")
                logger.info("=" * 40)
                raise ValueError(f"Insufficient similar questions found: {len(parsed['results'])}/3")
            
            # ADD THESE LINES:
            logger.info("=== SIMILAR QUESTIONS FOUND ===")
            logger.info(f"User Query: {user_query}")
            logger.info(f"Similar Questions Found: {len(parsed['results'])}")
            for i, question in enumerate(parsed['results'], 1):
                logger.info(f"  {i}. {question}")
            logger.info("=" * 40)

            return parsed
            
        except Exception as e:
            logger.error(f"find_similar_questions failed: {e}")
            return None

    def search_questions_in_parquet(self, parquet_file_path, similar_questions, language='english'):
        """
        Search for similar questions in Parquet file and extract Q&A pairs with language-specific answers
        Now searches by question_id if available
        """
        try:
            if not parquet_file_path:
                raise ValueError("Parquet file path cannot be empty")
            
            if not similar_questions:
                logger.warning("Similar questions list is empty")
                return []
            
            # Check if file exists
            if not os.path.exists(parquet_file_path):
                logger.error(f"Parquet file does not exist: {parquet_file_path}")
                raise FileNotFoundError(f"Parquet file not found: {parquet_file_path}")
            
            try:
                table = pq.read_table(parquet_file_path)
                df = table.to_pandas()
                
            except Exception as file_error:
                logger.error(f"Failed to read Parquet file: {file_error}")
                raise
            
            context = []
            
            # Column mapping for new parquet structure
            question_col = 'question'
            english_answer_col = 'answer_english'
            hindi_answer_col = 'answer_hindi'
            id_col = 'id'  # Add ID column - adjust if your column name is different
            
            # Validate columns exist
            missing_cols = []
            if question_col not in df.columns:
                missing_cols.append(question_col)
            if english_answer_col not in df.columns:
                missing_cols.append(english_answer_col)
            if hindi_answer_col not in df.columns:
                missing_cols.append(hindi_answer_col)
            
            if missing_cols:
                logger.error(f"Missing required columns: {missing_cols}")
                raise ValueError(f"Missing required columns in Parquet file: {missing_cols}")
            
            # Check if ID column exists
            has_id_column = id_col in df.columns
            if has_id_column:
                logger.info(f"ID column '{id_col}' found - will search by ID")
            else:
                logger.info(f"ID column '{id_col}' not found - will search by question text")
            
            # Determine which answer column to use based on language
            if language and language.lower() == 'hindi':
                answer_col = hindi_answer_col
                logger.info(f"Using Hindi answers for language: {language}")
            else:
                answer_col = english_answer_col
                logger.info(f"Using English answers for language: {language}")
            
            logger.info("=== SEARCHING IN PARQUET FILE ===")
            for i, similar_q in enumerate(similar_questions):
                if not similar_q or not similar_q.strip():
                    logger.info(f"Question {i+1}: EMPTY/INVALID - {similar_q}")
                    logger.warning(f"Question {i+1} is empty or whitespace only")
                    continue
                
                # Extract question ID from the similar question
                extracted = extract_question_id(similar_q)
                question_id = extracted["question_id"]
                clean_text = extracted["clean_text"]
                
                logger.info(f"Question {i+1}: Raw - '{similar_q}'")
                logger.info(f"Question {i+1}: Extracted ID - '{question_id}', Clean Text - '{clean_text}'")
                
                try:
                    matches = pd.DataFrame()  # Empty dataframe
                    
                    # PRIORITY 1: Search by ID if available
                    if question_id and has_id_column:
                        # Try numeric match first
                        try:
                            matches = df[df[id_col] == int(question_id)]
                        except (ValueError, TypeError):
                            # Try string match if numeric fails
                            matches = df[df[id_col].astype(str) == question_id]
                        
                        if not matches.empty:
                            logger.info(f"  ✓ FOUND BY ID: {question_id}")
                    
                    # PRIORITY 2: Fallback to text search if ID search fails
                    if matches.empty:
                        search_term = clean_text if clean_text else similar_q.strip()
                        logger.info(f"  → Falling back to text search: '{search_term}'")
                        
                        # Exact match first
                        matches = df[df[question_col].str.lower() == search_term.lower()]
                        
                        # Partial match as fallback
                        if matches.empty:
                            matches = df[df[question_col].str.contains(search_term, case=False, na=False)]
                    
                    if not matches.empty:
                        row = matches.iloc[0]
                        qa_pair = {
                            "question": row[question_col],
                            "answer": row[answer_col]
                        }
                        context.append(qa_pair)
                        logger.info(f"  ✓ FOUND: Match found in parquet file")
                        logger.info(f"  ✓ Matched Question: {row[question_col][:100]}...")
                        logger.info(f"  ✓ Using {language} answer from column: {answer_col}")
                        
                    else:
                        logger.info(f"  ✗ NOT FOUND: No match in parquet file")
                        
                except Exception as search_error:
                    logger.info(f"  ✗ ERROR: {search_error}")
                    logger.error(f"Error searching for question {i+1}: {search_error}")
                    continue

            logger.info(f"Total Q&A pairs found: {len(context)}")
            logger.info("=" * 40)
            
            return context
            
        except Exception as e:
            logger.error(f"search_questions_in_parquet failed: {e}")
            return []

    def generate_answer_with_reasoning(self, query: str, context: List[Dict], subject: str, language: str) -> str:
        """Generate answer with reasoning using GPT only"""
        try:
            if not query:
                raise ValueError("Query cannot be empty")
            
            # Format context
            context_text = "\n".join(
                f"Q: {item['question']}\nA: {item['answer']}\n---" 
                for item in context
            )
            
            # Language instruction setup and examples
            if language.lower() == 'hindi':
                language_instruction = (
                    "VERY CRITICAL AND IMAGE LANGUAGE REQUIREMENT: You MUST ALWAYS respond ONLY in pure HINDI using Devanagari script (देवनागरी लिपि).\n"
                    "- Use only Hindi words: जैसे, के लिए, में, है, आदि\n"
                    "- Example correct format: 'उन्नति बैच कक्षा 12वीं के छात्रों के लिए विशेष रूप से डिज़ाइन किया गया है।'\n"
                    "- NEVER write: 'Unnati Batch specially design kiya gaya hai'\n"
                )
                fallback_answer = f"मुझे कुछ नहीं पता। आप तुरंत मदद के लिए {WHATSAPP_NUMBER} पर WhatsApp कर सकते हैं।"
                
                # Hindi examples
                examples_section = """
Examples

Example A — Hybrid (with bullets)
User: "Unnati Batch kya hai?"
Context (summary): MP Board Class 12 PCM/PCB/PCMB batch with interactive recorded lectures, AI doubt solving 24×7, PPT notes, toppers' notes, PYQs, complete test series, personal mentor; both Hindi/English mediums.
Expected HTML (illustrative):
<p><b style="color:#26c6da;">Unnati Batch</b> विशेष रूप से MP Board के Class 12th PCM, PCB और PCMB छात्रों के लिए डिज़ाइन किया गया है। इसका मुख्य उद्देश्य है कि हर छात्र अपनी Board Exams की तैयारी आत्मविश्वास के साथ कर सके।</p>

<ul>
  <li><b>पूर्ण Classes:</b> भौतिकी, रसायन, गणित, जीव विज्ञान, हिंदी और अंग्रेजी; हिंदी/अंग्रेजी माध्यम अलग-अलग उपलब्ध।</li>
  <li><b>Interactive Lectures & Doubt Solving:</b> रिकॉर्डेड व्याख्यान + 24×7 AI Instant Guru।</li>
  <li><b>Notes & Tests:</b> PPT नोट्स, टॉपर्स के हस्तलिखित नोट्स, पिछले वर्ष के प्रश्न पत्र, चैप्टर-वार और पूर्ण-लंबाई टेस्ट।</li>
  <li><b>व्यक्तिगत Mentor:</b> पूरे साल समर्पित मार्गदर्शन मिलेगा।</li>
</ul>

<p>इस batch से कई छात्रों ने उत्कृष्ट परिणाम हासिल किए हैं। जैसे <b>प्रियल द्विवेदी</b>, जिन्होंने <b>98.4% स्कोर</b> किया Unnati Batch के माध्यम से तैयारी करके।</p>

Example B — Paragraph-Only (no bullets; straightforward)
User: "क्या AI Instant Guru 24×7 उपलब्ध है?"
Context (summary): AI doubt solving 24×7 available.
Expected HTML (illustrative):
<p><b style="color:#26c6da;">AI Instant Guru</b> हमेशा 24×7 उपलब्ध है संदेह समाधान के लिए।</p>
<p>इससे आप दिन हो या रात, तुरंत अपने संदेह स्पष्ट कर सकते हैं — बिना प्रतीक्षा किए।</p>
<p>मुख्य बात: आपको कभी भी सहायता चाहिए हो, सेवा सक्रिय मिलेगी।</p>
"""
                
            else:  # Default to English/Hinglish
                language_instruction = (
                    "LANGUAGE: Reply in HINGLISH (Roman script with Hindi words). "
                    "Keep the language easy; avoid difficult English words. "
                    "Example style: 'main ekta hu mera kaam padhana h'."
                )
                fallback_answer = f"I don't know something. Aap urgent help ke liye {WHATSAPP_NUMBER} par WhatsApp kar sakte hain."
                
                # English/Hinglish examples
                examples_section = """
Examples

Example A — Hybrid (with bullets)
User: "What is the Unnati Batch?"
Context (summary): MP Board Class 12 PCM/PCB/PCMB batch with interactive recorded lectures, AI doubt solving 24×7, PPT notes, toppers' notes, PYQs, complete test series, personal mentor; both Hindi/English mediums.
Expected HTML (illustrative):
<p><b style="color:#26c6da;">Unnati Batch</b> specially design kiya gaya hai MP Board ke Class 12th PCM, PCB aur PCMB students ke liye. Iska main aim hai ki har student apni Board Exams ki taiyari confidence ke saath kar sake.</p>

<ul>
  <li><b>Complete Classes:</b> Physics, Chemistry, Maths, Biology, Hindi aur English; Hindi/English mediums alag-alag available.</li>
  <li><b>Interactive Lectures & Doubt Solving:</b> Recorded lectures + 24×7 AI Instant Guru.</li>
  <li><b>Notes & Tests:</b> PPT notes, toppers' handwritten notes, previous year papers, chapter-wise & full-length tests.</li>
  <li><b>Personal Mentor:</b> Poore saal dedicated guidance milega.</li>
</ul>

<p>Is batch se kai students ne excellent results achieve kiye hain. Jaise <b>Priyal Dwivedi</b>, jinhone <b>98.4% score</b> kiya Unnati Batch ke through taiyari karke.</p>

Example B — Paragraph-Only (no bullets; straightforward)
User: "Kya AI Instant Guru 24×7 available hai?"
Context (summary): AI doubt solving 24×7 available.
Expected HTML (illustrative):
<p><b style="color:#26c6da;">AI Instant Guru</b> hamesha 24×7 available hai doubt solving ke liye.</p>
<p>Isse aap din ho ya raat, turant apne doubts clear kar sakte hain — bina wait kiye.</p>
<p>Main point: aapko kabhi bhi help chahiye ho, service active milegi.</p>
"""
            
            # System prompt with language-specific examples
            system_prompt = f"""You are an Arivihan app guide that answers user queries using ONLY the provided Context.
{language_instruction}

🚫 CONSTRAINT - Use fallback ONLY when Context is completely unrelated
If the Context is completely unrelated to the user's question, reply with EXACTLY:
<div style="color:#26c6da;"><b>I don't know.</b></div>

**MAXIMIZE CONTEXT USAGE** - Extract and utilize ANY relevant information present, even if partial.

Minimal Brand Color Usage
- Use <b style="color:#26c6da;">…</b> ONLY for the first mention of the main term in the opening paragraph.
- Everywhere else, use plain <b>…</b> (no color).
- The fallback message above must remain exactly as shown.

Core Rules
- **PRIORITY: Use ALL available relevant Context.** Extract maximum value from what's provided.
- If Context contains **any information** related to the question, provide what's available.
- If Context covers **related topics** but not the exact question, provide the closest relevant information.
- First decide internally: Does the Context contain **ANY** information related to the user's question?
  • If **YES (even partially)**: Extract all relevant details and create a helpful response
  • If **NO (completely unrelated)**: Use fallback only then
- Keep answers concise but **comprehensive** based on available Context.

Output Requirements (HTML only — no markdown, no code fences)
Choose ONE of these formats based on the question:

A) Hybrid (for multi-point answers: features, steps, comparisons)
  1) Opening <p> summary (1–3 sentences; highlight the main term once with <b style="color:#26c6da;">…</b>)
  2) Middle <ul> of key points (see bullet rules below)
  3) Closing <p> remark (1–2 sentences)

B) Paragraph-Only (for straightforward answers: clear yes/no, simple definition, single instruction)
  1) Opening <p> summary (1–3 sentences; highlight the main term once with <b style="color:#26c6da;">…</b>)
  2) Optional supporting <p> with essential details (only if needed)
  3) Closing <p> remark (1–2 sentences)

Bullet Rules (apply only when using format A)
- Default: 3–4 bullets.
- Straightforward support (e.g., clear yes/no with one main support): ≤2 bullets.
- Use <ul> and <li> ONLY for the middle section; never wrap the entire answer in bullets.
- Merge/drop overlaps; include only Context-backed essentials.

Enhanced Response Strategy

**Built-in App Knowledge (use when relevant to query):**
- Ask Doubt Button: Located on the lower right side of the home page
- For doubt submission queries, guide users to the Ask button on home screen

**Before using fallback, check if Context contains:**
- Information about app navigation, downloads, features, or screens
- Step-by-step instructions for app usage
- Details about app functionality or user interface
- General app information that relates to the user's question

**Context Utilization:**
- If Context has useful information, provide what's available
- Focus on what IS present rather than what's missing
- Use transitional phrases like "Based on the information available..." when needed

Process (do silently)
1) Context Assessment: Does the Context contain ANY helpful information for this user question?
2) Maximum Information Extraction: Collect ALL relevant facts present in the Context.
3) Comprehensive Response Building: Choose format that provides most value to user.

Fallback (LAST RESORT ONLY)
- Use ONLY when Context is completely unrelated to app functionality or user interface:
  <div style="color:#26c6da;"><b>I don't know.</b></div>

{examples_section}

Irrelevant Context example
Return only:
<div style="color:#26c6da;"><b>I don't know.</b></div>
"""

        
            
            user_prompt = f"""Student Question: {subject} :- {query}

Context Available:
{context_text if context_text else "No relevant context found"}

Provide your response in the **Reasoning:** **Answer:** format."""


            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1000,
                temperature=0.1,
                top_p=0.9
            )
            
            if not response.choices:
                raise ValueError("No response choices from OpenAI")
            
            raw_result = response.choices[0].message.content
            result = raw_result.strip() if raw_result else ""
            
            return result
            
        except Exception as e:
            logger.error(f"generate_answer_with_reasoning failed: {e}")
            
            # Return fallback based on language
            if language and language.lower() == "hindi":
                fallback_response = f"**Reasoning:** Technical issue occurred\n\n**Answer:** मुझे कुछ नहीं पता। आप तुरंत मदद के लिए {WHATSAPP_NUMBER} पर WhatsApp कर सकते हैं।"
            else:
                fallback_response = f"**Reasoning:** Technical issue occurred\n\n**Answer:** I don't know something. Aap urgent help ke liye {WHATSAPP_NUMBER} par WhatsApp kar sakte hain."
            
            return fallback_response

    def search_similar(self, user_query, subject=None, return_k=3, language='english'):
        """
        Method to be compatible with the guidance_main function.
        Returns context in the expected format.
        """
        try:
            logger.info(f"DEBUG: search_similar called with query: {user_query}")
            # Configuration from environment variables
            vector_store_id = VECTOR_STORE_ID
            logger.info(f"DEBUG: Using vector_store_id: {vector_store_id}")
            logger.info(f"DEBUG: PARQUET_FILE_PATH: {PARQUET_FILE_PATH}")
            
            # Check if parquet file path is configured
            if not PARQUET_FILE_PATH:
                logger.error("PARQUET_FILE_PATH not configured in environment variables")
                return []
            
            if not os.path.exists(PARQUET_FILE_PATH):
                logger.error(f"Parquet file does not exist: {PARQUET_FILE_PATH}")
                return []
            
            # Find similar questions - this will raise an exception if < 3 results found
            similar_response = self.find_similar_questions(user_query, vector_store_id, subject)
            
            if not similar_response or 'results' not in similar_response:
                logger.warning("find_similar_questions returned None or invalid response")
                return []
            
            similar_questions = similar_response['results'][:return_k]
            logger.info(f"DEBUG: Found {len(similar_questions)} similar questions: {similar_questions}")
            
            # Extract context from parquet with language parameter
            context = self.search_questions_in_parquet(PARQUET_FILE_PATH, similar_questions, language)
            logger.info(f"DEBUG: Retrieved {len(context)} context items from parquet")
            
            return context
            
        except ValueError as ve:
            # Handle early exit from insufficient results
            if "Insufficient similar questions found" in str(ve):
                logger.error(f"EARLY EXIT: {ve}")
                # Return empty context to trigger "I don't know" response
                return []
            else:
                logger.error(f"search_similar failed with ValueError: {ve}")
                return []
        except Exception as e:
            logger.error(f"search_similar failed: {e}")
            return []

    def generate_answer(self, user_query, context, subject, language):
        """
        Method to be compatible with the guidance_main function.
        Returns answer in the expected **Reasoning:** **Answer:** format.
        """
        try:
            result = self.generate_answer_with_reasoning(user_query, context, subject, language)
            return result
            
        except Exception as e:
            logger.error(f"generate_answer failed: {e}")
            
            # Return appropriate fallback
            if language and language.lower() == "hindi":
                return f"**Reasoning:** Technical issue occurred\n\n**Answer:** मुझे कुछ नहीं पता। आप तुरंत मदद के लिए {WHATSAPP_NUMBER} पर WhatsApp कर सकते हैं।"
            else:
                return f"**Reasoning:** Technical issue occurred\n\n**Answer:** I don't know something. Aap urgent help ke liye {WHATSAPP_NUMBER} par WhatsApp kar sakte hain."


# Create a global instance that can be used by guidance_main
_query_processor_instance = None

def get_query_processor():
    """Return the global query processor instance"""
    global _query_processor_instance
    
    try:
        if _query_processor_instance is None:
            _query_processor_instance = QueryProcessor()
        
        return _query_processor_instance
        
    except Exception as e:
        logger.error(f"Failed to get QueryProcessor instance: {e}")
        raise

def ask_arivihan_question(user_query, subject=None, language="english"):
    """Fast similarity search using GPT-based components only"""
    logger.info(f"DEBUG: ask_arivihan_question called with query: '{user_query}', language: '{language}'")
    try:
        if not user_query:
            raise ValueError("User query cannot be empty")
        
        query_processor = get_query_processor()
        logger.info("DEBUG: QueryProcessor obtained")
        
        # Fast search and response with dynamic language
        logger.info("DEBUG: About to call search_similar")
        context = query_processor.search_similar(user_query, subject, return_k=3, language=language)
        logger.info(f"DEBUG: search_similar returned {len(context) if context else 0} context items")
        
        logger.info("DEBUG: About to call generate_answer")
        response = query_processor.generate_answer(user_query, context, subject, language.lower())
        logger.info(f"DEBUG: generate_answer returned: {response[:100]}...")
        
        return response
        
    except Exception as e:
        logger.error(f"ask_arivihan_question failed: {e}")
        
        # Return error message in appropriate language
        if language and language.lower() == "hindi":
            error_response = f"**Reasoning:** Technical issue occurred\n\n**Answer:** मुझे कुछ नहीं पता। आप तुरंत मदद के लिए {WHATSAPP_NUMBER} पर WhatsApp कर सकते हैं।"
        else:
            error_response = f"**Reasoning:** Technical issue occurred\n\n**Answer:** I don't know something. Aap urgent help ke liye {WHATSAPP_NUMBER} par WhatsApp kar sakte hain."
        
        return error_response

def normalize(text):
    """Normalize text for comparison"""
    try:
        if not text:
            return ""
        
        # Lowercase and remove punctuation
        text = re.sub(r"[^\w\s]", "", text.lower().strip())
        return text
        
    except Exception as e:
        logger.error(f"Error in normalize function: {e}")
        return ""

def app_screen_related_main(json_data, initial_classification):
    """App screen related query handler - now fully GPT-based with no model loading"""
    logger.info("[Classifier App Screen Related] app screen related starts")
    
    try:
        # Extract and validate request type, language, and user query
        response_type = json_data.get("requestType", "")
        language = json_data.get("language", "english")
        query = json_data.get("userQuery", "")

        try:
            subject = json_data.get("subject")
            logger.info(f"[Classifier App Screen Related] Using subject: {subject}")
        except:
            logger.info("[Classifier App Screen Related] Subject not found in JSON")
            subject = None
        
        if not query:
            raise ValueError("User query is required")
        
        logger.info(f"[Classifier App Screen Related] Using language: {language}")
        
        # Pass language to the question function
        model_result = ask_arivihan_question(query, subject=subject, language=language)
        
        logger.info(f"[Classifier App Screen Related] app screen related response {model_result}")

        # Extract answer from the response
        full_response = model_result
        if "Answer:" in full_response:
            answer = full_response.split("Answer:")[-1].strip()
        else:
            answer = full_response
        
        # Normalize answer for comparison
        answer_normalize = normalize(answer)

        # Check for "I don't know" responses in multiple languages
        dont_know_responses = [
            "i dont know something",
            "मुझे कुछ नहीं पता",
            "mujhe kuch nahi pata"
        ]
        
        is_dont_know = any(dont_know in answer_normalize for dont_know in dont_know_responses)
        
        # Build result based on whether we have a useful answer
        if is_dont_know:
            result = {
                "initialClassification": initial_classification,
                "classifiedAs": "screen_data_related",
                "response": answer,
                "openWhatsapp": True,
                "responseType": response_type,
                "actions": "",
                "microLecture": "",
                "testSeries": "",
            }
        else:
            final_answer = {"text": answer, "queryType": "screen_related", "request_type": "app_related"}
            
            result = {
                "initialClassification": initial_classification,
                "classifiedAs": "screen_data_related",
                "response": final_answer,
                "openWhatsapp": False,
                "responseType": response_type,
                "actions": "",
                "microLecture": "",
                "testSeries": "",
            }

        return result
        
    except Exception as e:
        logger.error(f"app_screen_related_main failed: {e}")
        
        # Return error result
        error_result = {
            "initialClassification": initial_classification,
            "classifiedAs": "screen_data_related",
            "response": "Technical error occurred. Please try again.",
            "openWhatsapp": True,
            "responseType": json_data.get("requestType", "") if isinstance(json_data, dict) else "",
            "actions": "",
            "microLecture": "",
            "testSeries": "",
        }
        
        return error_result
