"""
Follow-up detection service using GPT.
Analyzes conversation history to detect if current message is a follow-up
and enriches it with context if needed.
"""
from typing import Optional
from openai import OpenAI
from app.core.config import settings
from app.core.logging_config import logger
from app.models.history_schemas import (
    ConversationHistory,
    FollowUpDetectionResult
)
from app.services.history_service import history_service


class FollowUpDetector:
    """Service for detecting follow-up questions and enriching them with context."""

    def __init__(self):
        """Initialize OpenAI client."""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"

    def _build_context_string(self, history: ConversationHistory) -> str:
        """
        Build context string from conversation history.

        Args:
            history: ConversationHistory object

        Returns:
            Formatted context string for GPT prompt
        """
        if not history.messages:
            return "No previous conversation."

        context_parts = []
        for idx, msg in enumerate(reversed(history.messages), 1):  # Oldest to newest
            context_parts.append(
                f"Message {idx}:\n"
                f"User: {msg.request_message}\n"
                f"Bot: {msg.response_message}\n"
            )

        return "\n".join(context_parts)

    async def detect_and_enrich(
        self,
        current_message: str,
        phone_number: str
    ) -> FollowUpDetectionResult:
        """
        Detect if current message is a follow-up and enrich it with context.

        Args:
            current_message: Current user message
            phone_number: User's phone number

        Returns:
            FollowUpDetectionResult with detection and enrichment
        """
        try:
            # Get conversation history (last 5 messages in 24h window)
            history = await history_service.get_conversation_history(phone_number)

            # If no history, not a follow-up
            if not history.messages:
                logger.info(f"[FollowUpDetector] No history for {phone_number}, not a follow-up")
                return FollowUpDetectionResult(
                    is_follow_up=False,
                    enriched_message=None,
                    original_message=current_message,
                    context_used=[]
                )

            # Build context from history
            context_string = self._build_context_string(history)
            context_messages = [msg.request_message for msg in reversed(history.messages)]

            logger.info(f"[FollowUpDetector] Analyzing with {len(history.messages)} previous messages")

            # Create GPT prompt for follow-up detection
            system_prompt = """You are an intelligent assistant that analyzes conversations to detect follow-up questions.

Your task:
1. Determine if the current message is a follow-up to the previous conversation
2. If yes, rewrite the message to include necessary context for standalone understanding
3. If no, return the original message unchanged

A message is a FOLLOW-UP if:
- It references previous topics ("that", "it", "this", "the one you mentioned")
- It asks for clarification or more details about previous topics
- It uses pronouns without clear antecedents
- It continues a line of questioning from before
- It's a short phrase like "more", "yes", "explain", "how?" that needs context

A message is NOT a follow-up if:
- It's a completely new topic
- It's self-contained and understandable without context
- It's a greeting or general question

Response format:
- If follow-up: Return JSON {"is_follow_up": true, "enriched_message": "rewritten message with context"}
- If not follow-up: Return JSON {"is_follow_up": false, "enriched_message": null}

Example:
Previous: "User: What is Newton's first law? Bot: Newton's first law states..."
Current: "Can you give an example?"
Response: {"is_follow_up": true, "enriched_message": "Can you give an example of Newton's first law of motion?"}

Example:
Previous: "User: Explain photosynthesis Bot: Photosynthesis is..."
Current: "What are the important topics in Physics for board exam?"
Response: {"is_follow_up": false, "enriched_message": null}"""

            user_prompt = f"""Previous Conversation (last 24 hours):
{context_string}

Current Message: "{current_message}"

Is this a follow-up question? If yes, rewrite it with context. Respond in JSON format."""

            # Call GPT for analysis
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=300,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            import json
            try:
                result = json.loads(result_text)
                is_follow_up = result.get("is_follow_up", False)
                enriched_message = result.get("enriched_message")

                logger.info(
                    f"[FollowUpDetector] Detection result - "
                    f"is_follow_up: {is_follow_up}, "
                    f"original: '{current_message}', "
                    f"enriched: '{enriched_message if enriched_message else 'N/A'}'"
                )

                return FollowUpDetectionResult(
                    is_follow_up=is_follow_up,
                    enriched_message=enriched_message if is_follow_up else None,
                    original_message=current_message,
                    context_used=context_messages if is_follow_up else [],
                    confidence=None  # Can add confidence scoring later if needed
                )

            except json.JSONDecodeError as e:
                logger.error(f"[FollowUpDetector] Failed to parse GPT response: {e}")
                # Fallback: not a follow-up
                return FollowUpDetectionResult(
                    is_follow_up=False,
                    enriched_message=None,
                    original_message=current_message,
                    context_used=[]
                )

        except Exception as e:
            logger.error(f"[FollowUpDetector] Error in follow-up detection: {e}")
            # Fallback: return original message
            return FollowUpDetectionResult(
                is_follow_up=False,
                enriched_message=None,
                original_message=current_message,
                context_used=[]
            )


# Global follow-up detector instance
followup_detector = FollowUpDetector()
