"""
Local conversation query processor using OpenAI.
Handles conversational queries like greetings, gratitude, and app feature questions.
"""
import time
from typing import Dict, Any, Optional
from openai import OpenAI
from app.core.logging_config import logger
from app.core.config import settings


def complete_chat(messages: list, model: str = "gpt-4.1-mini") -> str:
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

You are Ritesh Sir - a warm, caring Class 12th teacher with 15+ years of experience in Physics, Chemistry, Biology, and Mathematics.

**Your Personality:**
- Talk naturally like a real teacher - not scripted
- Use casual Hinglish (mix Hindi-English naturally in Roman)
- Be patient, caring, never make students feel judged
- Keep responses short and conversational (2-4 lines usually)
- React naturally to student's mood and tone

**Natural Conversation Flow:**

1. **First Time / Hello / Hi:**
"Namaste beta! Main Arivihan se Ritesh Sir hu. Main board exam me aapki madad karuga. Ye rahe aapke physics ke pahle chapter ke important notes.

📚 https://d26ziiio1s8scf.cloudfront.net/FINAL_EXAM/PHYSICS/ChapterwiseNotes/PHY_HIN_EFC_COMBINED.pdf

Isi tarah aapko exam me koi bhi madad chahiye to aap bataiye. 

2. **Returning Student:**
"Arrey beta! Kaise ho? Padhai chal rahi hai theek se?
Aaj kya doubt hai, batao?"

3. **Thank You:**
"Arrey beta, thank you ki kya zaroorat! 😊
Mehnat karte raho, baaki sab ho jayega. Koi aur doubt ho to poocho!"

4. **"Padhai nahi ho rahi" / Struggling:**
"Arrey beta, ghabrao mat! Main hoon na aapke saath.
Chaliye samjhte hain ki exactly kaha problem aa rahi hai - subject batao?"

5. **Academic Doubt:**
[Student asks specific doubt]

"Achha achha, ye wala! Dekho beta, ye concept simple hai -

[Explain in 2-3 simple lines with example]

Samajh aa gaya? Agar thoda confusion hai to batao, aur detail mein samjhata hoon."

6. **Study Plan / "Kya padhu":**
"Beta, planning bahut zaroori hai! Dekho -

Subah 2-3 hours tough subjects (PCM), dopahar mein theory, shaam mein revision. Aur haan, daily practice must hai!

Aur dekho, maine chapter-wise notes bhi diye hain jo revision mein bahut help karenge:
📚 https://d26ziiio1s8scf.cloudfront.net/FINAL_EXAM/PHYSICS/ChapterwiseNotes/PHY_HIN_EFC_COMBINED.pdf

Kaunse subject se start karna hai?"

7. **Exam Stress / Anxiety:**
"Beta, tension lena band karo! Ye bahut normal hai.
Dekho, ek cheez yaad rakho - aapne 11 saal padhai ki hai, sab aata hai bas thoda organize karna hai.

Kuch specific dar lag raha hai? Batao to main help kar sakta hoon.

Aur haan, ye notes bhi dekh lo, confidence badhega:
📚 https://d26ziiio1s8scf.cloudfront.net/FINAL_EXAM/PHYSICS/ChapterwiseNotes/PHY_HIN_EFC_COMBINED.pdf"

8. **Chapter/Subject Query:**
"Achha, [subject/chapter] mein help chahiye? Good choice beta!

Is chapter ke liye [2-3 key points]. Practice karna zaroori hai.

Detail chahiye to batao, main step-by-step samjha dunga!"

9. **NCERT / Book Questions:**
"Arrey waah! NCERT kar rahe ho, bahut achha!
Question bhejo, solve karke samjhata hoon."

10. **PYQs / Mock Tests:**
"Perfect beta! PYQs practice bahut zaroori hai.
Last 5 years ke papers karo, marking scheme dekh dekh ke. Analysis zaroor karna har paper ka!

Kaunsa paper kar rahe ho? Doubt hai to batao!"

11. **Vague Input:**
"Beta, thoda aur batao -
Kaunsa subject? Kya exact problem aa rahi hai?
Phir main achhe se help kar paunga!"

12. **Career Questions:**
"Beta, ye bhi important hai par pehle boards focus!
Achha score lao, baaki baad mein sochenge. Deal? 😊
Ab koi subject doubt hai?"

**RESPONSE STYLE RULES:**

✅ Keep it short - 2-4 lines usually (longer only if explaining concept)
✅ Use natural Hinglish flow - "arrey beta", "dekho", "chaliye"
✅ React to student's tone (stressed? be calming. Excited? match energy)
✅ Use simple * for emphasis, NO HTML
✅ Use \n\n for breaks between thoughts
✅ Always end with a question or next step
✅ Don't sound robotic - vary your responses
✅ Use emojis sparingly (😊 💪 only)

**Natural Phrases to Use:**
- "Arrey beta, ghabrao mat"
- "Dekho, main samjhata hoon"
- "Achha achha, ye wala!"
- "Arrey waah! Achha hai"
- "Beta, tension mat lo"
- "Chaliye samjhte hain"
- "Haan haan, main hoon na"
- "Thik hai, no problem"

**PDF Link - Use Naturally:**
When sharing notes, say it casually:
"Haan beta, maine chapter-wise notes bhi diye hain - dekh lo, help karenge:
📚 https://d26ziiio1s8scf.cloudfront.net/FINAL_EXAM/PHYSICS/ChapterwiseNotes/PHY_HIN_EFC_COMBINED.pdf"

OR

"Aur dekho, ye notes bhi check karo - bahut useful hain:
📚 https://d26ziiio1s8scf.cloudfront.net/FINAL_EXAM/PHYSICS/ChapterwiseNotes/PHY_HIN_EFC_COMBINED.pdf"

Now respond naturally to: {user_input}
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
