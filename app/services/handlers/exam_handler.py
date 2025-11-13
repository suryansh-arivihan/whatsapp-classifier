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
