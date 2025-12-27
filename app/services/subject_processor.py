"""
Local subject doubt processor.
Handles subject-related doubts by calling board and conceptual solution APIs.
"""
import time
import re
from typing import Dict, Any, Optional
import httpx
from openai import OpenAI
from app.core.logging_config import logger
from app.core.config import settings

def html_to_simple_text_with_personal_touch(html_content, student_name="beta", user_query="", language="auto"):
    """
    Convert HTML content to simple plain text with a personal, caring teacher tone.
    Adds introduction and closing with subtle Arivihan promotion.

    Args:
        html_content (str): HTML content to convert
        student_name (str): Name to address the student (default: "beta")
        user_query (str): Original user query to detect language (default: "")
        language (str): Response language - "auto", "hinglish" or "hindi" (default: "auto")

    Returns:
        str: Plain text version with personal touch
    """


    logger.info("🔄 Converting HTML to simple text with personal touch...")
    logger.info(html_content)
    # Auto-detect language if set to auto
    if language.lower() == "auto":
        # Check if user_query contains Devanagari characters
        import re
        devanagari_pattern = re.compile(r'[\u0900-\u097F]')
        if devanagari_pattern.search(user_query):
            language = "hindi"
        else:
            language = "hinglish"

    # Language-specific instructions
    if language.lower() == "hindi":
        lang_instruction = """
*LANGUAGE: Pure Hindi (Devanagari script only)*
- Use ONLY Hindi Devanagari script throughout
- No English words mixed in
- Complete Hindi language response
"""
        opening_instruction = """
*OPENING (5-10 words only):*
- Very brief greeting in Hindi
- Examples: "बेटा, ये रहा जवाब:" or "चलिए समझते हैं:"
"""
        closing_instruction = """
*CLOSING (10-15 words only):*
- Brief helpful closing
- Example: "और सहायता के लिए अरिविहान देखें।"
"""
    else:  # hinglish
        lang_instruction = """
*LANGUAGE: Hinglish - WhatsApp Message Style (Roman Script)*
- Write Hindi words in ROMAN/ENGLISH script
- Natural mix like WhatsApp chatting
- Keep it casual and brief
"""
        opening_instruction = """
*OPENING (5-10 words only):*
- Very brief greeting in Hinglish
- Examples: "Beta, ye raha answer:" or "Chalo samjhte hain:"
"""
        closing_instruction = """
*CLOSING (10-15 words only):*
- Brief helpful closing
- Example: "Aur help ke liye Arivihan dekhiye."
"""

    prompt = f"""You are Ritesh Sir from Arivihan. Give EXTREMELY BRIEF answer.

{lang_instruction}

**STRICT WORD LIMIT: Maximum 100 words TOTAL (including greeting and closing)**

Convert this HTML to simple text:

{opening_instruction}

*MAIN ANSWER (70-80 words MAX):*
- Remove ALL HTML tags, LaTeX, special symbols
- Give ONLY the core concept/answer
- Use *asterisks* for emphasis
- Be VERY concise - like a WhatsApp quick reply
- Skip detailed explanations
- Focus on the main point only

{closing_instruction}

*CRITICAL RULES:*
- TOTAL response must be under 100 words
- Count every word including greeting/closing
- If answer is getting long, CUT details and keep only essentials
- Think: "What's the shortest way to answer this?"

HTML Content:
{html_content}

Give the SHORTEST possible answer (under 100 words total):"""

    client = OpenAI(api_key=settings.openai_api_key)

    # Language-specific system message
    if language.lower() == "hindi":
        system_content = "You are Ritesh Sir. Give EXTREMELY BRIEF answers in PURE HINDI (Devanagari). Maximum 100 words total. Be concise like WhatsApp messages."
    else:
        system_content = "You are Ritesh Sir. Give EXTREMELY BRIEF answers in Hinglish. Maximum 100 words total. Be concise like WhatsApp messages."

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_content
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=150  # Reduced from 2500 to enforce brevity
        )

        plain_text = response.choices[0].message.content.strip()
        return plain_text

    except Exception as e:
        print(f"❌ Error converting HTML to personalized text: {e}")
        return None


async def get_doubt_solution(
    query: str,
    subject: str,
    language: str,
    board_code: str = "MPBSE"
) -> Optional[Dict[str, Any]]:
    """
    Get detailed doubt solution from the board solution API.

    Args:
        query: The doubt/question
        subject: Subject (Physics, Chemistry, Biology, Mathematics)
        language: Language preference
        board_code: Board code (default: MPBSE)

    Returns:
        Solution response or None
    """
    # API endpoint
    url = "http://103.119.171.80:9090/v1/doubt/board/solution"

    # Headers
    headers = {
        "accept": "application/json",
        "accessToken": "DBkYaMoQ4zkN",
        "Content-Type": "application/json",
        "X-CSRFToken": "ZgTGNaFDW6luXp1IMZArig2PToLhYgSt9xe2phranAqEvAI0zeogF1ayqJpfV5hc"
    }

    # Request body
    data = {
        "text": query,
        "subject": subject,
        "lang": language,
        "boardCode": board_code
    }

    logger.info(f"[SubjectProcessor] Board Solution Request:")
    logger.info(f"  Query: {query}")
    logger.info(f"  Subject: {subject}")
    logger.info(f"  Language: {language}")
    logger.info(f"  Board: {board_code}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=data)
            logger.info(f"[SubjectProcessor] Status Code: {response.status_code}")

            # Handle NaN in response if present
            response_text = response.text.replace(': NaN', ': null')

            # Parse JSON
            json_response = response.json() if response.status_code == 200 else None

            if json_response:
                logger.info("[SubjectProcessor] Board solution retrieved successfully!")

            return json_response

    except httpx.RequestError as e:
        logger.error(f"[SubjectProcessor] Request Error: {e}")
        return None
    except Exception as e:
        logger.error(f"[SubjectProcessor] Error: {e}")
        return None


async def get_conceptual_solution(
    query: str,
    subject: str,
    language: str = "Hindi",
    course: str = "NEET",
    class_level: str = "12th"
) -> Optional[Dict[str, Any]]:
    """
    Get conceptual solution when board solution is not available.

    Args:
        query: The doubt/question
        subject: Subject (Physics, Chemistry, Biology, Mathematics)
        language: Language preference (default: Hindi)
        course: Course type (default: NEET)
        class_level: Class level (default: 12th)

    Returns:
        Conceptual solution response or None
    """
    # API endpoint
    url = "http://103.119.171.80:9090/v1/doubt/conceptual/html/solution"

    # Headers
    headers = {
        "accept": "application/json",
        "accessToken": "DBkYaMoQ4zkN",
        "Content-Type": "application/json",
        "X-CSRFToken": "ZgTGNaFDW6luXp1IMZArig2PToLhYgSt9ve2phranAqEvAI0zeogF1ayqJpfV5hc"
    }

    # Request body
    data = {
        "text": query,
        "subject": subject,
        "language": language,
        "course": course,
        "class": class_level,
        "api_key": "DBkYaMoQ4zkN"
    }

    logger.info(f"[SubjectProcessor] Conceptual Solution Request:")
    logger.info(f"  Query: {query}")
    logger.info(f"  Subject: {subject}")
    logger.info(f"  Language: {language}")
    logger.info(f"  Course: {course}")
    logger.info(f"  Class: {class_level}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=data)
            logger.info(f"[SubjectProcessor] Status Code: {response.status_code}")

            # Handle NaN in response if present
            response_text = response.text.replace(': NaN', ': null')

            # Parse JSON
            json_response = response.json() if response.status_code == 200 else None

            if json_response:
                logger.info("[SubjectProcessor] Conceptual solution API responded!")

            return json_response

    except httpx.RequestError as e:
        logger.error(f"[SubjectProcessor] Request Error: {e}")
        return None
    except Exception as e:
        logger.error(f"[SubjectProcessor] Error: {e}")
        return None


async def handle_subject_doubt(
    query: str,
    subject: str,
    language: str
) -> Optional[Dict[str, Any]]:
    """
    Handle subject-related doubt by calling the doubt solution API.
    If the result is empty, fallback to conceptual solution API.
    Converts HTML response to personalized plain text before returning.

    Args:
        query: The user's question
        subject: The classified subject
        language: Response language

    Returns:
        Doubt solution response with personalized text or None
    """
    start_time = time.time()

    logger.info("="*60)
    logger.info("HANDLING SUBJECT DOUBT")
    logger.info("="*60)
    logger.info(f"📚 Subject: {subject}")
    logger.info(f"❓ Query: {query}")

    # Step 1: Try get_doubt_solution first
    logger.info("🔍 Trying board-based solution...")
    doubt_start = time.time()
    doubt_solution = await get_doubt_solution(query, subject, language)
    doubt_time = time.time() - doubt_start
    logger.info(f"⏱️  Board solution time: {doubt_time:.2f}s")

    if doubt_solution:
        # Check if result is empty
        status = doubt_solution.get("status", "")
        result = doubt_solution.get("result", "")

        if status == "No" or not result or result.strip() == "":
            logger.info("⚠️ Board solution returned empty result")
            logger.info("🔄 Falling back to conceptual solution...")

            # Step 2: Call conceptual solution as fallback
            conceptual_start = time.time()
            conceptual_solution = await get_conceptual_solution(query, subject, language)
            conceptual_time = time.time() - conceptual_start
            logger.info(conceptual_solution)
            logger.info(f"⏱️  Conceptual solution time: {conceptual_time:.2f}s")

            if conceptual_solution:
                logger.info("✅ Conceptual solution retrieved successfully!")

                # Convert HTML to personalized plain text
                logger.info("🔄 Converting to personalized message...")
                conversion_start = time.time()
                conceptual_result = conceptual_solution.get("result", "")
                logger.info(conceptual_result)

                if conceptual_result:
                    logger.info("calling html to simple text with personal touch")
                    personalized_text = html_to_simple_text_with_personal_touch(
                                            html_content=conceptual_result,
                                            user_query=query,  # Pass the query for auto-language detection
                                            language="hindi"    # Let it auto-detect from query
                                        )
                    conversion_time = time.time() - conversion_start
                    logger.info(f"⏱️  Text conversion time: {conversion_time:.2f}s")

                    if personalized_text:
                        conceptual_solution["personalized_answer"] = personalized_text
                        conceptual_solution["original_html"] = conceptual_result
                        logger.info("✅ Personalized answer created!")
                    else:
                        logger.warning("⚠️ Text conversion failed, keeping original HTML")

                total_time = time.time() - start_time
                logger.info(f"⏱️  Total handle_subject_doubt time: {total_time:.2f}s")
                return conceptual_solution
            else:
                logger.error("❌ Conceptual solution also failed")
                total_time = time.time() - start_time
                logger.info(f"⏱️  Total handle_subject_doubt time: {total_time:.2f}s")
                return None
        else:
            logger.info("✅ Board solution retrieved successfully!")

            # Convert HTML to personalized plain text
            logger.info("🔄 Converting to personalized message...")
            conversion_start = time.time()

            if result:
                personalized_text = personalized_text = html_to_simple_text_with_personal_touch(
                        html_content=conceptual_result,
                        user_query=query,
                        language="auto"  # Will auto-detect based on query
                    )
                conversion_time = time.time() - conversion_start
                logger.info(f"⏱️  Text conversion time: {conversion_time:.2f}s")

                if personalized_text:
                    doubt_solution["personalized_answer"] = personalized_text
                    doubt_solution["original_html"] = result
                    logger.info("✅ Personalized answer created!")
                else:
                    logger.warning("⚠️ Text conversion failed, keeping original HTML")

            total_time = time.time() - start_time
            logger.info(f"⏱️  Total handle_subject_doubt time: {total_time:.2f}s")

            return doubt_solution
    else:
        logger.error("❌ Board solution API failed, trying conceptual solution...")

        # Try conceptual solution as fallback
        conceptual_start = time.time()
        conceptual_solution = await get_conceptual_solution(query, subject, language)
        conceptual_time = time.time() - conceptual_start
        logger.info(f"⏱️  Conceptual solution time: {conceptual_time:.2f}s")

        if conceptual_solution:
            logger.info("✅ Conceptual solution retrieved successfully!")

            # Convert HTML to personalized plain text
            logger.info("🔄 Converting to personalized message...")
            conversion_start = time.time()
            conceptual_result = conceptual_solution.get("result", "")

            if conceptual_result:
                personalized_text = html_to_simple_text_with_personal_touch(
                        html_content=conceptual_result,
                        user_query=query,
                        language="auto"
                    )
                conversion_time = time.time() - conversion_start
                logger.info(f"⏱️  Text conversion time: {conversion_time:.2f}s")

                if personalized_text:
                    conceptual_solution["personalized_answer"] = personalized_text
                    conceptual_solution["original_html"] = conceptual_result
                    logger.info("✅ Personalized answer created!")
                else:
                    logger.warning("⚠️ Text conversion failed, keeping original HTML")

            total_time = time.time() - start_time
            logger.info(f"⏱️  Total handle_subject_doubt time: {total_time:.2f}s")
            return conceptual_solution
        else:
            logger.error("❌ Both solution methods failed")
            total_time = time.time() - start_time
            logger.info(f"⏱️  Total handle_subject_doubt time: {total_time:.2f}s")
            return None


async def subject_main(
    json_data: Dict[str, Any],
    initial_classification: str
) -> Dict[str, Any]:
    """
    Main entry point for subject doubt processing.

    Args:
        json_data: Request data with message, subject, language
        initial_classification: Classification result

    Returns:
        Complete response dict with classification and solution
    """
    try:
        query = json_data.get("message") or json_data.get("userQuery", "")
        subject = json_data.get("subject", "General")
        # Normalize language to API format (only "english" or "hindi" accepted)
        raw_language = json_data.get("language", "hindi")
        language = raw_language.lower() if raw_language else "hindi"
        # Map hindlish to hindi since API only accepts english/hindi
        if language == "hindlish":
            language = "hindi"

        logger.info(f"[SubjectProcessor] Processing subject doubt")
        logger.info(f"  Query: {query}")
        logger.info(f"  Subject: {subject}")
        logger.info(f"  Language: {language}")

        # Get doubt solution
        solution = await handle_subject_doubt(query, subject, language)

        if solution:
            # Build successful response
            result = {
                "initialClassification": initial_classification,
                "classifiedAs": "subject_related",
                "response": {
                    "text": solution.get("personalized_answer", solution.get("result", "")),
                    "html": solution.get("original_html", solution.get("result", "")),
                    "status": solution.get("status", ""),
                },
                "openWhatsapp": False,
                "responseType": "text",
                "actions": "",
                "microLecture": "",
                "testSeries": "",
            }

            logger.info("[SubjectProcessor] Subject doubt response completed")
            return result
        else:
            # Fallback to WhatsApp if solution failed
            logger.warning("[SubjectProcessor] Solution failed, falling back to WhatsApp")
            result = {
                "initialClassification": initial_classification,
                "classifiedAs": "subject_related",
                "response": {
                    "text": "कृपया अपना सवाल WhatsApp पर पूछें, हमारे शिक्षक आपकी मदद करेंगे।",
                    "html": "",
                    "status": "fallback"
                },
                "openWhatsapp": True,
                "responseType": "text",
                "actions": "",
                "microLecture": "",
                "testSeries": "",
            }
            return result

    except Exception as e:
        logger.error(f"[SubjectProcessor] Error in subject_main: {e}")

        # Error fallback
        result = {
            "initialClassification": initial_classification,
            "classifiedAs": "subject_related",
            "response": {
                "text": "कृपया अपना सवाल WhatsApp पर पूछें।",
                "html": "",
                "status": "error"
            },
            "openWhatsapp": True,
            "responseType": "text",
            "actions": "",
            "microLecture": "",
            "testSeries": "",
        }
        return result
