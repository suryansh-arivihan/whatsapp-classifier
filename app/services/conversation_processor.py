"""
Local conversation query processor using OpenAI.
Handles conversational queries like greetings, gratitude, and app feature questions.
"""
import time
from typing import Dict, Any, Optional
from openai import OpenAI
from app.core.logging_config import logger
from app.core.config import settings


def complete_chat(messages: list, model: str = "gpt-4o-mini") -> str:
    """
    Call OpenAI chat completion API.

    Args:
        messages: List of message dictionaries
        model: OpenAI model to use

    Returns:
        Generated response text
    """
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(model=model, messages=messages)
        chat_gpt_response = response.choices[0].message.content
        return chat_gpt_response
    except Exception as e:
        logger.error(f"[ConversationProcessor] complete_chat error: {e}")
        raise


def create_conversation_prompt(user_input: str) -> str:
    """
    Create a prompt for the conversation model based on the user's input.

    Args:
        user_input: The user's input text

    Returns:
        A formatted prompt with instructions for the AI
    """
    return f"""
    User Input: {user_input}
    Based on the user's input, respond appropriately as per the following guidelines:

    1. **Greetings**:
    - If the user greets in **English** (e.g., 'Hello', 'Hi'):
        Respond: 'Hi! Welcome to Arivihan Doubt Solving. How may I help you?'
    - If the user greets in **Hindi** (e.g., 'नमस्ते', 'सुप्रभात'):
        Respond: 'नमस्ते! अरिविहान डाउट सॉल्विंग में आपका स्वागत है। मैं आपकी क्या सहायता कर सकता हूँ?'
    - If the user greets in **Hinglish** (e.g., 'Hi! मुझे मदद चाहिए।'):
        Respond: 'Hi! अरिविहान डाउट सॉल्विंग में आपका स्वागत है। आपकी किस विषय में मदद कर सकते हैं?'

    2. **Expressions of Gratitude**:
    - If the user expresses gratitude (e.g., 'Thank you', 'Thanks', 'धन्यवाद', 'शुक्रिया'):
        Respond warmly: 'You are welcome! Is there anything else we can assist you with?'

    3. **App Feature Questions**:
    - If the user asks about doubt solving (e.g., 'Who solves doubts', 'AI या teachers', 'doubt solving कैसे होता है'):
        Respond in Hindi: 'अरिविहान में आपको दोनों सुविधाएं मिलती हैं - AI Instant Guru से तुरंत डाउट solve कर सकते हैं 24×7, और साथ ही expert teachers भी आपकी मदद करते हैं। आप जब चाहें तब doubt clear कर सकते हैं!'
    - If the user asks about AI features:
        Respond: 'हमारा AI Instant Guru 24×7 उपलब्ध है आपके doubts solve करने के लिए। साथ ही experienced teachers भी हैं जो detailed guidance देते हैं।'

    4. **Other Scenarios**:
    - If the input doesn't fit these categories, politely ask for clarification:
        Respond: 'I'm here to help! Could you please elaborate on your query?'

    Always match the tone and language of the user's input when responding.
    """


def process_conversational_doubt(json_data: Dict[str, Any]) -> Optional[str]:
    """
    Process user input and generate appropriate conversational responses using GPT.

    This function handles basic conversational patterns including greetings,
    expressions of gratitude, and other general queries. It attempts to match
    the language and tone of the user's input.

    Args:
        json_data: A dictionary containing the user's input with a 'text' key

    Returns:
        The AI-generated response, or None if all attempts fail
    """
    # Track execution time
    start_time = time.time()

    # Define constants
    MAX_ATTEMPTS = 5
    RETRY_DELAY = 30  # seconds

    attempts = 0
    while attempts < MAX_ATTEMPTS:
        try:
            # Extract user doubt from input
            user_input = json_data.get("text", "")
            logger.info(f"[ConversationProcessor] INPUT User doubt: {user_input}")

            # Construct the prompt for GPT
            prompt = create_conversation_prompt(user_input)
            logger.info(f"[ConversationProcessor] PROMPT Created prompt of length: {len(prompt)}")

            # Prepare message for GPT
            message = [
                {"role": "user", "content": prompt}
            ]

            # Get response from GPT
            logger.info("[ConversationProcessor] API Calling complete_chat function")
            conceptual_response = complete_chat(message)

            # Log the successful response
            logger.info(f"[ConversationProcessor] SUCCESS Generated response: {conceptual_response}")

            # Calculate and log execution time
            execution_time = time.time() - start_time
            logger.info(f"[ConversationProcessor] COMPLETED process_conversation_doubt completed in {execution_time:.2f} seconds")

            # Return the response
            return conceptual_response

        except Exception as e:
            # Log exception details
            attempts += 1
            logger.error(f"[ConversationProcessor] ATTEMPT {attempts}/{MAX_ATTEMPTS} Error: {str(e)}")

            # If not the final attempt, wait before retrying
            if attempts < MAX_ATTEMPTS:
                logger.info(f"[ConversationProcessor] RETRY Waiting {RETRY_DELAY} seconds before retry")
                time.sleep(RETRY_DELAY)

    # Log failure after maximum attempts
    execution_time = time.time() - start_time
    logger.error(f"[ConversationProcessor] FAILED Exceeded maximum attempts ({MAX_ATTEMPTS}). Process failed after {execution_time:.2f} seconds")

    # Return None to indicate failure
    return None


def conversation_main(json_data: Dict[str, Any], initial_classification: str) -> Dict[str, Any]:
    """
    Main entry point for conversation processing.

    Args:
        json_data: Request data with message/userQuery
        initial_classification: Classification result

    Returns:
        Complete response dict with classification and response
    """
    try:
        # Extract request type if available
        try:
            response_type = json_data.get("requestType", "text")
        except:
            logger.info(f"[ConversationProcessor] requestType not received")
            response_type = "text"

        # Get user query - handle both 'userQuery' and 'message' keys
        text = json_data.get("userQuery") or json_data.get("message", "")
        json_data["text"] = text

        logger.info(f"[ConversationProcessor] Processing conversation query: {text}")

        # Process the conversational doubt
        model_response = process_conversational_doubt(json_data)

        if model_response:
            logger.info(f"[ConversationProcessor] conversation response is: {model_response}")

            result = {
                "initialClassification": initial_classification,
                "classifiedAs": "conversation_based",
                "response": model_response,
                "openWhatsapp": False,
                "responseType": response_type,
                "actions": "",
                "microLecture": "",
                "testSeries": "",
            }
        else:
            # If processing failed, fall back to opening WhatsApp
            logger.warning("[ConversationProcessor] Failed to generate response, falling back to WhatsApp")
            result = {
                "initialClassification": initial_classification,
                "classifiedAs": "conversation_based",
                "response": "",
                "openWhatsapp": True,
                "responseType": response_type,
                "actions": "",
                "microLecture": "",
                "testSeries": ""
            }

    except Exception as e:
        logger.error(f"[ConversationProcessor] error: {e}")

        result = {
            "initialClassification": initial_classification,
            "classifiedAs": "conversation_based",
            "response": "",
            "openWhatsapp": True,
            "responseType": json_data.get("requestType", "text"),
            "actions": "",
            "microLecture": "",
            "testSeries": ""
        }

    return result
