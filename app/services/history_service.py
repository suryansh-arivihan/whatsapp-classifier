"""
DynamoDB service for conversation history management.
Handles saving and retrieving conversation history with 24-hour sliding window.
"""
import time
import boto3
from decimal import Decimal
from typing import List, Optional
from app.core.config import settings
from app.core.logging_config import logger
from app.models.history_schemas import (
    ConversationMessage,
    ConversationHistory,
    HistorySaveRequest
)


class HistoryService:
    """Service for managing conversation history in DynamoDB."""

    def __init__(self):
        """Initialize DynamoDB client."""
        self.table_name = settings.dynamodb_table_name
        self.retention_days = settings.history_retention_days
        self.messages_limit = settings.history_messages_limit
        self.window_hours = settings.history_window_hours

        # Initialize DynamoDB client
        try:
            self.dynamodb = boto3.resource(
                'dynamodb',
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )
            self.table = self.dynamodb.Table(self.table_name)
            logger.info(f"[HistoryService] Initialized DynamoDB client for table: {self.table_name}")
        except Exception as e:
            logger.error(f"[HistoryService] Failed to initialize DynamoDB client: {e}")
            self.dynamodb = None
            self.table = None

    def _calculate_ttl(self) -> int:
        """
        Calculate TTL (Time To Live) for DynamoDB item.

        Returns:
            Unix timestamp for deletion (current_time + retention_days)
        """
        ttl_seconds = int(time.time()) + (self.retention_days * 24 * 60 * 60)
        return ttl_seconds

    def _get_cutoff_timestamp(self) -> int:
        """
        Calculate cutoff timestamp for sliding window.

        Returns:
            Unix timestamp in milliseconds (current_time - window_hours)
        """
        current_ms = int(time.time() * 1000)
        cutoff_ms = current_ms - (self.window_hours * 60 * 60 * 1000)
        return cutoff_ms

    async def save_conversation(self, request: HistorySaveRequest) -> bool:
        """
        Save a conversation to DynamoDB.

        Args:
            request: HistorySaveRequest with conversation details

        Returns:
            True if saved successfully, False otherwise
        """
        if not self.table:
            logger.warning("[HistoryService] DynamoDB not initialized, skipping save")
            return False

        try:
            # Convert float to Decimal for DynamoDB compatibility
            processing_time_decimal = Decimal(str(request.processing_time_ms))

            item = {
                'phone_number': request.phone_number,
                'timestamp': request.timestamp,
                'request_message': request.request_message,
                'response_message': request.response_message,
                'classification': request.classification,
                'language': request.language,
                'is_follow_up': request.is_follow_up,
                'processing_time_ms': processing_time_decimal,  # Use Decimal instead of float
                'ttl': request.ttl
            }

            # Add optional fields
            if request.sub_classification:
                item['sub_classification'] = request.sub_classification
            if request.subject:
                item['subject'] = request.subject

            # Put item to DynamoDB
            self.table.put_item(Item=item)

            logger.info(f"[HistoryService] Saved conversation for {request.phone_number}")
            return True

        except Exception as e:
            logger.error(f"[HistoryService] Error saving conversation: {e}")
            return False

    async def get_conversation_history(
        self,
        phone_number: str,
        limit: Optional[int] = None
    ) -> ConversationHistory:
        """
        Retrieve conversation history for a phone number within 24-hour window.

        Args:
            phone_number: User's phone number
            limit: Maximum number of messages to retrieve (default: from config)

        Returns:
            ConversationHistory object with messages
        """
        if not self.table:
            logger.warning("[HistoryService] DynamoDB not initialized, returning empty history")
            return ConversationHistory(phone_number=phone_number, messages=[], total_count=0)

        try:
            cutoff_timestamp = self._get_cutoff_timestamp()
            message_limit = limit or self.messages_limit

            logger.info(f"[HistoryService] Fetching history for {phone_number} (last {self.window_hours}h)")

            # Query DynamoDB with sliding window
            response = self.table.query(
                KeyConditionExpression='phone_number = :phone AND #ts > :cutoff',
                ExpressionAttributeNames={
                    '#ts': 'timestamp'
                },
                ExpressionAttributeValues={
                    ':phone': phone_number,
                    ':cutoff': cutoff_timestamp
                },
                ScanIndexForward=False,  # Newest first
                Limit=message_limit
            )

            items = response.get('Items', [])

            # Convert to ConversationMessage objects
            messages = []
            for item in items:
                messages.append(ConversationMessage(
                    timestamp=item['timestamp'],
                    request_message=item['request_message'],
                    response_message=item['response_message'],
                    classification=item['classification'],
                    sub_classification=item.get('sub_classification'),
                    subject=item.get('subject'),
                    language=item['language'],
                    is_follow_up=item.get('is_follow_up', False)
                ))

            logger.info(f"[HistoryService] Retrieved {len(messages)} messages for {phone_number}")

            return ConversationHistory(
                phone_number=phone_number,
                messages=messages,
                total_count=len(messages)
            )

        except Exception as e:
            logger.error(f"[HistoryService] Error retrieving conversation history: {e}")
            return ConversationHistory(phone_number=phone_number, messages=[], total_count=0)

    async def delete_old_conversations(self, phone_number: str) -> int:
        """
        Manually delete conversations older than retention period.
        Note: TTL handles this automatically, this is for manual cleanup if needed.

        Args:
            phone_number: User's phone number

        Returns:
            Number of items deleted
        """
        if not self.table:
            logger.warning("[HistoryService] DynamoDB not initialized")
            return 0

        try:
            cutoff_timestamp = int(time.time() * 1000) - (self.retention_days * 24 * 60 * 60 * 1000)

            # Query old items
            response = self.table.query(
                KeyConditionExpression='phone_number = :phone AND #ts < :cutoff',
                ExpressionAttributeNames={
                    '#ts': 'timestamp'
                },
                ExpressionAttributeValues={
                    ':phone': phone_number,
                    ':cutoff': cutoff_timestamp
                }
            )

            items = response.get('Items', [])
            deleted_count = 0

            # Delete each item
            for item in items:
                self.table.delete_item(
                    Key={
                        'phone_number': item['phone_number'],
                        'timestamp': item['timestamp']
                    }
                )
                deleted_count += 1

            logger.info(f"[HistoryService] Deleted {deleted_count} old conversations for {phone_number}")
            return deleted_count

        except Exception as e:
            logger.error(f"[HistoryService] Error deleting old conversations: {e}")
            return 0


# Global history service instance
history_service = HistoryService()
