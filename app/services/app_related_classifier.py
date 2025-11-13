import time
import pandas as pd
from openai import OpenAI
import os
import re
import time
import logging
from dotenv import load_dotenv
from app.services.app_related_screen import app_screen_related_main



load_dotenv() 


logging.basicConfig(
    filename='ml.log',             
    level=logging.INFO,              
    format='%(asctime)s - %(levelname)s - %(message)s'  
)
logger = logging.getLogger()

OPENAI_ORGANIZATION = os.getenv("OPENAI_ORGANIZATION")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL_MINI", "gpt-4.1-mini")



# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

class ClassifierAgent:
    def __init__(self, client):
        self.client = client
        self.categories = {
            'app_data_related': 'Questions about accessing lectures, notes, tests, or PYQs.',
            'subscription_data_related': 'Questions about subscription plans, pricing, or coupon codes.',
            'screen_data_related': 'Questions about navigation, where to click, technical issues, or unclear content.'
        }
        self.valid_categories = set(self.categories.keys())

    def classify(self, question):
        system_prompt = f"""You are a classification assistant for a student query system. Your job is to classify each query into exactly ONE of the following categories based on the user's **primary intent and main action**.

Return ONLY one of the following:
→ app_data_related
→ subscription_data_related  
→ screen_data_related

---

## 🔍 **CLASSIFICATION LOGIC** (Follow this order):

### **STEP 1: Check Primary Action Intent**

🔸 **If the PRIMARY ACTION is about HOW-TO/NAVIGATION/DOWNLOAD PROCESS** → **screen_data_related**

**Navigation/Process Keywords (HIGH PRIORITY):**
- **Download Process**: "download kaise", "download kahan se", "download hoge kahan", "download karu kaise", "download nahi ho raha", "download kar sakta hun"
- **How-to Actions**: "kaise use", "kaise login", "kaise access", "kaise start", "kaise open", "kaise banaye", "kaise karu"
- **Technical Help**: "crash", "not working", "button nahi dikh raha", "error", "problem", "issue"
- **Account/Profile**: "login", "signup", "profile setup", "account banaye", "register kaise"
- **App Navigation**: "kahan milega feature", "kahan hai option", "kahan se access", "menu kahan hai"
- **App Features**: "batch kya hai", "feature kya hai", "app me kya hai", "kaise kaam karta hai"

### **STEP 2: Check Content Access Intent**

🔹 **If the PRIMARY ACTION is about ACCESSING/GETTING SPECIFIC CONTENT** → **app_data_related**

**Content Access Keywords:**
- **Want Content**: "chahiye", "dena h", "dekhna h", "padhna h", "karna h", "mil sakta hai"
- **Get Content**: "milega", "available hai", "do", "provide", "bhej do", "de do"
- **Content Types**: "test", "lecture", "notes", "PYQ", "chapter", "video", "class", "mock test"
- **Study Materials**: "ppt notes", "handwritten notes", "formula sheet", "summary", "papers"

### **STEP 3: Check Subscription Intent**

🔸 **If about PLANS/PRICING/PAYMENT** → **subscription_data_related**

---

## 📋 **DETAILED CATEGORIES**

### 🟠 **screen_data_related** (Navigation/How-to/Technical)

Use when the **main focus** is on:
- **Download Process**: How to download, where to download from, download procedure, download issues
- **App Usage**: How to use features, navigate, access functions, find options
- **Technical Issues**: App crashes, buttons not visible, login problems, errors
- **Account Management**: Profile setup, login/signup process, registration
- **Feature Explanation**: What is batch, what is feature X, how does Y work
- **Navigation Help**: Where to find something in the app, how to reach a section

✅ **EXAMPLES**:
- "lecture kaha download hoge" → screen_data_related (download process)
- "notes kaise download karu" → screen_data_related (download method)
- "video download nahi ho raha" → screen_data_related (technical issue)
- "app kaise use karte hain" → screen_data_related (app usage)
- "login kaise karu" → screen_data_related (account access)
- "test kaise start karte hain" → screen_data_related (process help)
- "Unnati batch kya hota hai" → screen_data_related (feature explanation)
- "menu kahan hai" → screen_data_related (navigation)
- "profile kaise banate hain" → screen_data_related (account setup)
- "lecture kahan se access karu" → screen_data_related (navigation help)
- "notes download kar sakta hun kaise" → screen_data_related (download process)

### 🔹 **app_data_related** (Content Access/Availability)

Use when the **main focus** is on:
- **Getting specific educational content**: tests, lectures, notes, chapters, videos
- **Content availability**: Is X content available, content exists or not
- **Content requests**: Need/want specific study material
- **Taking/Using content**: Want to take test, watch lecture, read notes

✅ **EXAMPLES**:
- "mujhe physics ka test chahiye" → app_data_related (content request)
- "mujhe test dena h" → app_data_related (content usage)
- "chemistry ke lectures milege kya" → app_data_related (content availability)  
- "electric charge ka chapter dekhna h" → app_data_related (content access)
- "notes do biology ke" → app_data_related (content request)
- "mock test dena h" → app_data_related (content usage)
- "PYQ papers available hain" → app_data_related (content availability)
- "will I get chapter on electric charge" → app_data_related (content access)
- "physics ka lecture chahiye" → app_data_related (content request)
- "test attempt karna hai" → app_data_related (content usage)

### 🔸 **subscription_data_related** (Plans/Payment)

Use when the **main focus** is on:
- **Plans**: subscription plans, monthly/yearly plans, combo plans, plan features
- **Pricing**: cost, price, discount, offers, coupons, kitna paisa
- **Payment**: buy, purchase, payment process, unlock via payment
- **Plan Benefits**: what's included in plan, plan comparison

✅ **EXAMPLES**:
- "subscription plan kya hai" → subscription_data_related
- "PCM plan ka price kya hai" → subscription_data_related
- "payment kaise karu" → subscription_data_related
- "monthly plan me kya milta hai" → subscription_data_related
- "discount coupon hai kya" → subscription_data_related
- "plan khareedna hai" → subscription_data_related
- "unlock karne ke liye paisa lagta hai" → subscription_data_related

---

## 🎯 **KEY DECISION RULES**

### **Rule 1: Action-First Classification**
```
Question: "lecture kaha download hoge"
Primary Action: DOWNLOAD PROCESS (how/where to download)
Secondary Context: lecture (content type)
Classification: screen_data_related
```

### **Rule 2: Intent vs Context**
```
"notes kaise download karu" → screen_data_related (download process)
"notes chahiye chemistry ke" → app_data_related (content request)
```

### **Rule 3: Process vs Content**
```
"test kaise start karu" → screen_data_related (process help)
"test dena h physics ka" → app_data_related (content access)
```

### **Rule 4: Navigation vs Availability**
```
"lecture kahan milega" → screen_data_related (where to find in app)
"lecture available hai kya" → app_data_related (content availability)
```

---

## 🔧 **CLASSIFICATION PRIORITY ORDER**

1. **Check for DOWNLOAD/PROCESS words** → If found → **screen_data_related**
2. **Check for PLAN/PAYMENT words** → If found → **subscription_data_related**
3. **Check for CONTENT ACCESS intent** → If found → **app_data_related**
4. **Default to context-based classification**

---

## ⚠️ **COMMON MISTAKES TO AVOID**

❌ **Wrong**: "lecture download kaise karu" → app_data_related
✅ **Correct**: "lecture download kaise karu" → screen_data_related (download process)

❌ **Wrong**: "notes kahan se download hoge" → app_data_related  
✅ **Correct**: "notes kahan se download hoge" → screen_data_related (download location)

❌ **Wrong**: "test kaise attempt karu" → app_data_related
✅ **Correct**: "test kaise attempt karu" → screen_data_related (process help)

## 📌 **FINAL CHECK**

Ask yourself:
1. **Is the user asking HOW TO DO something?** → screen_data_related
2. **Is the user asking about PLANS/PAYMENT?** → subscription_data_related  
3. **Is the user asking for SPECIFIC CONTENT?** → app_data_related

**Remember**: The PRIMARY ACTION determines the category, not the subject matter.

---

**Query**: {question}
**Category**:"""

        user_prompt = system_prompt.format(question=question)

        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0,
                max_tokens=50
            )

            raw_response = response.choices[0].message.content.strip().lower()

            if raw_response in self.valid_categories:
                return raw_response
            else:
                logger.info(f"⚠️ Unrecognized response: {raw_response}")
                return 'screen_data_related'

        except Exception as e:
            logger.info(f"❌ Error in classification: {str(e)}")
            return 'screen_data_related'


class SupervisorAgent:
    def __init__(self, classifier_agent):
        self.classifier_agent = classifier_agent

    def handle_doubt(self, question):
        return self.classifier_agent.classify(question)


# Initialize agents
classifier_agent = ClassifierAgent(client)
supervisor_agent = SupervisorAgent(classifier_agent)

def normalize(text):
    # Lowercase
    text = text.lower()
    # Remove punctuation like apostrophes
    text = re.sub(r"[^\w\s]", "", text)
    # Remove extra whitespace
    text = text.strip()
    return text

async def app_related_classifier_main(json_data, user_id, initial_classification):
    """
    Main classifier for app-related queries with sub-classification:
    - subscription_data_related: Send promotional message
    - app_data_related: Route to app_handler
    - screen_data_related: Route to app_related_screen
    """
    question = json_data["userQuery"]

    logger.info(f"[Classifier App Related Main] app related main classification starts")

    app_classification = supervisor_agent.handle_doubt(question)
    logger.info(f"[Classifier App Related Main] Sub-classified as: {app_classification}")

    if app_classification == "subscription_data_related":
        logger.info(f"[Classifier App Related Main] subscription_data_related classification")

        # Send subscription promotional message
        subscription_message = """🔥 *Arre sunno sunno! Board Exams aa rahe hain!* 😱

*Tumhare dost UNNATI BATCH join kar chuke hain... aur tum?* 🤔

*Dekho kya miss ho raha hai:*

📚 LIVE Classes - ghar baithe school jaisa padhai! (Physics, Chemistry, Maths/Bio, English, Hindi + Arts & Commerce)
📝 3000+ Questions solve karoge - PYQs included!
✍️ Toppers ki Copy dekh ke likhna seekhoge - presentation game strong! 💪
📋 Most Probable Questions wale Sample Papers milenge!
⏰ Daily Time Table - ab koi excuse nahi chalega! 😎
💬 24×7 Doubt Solving - raat ko 2 baje bhi doubt clear! 🌙
🎯 60+ Mock Tests + 12 Pre-Boards - exam se pehle exam!
��‍🏫 MP Board ke BEST Teachers padhayenge! 🌐 Hindi & English dono medium mein!
💯 90%+ guaranteed - Unnati ka promise hai ye! ⭐

*Sabse bada dhamaka:*
❌ Rs. 2999 ✅ Sirf Rs. 2499 EXAM TAK KE LIYE! 😍
🎁 Aur suno! Early Bird Discount bhi chahiye? Code lagao: RITESH40 🔥
⚠️ Seats tezi se bhar rahi hain! Kal tak sochoge toh price badh jayegi! 😬
🚀 Abhi join karo!

Baaki sab 90% la rahe hain... tum 60% pe atke rahoge? 🙈
📲 *JOIN NOW - ye mauka phir nahi milega!* ⏳"""

        result = {
            "initialClassification": initial_classification,
            "classifiedAs": "subscription_data_related",
            "response": {"text": subscription_message, "queryType": "subscription", "request_type": "app_related"},
            "openWhatsapp": False,
            "responseType": json_data.get("requestType", ""),
            "actions": "",
            "microLecture": "",
            "testSeries": "",
        }

        logger.info(f"[Classifier App Related Main] Subscription message sent")
        return result

    elif app_classification == "screen_data_related":
        logger.info(f"[Classifier App Related Main] screen_data_related classification")

        result = app_screen_related_main(json_data, initial_classification)

        # Check if the response indicates "I don't know"
        if isinstance(result.get("response"), dict) and "text" in result["response"]:
            answer = normalize(result["response"]["text"])
        else:
            answer = normalize(str(result.get("response", "")))

        if answer == "i dont know something" or answer == "div stylecolor26c6dabi dont knowbdiv":
            logger.info(f"[Classifier App Related Main] app screen data couldn't answer - returning basic response")
            result = {
                "initialClassification": initial_classification,
                "classifiedAs": "screen_data_related",
                "response": "I couldn't find information about that. Please contact support for assistance.",
                "openWhatsapp": True,
                "responseType": json_data.get("requestType", ""),
                "actions": "",
                "microLecture": "",
                "testSeries": "",
            }

        return result

    elif app_classification == "app_data_related":
        logger.info(f"[Classifier App Related Main] app_data_related classification - using content templates")

        # Import content classification and response modules
        try:
            from app.services.content_classifier import simple_classify
            from app.services.content_responses import app_content_main

            # Normalize language to API format (only "english" or "hindi" accepted)
            raw_language = json_data.get("language", "hindi")
            language = raw_language.lower() if raw_language else "hindi"
            # Map hinglish to hindi since API only accepts english/hindi
            if language == "hinglish":
                language = "hindi"

            # Classify content type (lecture, notes, test, etc.)
            content_type = None
            try:
                content_type = simple_classify(question)
                logger.info(f"[Classifier App Related Main] Content type: {content_type}")
            except Exception as e:
                logger.warning(f"[Classifier App Related Main] Content classification failed: {e}")
                # Default to lecture if classification fails
                content_type = "lecture"

            # Prepare data for content response generator
            content_json_data = {
                "message": question,
                "userQuery": question,
                "subject": json_data.get("subject"),
                "language": language
            }

            # Generate content response
            processor_response = app_content_main(content_json_data, initial_classification, content_type)

            # Return in expected format
            result = {
                "initialClassification": initial_classification,
                "classifiedAs": "app_data_related",
                "response": processor_response.get("response", {}),
                "openWhatsapp": processor_response.get("openWhatsapp", False),
                "responseType": json_data.get("requestType", ""),
                "actions": processor_response.get("actions", ""),
                "microLecture": processor_response.get("microLecture", ""),
                "testSeries": processor_response.get("testSeries", ""),
            }

            logger.info(f"[Classifier App Related Main] app_data_related content response generated")
            return result

        except Exception as e:
            logger.error(f"[Classifier App Related Main] Error generating content response: {e}")
            result = {
                "initialClassification": initial_classification,
                "classifiedAs": "app_data_related",
                "response": f"Error processing request: {str(e)}",
                "openWhatsapp": True,
                "responseType": json_data.get("requestType", ""),
                "actions": "",
                "microLecture": "",
                "testSeries": "",
            }
            return result

    else:
        logger.info(f"[Classifier App Related Main] No specific category matched")
        result = {
            "initialClassification": initial_classification,
            "classifiedAs": "app_related",
            "response": "Unable to classify your request. Please provide more details.",
            "openWhatsapp": True,
            "responseType": json_data.get("requestType", ""),
            "actions": "",
            "microLecture": "",
            "testSeries": "",
        }

    return result

    
