"""
Handler for app-related queries.
Handles questions about app features, navigation, pricing, subscriptions, etc.
Also includes content classification for lectures, notes, tests.
Uses local content response templates.
"""
from typing import Dict, Any
from app.services.handlers.base_handler import BaseResponseHandler
from app.core.logging_config import logger
from app.services.content_classifier import simple_classify
from app.services.content_responses import app_content_main


class AppHandler(BaseResponseHandler):
    """Handler for app-related classification responses using local templates."""

    def __init__(self):
        """Initialize the app handler."""
        pass

    async def handle(self, query: str, classification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate app-related response for the query using local templates.
        Performs content classification for lecture/notes/test requests.

        Args:
            query: The user's query (translated if needed)
            classification_data: Dict containing classification details

        Returns:
            Dict with response data
        """
        try:
            logger.info(f"[AppHandler] Processing query locally: {query[:100]}...")

            # Classify the content type (lecture, notes, test, etc.)
            content_type = None
            try:
                content_type = simple_classify(query)
                logger.info(f"[AppHandler] Content type: {content_type}")
            except Exception as e:
                logger.warning(f"[AppHandler] Content classification failed: {e}")
                # Default to lecture if classification fails
                content_type = "lecture"

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
                "subject": classification_data.get("subject"),
                "language": language
            }

            # Get classification type
            initial_classification = classification_data.get("main_classification", "app_related")

            # Process using local content response generator
            processor_response = app_content_main(json_data, initial_classification, content_type)

            # Wrap the processor response
            response = {
                "status": "success",
                "data": processor_response,
                "message": "App-related response generated successfully (local)",
                "metadata": {
                    "subject": classification_data.get("subject"),
                    "language": classification_data.get("language"),
                    "content_type": content_type,
                    "processor": "local"
                }
            }

            logger.info(f"[AppHandler] Local response generated successfully")
            return response

        except Exception as e:
            logger.error(f"[AppHandler] Error generating local response: {e}")
            return {
                "status": "error",
                "data": None,
                "message": f"Failed to generate app-related response: {str(e)}"
            }


# Global handler instance
app_handler = AppHandler()
