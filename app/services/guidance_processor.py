"""
Local guidance query processor using OpenAI vector store and Parquet file.
Handles guidance queries without external API calls.
"""
import os
import json
import re
from typing import Dict, Any, List, Optional
import pandas as pd
from openai import OpenAI
from app.core.logging_config import logger
from app.core.config import settings


class QueryProcessor:
    """Process guidance queries using vector store and Parquet file."""

    def __init__(self):
        """Initialize the query processor with OpenAI client."""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.parquet_file_path = os.getenv("PARQUET_FILE_PATH")
        self.vector_store_id = os.getenv("VECTOR_STORE_ID", "vs_68b97d5ff1d48191adc2165ceaa4f969")

        if not self.parquet_file_path:
            logger.warning("[QueryProcessor] PARQUET_FILE_PATH not set in environment")

    def find_similar_questions(self, query: str, top_k: int = 3) -> List[str]:
        """
        Find similar questions using OpenAI vector store.

        Args:
            query: User's question
            top_k: Number of similar questions to return

        Returns:
            List of similar question IDs
        """
        try:
            response = self.client.responses.create(
                model="gpt-4.1-mini",
                modalities=["text"],
                messages=[
                    {
                        "role": "user",
                        "content": f"Find similar questions to: {query}"
                    }
                ],
                tools=[
                    {
                        "type": "file_search",
                        "file_search": {
                            "vector_stores": [{"id": self.vector_store_id}],
                            "max_num_results": top_k
                        }
                    }
                ]
            )

            similar_ids = []
            for choice in response.choices:
                if hasattr(choice.message, 'annotations'):
                    for annotation in choice.message.annotations:
                        if hasattr(annotation, 'file_citation'):
                            file_id = annotation.file_citation.file_id
                            similar_ids.append(file_id)

            logger.info(f"[QueryProcessor] Found {len(similar_ids)} similar questions")
            return similar_ids[:top_k]

        except Exception as e:
            logger.error(f"[QueryProcessor] Error finding similar questions: {e}")
            return []

    def search_questions_in_parquet(self, question_ids: List[str]) -> List[Dict[str, str]]:
        """
        Search for questions in Parquet file by IDs.

        Args:
            question_ids: List of question IDs to search for

        Returns:
            List of dicts with question and answer
        """
        try:
            if not self.parquet_file_path or not os.path.exists(self.parquet_file_path):
                logger.warning("[QueryProcessor] Parquet file not found")
                return []

            df = pd.read_parquet(self.parquet_file_path)
            results = []

            for qid in question_ids:
                matching_rows = df[df['id'] == qid]
                if not matching_rows.empty:
                    row = matching_rows.iloc[0]
                    results.append({
                        'question': row.get('question', ''),
                        'answer': row.get('answer', '')
                    })

            logger.info(f"[QueryProcessor] Found {len(results)} matching Q&A pairs")
            return results

        except Exception as e:
            logger.error(f"[QueryProcessor] Error reading Parquet file: {e}")
            return []

    def generate_answer_with_reasoning(
        self,
        query: str,
        similar_qa: List[Dict[str, str]],
        language: str = "Hindi"
    ) -> str:
        """
        Generate answer using similar Q&A pairs with reasoning.

        Args:
            query: User's original query
            similar_qa: List of similar question-answer pairs
            language: Response language (Hindi or English/Hinglish)

        Returns:
            HTML formatted answer string
        """
        try:
            # Build context from similar Q&A pairs
            context = ""
            for i, qa in enumerate(similar_qa, 1):
                context += f"\nExample {i}:\n"
                context += f"Q: {qa['question']}\n"
                context += f"A: {qa['answer']}\n"

            # Create prompt based on language
            if language.lower() == "hindi":
                system_prompt = """आप रितेश सर हैं, एक प्रिय और अनुभवी कक्षा 12वीं के शिक्षक और मार्गदर्शक। आपकी भूमिका बोर्ड परीक्षा की तैयारी कर रहे छात्रों को शैक्षिक मार्गदर्शन, भावनात्मक समर्थन और व्यावहारिक सलाह प्रदान करना है।

आपका शिक्षण दर्शन:
- आप प्रत्येक छात्र की सफलता और भलाई की गहराई से परवाह करते हैं
- आप बोर्ड परीक्षा के दौरान छात्रों के दबाव और तनाव को समझते हैं
- आप शैक्षिक मार्गदर्शन और भावनात्मक समर्थन दोनों प्रदान करते हैं
- आप धैर्यवान, उत्साहवर्धक हैं और हमेशा मदद के लिए उपलब्ध हैं

महत्वपूर्ण निर्देश:
1. हमेशा सरल सादे टेक्स्ट में जवाब दें (कोई HTML नहीं)
2. हमेशा हिंग्लिश (हिंदी + अंग्रेजी रोमन लिपि में) में जवाब दें - यह अनिवार्य है क्योंकि हम भारत में रहते हैं
3. बोल्ड टेक्स्ट के लिए single * का उपयोग करें (उदाहरण: *महत्वपूर्ण बिंदु*)
4. पठनीयता के लिए लाइन ब्रेक के साथ सरल फॉर्मेटिंग का उपयोग करें
5. उत्तर व्यावहारिक, विस्तृत और कार्यान्वित करने योग्य होने चाहिए

प्रतिक्रिया दिशानिर्देश:
- यदि प्रश्न शैक्षिक है: उदाहरणों के साथ स्पष्ट, चरण-दर-चरण मार्गदर्शन प्रदान करें
- यदि प्रश्न अस्पष्ट है या संदर्भ की कमी है: तार्किक तर्क का उपयोग करके अंतर्निहित चिंता को समझें और प्रासंगिक मार्गदर्शन प्रदान करें
- यदि कोई स्पष्ट शैक्षिक संदर्भ नहीं है: भावनात्मक समर्थन और प्रेरक मार्गदर्शन प्रदान करें, विशेष रूप से यह ध्यान में रखते हुए कि बोर्ड परीक्षा नजदीक आ रही है
- हमेशा छात्र की भावनाओं और चिंताओं को स्वीकार करें
- प्रोत्साहन और सकारात्मक पुष्टि के साथ प्रतिक्रिया समाप्त करें

उदाहरण प्रारूप:

*मुख्य विषय/शीर्षक*

बेटा, मैं समझ सकता हूं तुम्हें क्या समस्या आ रही है। चलो, इसको solve करते हैं...

*पहला बिंदु:*
- व्यावहारिक सुझावों के साथ हिंग्लिश में विस्तृत व्याख्या
- चरण-दर-चरण दृष्टिकोण जो आसानी से follow हो सके

*दूसरा बिंदु:*
- सरल भाषा में अधिक मार्गदर्शन
- वास्तविक उदाहरण जो relatable हों

याद रखना बेटा, तुमने पूरे साल मेहनत की है। अपने आप पर विश्वास रखो और focused रहो। Exams पास आ रहे हैं but तुम तैयार हो!

लहजा/टोन:
- गर्मजोशी भरा, सहायक और उत्साहवर्धक (एक देखभाल करने वाले भारतीय शिक्षक की तरह)
- वाक्यांशों का उपयोग करें जैसे "बेटा," "टेंशन मत लो," "मैं हूं ना मदद करने के लिए," "तुम कर सकते हो"
- हिंदी और अंग्रेजी को स्वाभाविक रूप से रोमन लिपि में मिलाएं
- भावनात्मक बुद्धिमत्ता के साथ शैक्षिक कठोरता को संतुलित करें
- परीक्षा के तनाव के प्रति सहानुभूति दिखाते हुए आशावाद बनाए रखें
- भाषा को संवादात्मक और समझने में आसान रखें
"""
            else:
                system_prompt = """You are Ritesh Sir, a warm and experienced Class 12th teacher who genuinely cares about students.

Your Natural Style:
- Talk like a real teacher, not a chatbot
- Use simple Hinglish (Hindi + English in Roman) - natural mixing
- Keep responses SHORT: 30-35 words maximum
- Be personal, warm, and encouraging
- React naturally to student's mood

Core Rules:
1. ALWAYS plain text (NO HTML tags)
2. ALWAYS Hinglish in Roman script
3. Use * only for emphasis (not for every word)
4. Short responses - like real conversation
5. End with question or encouragement

Response Length Guide:
- *Academic doubts*: 30-35 words (brief explanation + quick tip)
- *Guidance/advice*: 4-5 lines maximum (personal and natural)
- *Greetings/casual*: 2-3 lines only

Natural Conversation Examples:

*Academic Doubt:*
"Beta, ye concept simple hai! Dekho - [2-3 line explanation with example]. 
Practice karo 5-10 questions daily, confidence aa jayega. 
Samajh aa gaya? Koi confusion ho to batao!" 
(~30 words)

*Study Guidance:*
" beta, planning bahut zaroori hai! 
Subah tough subjects (PCM), dopahar theory, shaam revision. 
Daily 2-3 hours consistent practice karo, aur PYQs zaroor solve karo.
Tension mat lo, main hoon na help karne! Kaunse subject se start karein?" 
(~30 words)

*Emotional Support:*
"Beta, ghabrao mat! Ye stress normal hai.
Dekho, tumne 11 saal padhai ki hai - sab kuch aata hai tumhe.
Bas thoda organize karo aur daily thoda karo.
Main hoon na saath mein! Kya specific tension hai? Batao."
(~45 words)

*Greeting/Hello:*
"Namaste beta! Main Ritesh Sir. Kaise ho? 
Boards ki tayyari kaisi chal rahi hai? Batao, kya help chahiye?"
(~20 words)

Your Natural Phrases:
- " beta, ghabrao mat"
- "Dekho, main samjhata hoon"
- "Achha achha, ye wala!"
- "Beta, tension mat lo"
- "Chaliye samjhte hain"
- "Main hoon na tumhare saath"
- " waah! Bahut achha"
- "Thik hai, no problem"

Tone Guidelines:
- Be conversational, not scripted
- Match student's energy (stressed? calm them. excited? match it)
- Use "beta" naturally, not in every sentence
- Don't over-explain - keep it crisp
- Always end with question or next step

Critical Instructions:
✅ Maximum 30-35 words for academic explanations
✅ Maximum 4-5 lines for guidance/advice
✅ Maximum 2-3 lines for casual chat
✅ Sound human - vary your responses
✅ React to student's tone and mood
✅ No robotic templates or fixed formats
✅ Use simple * for emphasis only when needed

Remember:
- You're a real teacher, not an AI
- Keep it short and natural
- Be warm but not over-the-top
- Students trust you - be genuine
"""

            user_prompt = f"""Based on these similar questions and answers:
{context}

Please answer this question: {query}

Provide a comprehensive, well-structured answer in HTML format."""

            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            answer = response.choices[0].message.content.strip()
            logger.info("[QueryProcessor] Generated answer successfully")
            return answer

        except Exception as e:
            logger.error(f"[QueryProcessor] Error generating answer: {e}")
            # Return fallback response
            if language.lower() == "hindi":
                return "<h2>क्षमा करें</h2><p>इस समय आपके प्रश्न का उत्तर देने में कठिनाई हो रही है। कृपया बाद में पुनः प्रयास करें।</p>"
            else:
                return "<h2>Sorry</h2><p>We're having trouble answering your question at the moment. Please try again later.</p>"

    def search_similar(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
        """
        Search for similar questions and return Q&A pairs.

        Args:
            query: User's question
            top_k: Number of similar questions to find

        Returns:
            List of question-answer pairs
        """
        similar_ids = self.find_similar_questions(query, top_k)
        if similar_ids:
            return self.search_questions_in_parquet(similar_ids)
        return []

    def generate_answer(self, query: str, language: str = "Hindi") -> str:
        """
        Generate answer for query using similar Q&A pairs.

        Args:
            query: User's question
            language: Response language

        Returns:
            HTML formatted answer
        """
        similar_qa = self.search_similar(query)
        return self.generate_answer_with_reasoning(query, similar_qa, language)


# Global processor instance
query_processor = QueryProcessor()


def ask_arivihan_question(query: str, subject: str, language: str = "Hindi") -> Dict[str, Any]:
    """
    Main function to process guidance queries.

    Args:
        query: User's question
        subject: Subject of the query
        language: Response language (Hindi or English/Hinglish)

    Returns:
        Dict with response text and metadata
    """
    try:
        logger.info(f"[ask_arivihan_question] Processing query: {query[:100]}...")
        logger.info(f"[ask_arivihan_question] Subject: {subject}, Language: {language}")

        # Generate answer using query processor
        answer_html = query_processor.generate_answer(query, language)

        # Determine if WhatsApp should open based on content
        # Open WhatsApp if the response suggests contacting support
        open_whatsapp = False
        if any(keyword in answer_html.lower() for keyword in ['contact', 'support', 'help desk', 'संपर्क', 'सहायता']):
            open_whatsapp = True

        response = {
            "text": answer_html,
            "queryType": "guidance_related",
            "openWhatsapp": open_whatsapp
        }

        logger.info("[ask_arivihan_question] Response generated successfully")
        return response

    except Exception as e:
        logger.error(f"[ask_arivihan_question] Error: {e}")
        # Return fallback response
        if language.lower() == "hindi":
            fallback = "<h2>क्षमा करें</h2><p>इस समय आपके प्रश्न का उत्तर देने में कठिनाई हो रही है। कृपया बाद में पुनः प्रयास करें।</p>"
        else:
            fallback = "<h2>Sorry</h2><p>We're having trouble answering your question at the moment. Please try again later.</p>"

        return {
            "text": fallback,
            "queryType": "guidance_related",
            "openWhatsapp": False
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
        query = json_data.get("message", "")
        subject = json_data.get("subject", "General")
        # Normalize language to API format (only "english" or "hindi" accepted)
        raw_language = json_data.get("language", "hindi")
        language = raw_language.lower() if raw_language else "hindi"
        # Map hindlish to hindi since API only accepts english/hindi
        if language == "hindlish":
            language = "hindi"

        logger.info(f"[guidance_main] Processing guidance query")

        # Generate response using ask_arivihan_question
        response_data = ask_arivihan_question(query, subject, language)

        # Build final response
        result = {
            "classifiedAs": initial_classification,
            "response": response_data,
            "openWhatsapp": response_data.get("openWhatsapp", False)
        }

        logger.info("[guidance_main] Guidance response completed")
        return result

    except Exception as e:
        logger.error(f"[guidance_main] Error: {e}")
        return {
            "classifiedAs": initial_classification,
            "response": {
                "text": "<h2>Error</h2><p>Unable to process your guidance query.</p>",
                "queryType": "guidance_related",
                "openWhatsapp": False
            },
            "openWhatsapp": False
        }
