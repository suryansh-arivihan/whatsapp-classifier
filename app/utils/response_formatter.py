"""
Response formatting utilities to transform ClassificationResponse to simple format.
Extracts user-facing message from complex handler responses.
"""
from typing import Dict, Any
from app.models.schemas import ClassificationResponse
from app.core.logging_config import logger


def extract_user_message(response_data: Dict[str, Any], classification: str) -> str:
    """
    Extract the user-facing message from response_data based on classification type.

    Args:
        response_data: The response_data dict from handlers
        classification: The main classification type

    Returns:
        str: The extracted message for the user
    """
    if not response_data or 'data' not in response_data:
        logger.warning("[ResponseFormatter] No data in response_data")
        return "Unable to generate response"

    data = response_data['data']

    try:
        # Handler-specific extraction based on classification
        if classification == 'guidance_based':
            # Path: data.response.text
            message = data.get('response', {}).get('text', '')
            if message:
                return message
            logger.warning("[ResponseFormatter] No text found in guidance response")
            return "No guidance available"

        elif classification == 'app_related':
            # Path: data.response (can be string or dict with text)
            message = data.get('response', '')

            # If response is a direct string
            if isinstance(message, str) and message:
                return message

            # If response is a dict with text key (for screen_data_related)
            if isinstance(message, dict) and 'text' in message:
                return message['text']

            logger.warning("[ResponseFormatter] No response string in app_related")
            return "No content available"

        elif classification == 'exam_related_info':
            # Priority 1: formatted_response (if GPT formatting was applied)
            if 'formatted_response' in data and data['formatted_response']:
                return data['formatted_response']

            # Priority 2: response as direct string (for local templates like important_questions)
            response = data.get('response')
            if isinstance(response, str) and response:
                return response

            # Priority 3: response.text
            if isinstance(response, dict) and 'text' in response:
                return response['text']

            # Priority 4: Format alternatives/questions
            if isinstance(response, dict):
                formatted = format_exam_response(response)
                if formatted:
                    return formatted

            logger.warning("[ResponseFormatter] Could not extract exam response")
            return "Exam information not available"

        elif classification == 'subject_related':
            # Path: data.response.text
            message = data.get('response', {}).get('text', '')
            if message:
                return message
            logger.warning("[ResponseFormatter] No text found in subject response")
            return "No answer available"

        elif classification == 'conversation_based':
            # Path: data.response (direct string)
            message = data.get('response', '')
            if isinstance(message, str) and message:
                return message
            logger.warning("[ResponseFormatter] No response string in conversation")
            return "Hello! How can I help you?"

        elif classification == 'complaint':
            # Path: data.text
            message = data.get('text', '')
            if message:
                return message
            logger.warning("[ResponseFormatter] No text found in complaint")
            return "Thank you for your feedback"

        else:
            # Unknown classification type - try generic extraction
            logger.warning(f"[ResponseFormatter] Unknown classification: {classification}")
            return extract_generic_message(data)

    except Exception as e:
        logger.error(f"[ResponseFormatter] Error extracting message: {e}")
        return "Error generating response"


def format_exam_response(response: Dict[str, Any]) -> str:
    """
    Format exam response alternatives or questions into readable text.

    Args:
        response: The response dict that may contain alternatives or questions

    Returns:
        str: Formatted response text
    """
    try:
        # Format alternatives
        if 'alternatives' in response and response['alternatives']:
            alts = response['alternatives']
            if isinstance(alts, list) and alts:
                formatted = "Here are some suggestions:\n\n"
                formatted += "\n".join(f"• {alt}" for alt in alts)
                return formatted

        # Format questions
        if 'questions' in response and response['questions']:
            questions = response['questions']
            if isinstance(questions, list) and questions:
                formatted_questions = []
                for i, q in enumerate(questions, 1):
                    if isinstance(q, dict):
                        question_text = q.get('question', '')
                        solution_text = q.get('solution', '')
                        formatted_questions.append(f"Q{i}: {question_text}")
                        if solution_text:
                            formatted_questions.append(f"Solution: {solution_text}\n")
                return "\n\n".join(formatted_questions)

        # If there's a direct text field
        if 'text' in response:
            return response['text']

        return ""

    except Exception as e:
        logger.error(f"[ResponseFormatter] Error formatting exam response: {e}")
        return ""


def extract_generic_message(data: Dict[str, Any]) -> str:
    """
    Generic message extraction fallback for unknown handler types.

    Args:
        data: The data dict from response_data

    Returns:
        str: Best-effort extracted message
    """
    # Try common patterns
    if isinstance(data.get('response'), str):
        return data['response']

    if isinstance(data.get('response'), dict):
        if 'text' in data['response']:
            return data['response']['text']

    if 'text' in data:
        return data['text']

    if 'message' in data:
        return data['message']

    # Last resort - stringify the data
    return str(data.get('response', 'Response generated successfully'))


def transform_to_simple_format(full_response: ClassificationResponse) -> Dict[str, str]:
    """
    Transform full ClassificationResponse to simple {status, message} format.

    Args:
        full_response: The complete ClassificationResponse object

    Returns:
        Dict with keys: status, message
    """
    try:
        response_data = full_response.response_data

        # Handle case where response_data is None
        if not response_data:
            logger.warning("[ResponseFormatter] response_data is None")
            return {
                "status": "error",
                "message": "No response generated"
            }

        # Check status
        status = response_data.get('status', 'error')

        # If error, return error message
        if status == 'error':
            error_message = response_data.get('message', 'An error occurred')
            logger.info(f"[ResponseFormatter] Returning error: {error_message}")
            return {
                "status": "error",
                "message": error_message
            }

        # Extract the actual user message
        message = extract_user_message(response_data, full_response.classification)

        logger.info(f"[ResponseFormatter] Extracted message length: {len(message)} chars")
        logger.info(f"[ResponseFormatter] Message preview: {message[:100]}...")

        return {
            "status": "success",
            "message": message
        }

    except Exception as e:
        logger.error(f"[ResponseFormatter] Error in transformation: {e}", exc_info=True)
        return {
            "status": "error",
            "message": "Failed to format response"
        }
