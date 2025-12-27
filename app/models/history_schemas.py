"""
Pydantic models for conversation history.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ConversationMessage(BaseModel):
    """Single conversation message for history context."""

    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
    request_message: str = Field(..., description="User's message")
    response_message: str = Field(..., description="Bot's response")
    classification: str = Field(..., description="Main classification type")
    sub_classification: Optional[str] = Field(None, description="Sub-classification type")
    subject: Optional[str] = Field(None, description="Subject (if applicable)")
    language: str = Field(..., description="Language of the conversation")
    is_follow_up: bool = Field(default=False, description="Whether this was a follow-up question")


class ConversationHistory(BaseModel):
    """Conversation history for a user."""

    phone_number: str = Field(..., description="User's phone number")
    messages: List[ConversationMessage] = Field(default_factory=list, description="List of messages")
    total_count: int = Field(default=0, description="Total number of messages in history")


class FollowUpDetectionResult(BaseModel):
    """Result of follow-up detection analysis."""

    is_follow_up: bool = Field(..., description="Whether the current message is a follow-up")
    enriched_message: Optional[str] = Field(None, description="Enriched message with context (if follow-up)")
    original_message: str = Field(..., description="Original user message")
    context_used: List[str] = Field(default_factory=list, description="Previous messages used as context")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1) if applicable")
    should_stop_conversation: bool = Field(default=False, description="Whether user wants to stop the conversation")


class HistorySaveRequest(BaseModel):
    """Request to save conversation history to DynamoDB."""

    phone_number: str = Field(..., description="User's phone number")
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
    request_message: str = Field(..., description="User's message")
    response_message: str = Field(..., description="Bot's response")
    classification: str = Field(..., description="Main classification")
    sub_classification: Optional[str] = Field(None, description="Sub-classification")
    subject: Optional[str] = Field(None, description="Subject")
    language: str = Field(..., description="Language")
    is_follow_up: bool = Field(default=False, description="Follow-up flag")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    ttl: int = Field(..., description="TTL for DynamoDB auto-deletion")
