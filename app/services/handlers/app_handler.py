"""
Handler for app-related queries.
Routes to app_related_classifier for proper sub-classification:
- screen_data_related: Navigation/how-to questions -> app_screen_related_main
- app_data_related: Content requests -> content templates
- subscription_data_related: Pricing/plans -> subscription template
"""
from typing import Dict, Any
from app.services.handlers.base_handler import BaseResponseHandler
from app.core.logging_config import logger
from app.services.app_related_classifier import app_related_classifier_main


class AppHandler(BaseResponseHandler):
    """Handler for app-related classification responses using sub-classification routing."""

    async def handle(self, query: str, classification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route app-related queries through app_related_classifier for sub-classification.

        Args:
            query: The user's query (translated if needed)
            classification_data: Dict containing classification details

        Returns:
            Dict with response data
        """
        try:
            logger.info(f"[AppHandler] Routing to app_related_classifier for sub-classification...")

            # Prepare json_data for app_related_classifier_main
            json_data = {
                "userQuery": query,
                "message": query,
                "subject": classification_data.get("subject"),
                "language": classification_data.get("language", "hindi"),
                "requestType": "text"
            }

            # Get initial classification
            initial_classification = classification_data.get("classification", "app_related")

            # Get phone_number from classification_data (use as user_id for app classifier)
            phone_number = classification_data.get("phone_number", "unknown")

            # Route through app_related_classifier_main for proper sub-classification
            # This will automatically route to:
            # - screen_data_related -> app_screen_related_main (GPT-based FAQ)
            # - app_data_related -> content templates
            # - subscription_data_related -> subscription message
            result = await app_related_classifier_main(json_data, phone_number, initial_classification)

            # Wrap the result in the expected handler response format
            response = {
                "status": "success",
                "data": result,
                "message": "App-related response generated via classifier routing",
                "metadata": {
                    "subject": classification_data.get("subject"),
                    "language": classification_data.get("language"),
                    "classified_as": result.get("classifiedAs"),
                    "processor": "app_related_classifier"
                }
            }

            logger.info(f"[AppHandler] Classifier routing completed: {result.get('classifiedAs')}")
            return response

        except Exception as e:
            logger.error(f"[AppHandler] Error in classifier routing: {e}")
            return {
                "status": "error",
                "data": None,
                "message": f"Failed to route app-related query: {str(e)}"
            }


# Global handler instance
app_handler = AppHandler()
