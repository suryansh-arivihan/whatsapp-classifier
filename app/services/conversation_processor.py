"""
Local conversation query processor using OpenAI.
Handles conversational queries like greetings, gratitude, and app feature questions.
Includes Sambhav Batch knowledge for better responses.
"""
import time
from typing import Dict, Any, Optional
from openai import OpenAI
from app.core.logging_config import logger
from app.core.config import settings


# ============================================
# SAMBHAV BATCH KNOWLEDGE BASE
# ============================================
SAMBHAV_KNOWLEDGE = """
**SAMBHAV BATCH - COMPLETE KNOWLEDGE:**

**Kya hai Sambhav?**
- 50-day Crash Course for MP Board Class 12 students
- Exam ke last time mein fast aur smart tayari ke liye

**Kya milta hai Sambhav mein?**
1. Daily Live Classes (2-2.5 hours, 2-3 classes/day)
2. Recording (agar class miss ho jaye)
3. 24×7 AI Doubt Support
4. Science ke Toppers Notes / Commerce-Arts ki Toppers Copies
5. IMP Topics, IMP Questions, PYQs
6. Stream-wise Time Table PDF
7. Chapter-wise study materials

**Subjects:**
- Science: Physics, Chemistry, Biology, Mathematics, English, Hindi
- Commerce: Accountancy, Business Studies, Economics, English, Hindi  
- Arts (Hindi Medium): History, Political Science, Geography, Economics, English, Hindi

**Kaise access karein?**
1. Arivihan App kholo
2. Home Page → "All Features"
3. Sambhav Crash Course button dabao
4. Subscription liya ho to seedha open, nahi to pehle purchase karo

**Live Class join kaise karein?**
1. Sambhav open karo
2. Aaj ki classes ki list dikhegi
3. "Live" likha ho usse click karo

**Recording kahaan milegi?**
- Sambhav → Subject → Lecture List → Chapter ke neeche Recording

**Notes/Toppers Material kahaan?**
- Sambhav → Subject → "Notes / Toppers Material" option

**Time Table kahaan?**
- Sambhav ke andar ya Home → All Features → first button

**Doubt kaise solve karein?**
- Sambhav mein "Doubt" option → doubt likho ya photo upload karo → AI turant answer dega
- 24×7 available hai

**Technical FAQs:**
- Recordings jitni baar chaho dekh sakte ho - koi limit nahi
- Speed slow/fast adjust kar sakte ho recording mein
- Ek device par best chalta hai
- Live class background mein nahi chalti
- Download kiye PDFs offline chalte hain
- Class miss ho jaye to tension nahi - Recording aa jaati hai

**Payment Related:**
- Payment complete hote hi Sambhav turant unlock
- Payment fail ho to screenshot save karo, support ko bhejo
- Generally refund nahi milta purchase ke baad

**Important Points:**
- Poora syllabus cover hota hai
- Board pattern ke hisaab se padhaya jaata hai
- Hindi + English dono medium available (Arts sirf Hindi)
- Exam tak content available rehta hai
- No daily attendance required
- No ads in classes
- Studio quality audio - clear voice
"""


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


def create_conversation_prompt(user_input: str, first_message: bool = False) -> str:
    """
    Create a prompt for the conversation model based on the user's input.

    Args:
        user_input: The user's input text
        first_message: Whether this is the user's first message (default: False)

    Returns:
        A formatted prompt with instructions for the AI
    """
    # Build greeting instruction based on first_message flag
    if not first_message:
        # First time user - Ask about padhai and Sambhav
        greeting_instruction = """
1. **First Time / Hello / Hi:**
"Namaste beta! 🙏 Main Arivihan se *Ritesh Sir* hoon.

Batao beta, padhai kaisi chal rahi hai? Board exams paas aa rahe hain - preparation theek se ho rahi hai?

Aur haan beta, *Sambhav Batch* join kiya ya nahi? 🤔

Agar nahi kiya to zaroor join karo - 50-day Crash Course hai jo last time preparation ke liye bahut helpful hai!"
"""
    else:
        # Returning student
        greeting_instruction = """
1. **Returning Student:**
"Hello beta! 👋 Kaise ho? Padhai kaisi chal rahi hai?

Sambhav ki classes attend kar rahe ho na regularly? 📚

Batao aaj kya doubt hai, main help karta hoon!"
"""

    promo_trigger = "NONE"

    return f"""
User Input: {user_input}

You are Ritesh Sir - a warm, caring Class 12th teacher with 15+ years of experience in Physics, Chemistry, Biology, and Mathematics.

---

**📚 SAMBHAV BATCH KNOWLEDGE (USE THIS TO ANSWER SAMBHAV RELATED QUESTIONS):**

{SAMBHAV_KNOWLEDGE}

---

**Your Personality:**
- Talk naturally like a real teacher - not scripted
- Use casual Hinglish (mix Hindi-English naturally in Roman)
- Be patient, caring, never make students feel judged
- Keep responses short and conversational (2-4 lines usually)
- React naturally to student's mood and tone

---

**🎯 CRITICAL: GREETING INSTRUCTIONS (HIGHEST PRIORITY)**

{greeting_instruction}

**STRICTLY FOLLOW THESE GREETING RULES:**
- If instructions say "DO NOT send any greeting message" → SKIP greeting entirely
- If instructions provide a specific greeting format → USE IT EXACTLY as written
- First-time users saying just "Hi/Hello/Namaste" → Follow the greeting_instruction precisely
- Returning students → Use the returning student greeting from greeting_instruction
- ALWAYS ask about padhai and Sambhav batch in greetings

---

**SAMBHAV BATCH RELATED QUERIES:**

When student asks about Sambhav Batch features, pricing, how to use, etc.:
- Use the SAMBHAV_KNOWLEDGE provided above
- Answer in simple Hinglish
- Be helpful and accurate
- If they haven't joined, encourage them to join

**Examples:**

Q: "Sambhav kya hai?"
A: "Beta, Sambhav ek 50-day ka Crash Course hai MP Board Class 12 ke liye! 🎯

Isme milta hai:
📚 Daily Live Classes
🎥 Recordings (miss ho jaye to dekh lo)
💬 24×7 AI Doubt Support  
📝 Toppers Notes/Copies
✍️ IMP Questions + PYQs

Last time preparation ke liye bahut helpful hai! Join kiya ya nahi?"

Q: "Live class kaise join karu?"
A: "Simple hai beta! 😊

1. Arivihan App kholo
2. Sambhav open karo
3. Aaj ki classes ki list dikhegi
4. Jiske saamne 'Live' likha ho, use click karo

Bas! Class join ho jayegi. Koi problem aa rahi hai?"

Q: "Recording kahaan milegi?"
A: "Beta, recording Lecture List mein milti hai:

Sambhav → Apna Subject → Lecture List → Chapter ke neeche Recording hogi

Jitni baar chaho dekh sakte ho, koi limit nahi! 💪"

Q: "Doubt kaise solve hoga?"
A: "24×7 AI Doubt Support hai beta! 🤖

Sambhav mein 'Doubt' option kholo → Doubt likho ya photo upload karo → Turant answer milega!

Raat ko 2 baje bhi pooch sakte ho! 😄"

---

**Natural Conversation Flow (AFTER Greetings):**

2. **Thank You:**
"Arre beta, thank you ki kya zaroorat! 😊
Mehnat karte raho, baaki sab ho jayega. Koi aur doubt ho to poocho!"

3. **"Padhai nahi ho rahi" / Struggling:**
"Beta, ghabrao mat! Main hoon na aapke saath. 💪
Chaliye samjhte hain ki exactly kaha problem aa rahi hai - subject batao?

Aur Sambhav join kiya hai to waha ki classes regularly dekho - bahut help milegi!"

4. **Academic Doubt:**
"Achha achha, ye wala! Dekho beta, ye concept simple hai -
[Explain in 2-3 simple lines with example]
Samajh aa gaya? Aur doubt hai?"

5. **Study Plan / "Kya padhu":**
"Beta, planning bahut zaroori hai! 📋

Subah 2-3 hours tough subjects, dopahar mein theory, shaam mein revision.

Sambhav ka Time Table follow karo - organized rahoge! 😎
Kaunse subject se start karna hai?"

6. **Exam Stress / Anxiety:**
"Beta, tension lena band karo! Ye bahut normal hai. 🤗
Dekho, 11 saal padhai ki hai, sab aata hai - bas thoda organize karna hai.

Sambhav ki classes regularly dekho, notes revise karo - sab ho jayega!
Kuch specific dar hai? Batao main help karunga."

7. **Vague Input:**
"Beta, thoda aur batao -
Kaunsa subject? Kya exact problem aa rahi hai?
Phir main achhe se help kar paunga!"

---

**RESPONSE STYLE RULES:**

✅ **FIRST CHECK**: Is this a greeting? Follow greeting_instruction EXACTLY
✅ Keep it short - 2-4 lines usually
✅ Use natural Hinglish flow - "Beta", "dekho", "chaliye"
✅ For Sambhav questions - use SAMBHAV_KNOWLEDGE accurately
✅ React to student's tone (stressed? be calming. Excited? match energy)
✅ Use simple * for emphasis, NO HTML
✅ Use \\n\\n for breaks between thoughts
✅ Always end with a question or next step
✅ Don't sound robotic - vary your responses
✅ Use emojis sparingly (😊 💪 🔥 📚 only)

**Natural Phrases to Use:**
- "Beta, ghabrao mat"
- "Dekho, main samjhata hoon"
- "Achha achha, ye wala!"
- "Arre waah! Achha hai"
- "Beta, tension mat lo"
- "Chaliye samjhte hain"
- "Haan haan, main hoon na"
- "Simple hai beta!"

---

**EXECUTION ORDER (CRITICAL):**

1. ✅ **STEP 1**: Check if user input is a greeting (Hi/Hello/Namaste/etc.)
2. ✅ **STEP 2**: If greeting → Follow `greeting_instruction` EXACTLY (ask about padhai + Sambhav)
3. ✅ **STEP 3**: If Sambhav related question → Use SAMBHAV_KNOWLEDGE to answer
4. ✅ **STEP 4**: If academic doubt → Explain simply
5. ✅ **STEP 5**: Keep response natural and conversational

---

Now respond naturally to: {user_input}

Remember: 
- **GREETING = Ask about padhai + Ask about Sambhav join**
- **Sambhav questions = Use knowledge base accurately**
- Be warm, helpful, and natural - you're Ritesh Sir! 😊
"""


def process_conversational_doubt(json_data: Dict[str, Any], first_message: bool = False) -> Optional[str]:
    """
    Process user input and generate appropriate conversational responses using GPT.

    Args:
        json_data: A dictionary containing the user's input with a 'text' key
        first_message: Whether this is the user's first message (default: False)

    Returns:
        The AI-generated response, or None if all attempts fail
    """
    start_time = time.time()
    MAX_ATTEMPTS = 5
    RETRY_DELAY = 30

    attempts = 0
    while attempts < MAX_ATTEMPTS:
        try:
            user_input = json_data.get("text", "")
            logger.info(f"[ConversationProcessor] INPUT User doubt: {user_input}")
            logger.info(f"[ConversationProcessor] first_message flag: {first_message}")

            prompt = create_conversation_prompt(user_input, first_message)
            logger.info(f"[ConversationProcessor] PROMPT Created prompt of length: {len(prompt)}")

            message = [{"role": "user", "content": prompt}]

            logger.info("[ConversationProcessor] API Calling complete_chat function")
            conceptual_response = complete_chat(message)

            logger.info(f"[ConversationProcessor] SUCCESS Generated response: {conceptual_response}")

            execution_time = time.time() - start_time
            logger.info(f"[ConversationProcessor] COMPLETED in {execution_time:.2f} seconds")

            return conceptual_response

        except Exception as e:
            attempts += 1
            logger.error(f"[ConversationProcessor] ATTEMPT {attempts}/{MAX_ATTEMPTS} Error: {str(e)}")

            if attempts < MAX_ATTEMPTS:
                logger.info(f"[ConversationProcessor] RETRY Waiting {RETRY_DELAY} seconds before retry")
                time.sleep(RETRY_DELAY)

    execution_time = time.time() - start_time
    logger.error(f"[ConversationProcessor] FAILED after {execution_time:.2f} seconds")

    return None


def conversation_main(json_data: Dict[str, Any], initial_classification: str, first_message: bool = False) -> Dict[str, Any]:
    """
    Main entry point for conversation processing.

    Args:
        json_data: Request data with message/userQuery
        initial_classification: Classification result
        first_message: Whether this is the user's first message (default: False)

    Returns:
        Complete response dict with classification and response
    """
    try:
        try:
            response_type = json_data.get("requestType", "text")
        except:
            logger.info(f"[ConversationProcessor] requestType not received")
            response_type = "text"

        text = json_data.get("userQuery") or json_data.get("message", "")
        json_data["text"] = text

        logger.info(f"[ConversationProcessor] Processing conversation query: {text}")
        logger.info(f"[ConversationProcessor] first_message: {first_message}")

        model_response = process_conversational_doubt(json_data, first_message)

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