"""
Handler for conversation-based queries.
Handles casual greetings, thanks, and social interactions.
Uses local ConversationProcessor instead of external API.
"""
from typing import Dict, Any
from app.services.handlers.base_handler import BaseResponseHandler
from app.core.logging_config import logger
from app.services.conversation_processor import conversation_main
from app.services.history_service import history_service


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

            # Check if this is the user's first message by checking conversation history
            first_message = True  # Default to True if we can't determine
            phone_number = classification_data.get("phone_number")

            if phone_number:
                try:
                    history = await history_service.get_conversation_history(phone_number, limit=1)
                    # If user has any previous messages, it's not their first message
                    first_message = history.total_count == 0
                    logger.info(f"[ConversationHandler] User {phone_number} has {history.total_count} previous messages, first_message={first_message}")
                except Exception as e:
                    logger.warning(f"[ConversationHandler] Could not check conversation history: {e}, assuming first_message=True")
            else:
                logger.info(f"[ConversationHandler] No phone_number provided, assuming first_message=True")

            # Process using local conversation processor
            processor_response = conversation_main(json_data, initial_classification, first_message)

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
