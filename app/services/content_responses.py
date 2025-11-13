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

*Lagta h sab samajh aa gaya?* 🤔

👉 *To fir pakka pata karne ka ek hi tarika h - TEST DO!*

🎯 *Chapter-wise test mein check hoga:*

✅ *Sare derivations* yaad h ya nahi
✅ *Formulas* sahi se apply ho rahe h ya nahi
✅ *Concepts* clear h ya confusion h
✅ Kahan *revision* ki zaroorat h

📝 *Ek chapter khatam kiya? Turant test do!*

💡 Agar marks ache aaye → Next chapter
💡 Agar marks kam aaye → Revision karo phir aage badho

Chapter-wise test do:
📘 *Physics*: [link]
🧪 *Chemistry*: [link]
➗ *Maths*: [link]
🧬 *Biology*: [link]

*Har chapter ko properly complete karne ke liye Arivihan app download karo!* 📲

👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId""",

        "hindi": """📚 *अध्याय पूरा कर लिया?*

*लगता है सब समझ आ गया?* 🤔

👉 *तो फिर पक्का पता करने का एक ही तरीका है - टेस्ट दो!*

🎯 *अध्याय-वार टेस्ट में जाँच होगी:*

✅ *सारे व्युत्पन्न* याद हैं या नहीं
✅ *सूत्र* सही से लागू हो रहे हैं या नहीं
✅ *अवधारणाएँ* स्पष्ट हैं या भ्रम है
✅ कहाँ *पुनरावृत्ति* की ज़रूरत है

📝 *एक अध्याय खत्म किया? तुरंत टेस्ट दो!*

💡 अगर अंक अच्छे आये → अगला अध्याय
💡 अगर अंक कम आये → पुनरावृत्ति करो फिर आगे बढ़ो

अध्याय-वार टेस्ट दो:
📘 *भौतिकी*: [link]
🧪 *रसायन विज्ञान*: [link]
➗ *गणित*: [link]
🧬 *जीव विज्ञान*: [link]

*हर अध्याय को ठीक से पूरा करने के लिए अरिविहान ऐप डाउनलोड करो!* 📲

👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId"""
    },

    "test_full_length": {
        "hinglish": """⏰ *Exam mein time pe paper khatam nahi hota?*

*Padh to lete ho... par exam mein marks nahi aate?* 😟

🎯 *Problem kya h?*

❌ Sirf padhna kaafi nahi h
❌ Practice ke bina kuch nahi hota h
❌ *Real exam jaisa test* dena bahut zaroori h!

✨ *Arivihan par aaj hi test do aur pata karo:*

✅ Tumhari *speed* kitni h
✅ *Time management* kaise improve karna h
✅ Kaun se *questions* skip karne chahiye
✅ Kahan *marks cut* rahe h

📝 *Test doge tabhi to pata chalega - taiyaari kaisi h!*

Abhi test do:
📘 *Physics*: [link]
🧪 *Chemistry*: [link]
➗ *Maths*: [link]
🧬 *Biology*: [link]

*Exam se pehle apni preparation test karo - Arivihan app download karo!* 📲

👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId""",

        "hindi": """⏰ *परीक्षा में समय पर पेपर खत्म नहीं होता?*

*पढ़ तो लेते हो... पर परीक्षा में अंक नहीं आते?* 😟

🎯 *समस्या क्या है?*

❌ सिर्फ पढ़ना काफी नहीं है
❌ अभ्यास के बिना कुछ नहीं होता है
❌ *असली परीक्षा जैसा टेस्ट* देना बहुत ज़रूरी है!

✨ *अरिविहान पर आज ही टेस्ट दो और पता करो:*

✅ तुम्हारी *गति* कितनी है
✅ *समय प्रबंधन* कैसे सुधारना है
✅ कौन से *प्रश्न* छोड़ने चाहिए
✅ कहाँ *अंक कट* रहे हैं

📝 *टेस्ट दोगे तभी तो पता चलेगा - तैयारी कैसी है!*

अभी टेस्ट दो:
📘 *भौतिकी*: [link]
🧪 *रसायन विज्ञान*: [link]
➗ *गणित*: [link]
🧬 *जीव विज्ञान*: [link]

*परीक्षा से पहले अपनी तैयारी जाँचो - अरिविहान ऐप डाउनलोड करो!* 📲

👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId"""
    },

    "lecture": {
        "hinglish": """❌ *Lecture mein neend aa jati h?*

❌ *Sirf sunne se samajh nahi aata?*

✅ *Ab lectures BORING nahi rahenge!*

🎯 *Arivihan ke special lectures:*

✨ Teacher aapse sawal puchenge - aur aap bolkar jawab doge, bilkul class ki tarah!
✨ Beech mein koi cheez *samajh nahi aayi*? Ruko mat - wahi lecture mein *turant doubt pooch lo* aur clear kar lo!
✨ Bas sunna nahi - *ab padhna bhi h*

📚 Ye h *padhne ka asli tarika*

Ek baar try karo:
📘 *Physics*: [link]
🧪 *Chemistry*: [link]
➗ *Maths*: [link]
🧬 *Biology*: [link]

*Real classroom experience ke liye Arivihan app download karo!* 📲

👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId""",

        "hindi": """❌ *लेक्चर में नींद आ जाती है?*

❌ *सिर्फ सुनने से समझ नहीं आता?*

✅ *अब lectures BORING नहीं रहेंगे!*

🎯 *अरिविहान के special lectures:*

✨ टीचर आपसे सवाल पूछेंगे - और आप बोलकर जवाब दोगे, बिल्कुल क्लास की तरह!

✨ बीच में कोई चीज़ *समझ नहीं आई?* रुको मत - वहीं लेक्चर में *तुरंत doubt पूछ लो* और clear कर लो!

✨ बस सुनना नहीं - *अब पढ़ना भी है*

📚 ये है *पढ़ने का असली तरीका*

एक बार try करो:
📘 *भौतिकी*: [link]
🧪 *रसायन विज्ञान*: [link]
➗ *गणित*: [link]
🧬 *जीव विज्ञान*: [link]

*Real classroom experience के लिए अरिविहान app download करो!* 📲

👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId"""
    },

    "toppers_notes": {
        "hinglish": """🏆 *Toppers kaise padhte the?*

*Soch rahe ho toppers ka secret kya h?*
Ab tumhe bhi mil sakta h! ✨

📝 *Arivihan par milte h TOPPERS NOTES!*

🎯 Kya unique h:
✅ MP Board ke *real toppers ke notes*
✅ Dekho *toppers kaise padhte the*
✅ Unki study technique samjho
✅ Same pattern follow karo = Better results

💡 Toppers ka secret ab tumhara secret!

Toppers ki strategy khud dekho:
📘 *Physics*: [link]
🧪 *Chemistry*: [link]
➗ *Maths*: [link]
🧬 *Biology*: [link]

*Toppers jaise padhne ke liye abhi install karo Arivihan app!* 📲
👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId""",

        "hindi": """🏆 *टॉपर्स कैसे पढ़ते थे?*

*सोच रहे हो टॉपर्स का सीक्रेट क्या है?*
अब तुम्हें भी मिल सकता है! ✨

📝 *अरिविहान पर मिलते हैं TOPPERS NOTES!*

🎯 क्या यूनिक है:
✅ MP Board के *असली टॉपर्स के नोट्स*
✅ देखो *टॉपर्स कैसे पढ़ते थे*
✅ उनकी स्टडी टेक्निक समझो
✅ Same pattern फॉलो करो = बेहतर रिजल्ट्स

💡 टॉपर्स का सीक्रेट अब तुम्हारा सीक्रेट!

टॉपर्स की स्ट्रेटेजी खुद देखो:
📘 *भौतिकी*: [link]
🧪 *रसायन विज्ञान*: [link]
➗ *गणित*: [link]
🧬 *जीव विज्ञान*: [link]

*टॉपर्स जैसे पढ़ने के लिए अभी इंस्टॉल करो अरिविहान ऐप!* 📲
👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId"""
    },

    "notes": {
        "hinglish": """📖 *Lecture Notes chahiye?*

*Padhai karte time notes banane mein time waste ho jata h?*
Ab nahi! ❌

✨ *Arivihan par milte h complete PPT Notes!*

🎯 Kya fayda h:
✅ Notes banane ki *tension khatam*
✅ Apna pura dhyan *sirf padhne par* do
✅ Chapter-wise organized aur sath hi Lecture-wise bhi

👀 Dekhne mein kya ja raha h? Ek baar check karo:
📘 *Physics*: [link]
🧪 *Chemistry*: [link]
➗ *Maths*: [link]
🧬 *Biology*: [link]

*Sabhi chapters ke Lecture Notes ke liye abhi install karo Arivihan app!* 📲
👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId""",

        "hindi": """📖 *लेक्चर नोट्स चाहिए?*

*पढ़ाई करते समय नोट्स बनाने में समय बर्बाद हो जाता है?*
अब नहीं! ❌

✨ *अरिविहान पर मिलते हैं complete PPT Notes!*

🎯 क्या फायदा है:
✅ नोट्स बनाने की *टेंशन खत्म*
✅ अपना पूरा ध्यान *सिर्फ पढ़ने पर* दो
✅ Chapter-wise organized और साथ ही Lecture-wise भी

👀 देखने में क्या जा रहा है? एक बार चेक करो:
📘 *भौतिकी*: [link]
🧪 *रसायन विज्ञान*: [link]
➗ *गणित*: [link]
🧬 *जीव विज्ञान*: [link]

*सभी अध्यायों के लेक्चर नोट्स के लिए अभी इंस्टॉल करो अरिविहान ऐप!* 📲
👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId"""
    },

    "important_questions": {
        "hinglish": """📚 *Important Questions chahiye?*

*Arivihan par sirf questions nahi milte…*
✨ Har question ka *DETAILED EXPLANATION* milta h!

🎯 *Kya special h*:
✅ 1 mark questions ka bhi *pura explanation* (jo kahin nahi milta!)
✅ Common mistakes *bataye jate h* - exam mein kya galti NAHI karni
✅ Examiner kya dekhta h - ye bhi *samjhaya jata h*
✅ Step-by-step solution har question ka

😎 Vishwas nahi hota? Pehle dekh lo:
📘 *Physics*: [link]
🧪 *Chemistry*: [link]
➗ *Maths*: [link]
🧬 *Biology*: [link]

*Sabhi chapters ke Important Questions se padhne ke liye abhi install karo Arivihan app!* 📲
👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId""",

        "hindi": """📚 *महत्वपूर्ण प्रश्न चाहिए?*

*अरिविहान पर सिर्फ प्रश्न नहीं मिलते…*
✨ हर प्रश्न की *विस्तृत व्याख्या* मिलती है!

🎯 *क्या खास है*:
✅ 1 अंक के प्रश्नों की भी *पूरी व्याख्या* (जो कहीं नहीं मिलती!)
✅ सामान्य गलतियाँ *बताई जाती हैं* - परीक्षा में क्या गलती नहीं करनी है
✅ परीक्षक क्या देखता है - यह भी *समझाया जाता है*
✅ हर प्रश्न का चरण-दर-चरण हल है

😎 विश्वास नहीं होता? पहले देख लो:
📘 *भौतिकी*: [link]
🧪 *रसायन विज्ञान*: [link]
➗ *गणित*: [link]
🧬 *जीव विज्ञान*: [link]

*सभी अध्यायों के महत्वपूर्ण प्रश्नों से पढ़ने के लिए अभी इंस्टॉल करो अरिविहान ऐप!* 📲
👉 https://arivihan.com/deeplink?redirectTo=doubt&doubtId=chatSessionId"""
    }
}


def get_content_response(content_type: str, language: str = "hindi") -> str:
    """
    Get the appropriate content response based on content type and language.

    Args:
        content_type: One of: lecture, notes, toppers_notes, test_chapterwise, test_full_length
        language: Hindi or Hinglish (default: Hinglish)

    Returns:
        Formatted response string
    """
    try:
        # Normalize language
        lang_key = "hindi" if language.lower() == "hindi" else "hinglish"

        # Get response template
        if content_type in CONTENT_RESPONSES:
            response = CONTENT_RESPONSES[content_type][lang_key]
            logger.info(f"[ContentResponses] Generated {content_type} response in {lang_key}")
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
