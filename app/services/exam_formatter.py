"""
Exam response formatter using GPT.
Formats PYQ questions and exam responses into readable WhatsApp messages.
"""
import re
from typing import Dict, Any, List
from openai import OpenAI
from app.core.logging_config import logger
from app.core.config import settings


def clean_html(html_text: str) -> str:
    """
    Remove HTML tags from text.

    Args:
        html_text: Text with HTML tags

    Returns:
        Clean text without HTML tags
    """
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', html_text)
    # Clean up extra whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    # Remove "Q." prefix if present
    clean = re.sub(r'^Q\.\s*', '', clean)
    return clean


def format_pyq_questions(response_data: Dict[str, Any], language: str = "hindi") -> str:
    """
    Format PYQ questions into a readable WhatsApp message using GPT.

    Args:
        response_data: Response from exam API containing questions
        language: User's preferred language

    Returns:
        Formatted WhatsApp message
    """
    try:
        client = OpenAI(api_key=settings.openai_api_key)

        # Extract questions data
        questions = response_data.get("questions", [])
        questions_count = response_data.get("questions_count", len(questions))
        matched_chapter = response_data.get("matched_chapter", "")
        verified_subject = response_data.get("verified_subject", "")
        message = response_data.get("message", "")

        if not questions:
            return "कोई प्रश्न नहीं मिला। कृपया दूसरा topic try करें।" if language == "Hindi" else "No questions found. Please try another topic."

        # Prepare questions list for GPT
        questions_text = ""
        for idx, q in enumerate(questions, 1):
            question_text = clean_html(q.get("question", ""))
            marks = q.get("marks", "")
            year = q.get("year", "")
            q_type = q.get("question_type", "")
            q_lang = q.get("language", "")

            questions_text += f"\n{idx}. [{marks} marks, {year}, {q_type}, {q_lang}]\n{question_text}\n"

        # Create prompt for GPT
        if language.lower() == "hindi":
            system_prompt = """आप एक शिक्षा सहायक हैं जो पिछले वर्षों के प्रश्नों को WhatsApp के लिए फॉर्मेट करते हैं।

निर्देश:
1. एक आकर्षक शुरुआत दें जैसे "📚 *[Subject] - [Chapter] के Previous Year Questions*"
2. कुल प्रश्नों की संख्या बताएं
3. हर प्रश्न को साफ-सुथरा फॉर्मेट करें:
   - प्रश्न नंबर के साथ
   - [अंक, वर्ष, प्रकार] ब्रैकेट में
   - प्रश्न को अगली line में
4. Emojis का उपयोग करें: 📝 ✅ 📌 ⭐
5. अंत में motivational line जोड़ें
6. सभी HTML tags हटा दें
7. शुद्ध हिंदी में लिखें

फॉर्मेट example:
📚 *Physics - Electric Charges के PYQ*

✅ कुल 11 प्रश्न मिले

📝 *प्रश्न 1* [1 अंक, 2025]
One coulomb charge has _____ electrons.

📝 *प्रश्न 2* [3 अंक, 2025]
विद्युत आवेश के क्वाण्टीकरण का गणितीय रूप लिखिये।

...

⭐ *इन सभी प्रश्नों को solve करके अपनी तैयारी मजबूत बनाएं!*
"""
        else:
            system_prompt = """You are an education assistant who formats previous year questions for WhatsApp.

Instructions:
1. Start with an engaging header like "📚 *[Subject] - [Chapter] Previous Year Questions*"
2. Show total number of questions found
3. Format each question cleanly:
   - Question number
   - [Marks, Year, Type] in brackets
   - Question on next line
4. Use emojis: 📝 ✅ 📌 ⭐
5. Add a motivational closing line
6. Remove all HTML tags
7. Write in Hinglish (Hindi-English mix)

Format example:
📚 *Physics - Electric Charges ke PYQ*

✅ Total 11 questions mile

📝 *Question 1* [1 mark, 2025]
One coulomb charge has _____ electrons.

📝 *Question 2* [3 marks, 2025]
Vidyut aavesh ke quantisation ka mathematical form likhiye.

...

⭐ *In sabhi questions ko solve karke apni preparation strong banao!*
"""

        user_prompt = f"""Subject: {verified_subject}
Chapter: {matched_chapter}
Total Questions: {questions_count}

Questions List:
{questions_text}

Please format these questions into an engaging WhatsApp message."""

        # Call GPT
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )

        formatted_message = response.choices[0].message.content.strip()
        logger.info(f"[ExamFormatter] Successfully formatted {questions_count} questions")

        return formatted_message

    except Exception as e:
        logger.error(f"[ExamFormatter] Error formatting questions: {e}")
        # Fallback to simple formatting
        return format_questions_simple(response_data, language)


def format_questions_simple(response_data: Dict[str, Any], language: str = "hindi") -> str:
    """
    Simple fallback formatting without GPT.

    Args:
        response_data: Response from exam API
        language: User's preferred language

    Returns:
        Simply formatted message
    """
    try:
        questions = response_data.get("questions", [])
        questions_count = len(questions)
        matched_chapter = response_data.get("matched_chapter", "")
        verified_subject = response_data.get("verified_subject", "")

        if language.lower() == "hindi":
            header = f"📚 *{verified_subject} - {matched_chapter} के Previous Year Questions*\n\n"
            header += f"✅ कुल {questions_count} प्रश्न मिले\n\n"
        else:
            header = f"📚 *{verified_subject} - {matched_chapter} ke Previous Year Questions*\n\n"
            header += f"✅ Total {questions_count} questions mile\n\n"

        formatted = header

        for idx, q in enumerate(questions, 1):
            question_text = clean_html(q.get("question", ""))
            marks = q.get("marks", "")
            year = q.get("year", "")

            formatted += f"📝 *Question {idx}* [{marks} marks, {year}]\n"
            formatted += f"{question_text}\n\n"

        if language.lower() == "hindi":
            formatted += "⭐ *इन प्रश्नों को solve करके अपनी तैयारी मजबूत बनाएं!*"
        else:
            formatted += "⭐ *In questions ko solve karke apni preparation strong banao!*"

        return formatted

    except Exception as e:
        logger.error(f"[ExamFormatter] Error in simple formatting: {e}")
        return "Questions found! Please check the app for details."


def generate_personalized_pyq_message(
    user_query: str,
    api_response: List[Dict[str, Any]],
    chat_session_id: str,
    language: str = "hindi"
) -> str:
    """
    Generate a personalized message for PYQ PDF resources using GPT.

    Args:
        user_query: The user's original query
        api_response: List of response objects from API
        chat_session_id: The chat session ID for the deeplink
        language: User's preferred language

    Returns:
        A personalized message string with WhatsApp formatting
    """
    try:
        client = OpenAI(api_key=settings.openai_api_key)

        # Extract PDF links and titles from response
        resources = []
        for item in api_response:
            if item.get('pdfLink'):
                resources.append({
                    'title': item.get('displayTitle', 'Document'),
                    'link': item.get('pdfLink'),
                    'type': 'PDF'
                })
            elif item.get('videoLink'):
                resources.append({
                    'title': item.get('displayTitle', 'Video'),
                    'link': item.get('videoLink'),
                    'type': 'Video'
                })

        if not resources:
            logger.warning("[PYQ_PDF] No resources found in API response")
            return get_fallback_message("pyq_pdf", language)

        # Create formatted resource list with links for GPT
        resources_text = "\n".join([
            f"Title: {r['title']}\nLink: {r['link']}\nType: {r['type']}"
            for r in resources
        ])

        # Create the app deeplink
        app_deeplink = f"https://arivihan.com/deeplink?redirectTo=doubt&doubtId={chat_session_id}"

        if language.lower() == "hindi":
            system_prompt = """आप Ritesh Sir हैं, एक caring और experienced teacher जो Arivihan के CEO हैं - एक edtech platform जो 12th MP Board के students को board exams की तैयारी में मदद करता है। आप WhatsApp पर एक student के doubt का जवाब दे रहे हैं।
आपकी communication style:

Friendly Hinglish (Hindi + English mix) का उपयोग करें
Students को प्यार से "beta" कहकर संबोधित करें
Warm, encouraging और supportive रहें
WhatsApp-friendly रखें
Minimal emojis (maximum 2-3, naturally placed)
Bold formatting के लिए text का उपयोग करें (WhatsApp style)

जरूरी निर्देश:

एक warm, personalized greeting से शुरू करें जो उनके query को acknowledge करे (1-2 sentences)
फिर सभी resources को उनके EXACT links के साथ इस format में list करें:
Resource Title
[exact link यहाँ]
सभी resources list करने के बाद, यह EXACT message जोड़ें:
"Inke acche solutions aapko milenge app par. Simple Ask Doubt par puch sakte ho! "
अंत में, app deeplink add करें जो provide किया जाएगा, इस तरह के text के साथ:
App mein dekho:
[deeplink यहाँ]

Greeting छोटी और friendly रखें। सभी resource links और app deeplink include करना सुनिश्चित करें।"""
        else:
            system_prompt = """"You are Ritesh Sir, a caring and experienced teacher who is CEO of Arivihan - an edtech platform helping 12th MP Board students prepare for board exams. You're answering a student's doubt on WhatsApp.
Your communication style:
- Use friendly Hinglish (Hindi + English mix)
- Address students as "beta" affectionately
- Be warm, encouraging and supportive
- Keep it WhatsApp-friendly
- Use minimal emojis (2-3 max, placed naturally)
- Use *text* for bold formatting (WhatsApp style)
IMPORTANT INSTRUCTIONS:
1. Start with a warm, personalized greeting that acknowledges their query (1-2 sentences)
2. Then list ALL the resources provided with their EXACT links in this format:
   :page_facing_up: *Resource Title*
   [exact link here]
3. After listing all resources, add this EXACT message:
   "Inke acche solutions aapko milenge app par. Simple *Ask Doubt* par puch sakte ho! :blush:"
4. Finally, add the app deeplink that will be provided with text like:
   :point_right: *App mein dekho:*
   [deeplink here]
Keep the greeting short and friendly. Make sure to include ALL resource links and the app deeplink."""

        user_prompt = f"""Student Query: {user_query}

Resources to share with student:
{resources_text}

App Deeplink: {app_deeplink}

Generate the COMPLETE WhatsApp message including:
1. Warm greeting
2. ALL resource links in proper format
3. The solutions message
4. The app deeplink at the end"""

        # Call GPT to generate the complete message
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        formatted_message = response.choices[0].message.content.strip()
        logger.info("[PYQ_PDF] Generated personalized message successfully")

        return formatted_message

    except Exception as e:
        logger.error(f"[PYQ_PDF] Error generating personalized message: {e}")
        return get_fallback_message("pyq_pdf", language)


def get_fallback_message(classified_as: str, language: str = "hindi") -> str:
    """
    Get fallback message for exam queries that don't have specific responses.

    Args:
        classified_as: The exam sub-classification type
        language: User's preferred language

    Returns:
        Appropriate fallback message
    """
    fallback_messages = {
        "pyq_pdf": {
            "hinglish": """📄 *Previous Year Papers PDF chahiye?*

📲 *Arivihan app download karo* - aapko sabhi PYQ papers milenge!

✨ *App mein kya milega*:
✅ Chapter-wise questions (solved)
✅ Full papers PDF
✅ Subject-wise organized
✅ Free download

*Abhi install karo Arivihan app!* 📲
👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId""",

            "hindi": """📄 *पिछले वर्षों के पेपर्स PDF चाहिए?*

📲 *अरिविहान ऐप डाउनलोड करो* - आपको सभी PYQ papers मिलेंगे!

✨ *ऐप में क्या मिलेगा*:
✅ Chapter-wise प्रश्न (solved)
✅ Full papers PDF
✅ Subject-wise organized
✅ Free download

*अभी इंस्टॉल करो अरिविहान ऐप!* 📲
👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId"""
        },

        "asking_syllabus": {
            "hinglish": """📚 *Syllabus chahiye?*

📲 *Arivihan app* par complete syllabus milega!

✨ *Kya milega*:
✅ Latest syllabus
✅ Chapter-wise breakdown
✅ Marking scheme
✅ Important topics highlighted

*Abhi check karo Arivihan app mein!* 📲
👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId""",

            "hindi": """📚 *सिलेबस चाहिए?*

📲 *अरिविहान ऐप* पर complete syllabus मिलेगा!

✨ *क्या मिलेगा*:
✅ Latest syllabus
✅ Chapter-wise breakdown
✅ Marking scheme
✅ Important topics highlighted

*अभी चेक करो अरिविहान ऐप में!* 📲
👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId"""
        },

        "asking_exam_pattern": {
            "hinglish": """📋 *Exam pattern ka detail chahiye?*

📲 *Arivihan app* download karo - complete exam pattern detail milega!

✨ *Aapko milega*:
✅ Paper structure
✅ Marking scheme
✅ Time management tips
✅ Section-wise breakdown

*Abhi dekho app mein!* 📲
👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId""",

            "hindi": """📋 *परीक्षा पैटर्न का विवरण चाहिए?*

📲 *अरिविहान ऐप* डाउनलोड करो - complete exam pattern detail मिलेगा!

✨ *आपको मिलेगा*:
✅ Paper structure
✅ Marking scheme
✅ Time management tips
✅ Section-wise breakdown

*अभी देखो ऐप में!* 📲
👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId"""
        }
    }

    # Default fallback for unknown types
    default_message = {
        "hinglish": """📲 *Arivihan app download karo* - aapke sabhi exam related queries ka answer milega!

👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId""",

        "hindi": """📲 *अरिविहान ऐप डाउनलोड करो* - आपके सभी परीक्षा से संबंधित प्रश्नों का उत्तर मिलेगा!

👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId"""
    }

    lang_key = "hindi" if language.lower() == "hindi" else "hinglish"

    if classified_as in fallback_messages:
        return fallback_messages[classified_as][lang_key]
    else:
        return default_message[lang_key]


async def format_exam_response(exam_response: Dict[str, Any], language: str = "hindi", user_query: str = "", subject: str = "", chat_session_id: str = "default") -> Dict[str, Any]:
    """
    Main function to format exam responses.

    Args:
        exam_response: Complete exam API response
        language: User's preferred language

    Returns:
        Updated response with formatted message
    """
    try:
        # Extract response data
        response = exam_response.get("response", {})
        classified_as = exam_response.get("classifiedAs", "")
        open_whatsapp = exam_response.get("openWhatsapp", False)

        # Check if response is empty
        if isinstance(response, dict):
            response_text = response.get("text", "")
            query_type = response.get("queryType", "")
        else:
            # Response is a string or other type
            response_text = str(response) if response else ""
            query_type = ""

        is_empty_response = not response_text or response_text.strip() == ""

        logger.info(f"[ExamFormatter] Processing - classifiedAs: {classified_as}, openWhatsapp: {open_whatsapp}, is_empty: {is_empty_response}, query_type: {query_type}")

        if query_type == "asking_pyq_question" and "questions" in response:
            # Format the questions
            formatted_message = format_pyq_questions(response, language)

            # Update the response with formatted message
            exam_response["formatted_response"] = formatted_message
            exam_response["has_formatted_response"] = True

            logger.info("[ExamFormatter] Exam response formatted successfully")

        elif classified_as == "pyq_pdf" or classified_as == "pyq_request":
            # Handle PYQ PDF - the exam API should return resources
            logger.info(f"[ExamFormatter] Processing {classified_as} - checking for resources in exam API response")

            # Extract resources from response.data structure
            api_resources = []

            if isinstance(response, dict) and "data" in response:
                raw_resources = response.get("data", [])
                logger.info(f"[ExamFormatter] Found {len(raw_resources)} raw resources")

                # Map the response format to expected format
                for item in raw_resources:
                    mapped_resource = {
                        'displayTitle': item.get('Title', 'Document'),
                        'pdfLink': item.get('download_link', ''),
                        'type': 'PDF',
                        'subject': item.get('Subject', ''),
                        'class': item.get('Class', ''),
                        'year': item.get('Year', ''),
                        'language': item.get('language', '')
                    }
                    if mapped_resource['pdfLink']:  # Only add if there's a valid link
                        api_resources.append(mapped_resource)

            logger.info(f"[ExamFormatter] Mapped {len(api_resources)} resources")

            if api_resources and len(api_resources) > 0:
                # Generate personalized message using resources from exam API
                personalized_message = generate_personalized_pyq_message(
                    user_query,
                    api_resources,
                    chat_session_id,
                    language
                )

                exam_response["formatted_response"] = personalized_message
                exam_response["has_formatted_response"] = True
                exam_response["resources"] = api_resources

                logger.info(f"[ExamFormatter] Generated personalized PYQ PDF message with {len(api_resources)} resources")
            else:
                # No resources found in exam API response, use fallback
                fallback_message = get_fallback_message("pyq_pdf", language)
                exam_response["formatted_response"] = fallback_message
                exam_response["has_formatted_response"] = True

                logger.warning("[ExamFormatter] No resources found in exam API response for pyq_pdf, using fallback")

        elif classified_as == "app_data_related" and query_type:
            # Handle app_data_related with query_type (test_full_length, test_chapterwise, etc.)
            from app.services.content_responses import get_content_response

            logger.info(f"[ExamFormatter] Processing app_data_related with query_type: {query_type}")

            # Map query_type to content_type
            content_response = get_content_response(query_type, language)

            exam_response["formatted_response"] = content_response
            exam_response["has_formatted_response"] = True

            logger.info(f"[ExamFormatter] Content response provided for query_type: {query_type}")

        elif is_empty_response or open_whatsapp:
            # Provide fallback message for empty responses
            fallback_message = get_fallback_message(classified_as, language)

            exam_response["formatted_response"] = fallback_message
            exam_response["has_formatted_response"] = True

            logger.info(f"[ExamFormatter] Fallback message provided for: {classified_as}")

        else:
            # For other exam types, keep original response
            exam_response["has_formatted_response"] = False
            logger.info(f"[ExamFormatter] No formatting needed for query type: {query_type}")

        return exam_response

    except Exception as e:
        logger.error(f"[ExamFormatter] Error formatting exam response: {e}")
        exam_response["has_formatted_response"] = False
        return exam_response
