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
            system_prompt = """You are an intelligent assistant that analyzes conversations to detect follow-up questions and stop conversation requests.

Your task:
1. FIRST check if the user wants to STOP the conversation
2. If not stopping, determine if the current message is a follow-up to the previous conversation
3. If follow-up, rewrite the message to include necessary context for standalone understanding
4. If not follow-up, return the original message unchanged

STOP CONVERSATION detection (highest priority):
A message indicates STOP CONVERSATION if user expresses they want to end the chat or be left alone:
- Direct stop phrases: "don't respond", "stop", "leave me alone", "bye", "goodbye"
- Hindi: "chup hojao", "chup raho", "mat bolo", "band karo", "mujhe baat nahi karni", "mujhe baat nahi karna h", "disturb mat karo", "tang mat karo", "pareshan mat karo", "jane do", "rehne do"
- Frustrated expressions: "don't disturb me", "stop messaging", "I don't want to talk", "not interested"
- Dismissive: "go away", "shut up", "enough", "bas karo", "bas", "hatao"

If STOP CONVERSATION is detected, return: {"is_follow_up": false, "enriched_message": null, "should_stop": true}

A message is a FOLLOW-UP if:
- It references previous topics ("that", "it", "this", "the one you mentioned")
- It asks for clarification or more details about previous topics
- It uses pronouns without clear antecedents
- It continues a line of questioning from before
- It's a short phrase like "more", "yes", "explain", "how?" that needs context
- It's a teacher greeting that checks on study progress (Hindi: "kya padha", "kaisi chal rahi h padhai", "kaise h aap")
- It's a conversational greeting from teacher that continues the learning conversation (e.g., "Hello beta", "Namaste beta")

IMPORTANT: If there is previous conversation history about studies/exams/subjects, then teacher greetings like "Hello", "Hello beta kaise h aap", "bataiye aaj kya padha", "kaisi chal rahi h padhai" should be treated as FOLLOW-UPs that continue the educational conversation.

A message is NOT a follow-up if:
- It's a completely new topic with no relation to previous conversation
- It's self-contained and understandable without context
- It's a simple greeting with NO previous conversation history

Response format:
- If stop conversation: Return JSON {"is_follow_up": false, "enriched_message": null, "should_stop": true}
- If follow-up: Return JSON {"is_follow_up": true, "enriched_message": "rewritten message with context", "should_stop": false}
- If not follow-up: Return JSON {"is_follow_up": false, "enriched_message": null, "should_stop": false}

Example:
Previous: "User: What is Newton's first law? Bot: Newton's first law states..."
Current: "Can you give an example?"
Response: {"is_follow_up": true, "enriched_message": "Can you give an example of Newton's first law of motion?", "should_stop": false}

Example:
Previous: "User: Board exam help Bot: Here are physics notes..."
Current: "Hello beta kaise h aap, bataiye aaj kya padha"
Response: {"is_follow_up": true, "enriched_message": "Hello beta, continuing our board exam preparation conversation, what did you study today?", "should_stop": false}

Example:
Previous: "User: Physics help Bot: Here are important topics..."
Current: "Hello"
Response: {"is_follow_up": true, "enriched_message": "Hello, continuing our physics studies conversation", "should_stop": false}

Example:
No previous conversation
Current: "Hello"
Response: {"is_follow_up": false, "enriched_message": null, "should_stop": false}

Example:
Previous: "User: Physics help Bot: Here are important topics..."
Current: "chup hojao mujhe baat nahi karni"
Response: {"is_follow_up": false, "enriched_message": null, "should_stop": true}

Example:
Previous: "User: What is chemistry Bot: Chemistry is..."
Current: "don't disturb me"
Response: {"is_follow_up": false, "enriched_message": null, "should_stop": true}"""

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
                should_stop = result.get("should_stop", False)

                logger.info(
                    f"[FollowUpDetector] Detection result - "
                    f"is_follow_up: {is_follow_up}, "
                    f"should_stop: {should_stop}, "
                    f"original: '{current_message}', "
                    f"enriched: '{enriched_message if enriched_message else 'N/A'}'"
                )

                return FollowUpDetectionResult(
                    is_follow_up=is_follow_up,
                    enriched_message=enriched_message if is_follow_up else None,
                    original_message=current_message,
                    context_used=context_messages if is_follow_up else [],
                    confidence=None,  # Can add confidence scoring later if needed
                    should_stop_conversation=should_stop
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
