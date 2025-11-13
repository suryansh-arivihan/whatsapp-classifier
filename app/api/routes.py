"""
API routes for the classification service.
"""
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import (
    ClassificationRequest,
    ClassificationResponse,
    HealthCheckResponse,
    ErrorResponse
)
from app.core.config import settings
from app.core.logging_config import logger
from app.services.classification_pipeline import classify_message
from app.utils.exceptions import ClassifierException


router = APIRouter()


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
    response_model=ClassificationResponse,
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

        # Validate input
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )

        # Execute classification pipeline
        response = await classify_message(request.message)

        logger.info(f"[API] Classification successful: {response.classification}")
        return response

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
