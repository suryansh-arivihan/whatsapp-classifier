"""
Pydantic models for request and response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ClassificationType(str, Enum):
    """Main classification categories."""
    SUBJECT_RELATED = "subject_related"
    APP_RELATED = "app_related"
    COMPLAINT = "complaint"
    GUIDANCE_BASED = "guidance_based"
    CONVERSATION_BASED = "conversation_based"
    EXAM_RELATED_INFO = "exam_related_info"


class ExamSubClassificationType(str, Enum):
    """Exam-related sub-classification categories."""
    FAQ = "faq"
    PYQ_PDF = "pyq_pdf"
    ASKING_PYQ_QUESTION = "asking_PYQ_question"
    ASKING_TEST = "asking_test"
    ASKING_IMPORTANT_QUESTION = "asking_important_question"


class SubjectType(str, Enum):
    """Academic subjects."""
    PHYSICS = "Physics"
    CHEMISTRY = "Chemistry"
    MATHEMATICS = "Mathematics"
    BIOLOGY = "Biology"


class LanguageType(str, Enum):
    """Supported languages."""
    ENGLISH = "English"
    HINDI = "Hindi"
    HINGLISH = "Hinglish"


class ClassificationRequest(BaseModel):
    """Request model for classification endpoint."""
    message: str = Field(..., description="User query to classify", min_length=1)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What is Newton's first law?",
                "metadata": {"user_id": "user123"}
            }
        }


class SubjectLanguageResponse(BaseModel):
    """Response model for subject and language detection."""
    subject: Optional[SubjectType] = Field(default=None, description="Detected subject if academic")
    language: LanguageType = Field(..., description="Detected language")


class ClassificationResponse(BaseModel):
    """Response model for classification endpoint."""
    classification: ClassificationType = Field(..., description="Main classification category")
    sub_classification: Optional[ExamSubClassificationType] = Field(
        default=None,
        description="Sub-classification for exam-related queries"
    )
    subject: Optional[SubjectType] = Field(
        default=None,
        description="Detected academic subject"
    )
    language: LanguageType = Field(..., description="Detected language")
    original_message: str = Field(..., description="Original query message")
    translated_message: Optional[str] = Field(
        default=None,
        description="Translated message if translation was performed"
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of classification"
    )
    response_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Response data from the handler (if applicable)"
    )
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "classification": "exam_related_info",
                "sub_classification": "asking_PYQ_question",
                "subject": "Physics",
                "language": "English",
                "original_message": "Show me PYQ questions on Newton's laws",
                "translated_message": None,
                "confidence_score": 0.92,
                "response_data": {
                    "status": "success",
                    "data": {"text": "Response from handler..."}
                },
                "processing_time_ms": 1250.5,
                "timestamp": "2025-11-13T10:30:00Z"
            }
        }


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
