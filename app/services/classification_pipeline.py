"""
Classification pipeline orchestrator.
Coordinates the complete classification flow:
1. Follow-up Detection & Context Enrichment (if history exists)
2. Subject & Language Detection
3. Translation (if needed)
4. Main Classification
5. Exam Sub-Classification (if exam_related_info)
6. Response Generation (via appropriate handler)
"""
import time
from typing import Optional
from app.core.logging_config import logger
from app.models.schemas import ClassificationResponse, LanguageType
from app.services.subject_language_detector import SubjectLanguageDetector
from app.services.translator import translate_query
from app.services.main_classifier import initial_main_classifier
from app.services.exam_classifier import exam_related_main_classifier
from app.services.followup_detector import followup_detector
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

    async def classify(self, message: str, phone_number: Optional[str] = None) -> ClassificationResponse:
        """
        Execute the complete classification pipeline.

        Args:
            message: User query message
            phone_number: User's phone number for history tracking (optional)

        Returns:
            ClassificationResponse with all classification details

        Raises:
            ClassificationError: If any step in the pipeline fails
        """
        start_time = time.time()
        is_follow_up = False
        original_message = message

        try:
            logger.info(f"[Pipeline] Starting classification for message: {message[:100]}...")

            # Step 0: Follow-up detection and context enrichment
            if phone_number:
                logger.info(f"[Pipeline] Checking follow-up for phone: {phone_number}")
                followup_result = await followup_detector.detect_and_enrich(message, phone_number)

                # Check if user wants to stop conversation
                if followup_result.should_stop_conversation:
                    logger.info(f"[Pipeline] User requested to stop conversation, returning empty response")
                    processing_time = (time.time() - start_time) * 1000
                    return ClassificationResponse(
                        classification="conversation_based",
                        sub_classification="stop_conversation",
                        subject=None,
                        language="hindi",
                        original_message=original_message,
                        translated_message=None,
                        confidence_score=1.0,
                        response_data={
                            "status": "success",
                            "message": "",  # Empty response as requested
                            "data": None,
                            "metadata": {
                                "is_follow_up": False,
                                "original_message": original_message,
                                "stop_conversation": True
                            }
                        },
                        processing_time_ms=processing_time
                    )

                if followup_result.is_follow_up and followup_result.enriched_message:
                    logger.info(
                        f"[Pipeline] Follow-up detected! "
                        f"Original: '{message}' -> "
                        f"Enriched: '{followup_result.enriched_message}'"
                    )
                    message = followup_result.enriched_message  # Use enriched message
                    is_follow_up = True
                else:
                    logger.info(f"[Pipeline] Not a follow-up, using original message")
            else:
                logger.info(f"[Pipeline] No phone_number provided, skipping follow-up detection")

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
                        "translated_message": translated_message,
                        "phone_number": phone_number  # Add phone_number for handlers
                    }

                    response_data = await handler.handle(query_to_classify, classification_data)
                    logger.info(f"[Pipeline] Handler response status: {response_data.get('status')}")
                    logger.info(f"[Pipeline] ========== HANDLER RESPONSE STRUCTURE ==========")
                    logger.info(f"[Pipeline] Keys in response_data: {list(response_data.keys())}")
                    logger.info(f"[Pipeline] Status: {response_data.get('status')}")
                    logger.info(f"[Pipeline] Message: {response_data.get('message')}")
                    if response_data.get('data'):
                        logger.info(f"[Pipeline] Data keys: {list(response_data['data'].keys()) if isinstance(response_data['data'], dict) else 'Not a dict'}")
                        logger.info(f"[Pipeline] Data content preview: {str(response_data['data'])[:200]}...")
                    logger.info(f"[Pipeline] ==================================================")
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

            # Add follow-up flag to response_data metadata if it exists
            if response_data and isinstance(response_data, dict):
                if 'metadata' not in response_data:
                    response_data['metadata'] = {}
                response_data['metadata']['is_follow_up'] = is_follow_up
                response_data['metadata']['original_message'] = original_message

            # Build response
            response = ClassificationResponse(
                classification=main_classification,
                sub_classification=sub_classification,
                subject=subject,
                language=language,
                original_message=original_message,  # Use actual original message
                translated_message=translated_message,
                confidence_score=0.85,  # Placeholder, can be enhanced later
                response_data=response_data,
                processing_time_ms=processing_time
            )

            logger.info(f"[Pipeline] ========== FINAL CLASSIFICATIONRESPONSE ==========")
            logger.info(f"[Pipeline] Classification: {response.classification}")
            logger.info(f"[Pipeline] Sub-classification: {response.sub_classification}")
            logger.info(f"[Pipeline] Subject: {response.subject}")
            logger.info(f"[Pipeline] Language: {response.language}")
            logger.info(f"[Pipeline] Response_data status: {response.response_data.get('status') if response.response_data else None}")
            logger.info(f"[Pipeline] Response_data keys: {list(response.response_data.keys()) if response.response_data else None}")
            logger.info(f"[Pipeline] Processing time: {processing_time:.2f}ms")
            logger.info(f"[Pipeline] =====================================================")

            return response

        except Exception as e:
            logger.error(f"[Pipeline] Classification pipeline failed: {e}")
            raise ClassificationError(f"Pipeline execution failed: {e}")


# Global pipeline instance
pipeline = ClassificationPipeline()


async def classify_message(message: str, phone_number: Optional[str] = None) -> ClassificationResponse:
    """
    Main entry point for classification.

    Args:
        message: User query message
        phone_number: User's phone number for history tracking (optional)

    Returns:
        ClassificationResponse with complete classification details
    """
    return await pipeline.classify(message, phone_number)
