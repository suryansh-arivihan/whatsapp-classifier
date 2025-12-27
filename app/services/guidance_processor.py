"""
Local guidance query processor using OpenAI vector store and Parquet file.
Handles guidance queries without external API calls.
Includes Sambhav Batch knowledge for contextual promotion.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
import pandas as pd
from openai import OpenAI
from app.core.logging_config import logger
from app.core.config import settings


# ============================================
# CONFIGURATION
# ============================================
WHATSAPP_NUMBER = "8305351495"


# ============================================
# SAMBHAV BATCH KNOWLEDGE BASE
# ============================================
SAMBHAV_KNOWLEDGE = """
**SAMBHAV BATCH - KEY INFO FOR SUBTLE PROMOTION:**

*Kya hai:* 50-day Crash Course for MP Board Class 12

*Features:*
- Daily Live Classes (2-2.5 hrs)
- Recordings available (miss ho jaye to dekh lo)
- 24×7 AI Doubt Support
- Science: Toppers Notes | Commerce/Arts: Toppers Copies
- IMP Topics + IMP Questions + PYQs
- Stream-wise Time Table PDF
- Board pattern ke hisaab se padhaya jaata hai

*Subjects:*
- Science: Physics, Chemistry, Biology, Maths, English, Hindi
- Commerce: Accountancy, Business Studies, Economics, English, Hindi
- Arts: History, Pol Science, Geography, Economics, English, Hindi

*Access:* Arivihan App → All Features → Sambhav Crash Course

*USP:* Last time fast preparation, poora syllabus cover, organized study
"""


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
    """Process guidance queries using vector store and Parquet file."""

    def __init__(self):
        """Initialize the query processor with OpenAI client."""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.parquet_file_path = os.getenv("PARQUET_FILE_PATH")
        self.vector_store_id = os.getenv("VECTOR_STORE_ID", "vs_68b97d5ff1d48191adc2165ceaa4f969")

        if not self.parquet_file_path:
            logger.warning("[QueryProcessor] PARQUET_FILE_PATH not set in environment")

    def find_similar_questions(self, query: str, subject: str = None, top_k: int = 3) -> dict:
        """
        Find similar questions using OpenAI vector store.
        Returns dict with 'results' key containing list of question strings.
        """
        try:
            # Enhance query with subject if provided
            if subject and subject.strip():
                enhanced_query = f"Subject: {subject.strip()} Query: {query.strip()}"
                logger.info(f"[VectorSearch] Enhanced query with subject: {enhanced_query}")
            else:
                enhanced_query = query.strip()
                logger.info(f"[VectorSearch] Using original query: {enhanced_query}")

            system_prompt = """# Enhanced Question Similarity Matching System

You are a precise semantic question matching assistant with these exact specifications:

The Sambhav Batch is a special 50-day crash course designed for Class 12 MP Board students to help them complete their entire board exam preparation in a short time with full confidence. It includes one-shot lectures for all important topics, PDFs of last year's important questions and answers, dedicated numerical videos, and essential tips and tricks for solving the question paper effectively. You also receive daily tasks, chapter-wise tests, and expert guidance from Arivan so that you stay focused and avoid confusion while aiming for 85% or above. You can join this batch through the Arivan application by selecting the subscription plan, and then access all the crash-course content under the "40 Days Board Exam Preparation" section along with your daily tasks.

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

**FINAL INSTRUCTION: You are a FILE SEARCH ENGINE. You CANNOT CREATE. You ONLY FIND and COPY from uploaded file. If you generate ANY new question, you have FAILED your task.**

IMPORTANT OUTPUT RULE: Return ONLY a single JSON object exactly like {"results": ["q1", "q2", "q3"]} with 1-3 strings. No prose, no extra keys, no markdown."""

            user_message = f"question: {enhanced_query}"
            
            response = self.client.responses.create(
                model="gpt-4.1-mini",
                input=[
                    {
                        "role": "system",
                        "content": [{"type": "input_text", "text": system_prompt}]
                    },
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": user_message}]
                    }
                ],
                tools=[{
                    "type": "file_search",
                    "vector_store_ids": [self.vector_store_id],
                    "max_num_results": top_k
                }],
                temperature=0.1,
                max_output_tokens=300,
                top_p=1,
                store=True
            )

            # Extract response content
            response_content = None
            if hasattr(response, 'output') and response.output:
                for item in response.output:
                    if hasattr(item, 'content') and item.content:
                        if isinstance(item.content, list) and len(item.content) > 0:
                            response_content = item.content[0].text
                            break
                        elif hasattr(item.content, 'text'):
                            response_content = item.content.text
                            break
                    if response_content:
                        break

            if not response_content:
                logger.error("[ERROR] No content in response")
                return None

            # Parse JSON response
            raw_text = response_content.strip()
            parsed = None
            
            try:
                parsed = json.loads(raw_text)
            except json.JSONDecodeError:
                # Fallback: extract JSON block
                match = re.search(r'\{.*\}', raw_text, flags=re.DOTALL)
                if match:
                    try:
                        parsed = json.loads(match.group(0))
                    except Exception as inner:
                        logger.error(f"[ERROR] Secondary JSON parse failed: {inner}")
                        logger.error(f"[ERROR] Raw text: {raw_text[:200]}")
                        return None
                else:
                    logger.error(f"[ERROR] No JSON found in: {raw_text[:200]}")
                    return None

            if not isinstance(parsed, dict) or "results" not in parsed or not isinstance(parsed["results"], list):
                logger.error("[ERROR] Invalid JSON structure - missing 'results' array")
                return None

            # Filter valid results
            parsed["results"] = [r for r in parsed["results"] if isinstance(r, str) and r.strip()][:top_k]
            
            if not parsed["results"]:
                logger.warning("[WARN] No valid similar questions returned")
                return None

            # Early exit check
            if len(parsed["results"]) < 1:
                logger.warning(f"[WARN] EARLY EXIT: Only found {len(parsed['results'])} similar questions")
                return None

            # Log found questions
            logger.info("=== SIMILAR QUESTIONS FOUND ===")
            logger.info(f"User Query: {query}")
            logger.info(f"Similar Questions Found: {len(parsed['results'])}")
            for i, question in enumerate(parsed['results'], 1):
                logger.info(f"  {i}. {question}")

            return parsed

        except Exception as e:
            logger.error(f"[ERROR] Vector search failed: {e}")
            return None

    def search_questions_in_parquet(self, similar_questions: List[str], language: str = 'hindi') -> List[Dict[str, str]]:
        """
        Search for similar questions in Parquet file and extract Q&A pairs.
        Properly searches by question_id if available.
        
        Args:
            similar_questions: List of question strings from vector search
            language: 'hindi' or 'english' for answer selection
        """
        try:
            if not self.parquet_file_path:
                logger.warning("[WARN] Parquet file path not configured")
                return []
                
            if not os.path.exists(self.parquet_file_path):
                logger.warning(f"[WARN] Parquet file not found: {self.parquet_file_path}")
                return []

            if not similar_questions:
                logger.warning("[WARN] Similar questions list is empty")
                return []

            df = pd.read_parquet(self.parquet_file_path)
            context = []

            # Column mapping
            question_col = 'question'
            english_answer_col = 'answer_english'
            hindi_answer_col = 'answer_hindi'
            id_col = 'id'

            # Validate columns exist
            missing_cols = []
            if question_col not in df.columns:
                missing_cols.append(question_col)
            if english_answer_col not in df.columns:
                missing_cols.append(english_answer_col)
            if hindi_answer_col not in df.columns:
                missing_cols.append(hindi_answer_col)

            if missing_cols:
                logger.error(f"[ERROR] Missing required columns: {missing_cols}")
                # Fallback: try to use 'answer' column if specific ones missing
                if 'answer' in df.columns:
                    english_answer_col = 'answer'
                    hindi_answer_col = 'answer'
                else:
                    return []

            # Check if ID column exists
            has_id_column = id_col in df.columns
            if has_id_column:
                logger.info(f"[Parquet] ID column '{id_col}' found - will search by ID")
            else:
                logger.info(f"[Parquet] ID column '{id_col}' not found - will search by question text")

            # Determine which answer column to use based on language
            if language and language.lower() == 'hindi':
                answer_col = hindi_answer_col
                logger.info(f"[Parquet] Using Hindi answers")
            else:
                answer_col = english_answer_col
                logger.info(f"[Parquet] Using English answers")

            logger.info("=== SEARCHING IN PARQUET FILE ===")
            for i, similar_q in enumerate(similar_questions):
                if not similar_q or not similar_q.strip():
                    logger.info(f"Question {i+1}: EMPTY/INVALID - skipping")
                    continue

                # Extract question ID from the similar question
                extracted = extract_question_id(similar_q)
                question_id = extracted["question_id"]
                clean_text = extracted["clean_text"]

                logger.info(f"Question {i+1}: Raw - '{similar_q[:80]}...'")
                logger.info(f"Question {i+1}: Extracted ID - '{question_id}', Clean Text - '{clean_text[:50]}...'")

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
                        logger.info(f"  → Falling back to text search: '{search_term[:50]}...'")

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
                        logger.info(f"  ✓ Matched Question: {row[question_col][:80]}...")
                    else:
                        logger.info(f"  ✗ NOT FOUND: No match in parquet file")

                except Exception as search_error:
                    logger.error(f"  ✗ ERROR: {search_error}")
                    continue

            logger.info(f"Total Q&A pairs found: {len(context)}")

            return context

        except Exception as e:
            logger.error(f"[ERROR] Parquet read failed: {e}")
            import traceback
            logger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
            return []

    def generate_answer(self, query: str, context: List[Dict[str, str]] = None, subject: str = None, language: str = 'hindi') -> str:
        """
        Generate answer using GPT with context from similar Q&A pairs.

        Args:
            query: User's original query
            context: List of similar question-answer pairs
            subject: Subject of the query
            language: Response language (hindi or english)

        Returns:
            Plain text formatted answer string
        """
        try:
            # Format context
            context_text = ""
            if context:
                context_text = "\n".join(
                    f"Q: {item['question']}\nA: {item['answer']}\n---"
                    for item in context
                )

            system_prompt = f"""You are Ritesh Sir - a warm, experienced Class 12th teacher for MP Board students.

---

**🎯 SAMBHAV BATCH KNOWLEDGE (For Subtle Promotion):**

{SAMBHAV_KNOWLEDGE}

---

**YOUR CORE IDENTITY:**
- 15+ years teaching experience in PCM/PCB
- You genuinely care about students' success
- Talk like a real Indian teacher - warm, supportive, practical
- Use natural Hinglish (Hindi + English in Roman script)

---

**⚠️ CRITICAL: RESPONSE LENGTH RULES (STRICT)**

| Query Type | Word Limit | Format |
|------------|------------|--------|
| Study tips/advice | 50-70 words | 2-3 key points |
| Subject guidance | 40-60 words | Direct answer + tip |
| Emotional support | 50-70 words | Empathy + practical step |
| Time management | 50-70 words | Quick schedule tip |
| Exam strategy | 50-70 words | 2-3 actionable tips |

**HARD LIMIT: Never exceed 80 words. Count before responding!**

---

**RESPONSE STRUCTURE (Simple & Clean):**

```
[Warm acknowledgment - 1 line]

[Main advice - 2-3 short points with bullets or simple lines]

[Sambhav mention if relevant - 1 line only]

[Encouraging closer + question - 1 line]
```

---

**SUBTLE SAMBHAV PROMOTION RULES:**

✅ **WHEN TO MENTION (Pick ONE that fits):**

| Student Says | Sambhav Mention |
|--------------|-----------------|
| "Syllabus complete nahi hua" | "Sambhav ka 50-day crash course poora syllabus cover karta hai!" |
| "Time table nahi ban raha" | "Sambhav mein ready-made time table milta hai - try karo!" |
| "Doubt solve nahi hota" | "Sambhav mein 24×7 AI doubt support hai - kabhi bhi poocho!" |
| "Notes nahi hain" | "Sambhav mein Toppers Notes/Copies milti hain - bahut helpful!" |
| "Kaise padhu" | "Sambhav ki daily classes follow karo - organized rahoge!" |
| "Practice nahi ho rahi" | "Sambhav mein IMP Questions + PYQs milte hain - daily karo!" |
| "Recording chahiye" | "Sambhav mein class miss ho jaye to recording dekh sakte ho!" |

❌ **WHEN NOT TO MENTION:**
- Simple greetings (Hi/Hello)
- Thank you messages
- Unrelated personal queries
- When already mentioned in conversation

**PROMOTION STYLE:**
- Maximum 1 line (8-12 words)
- Weave naturally into advice
- Never sound salesy
- Only when genuinely helpful

---

**FORMATTING RULES:**

✅ DO:
- Plain text only (NO HTML)
- Use * for emphasis sparingly (*important point*)
- Use \\n\\n for paragraph breaks
- Simple bullets with - or •
- Natural Hinglish flow

❌ DON'T:
- No HTML tags ever
- No long paragraphs
- No numbered lists (use bullets if needed)
- No over-formatting
- No repetitive phrases

---

**NATURAL TEACHER PHRASES:**

Openers:
- "Beta, samajh gaya main..."
- "Dekho, simple hai ye..."
- "Achha sawal hai!"
- "Haan beta, tension mat lo..."

Closers:
- "Koi doubt ho to batao!"
- "Try karo, fir batana!"
- "Mehnat karo, result aayega! 💪"
- "Aur help chahiye to poocho!"

Empathy:
- "Main samajh sakta hoon..."
- "Ye bahut normal hai..."
- "Ghabrao mat, main hoon na!"

---

**EXAMPLE RESPONSES:**

**Q: "Physics mein bahut weak hoon, kya karun?"**

"Beta, tension mat lo! Physics practice se strong hoti hai.

• Daily 1 chapter ke formulas revise karo
• Numerical solve karo - NCERT + PYQs
• Concepts clear karo pehle, then problems

Sambhav mein Physics ki daily classes hoti hain - abhi join karo! 📚"

*(~55 words)*

---

**Q: "Time manage nahi ho raha, bohot syllabus hai"**

"Beta, organized study se sab ho jayega!

• Subah 3 hrs - tough subjects (PCM/Accounts)
• Dopahar - theory padho
• Shaam - revision + PYQs

Sambhav ka time table follow karo - daily schedule ready milta hai!

Kis subject se start karna hai? Batao! 💪"

*(~50 words)*

---

**Q: "Bahut stress ho raha hai exam ka"**

"Beta, ghabrao mat! Ye feeling normal hai.

• Deep breaths lo, calm raho
• Daily small targets set karo
• Progress dekho, comparison nahi

11 saal padhai ki hai tumne - sab aata hai, bas revise karo!

Kya specific tension hai? Share karo, me yaha hu aapki help karne ke liye! 🤗"

*(~50 words)*

---

**EXECUTION CHECKLIST:**

1. ✅ Read query carefully
2. ✅ Identify query type (study/emotional/subject/time)
3. ✅ Draft response in 50-70 words
4. ✅ Check: Is Sambhav mention relevant? Add 1 line if yes
5. ✅ Count words - must be under 80
6. ✅ End with question or encouragement
7. ✅ Verify: No HTML, natural Hinglish, warm tone

---

**FINAL REMINDERS:**

🎯 **CONCISE** - 50-70 words, max 80
🎯 **HELPFUL** - Practical, actionable advice
🎯 **WARM** - Like a caring teacher
🎯 **SUBTLE** - Sambhav mention only when relevant (1 line)
🎯 **NATURAL** - Real conversation, not scripted

Now respond to the student's query naturally and concisely!
"""

            user_prompt = f"""Based on these similar questions and answers for context:
{context_text if context_text else "No relevant context found"}

Student's Question: {subject + ': ' if subject else ''}{query}

Remember:
- 50-70 words (max 80)
- Natural Hinglish
- Subtle Sambhav mention if relevant
- End with question/encouragement
- NO HTML, plain text only"""

            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500,
                top_p=0.9
            )

            if not response.choices:
                raise ValueError("No response choices from OpenAI")

            answer = response.choices[0].message.content.strip()
            logger.info("[GPT] Answer generated successfully")
            return answer

        except Exception as e:
            logger.error(f"[ERROR] GPT generation failed: {e}")
            return f"Beta, abhi kuch technical issue aa raha hai. Aap {WHATSAPP_NUMBER} par WhatsApp kar sakte hain! 🙏"

    def search_similar(self, user_query: str, subject: str = None, return_k: int = 3, language: str = 'hindi') -> List[Dict[str, str]]:
        """
        Search for similar questions and return Q&A pairs.
        Method compatible with original API.

        Args:
            user_query: User's question
            subject: Subject of the query
            return_k: Number of similar questions to find
            language: 'hindi' or 'english' for answer selection

        Returns:
            List of question-answer pairs
        """
        try:
            logger.info(f"[DEBUG] search_similar called with query: {user_query}")

            if not self.parquet_file_path or not os.path.exists(self.parquet_file_path):
                logger.warning("[WARN] Parquet file not configured or doesn't exist")
                return []

            # Find similar questions
            similar_response = self.find_similar_questions(user_query, subject, return_k)

            if not similar_response or 'results' not in similar_response:
                logger.warning("[WARN] find_similar_questions returned None or invalid response")
                return []

            similar_questions = similar_response['results'][:return_k]
            logger.info(f"[DEBUG] Found {len(similar_questions)} similar questions")

            # Extract context from parquet with language parameter
            context = self.search_questions_in_parquet(similar_questions, language)
            logger.info(f"[DEBUG] Retrieved {len(context)} context items from parquet")

            return context

        except ValueError as ve:
            if "Insufficient similar questions found" in str(ve):
                logger.info(f"[EARLY EXIT] {ve}")
                return []
            else:
                logger.error(f"[ERROR] search_similar failed with ValueError: {ve}")
                return []
        except Exception as e:
            logger.error(f"[ERROR] search_similar failed: {e}")
            return []


# Global processor instance
query_processor = QueryProcessor()


def ask_arivihan_question(query: str, subject: str, language: str = "hindi") -> Dict[str, Any]:
    """
    Main function to process guidance queries.

    Args:
        query: User's question
        subject: Subject of the query
        language: Response language (hindi or english)

    Returns:
        Dict with response text and metadata
    """
    try:
        logger.info(f"[ask_arivihan_question] Processing query: {query[:100]}...")
        logger.info(f"[ask_arivihan_question] Subject: {subject}, Language: {language}")

        # Find similar questions and get context
        context = []
        try:
            context = query_processor.search_similar(query, subject, return_k=3, language=language)
        except Exception as e:
            logger.warning(f"[WARN] Similarity search skipped: {e}")

        # Generate answer with context and subject
        answer_text = query_processor.generate_answer(query, context, subject, language)

        # Check for WhatsApp trigger
        open_whatsapp = any(kw in answer_text.lower() for kw in
                           ['contact', 'support', 'whatsapp', 'संपर्क', 'सहायता', WHATSAPP_NUMBER])

        response = {
            "text": answer_text,
            "queryType": "guidance_related",
            "openWhatsapp": open_whatsapp
        }

        logger.info("[ask_arivihan_question] Response generated successfully")
        return response

    except Exception as e:
        logger.error(f"[ask_arivihan_question] Error: {e}")
        return {
            "text": f"Beta, abhi kuch issue aa raha hai. Aap {WHATSAPP_NUMBER} par WhatsApp kar sakte hain! 🙏",
            "queryType": "guidance_related",
            "openWhatsapp": True
        }


def guidance_main(json_data: Dict[str, Any], initial_classification: str) -> Dict[str, Any]:
    """
    Main entry point for guidance processing.

    Args:
        json_data: Request data with message, subject, language
        initial_classification: Classification result

    Returns:
        Complete response dict with classification and response
    """
    try:
        query = json_data.get("message", json_data.get("userQuery", ""))
        subject = json_data.get("subject", "General")
        raw_language = json_data.get("language", "hindi")
        
        # Normalize language
        language = raw_language.lower() if raw_language else "hindi"
        if language == "hindlish":
            language = "hindi"

        logger.info(f"[guidance_main] Processing guidance query")
        logger.info(f"[guidance_main] Query: {query[:100]}...")
        logger.info(f"[guidance_main] Subject: {subject}, Language: {language}")

        # Generate response
        response_data = ask_arivihan_question(query, subject, language)

        result = {
            "classifiedAs": initial_classification,
            "response": response_data,
            "openWhatsapp": response_data.get("openWhatsapp", False)
        }

        logger.info("[guidance_main] Guidance response completed")
        return result

    except Exception as e:
        logger.error(f"[guidance_main] Error: {e}")
        import traceback
        logger.error(f"[guidance_main] Traceback: {traceback.format_exc()}")
        return {
            "classifiedAs": initial_classification,
            "response": {
                "text": f"Beta, kuch error aa gaya. Aap {WHATSAPP_NUMBER} par WhatsApp kar sakte hain! 🙏",
                "queryType": "guidance_related",
                "openWhatsapp": True
            },
            "openWhatsapp": True
        }


def normalize(text: str) -> str:
    """Normalize text for comparison."""
    try:
        if not text:
            return ""
        text = re.sub(r"[^\w\s]", "", text.lower().strip())
        return text
    except Exception as e:
        logger.error(f"[ERROR] Error in normalize function: {e}")
        return ""