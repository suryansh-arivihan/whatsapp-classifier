"""
API routes for the classification service.
"""
import time
import asyncio
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import (
    ClassificationRequest,
    ClassificationResponse,
    HealthCheckResponse,
    ErrorResponse
)
from app.models.history_schemas import HistorySaveRequest
from app.core.config import settings
from app.core.logging_config import logger
from app.services.classification_pipeline import classify_message
from app.services.history_service import history_service
from app.utils.exceptions import ClassifierException
from app.utils.response_formatter import transform_to_simple_format


router = APIRouter()


async def _save_conversation_history(
    phone_number: str,
    request_message: str,
    full_response: ClassificationResponse
):
    """
    Save conversation history to DynamoDB asynchronously.

    Args:
        phone_number: User's phone number
        request_message: User's original message
        full_response: Full ClassificationResponse object
    """
    try:
        # Extract response message from response_data
        response_message = ""
        if full_response.response_data:
            # Try to get the formatted message from various possible locations
            if isinstance(full_response.response_data, dict):
                data = full_response.response_data.get("data", {})
                if isinstance(data, dict):
                    # Check for formatted_response first
                    response_message = data.get("formatted_response", "")
                    # If not found, try response.text
                    if not response_message and "response" in data:
                        response_obj = data.get("response", {})
                        if isinstance(response_obj, dict):
                            response_message = response_obj.get("text", "")

        # Get metadata for is_follow_up flag
        is_follow_up = False
        if full_response.response_data and isinstance(full_response.response_data, dict):
            metadata = full_response.response_data.get("metadata", {})
            if isinstance(metadata, dict):
                is_follow_up = metadata.get("is_follow_up", False)

        # Create save request
        timestamp = int(time.time() * 1000)
        ttl = int(time.time()) + (settings.history_retention_days * 24 * 60 * 60)

        save_request = HistorySaveRequest(
            phone_number=phone_number,
            timestamp=timestamp,
            request_message=request_message,
            response_message=response_message or "Response generated",
            classification=full_response.classification,
            sub_classification=full_response.sub_classification,
            subject=full_response.subject,
            language=full_response.language,
            is_follow_up=is_follow_up,
            processing_time_ms=full_response.processing_time_ms,
            ttl=ttl
        )

        # Save to DynamoDB
        success = await history_service.save_conversation(save_request)

        if success:
            logger.info(f"[API] Saved conversation history for {phone_number}")
        else:
            logger.warning(f"[API] Failed to save conversation history for {phone_number}")

    except Exception as e:
        logger.error(f"[API] Error saving conversation history: {e}")


@router.get("/", response_model=dict)
async def root():
    """
    Root endpoint - API information.
    """
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "endpoints": {
            "classification": "/classify",
            "health": "/health",
            "docs": "/docs"
        }
    }


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint to verify service status.
    """
    return HealthCheckResponse(
        status="healthy",
        version=settings.api_version
    )


@router.post(
    "/classify",
    response_model=dict,  # Changed from ClassificationResponse to dict for simple format
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Classification failed"}
    }
)
async def classify(request: ClassificationRequest):
    """
    Classify an educational query.

    This endpoint performs the complete classification pipeline:
    1. Detects subject and language
    2. Translates if needed (Hindi/Hinglish to English)
    3. Classifies into main categories
    4. Sub-classifies if exam-related

    Args:
        request: ClassificationRequest with message and optional metadata

    Returns:
        ClassificationResponse with classification details

    Raises:
        HTTPException: If classification fails
    """
    try:
        logger.info(f"[API] Classification request received: {request.message[:100]}...")
        logger.info(f"[API] Phone number: {request.phone_number}")

        # Validate input
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )

        # Execute classification pipeline
        full_response = await classify_message(request.message, request.phone_number)

        logger.info(f"[API] ========== FULL RESPONSE (BEFORE TRANSFORMATION) ==========")
        logger.info(f"[API] Classification: {full_response.classification}")
        logger.info(f"[API] Response_data status: {full_response.response_data.get('status') if full_response.response_data else None}")
        logger.info(f"[API] ===============================================================")

        # Save conversation history asynchronously (fire-and-forget)
        if request.phone_number:
            asyncio.create_task(
                _save_conversation_history(
                    phone_number=request.phone_number,
                    request_message=request.message,
                    full_response=full_response
                )
            )

        # Transform to simple format {status, message}
        simple_response = transform_to_simple_format(full_response)

        logger.info(f"[API] ========== SIMPLIFIED RESPONSE TO CLIENT ==========")
        logger.info(f"[API] Status: {simple_response['status']}")
        logger.info(f"[API] Message length: {len(simple_response['message'])} chars")
        logger.info(f"[API] Message preview: {simple_response['message'][:200]}...")
        logger.info(f"[API] ========================================================")

        return simple_response  

    except ClassifierException as e:
        logger.error(f"[API] Classification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"[API] Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"[API] Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
