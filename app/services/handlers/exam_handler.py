"""
Handler for exam-related queries.
Handles exam patterns, PYQs, important questions, syllabus, etc.
Formats responses using GPT for better readability.
"""
from typing import Dict, Any
from app.services.handlers.base_handler import BaseResponseHandler
from app.core.logging_config import logger
from app.utils.api_client import external_api_client
from app.services.exam_formatter import format_exam_response
from app.services.content_responses import CONTENT_RESPONSES
from app.services.exam_faq_query import exam_faq_query_main


class ExamHandler(BaseResponseHandler):
    """Handler for exam-related classification responses with GPT formatting."""

    def __init__(self):
        """Initialize the exam handler."""
        self.api_client = external_api_client
        self.endpoint = "/exam/query/classifier"

    async def handle(self, query: str, classification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate exam-related response for the query by calling external API.
        Formats PYQ questions using GPT for WhatsApp readability.

        Args:
            query: The user's query (translated if needed)
            classification_data: Dict containing classification details (including sub_classification)

        Returns:
            Dict with response data and formatted message
        """
        try:
            logger.info(f"[ExamHandler] Processing query: {query[:100]}...")
            logger.info(f"[ExamHandler] Sub-classification: {classification_data.get('sub_classification')}")

            # Normalize language to API format (only "english" or "hindi" accepted)
            raw_language = classification_data.get("language", "hindi")
            language = raw_language.lower() if raw_language else "hindi"
            # Map hindlish to hindi since API only accepts english/hindi
            if language == "hindlish":
                language = "hindi"
            subject = classification_data.get("subject", "General")
            sub_classification = classification_data.get("sub_classification")

            # Check if this is an "asking_important_question" query
            # If yes, return the template directly without calling external API
            if sub_classification == "asking_important_question":
                logger.info("[ExamHandler] Detected asking_important_question - using local template")

                # Determine language key for template (hinglish or hindi)
                lang_key = "hindi" if language == "hindi" else "hinglish"

                # Get the important_questions template
                if "important_questions" in CONTENT_RESPONSES:
                    response_text = CONTENT_RESPONSES["important_questions"][lang_key]

                    # Build response with the template
                    response = {
                        "status": "success",
                        "data": {
                            "classifiedAs": "exam_related_info",
                            "sub_classification": "asking_important_question",
                            "response": response_text,
                            "openWhatsapp": False,
                            "responseType": "text",
                            "source": "local_template"
                        },
                        "message": "Important questions response generated from local template",
                        "metadata": {
                            "subject": classification_data.get("subject"),
                            "language": classification_data.get("language"),
                            "sub_classification": sub_classification,
                            "source": "local_template"
                        }
                    }

                    logger.info("[ExamHandler] Important questions template returned successfully")
                    return response
                else:
                    logger.warning("[ExamHandler] important_questions template not found in CONTENT_RESPONSES")

            # Check if this is a "faq" query
            # If yes, handle it locally using exam_faq_query.py
            if sub_classification == "faq":
                logger.info("[ExamHandler] Detected FAQ - using local exam_faq_query handler")

                # Prepare payload for FAQ handler
                faq_payload = {
                    "userQuery": query,
                    "subject": subject,
                    "language": language,
                    "requestType": "text"
                }

                # Call local FAQ handler
                faq_result = exam_faq_query_main(faq_payload, "exam_related_info")

                # Extract response from FAQ result
                faq_response = faq_result.get("response", "")
                open_whatsapp = faq_result.get("openWhatsapp", False)

                # Build response
                response = {
                    "status": "success",
                    "data": {
                        "classifiedAs": "exam_related_info",
                        "sub_classification": "faq",
                        "response": faq_response,
                        "openWhatsapp": open_whatsapp,
                        "responseType": "text",
                        "source": "local_faq_handler"
                    },
                    "message": "FAQ response generated from local handler",
                    "metadata": {
                        "subject": classification_data.get("subject"),
                        "language": classification_data.get("language"),
                        "sub_classification": sub_classification,
                        "source": "local_faq_handler"
                    }
                }

                logger.info(f"[ExamHandler] FAQ response returned successfully (openWhatsapp: {open_whatsapp})")
                return response

            # Generate a chat session ID (in production, this should come from your system)
            import uuid
            chat_session_id = str(uuid.uuid4())

            # Prepare payload for external API
            payload = self.api_client.get_base_payload(
                subject=subject,
                user_query=query,
                language=language
            )

            # Add sub-classification info to payload if available
            if sub_classification:
                payload["examSubType"] = sub_classification

            # Call external exam API
            logger.info("[ExamHandler] Calling exam query classifier API")
            api_response = await self.api_client.call_endpoint(
                endpoint=self.endpoint,
                payload=payload
            )

            # Format the response using GPT (for PYQ questions and PDF resources)
            # The formatter will detect pyq_pdf and fetch additional resources from /app/related/classifier
            formatted_data = await format_exam_response(
                api_response,
                language,
                user_query=query,
                subject=subject,
                chat_session_id=chat_session_id
            )

            # Wrap the external API response
            response = {
                "status": "success",
                "data": formatted_data,
                "message": "Exam-related response generated successfully",
                "metadata": {
                    "subject": classification_data.get("subject"),
                    "language": classification_data.get("language"),
                    "sub_classification": classification_data.get("sub_classification"),
                    "endpoint": self.endpoint,
                    "formatted": formatted_data.get("has_formatted_response", False)
                }
            }

            logger.info(f"[ExamHandler] Response generated successfully (formatted: {formatted_data.get('has_formatted_response', False)})")
            return response

        except Exception as e:
            logger.error(f"[ExamHandler] Error generating response: {e}")
            return {
                "status": "error",
                "data": None,
                "message": f"Failed to generate exam-related response: {str(e)}"
            }


# Global handler instance
exam_handler = ExamHandler()
