"""
Middleware for saving conversation history to DynamoDB.
Captures request/response and saves asynchronously without blocking.
"""
import time
import json
import asyncio
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.logging_config import logger
from app.services.history_service import history_service
from app.models.history_schemas import HistorySaveRequest


class MessageHistoryMiddleware(BaseHTTPMiddleware):
    """Middleware to save conversation history to DynamoDB."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Intercept request and response to save conversation history.

        Args:
            request: Incoming request
            call_next: Next middleware/handler in chain

        Returns:
            Response from handler
        """
        # Only process /classify endpoint
        if request.url.path != "/classify":
            return await call_next(request)

        # Extract phone_number and message from request body
        phone_number = None
        request_message = None
        request_body = None

        try:
            # Read request body
            body = await request.body()
            if body:
                request_body = json.loads(body.decode())
                phone_number = request_body.get("phone_number")
                request_message = request_body.get("message")

                logger.info(f"[HistoryMiddleware] Capturing request for phone: {phone_number}")

            # Reconstruct request for next handler
            async def receive():
                return {"type": "http.request", "body": body}

            request._receive = receive

        except Exception as e:
            logger.error(f"[HistoryMiddleware] Error reading request body: {e}")
            return await call_next(request)

        # Record start time
        start_time = time.time()

        # Call next handler
        response = await call_next(request)

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        # Only save if we have phone_number and this is a successful response
        if not phone_number or not request_message:
            logger.info("[HistoryMiddleware] Skipping save - no phone_number or request_message")
            return response

        # Extract response body (only for 200 OK)
        if response.status_code == 200:
            try:
                # Read response body
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk

                # Parse response
                response_data = json.loads(response_body.decode())

                # Extract response message and metadata
                response_message = response_data.get("message", "")
                classification = "unknown"
                sub_classification = None
                subject = None
                language = "english"
                is_follow_up = False

                # Try to extract from full_response if available (before transformation)
                # The response might have been transformed to simple format
                # We need to get this info from somewhere else...
                # For now, we'll store request in FastAPI state and retrieve it in middleware

                # Schedule async save (fire-and-forget)
                asyncio.create_task(
                    self._save_history_async(
                        phone_number=phone_number,
                        request_message=request_message,
                        response_message=response_message,
                        classification=classification,
                        sub_classification=sub_classification,
                        subject=subject,
                        language=language,
                        is_follow_up=is_follow_up,
                        processing_time_ms=processing_time_ms
                    )
                )

                # Reconstruct response with same body
                return Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )

            except Exception as e:
                logger.error(f"[HistoryMiddleware] Error processing response: {e}")

        return response

    async def _save_history_async(
        self,
        phone_number: str,
        request_message: str,
        response_message: str,
        classification: str,
        sub_classification: str,
        subject: str,
        language: str,
        is_follow_up: bool,
        processing_time_ms: float
    ):
        """
        Save conversation history to DynamoDB asynchronously.

        Args:
            phone_number: User's phone number
            request_message: User's message
            response_message: Bot's response
            classification: Main classification
            sub_classification: Sub-classification (if any)
            subject: Subject (if any)
            language: Language
            is_follow_up: Whether this was a follow-up
            processing_time_ms: Processing time in milliseconds
        """
        try:
            timestamp = int(time.time() * 1000)  # Current timestamp in milliseconds
            ttl = int(time.time()) + (90 * 24 * 60 * 60)  # 90 days from now

            save_request = HistorySaveRequest(
                phone_number=phone_number,
                timestamp=timestamp,
                request_message=request_message,
                response_message=response_message,
                classification=classification,
                sub_classification=sub_classification,
                subject=subject,
                language=language,
                is_follow_up=is_follow_up,
                processing_time_ms=processing_time_ms,
                ttl=ttl
            )

            success = await history_service.save_conversation(save_request)

            if success:
                logger.info(f"[HistoryMiddleware] Saved conversation for {phone_number}")
            else:
                logger.warning(f"[HistoryMiddleware] Failed to save conversation for {phone_number}")

        except Exception as e:
            logger.error(f"[HistoryMiddleware] Error in async save: {e}")
