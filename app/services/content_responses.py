"""
Content response templates for app-related queries.
Contains predefined responses for lecture, notes, tests in Hindi and Hinglish.
"""
from typing import Dict, Any
from app.core.logging_config import logger


# Response templates for each content type
CONTENT_RESPONSES = {
    "test_chapterwise": {
        "hinglish": """📚 *Chapter complete kar liya?*

👉 *To fir TEST DO aur apni taiyari check karo!*

🎯 *Chapter-wise test mein check hoga:*
✅ Derivations yaad h ya nahi
✅ Formulas sahi apply ho rahe h
✅ Concepts clear h ya confusion h

*Har chapter ko properly complete karne ke liye test do:*
📲 https://arivihan.com/deeplink?redirectTo=test-series-intro&type=REATTEMPT&testId=PHYTest1&id=board&position=0&subject=overall&combined=true

*Arivihan app se apni taiyari ko aur strong banao!* 💪""",

        "hindi": """📚 *अध्याय पूरा कर लिया?*

👉 *तो फिर टेस्ट दो और अपनी तैयारी चेक करो!*

🎯 *अध्याय-वार टेस्ट में चेक होगा:*
✅ व्युत्पत्ति (Derivations) याद हैं या नहीं
✅ सूत्र सही से लागू हो रहे हैं या नहीं
✅ अवधारणाएं स्पष्ट हैं या भ्रम है

*हर अध्याय को ठीक से पूरा करने के लिए टेस्ट दो:*
📲 https://arivihan.com/deeplink?redirectTo=test-series-intro&type=REATTEMPT&testId=PHYTest1&id=board&position=0&subject=overall&combined=true

*अरिविहान ऐप से अपनी तैयारी को और मजबूत बनाओ!* 💪""",
    },

    "test_full_length": {
        "hinglish": """⏰ *Exam mein time pe paper khatam nahi hote?*

*Padh to lete ho... par marks nahi aate?* 😟

✨ *Arivihan par aaj hi test do aur pata karo:*
✅ Tumhari *speed* kitni hai
✅ *Time management* kaise improve karein
✅ Kahan *marks cut* rahe hain

📝 *Test doge tabhi pata chalega - taiyaari kaisi hai!*

*Abhi test do:*
📲 https://arivihan.com/deeplink?redirectTo=test-series-intro&type=REATTEMPT&testId=PHYTest1&id=board&position=0&subject=overall&combined=true

*Arivihan app se apni taiyaari ko perfect banao!* 💪
""",

        "hindi": """⏰ *परीक्षा में समय पर पेपर खत्म नहीं होते?*

*पढ़ तो लेते हो... पर अंक नहीं आते?* 😟

✨ *अरिविहान पर आज ही टेस्ट दो और पता करो:*
✅ तुम्हारी *गति* कितनी है
✅ *समय प्रबंधन* कैसे सुधारें
✅ कहाँ *अंक कट* रहे हैं

📝 *टेस्ट दोगे तभी पता चलेगा - तैयारी कैसी है!*

*अभी टेस्ट दो:*
📲 https://arivihan.com/deeplink?redirectTo=test-series-intro&type=REATTEMPT&testId=PHYTest1&id=board&position=0&subject=overall&combined=true

*अरिविहान ऐप से अपनी तैयारी को परफेक्ट बनाओ!* 💪
"""
    },

    "lecture": {
        "hinglish": """

🎯 *Arivihan ke special lectures aaj hi dekhiye:*

✨ Jaha teacher  aapse sawal puchenge - aap bolkar jawab doge!
✨ Beech mein doubt aaye? *To turant pooch lo aur clear kar lo!*
✨ Bas sunna nahi - *ab padhna bhi hai*

📚 *Ye hai padhne ka asli tarika!*

*Abhi try karo:*
📲 https://arivihan.com/deeplink?redirectTo=chapter-list&SubjectId=9&SubjectName=Physics&SubjectCode=Physics&preExamPreparation=false

*Arivihan app se real classroom experience lo!* 💪
""",

        "hindi": """

🎯 *अरिविहान के विशेष लेक्चर आज ही देखिए:*

✨ जहाँ शिक्षक आपसे सवाल पूछेंगे - आप बोलकर जवाब दोगे!
✨ बीच में संदेह आए? *तो तुरंत पूछ लो और स्पष्ट कर लो!*
✨ बस सुनना नहीं - *अब पढ़ना भी है*

📚 *यह है पढ़ने का असली तरीका!*

*अभी कोशिश करो:*
📲 https://arivihan.com/deeplink?redirectTo=chapter-list&SubjectId=9&SubjectName=Physics&SubjectCode=Physics&preExamPreparation=false

*अरिविहान ऐप से वास्तविक कक्षा का अनुभव लो!* 💪
"""
    },

    "toppers_notes": {
        "hinglish": """

📝 *Arivihan par milte hain TOPPERS NOTES!*

🎯 Kya unique hai:
✅ MP Board ke *real toppers ke notes*
✅ Dekho *toppers kaise padhte the*
✅ Unki study technique samjho
✅ Same pattern follow karo = Better results

💡 *Toppers ka secret ab tumhara secret!*

*Toppers ki strategy dekho:*
📲 https://arivihan.com/deeplink?redirectTo=topper-notes&overall=false&preExamPreparation=false

*Toppers jaise padhne ke liye Arivihan app install karo!* 💪
""",

        "hindi":"""

📝 *अरिविहान पर मिलते हैं टॉपर्स नोट्स!*

🎯 क्या अनोखा है:
✅ एमपी बोर्ड के *असली टॉपर्स के नोट्स*
✅ देखो *टॉपर्स कैसे पढ़ते थे*
✅ उनकी अध्ययन तकनीक समझो
✅ वही पैटर्न फॉलो करो = बेहतर परिणाम

💡 *टॉपर्स का रहस्य अब तुम्हारा रहस्य!*

*टॉपर्स की रणनीति देखो:*
📲 https://arivihan.com/deeplink?redirectTo=topper-notes&overall=false&preExamPreparation=false

*टॉपर्स जैसे पढ़ने के लिए अरिविहान ऐप इंस्टॉल करो!* 💪
"""
    },

    "notes": {
        "hinglish": """
✨ *Arivihan par milte hain complete PPT Notes!*

🎯 Kya fayda hai:
✅ Notes banane ki *tension khatam*
✅ Apna pura dhyan *sirf padhne par* do
✅ Chapter-wise aur Lecture-wise organized

*Sabhi chapters ke Lecture Notes yahan:*
📲 https://arivihan.com/lecture-notes

*Complete notes ke liye Arivihan app install karo!* 💪
""",

        "hindi": """
✨ *अरिविहान पर मिलते हैं संपूर्ण पीपीटी नोट्स!*

🎯 क्या फायदा है:
✅ नोट्स बनाने की *टेंशन खत्म*
✅ अपना पूरा ध्यान *सिर्फ पढ़ने पर* दो
✅ अध्याय-वार और लेक्चर-वार व्यवस्थित

*सभी अध्यायों के लेक्चर नोट्स यहाँ:*
📲 https://arivihan.com/lecture-notes

*संपूर्ण नोट्स के लिए अरिविहान ऐप इंस्टॉल करो!* 💪
"""
    },

    "important_questions": {
        "hinglish": """📚 *Arivihan par milte hain - Important Notes!*

🎯 *Kya special hai*:
✅ 1 mark questions ka bhi *pura explanation*
✅ Common mistakes *bataye jate hain* - exam mein kya galti NAHI karni
✅ Examiner kya dekhta hai - ye bhi *samjhaya jata hai*
✅ Step-by-step solution har question ka

*Sabhi chapters ke Important Questions yahan:*
📲 https://arivihan.com/important-questions

*Detailed explanations ke liye Arivihan app install karo!* 💪
""",

        "hindi":  """📚 *अरिविहान पर मिलते हैं - महत्वपूर्ण नोट्स!*

🎯 *क्या विशेष है*:
✅ 1 अंक के प्रश्नों का भी *पूरा स्पष्टीकरण*
✅ सामान्य गलतियाँ *बताई जाती हैं* - परीक्षा में क्या गलती नहीं करनी
✅ परीक्षक क्या देखता है - यह भी *समझाया जाता है*
✅ हर प्रश्न का चरण-दर-चरण समाधान

*सभी अध्यायों के महत्वपूर्ण प्रश्न यहाँ:*
📲 https://arivihan.com/important-questions

*विस्तृत स्पष्टीकरण के लिए अरिविहान ऐप इंस्टॉल करो!* 💪
""" 
    }
}


def get_content_response(content_type: str, language: str = "hindi") -> str:
    """
    Get the appropriate content response based on content type and language.

    Args:
        content_type: One of: lecture, notes, toppers_notes, test_chapterwise, test_full_length,
                      chapterwise, full_length (API naming)
        language: Hindi or Hinglish (default: Hinglish)

    Returns:
        Formatted response string
    """
    try:
        # Normalize language
        lang_key = "hindi" if language.lower() == "hindi" else "hinglish"

        # Map API naming to CONTENT_RESPONSES keys
        content_type_mapping = {
            "full_length": "test_full_length",
            "chapterwise": "test_chapterwise",
            # Keep original keys for backward compatibility
            "test_full_length": "test_full_length",
            "test_chapterwise": "test_chapterwise",
            "lecture": "lecture",
            "notes": "notes",
            "toppers_notes": "toppers_notes",
            "important_questions": "important_questions"
        }

        # Get the mapped content type
        mapped_type = content_type_mapping.get(content_type, content_type)

        # Get response template
        if mapped_type in CONTENT_RESPONSES:
            response = CONTENT_RESPONSES[mapped_type][lang_key]
            logger.info(f"[ContentResponses] Generated {mapped_type} response (from {content_type}) in {lang_key}")
            return response
        else:
            # Default to lecture response if content_type not found
            logger.warning(f"[ContentResponses] Unknown content_type: {content_type}, defaulting to lecture")
            return CONTENT_RESPONSES["lecture"][lang_key]

    except Exception as e:
        logger.error(f"[ContentResponses] Error getting response: {e}")
        # Fallback response
        return "📲 *Arivihan app download karo aur apni padhai shuru karo!*\n\n👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId"


def app_content_main(json_data: Dict[str, Any], initial_classification: str, content_type: str) -> Dict[str, Any]:
    """
    Main entry point for app content processing.

    Args:
        json_data: Request data with message, language
        initial_classification: Classification result
        content_type: Type of content requested (lecture, notes, etc.)

    Returns:
        Complete response dict with classification and response
    """
    try:
        # Normalize language to API format (only "english" or "hindi" accepted)
        raw_language = json_data.get("language", "hindi")
        language = raw_language.lower() if raw_language else "hindi"
        # Map hindlish to hindi since API only accepts english/hindi
        if language == "hindlish":
            language = "hindi"

        logger.info(f"[AppContent] Processing app content request")
        logger.info(f"  Content Type: {content_type}")
        logger.info(f"  Language: {language}")

        # Get the appropriate response
        response_text = get_content_response(content_type, language)

        # Build response
        result = {
            "initialClassification": initial_classification,
            "classifiedAs": "app_related",
            "contentType": content_type,
            "response": response_text,
            "openWhatsapp": False,
            "responseType": "text",
            "actions": "",
            "microLecture": "",
            "testSeries": "",
        }

        logger.info("[AppContent] App content response completed")
        return result

    except Exception as e:
        logger.error(f"[AppContent] Error in app_content_main: {e}")

        # Error fallback
        result = {
            "initialClassification": initial_classification,
            "classifiedAs": "app_related",
            "contentType": content_type,
            "response": "📲 *Arivihan app download karo!*\n\n👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId",
            "openWhatsapp": False,
            "responseType": "text",
            "actions": "",
            "microLecture": "",
            "testSeries": "",
        }
        return result
