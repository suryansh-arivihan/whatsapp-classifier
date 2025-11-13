"""
Handler for conversation-based queries.
Handles casual greetings, thanks, and social interactions.
Uses local ConversationProcessor instead of external API.
"""
from typing import Dict, Any
from app.services.handlers.base_handler import BaseResponseHandler
from app.core.logging_config import logger
from app.services.conversation_processor import conversation_main


class ConversationHandler(BaseResponseHandler):
    """Handler for conversation-based classification responses using local processor."""

    def __init__(self):
        """Initialize the conversation handler."""
        pass

    async def handle(self, query: str, classification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate conversation response for the query using local processor.

        Args:
            query: The user's query (translated if needed)
            classification_data: Dict containing classification details

        Returns:
            Dict with response data
        """
        try:
            logger.info(f"[ConversationHandler] Processing query locally: {query[:100]}...")

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
                "requestType": "text",
                "subject": classification_data.get("subject"),
                "language": language
            }

            # Get classification type
            initial_classification = classification_data.get("main_classification", "conversation")

            # Process using local conversation processor
            processor_response = conversation_main(json_data, initial_classification)

            # Wrap the processor response
            response = {
                "status": "success",
                "data": processor_response,
                "message": "Conversation response generated successfully (local)",
                "metadata": {
                    "subject": classification_data.get("subject"),
                    "language": classification_data.get("language"),
                    "processor": "local"
                }
            }

            logger.info(f"[ConversationHandler] Local response generated successfully")
            return response

        except Exception as e:
            logger.error(f"[ConversationHandler] Error generating local response: {e}")
            return {
                "status": "error",
                "data": None,
                "message": f"Failed to generate conversation response: {str(e)}"
            }


# Global handler instance
conversation_handler = ConversationHandler()
