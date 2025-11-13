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
                model="gpt-4o-mini",
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
                system_prompt = """आप एक शैक्षिक मार्गदर्शन सहायक हैं। उपयोगकर्ता के प्रश्न का उत्तर दें।

महत्वपूर्ण निर्देश:
1. उत्तर HTML format में दें
2. Main headings के लिए <h2> tags का उपयोग करें
3. Sub-headings के लिए <h3> tags का उपयोग करें
4. Points के लिए <ul> और <li> tags का उपयोग करें
5. Important text के लिए <strong> या <b> tags का उपयोग करें
6. हमेशा शुद्ध हिंदी में जवाब दें
7. जवाब व्यावहारिक और विस्तृत होना चाहिए

उदाहरण Format:
<h2>मुख्य शीर्षक</h2>
<p>परिचय या संक्षिप्त विवरण...</p>

<h3>उप-शीर्षक 1</h3>
<ul>
<li><strong>बिंदु 1:</strong> विवरण...</li>
<li><strong>बिंदु 2:</strong> विवरण...</li>
</ul>

<h3>उप-शीर्षक 2</h3>
<p>अधिक जानकारी...</p>
"""
            else:
                system_prompt = """You are an educational guidance assistant. Answer the user's question.

Important Instructions:
1. Provide answer in HTML format
2. Use <h2> tags for main headings
3. Use <h3> tags for sub-headings
4. Use <ul> and <li> tags for bullet points
5. Use <strong> or <b> tags for important text
6. Always respond in English or Hinglish
7. Answer should be practical and detailed

Example Format:
<h2>Main Heading</h2>
<p>Introduction or brief description...</p>

<h3>Sub-heading 1</h3>
<ul>
<li><strong>Point 1:</strong> Description...</li>
<li><strong>Point 2:</strong> Description...</li>
</ul>

<h3>Sub-heading 2</h3>
<p>More information...</p>
"""

            user_prompt = f"""Based on these similar questions and answers:
{context}

Please answer this question: {query}

Provide a comprehensive, well-structured answer in HTML format."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
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
