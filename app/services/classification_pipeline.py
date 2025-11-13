"""
Classification pipeline orchestrator.
Coordinates the complete classification flow:
1. Subject & Language Detection
2. Translation (if needed)
3. Main Classification
4. Exam Sub-Classification (if exam_related_info)
5. Response Generation (via appropriate handler)
"""
import time
from typing import Optional
from app.core.logging_config import logger
from app.models.schemas import ClassificationResponse, LanguageType
from app.services.subject_language_detector import SubjectLanguageDetector
from app.services.translator import translate_query
from app.services.main_classifier import initial_main_classifier
from app.services.exam_classifier import exam_related_main_classifier
from app.utils.exceptions import ClassificationError

# Import all handlers
from app.services.handlers.guidance_handler import guidance_handler
from app.services.handlers.conversation_handler import conversation_handler
from app.services.handlers.exam_handler import exam_handler
from app.services.handlers.app_handler import app_handler
from app.services.handlers.subject_handler import subject_handler
from app.services.handlers.complaint_handler import complaint_handler


class ClassificationPipeline:
    """Orchestrates the complete classification pipeline."""

    def __init__(self):
        """Initialize the pipeline with required services."""
        self.subject_language_detector = SubjectLanguageDetector()

        # Map classification types to handlers
        self.handlers = {
            "guidance_based": guidance_handler,
            "conversation_based": conversation_handler,
            "exam_related_info": exam_handler,
            "app_related": app_handler,
            "subject_related": subject_handler,
            "complaint": complaint_handler
        }

    async def classify(self, message: str) -> ClassificationResponse:
        """
        Execute the complete classification pipeline.

        Args:
            message: User query message

        Returns:
            ClassificationResponse with all classification details

        Raises:
            ClassificationError: If any step in the pipeline fails
        """
        start_time = time.time()

        try:
            logger.info(f"[Pipeline] Starting classification for message: {message[:100]}...")

            # Step 1: Detect subject and language
            detection_result = self.subject_language_detector.detect(message)
            subject = detection_result.get("subject")
            language = detection_result.get("language")

            logger.info(f"[Pipeline] Detection - Subject: {subject}, Language: {language}")

            # Step 2: Translate if needed (Hindi or Hinglish)
            translated_message = None
            query_to_classify = message

            if language in [LanguageType.HINDI.value, LanguageType.HINGLISH.value]:
                logger.info(f"[Pipeline] Translating from {language} to English...")
                try:
                    translated_message = translate_query(message, stream="pcmb")
                    query_to_classify = translated_message
                    logger.info(f"[Pipeline] Translation completed: {translated_message[:100]}...")
                except Exception as e:
                    logger.warning(f"[Pipeline] Translation failed: {e}, proceeding with original message")
                    # If translation fails, continue with original message
                    query_to_classify = message

            # Step 3: Main classification
            logger.info(f"[Pipeline] Running main classification...")
            main_classification = initial_main_classifier(query_to_classify)
            logger.info(f"[Pipeline] Main classification: {main_classification}")

            # Step 4: Exam sub-classification (if exam_related_info)
            sub_classification = None
            if main_classification == "exam_related_info":
                logger.info(f"[Pipeline] Running exam sub-classification...")
                try:
                    sub_classification = exam_related_main_classifier(query_to_classify)
                    logger.info(f"[Pipeline] Exam sub-classification: {sub_classification}")
                except Exception as e:
                    logger.error(f"[Pipeline] Exam sub-classification failed: {e}")
                    # Continue without sub-classification if it fails
                    sub_classification = None

            # Step 5: Generate response using appropriate handler
            logger.info(f"[Pipeline] Generating response with handler...")
            response_data = None

            handler = self.handlers.get(main_classification)
            if handler:
                try:
                    classification_data = {
                        "classification": main_classification,
                        "sub_classification": sub_classification,
                        "subject": subject,
                        "language": language,
                        "original_message": message,
                        "translated_message": translated_message
                    }

                    response_data = await handler.handle(query_to_classify, classification_data)
                    logger.info(f"[Pipeline] Handler response: {response_data.get('status')}")
                except Exception as e:
                    logger.error(f"[Pipeline] Handler execution failed: {e}")
                    response_data = {
                        "status": "error",
                        "message": f"Handler failed: {str(e)}"
                    }
            else:
                logger.warning(f"[Pipeline] No handler found for classification: {main_classification}")

            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            # Build response
            response = ClassificationResponse(
                classification=main_classification,
                sub_classification=sub_classification,
                subject=subject,
                language=language,
                original_message=message,
                translated_message=translated_message,
                confidence_score=0.85,  # Placeholder, can be enhanced later
                response_data=response_data,
                processing_time_ms=processing_time
            )

            logger.info(f"[Pipeline] Classification completed in {processing_time:.2f}ms")
            return response

        except Exception as e:
            logger.error(f"[Pipeline] Classification pipeline failed: {e}")
            raise ClassificationError(f"Pipeline execution failed: {e}")


# Global pipeline instance
pipeline = ClassificationPipeline()


async def classify_message(message: str) -> ClassificationResponse:
    """
    Main entry point for classification.

    Args:
        message: User query message

    Returns:
        ClassificationResponse with complete classification details
    """
    return await pipeline.classify(message)
