"""
Handler for subject-related queries.
Handles academic questions about specific topics, concepts, formulas, or problem-solving.
Uses local SubjectProcessor for board and conceptual solutions.
"""
from typing import Dict, Any
from app.services.handlers.base_handler import BaseResponseHandler
from app.core.logging_config import logger
from app.services.subject_processor import subject_main


class SubjectHandler(BaseResponseHandler):
    """Handler for subject-related classification responses using local processor."""

    def __init__(self):
        """Initialize the subject handler."""
        pass

    async def handle(self, query: str, classification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate subject-related response for the query using local processor.

        Args:
            query: The user's query (translated if needed)
            classification_data: Dict containing classification details

        Returns:
            Dict with response data
        """
        try:
            logger.info(f"[SubjectHandler] Processing query locally: {query[:100]}...")

            # Prepare data for local processor
            # Normalize language to API format (only "english" or "hindi" accepted)
            raw_language = classification_data.get("language", "hindi")
            language = raw_language.lower() if raw_language else "hindi"
            # Map hindlish to hindi since API only accepts english/hindi
            if language == "hindlish":
                language = "hindi"

            json_data = {
                "message": query,
                "userQuery": query,
                "subject": classification_data.get("subject", "General"),
                "language": language
            }

            # Get classification type
            initial_classification = classification_data.get("main_classification", "subject_related")

            # Process using local subject processor
            processor_response = await subject_main(json_data, initial_classification)

            # Wrap the processor response
            response = {
                "status": "success",
                "data": processor_response,
                "message": "Subject doubt response generated successfully (local)",
                "metadata": {
                    "subject": classification_data.get("subject"),
                    "language": classification_data.get("language"),
                    "processor": "local"
                }
            }

            logger.info(f"[SubjectHandler] Local response generated successfully")
            return response

        except Exception as e:
            logger.error(f"[SubjectHandler] Error generating local response: {e}")
            return {
                "status": "error",
                "data": None,
                "message": f"Failed to generate subject-related response: {str(e)}"
            }


# Global handler instance
subject_handler = SubjectHandler()
