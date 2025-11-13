"""
Main classification service for categorizing educational queries.
Classifies queries into 6 main categories:
- subject_related
- app_related
- complaint
- guidance_based
- conversation_based
- exam_related_info
"""
import time
from langchain_openai import ChatOpenAI
from openai import AuthenticationError, APIStatusError
from app.core.config import settings
from app.core.logging_config import logger
from app.utils.exceptions import ClassificationError


class ClassifierAgent:
    """Agent responsible for classifying user queries into categories."""

    def __init__(self, llm):
        self.llm = llm
        self.categories = {
            'subject_related': 'Academic questions about specific topics, concepts, formulas, or any educational content explanation. Students asking for solutions to questions.',
            'app_related': 'Questions about app features, navigation, how to access content, technical functionality, batch details, course information, platform usage, pricing, payments, subscriptions, discounts, and how to join batches.',
            'complaint': 'Expressions of dissatisfaction, frustration, or problems with content quality, app functionality, locked content, or any negative experience.',
            'guidance_based': 'Questions about study planning, exam preparation strategies, motivation, career guidance, and general educational advice.',
            'conversation_based': 'Casual greetings, thanks, general chat, and social interactions without specific requests.',
            'exam_related_info': 'Questions about exam patterns, schedules, syllabus, important topics, exam strategies, and examination-related information. but not the study material related to exam.'
        }
        self.valid_categories = set(self.categories.keys())

    def classify(self, question):
        """Classify a question into one of the 6 categories."""
        prompt = f"""You are an expert classifier for Arivihan – an EdTech platform for 11th and 12th-grade students.

Your task is to classify each student query into EXACTLY ONE of these 6 categories based on the PRIMARY INTENT:

---

**1. subject_related**
INTENT: Student needs direct academic explanation of specific concepts OR solution to specific numerical problems ONLY.

This includes ONLY:

- **CONCEPTUAL QUESTIONS**: "What is X?", "Define X", "Explain X" for specific academic concepts
  - Examples: "What is force?", "Define photosynthosis", "Explain integration", "What is matrix?"

- **NUMERICAL PROBLEM SOLVING**: Requests to solve specific mathematical/physics/chemistry problems
  - Examples: "Solve this equation", "Find the derivative of x²", "Calculate the molarity", "Solve this physics numerical"

- **DIRECT CONCEPT EXPLANATIONS**: Asking for explanation of specific formulas, theorems, or academic principles
  - Examples: "Explain Newton's law", "What is Pythagoras theorem", "Define cellular respiration"

- **DIRECT FACTUAL QUESTIONS**: Simple factual questions asking for direct answers, including fill-in-the-blank format
  - Examples: "हमारी आकाशगंगा का नाम ______ है।", "The capital of India is ______", "H2O is called ______"

---

**This does NOT include (not subject_related):**

- Study strategy questions (how to prepare, when to study, what to study first)
- Problem-solving approach or general study methods
- Preparation techniques, time management, or motivation
- Questions about which topics are important for exams
- Vague requests without a clear concept or numerical focus
- **Requests for notes, full chapter question-answers, or textbook-based help (e.g., "12th class ke अर्थशास्त्र ke 1 part ke question answer")**
- **Broad exam-related inquiries (e.g., "JEE kya hai?")**
- **Requests for help with study difficulties like "Sir numerical mai problem aa rhi hai" (this is guidance_based, not subject_related)**
- **Paper/worksheet availability queries (e.g., "Tremashik pricha paper ka solution aap pr nahi hai kya?")**
- **ANY REQUESTS FOR PYQ (Previous Year Questions) - these should be classified as exam_related_info**
- **ANY REQUESTS FOR LECTURES - these should always be classified as app_related**
  👉 These are **not asking for specific academic explanations**, so should NOT be classified as subject_related.

**KEY INDICATOR:**
Is the student directly asking for explanation of a clearly defined academic concept, a specific numerical problem to be solved, or a direct factual answer?

---

**2. app_related**
INTENT: Student has questions about app features, navigation, platform functionality, subscription/pricing, OR any contact-related requests.

This includes:

**Platform & Content Queries:**
- Questions about batch details (Unnati, Sambhav, crash course features)
- How to access specific content or features
- Questions about app navigation and functionality
- Course structure and organization questions
- Timetable and schedule queries (not exam schedules)
- Questions about what content is available in batches
- Asking for demo classes
- How to study using the app
- Asking about lectures, notes, topper notes available on app, and teachers who are teaching
- Questions about lecture content, such as which exams are covered
- Asking about the time for which the batch is active or how much time it takes to cover the syllabus
- Questions about syllabus completion timeline ("Syllabus kab tak complete hoga?")
- Course duration and content coverage timeframes
- How to study from Arivihan for a specific exam
- **Questions about when specific content will be available on app** (e.g., "Board questions kb aayenge?")
- **How to access exam-specific materials from the platform** (e.g., "Pre board ke liye important questions kaise milege?")
- **Questions about what level of lectures are available (basic/advanced), what types of exams are covered (e.g., NEET, JEE, CUET), whether material is available for a particular exam, and what exams Arivihan supports**
- **Questions about last date to join a batch, batch duration, and app-specific schedule timelines**
- **ALL REQUESTS FOR LECTURES** (e.g., "Mujhe vidhyut aavesh ka pyq lecture chahiye", "Physics ka lecture chahiye", "Maths ke lectures kaha hai")
- **ALL REQUESTS FOR TESTS (accessing/getting tests)** (e.g., "Test chahiye", "Physics ka test do", "Chapterwise test kaha milege", "Mock test dena hai")
  - Keywords: "test chahiye", "test do", "test milega", "test kaha hai", "test dena hai", "mock test"
  - These are about ACCESSING/GETTING test content from the platform

**Financial & Subscription Queries:**
- **Questions about discounts, coupons, or pricing**
- **Batch purchase inquiries and payment-related questions**
- **Subscription duration and options, cost-related queries**
- **HOW TO JOIN a batch or course (since joining requires subscription purchase)**
- **Questions about joining process or enrollment**
- **Scholarship-related questions: "How much scholarship will I get?", "What scholarship amount can I expect?", "Scholarship kitna milega?"**
- **Questions about scholarship eligibility based on percentage/performance**
- **Questions referring to promotional content about scholarships or discounts**
- **Financial assistance and scholarship eligibility queries**
- **Questions about scholarship criteria and scholarship amounts**
- **Refund and payment issues**
- **Batch renewal questions and subscription renewal inquiries**

**Contact & Support Queries:**
- **Requests for teacher phone numbers** (e.g., "Sir aapka number dedo", "Teacher ka WhatsApp number chahiye")
- **Asking for personal contact details** (e.g., "Aapka mobile number kya hai?", "Contact details share karo")
- **Requests to open WhatsApp or other messaging apps** (e.g., "WhatsApp kholo", "WhatsApp par message karu?")
- **Asking for direct communication channels** (e.g., "Call kar sakta hun?", "Personal chat kar sakte hai?")
- **Requests for social media contacts** (e.g., "Instagram ID dedo", "Telegram group add karo")
- **Any attempt to establish communication outside the official platform**
- **Asking for personal meeting or direct contact** (e.g., "Milna hai", "Phone par baat karni hai")
- **Asking for customer care or official support contact numbers**

**IMPORTANT: This category is for INFORMATIONAL QUERIES about app features, pricing, contact, or platform functionality – NOT for reporting problems with them.**

**IMPORTANT: PYQ requests are NOT classified as app_related - they go to exam_related_info**

**IMPORTANT: ALL LECTURE REQUESTS are classified as app_related**

**IMPORTANT: ALL TEST ACCESS REQUESTS are classified as app_related (e.g., "test chahiye", "test kaha milege", "mock test dena hai")**

**KEY INDICATOR:**
Is the student asking HOW TO USE the app, WHAT IS AVAILABLE in the app/platform, anything related to PRICING, PAYMENT, PURCHASING, HOW TO JOIN, FINANCIAL ASSISTANCE (including scholarships), ANY CONTACT INFORMATION, **ANY LECTURE REQUESTS**, or **ANY TEST ACCESS REQUESTS** (wanting to get/take/find tests) **WITHOUT expressing dissatisfaction or reporting problems**?

---

**3. complaint**
INTENT: Student is expressing dissatisfaction, frustration, confusion, or reporting a problem of any kind.

This includes:

- **Content not loading, locked, or inaccessible**
- **Content/features not available when they should be** (e.g., "PYQs nahi hai", "notes available nahi hai", "topper notes nahi mil rahe")
- **Download/technical issues** (e.g., "notes download nahi ho rahe", "app crash ho raha hai")
- **Subject or topic not appearing** (e.g., "Bio app pe show nahi ho raha, only Maths aa raha hai")
- **Confusion with app updates or functionality** (e.g., "App pe naye updates aaye hai, samajh nahi aa raha kaise padhna hai")
- **Poor teaching quality, unclear explanations** (e.g., "Teacher acche se samjha nahi rahe", "Mujhe kuch samajh nahi aata")
- **App issues, glitches, buttons not working, content not displaying**
- **Payment, refund, or billing issues with problems or dissatisfaction**
- **CRM team not responding, poor or delayed customer service**
- **Any expression of frustration, dissatisfaction, or inconvenience**
- **Repeated complaints about support delays or lack of resolution**
- **Missing content that student expected to find** (e.g., "chemistry notes hindi me nhi h", "exercise nahi hai")
- **Features not working as expected** (e.g., "crash course ka option nhi aa rha hai")
- **Technical/app-related difficulties** (e.g., "App crash ho rhi hai", "Login nahi ho raha")

**CRITICAL DISTINCTION:**
- **app_related**: "Kya topper notes available hai?" (asking about availability)
- **complaint**: "Topper notes available nahi ho rahe" (reporting problem with access)

**KEY INDICATOR:**
If the student is FRUSTRATED, DISSATISFIED, REPORTING ANY KIND OF PROBLEM, or expressing that something is NOT WORKING/NOT AVAILABLE when it should be, it should be classified as a **complaint**.

---

**4. guidance_based**
INTENT: Student needs study advice, planning help, motivational support, study methodology guidance, or help with academic challenges.

This includes:
- Questions about study planning and strategies (general advice, not app features)
- Confusion about how to prepare or approach studies
- Concerns about exam readiness or performance
- Motivational queries about achieving good grades
- General academic advice and study methods to improve performance
- Questions about preparation effectiveness
- Exam preparation strategies and study techniques
- Questions about study approach: "Should I do this before that?"
- Problem-solving methodology questions (not specific concept explanations)
- Questions about handling difficulties in subjects or topics (e.g., "Sir numerical mai problem aa rhi hai","mujhe maths accha nahi lagta")
- Study sequence and priority questions
- **Requests for help with academic challenges without asking for specific concept explanations**
- **Seeking guidance on how to overcome study difficulties or improve in specific areas**
- **Asking for advice on study methods or approaches for better understanding**
- **Any question that starts with casual conversation but has educational intent** (e.g., "Hi sir, mujhe padhai mein help chahiye")

**KEY INDICATOR:** Is the student asking for STUDY ADVICE, PLANNING HELP, MOTIVATION, HOW TO APPROACH their studies, or SEEKING HELP with academic challenges (without requesting specific content explanations or app features)?

---

**5. conversation_based**
**INTENT: EXTREMELY LIMITED - ONLY pure social interaction with NO educational or platform-related intent whatsoever.**

**STRICT CRITERIA - This category should be used VERY RARELY and ONLY for:**

**ALLOWED (conversation_based):**
- **Standalone greetings with NO follow-up**: "Hi", "Hello", "Good morning" (ONLY if no other request follows)
- **Pure thank you messages**: "Thank you", "Thanks", "Dhanyawad" (ONLY if expressing gratitude with no other request)
- **Basic pleasantries with NO educational intent**: "How are you?", "Kaise hai aap?" (ONLY if purely social)

**NOT ALLOWED (should be classified in other categories):**
- **Any greeting followed by a question or request**: "Hi sir, mujhe help chahiye" → **guidance_based**
- **Thank you with context about platform/studies**: "Thanks for the notes" → **app_related**
- **Any conversation that has educational undertones**: "Hello, I'm a new student" → **app_related**
- **Casual questions about studies**: "How's your day? BTW, when will lectures start?" → **app_related**
- **Social interaction mixed with platform queries**: "Hi, can you help me with batch info?" → **app_related**
- **Polite conversation starters before real questions**: "Good morning sir, I wanted to ask about..." → classify based on the actual question
- **Any message that shows educational platform context**: "Hello from a student" → **app_related**

**CRITICAL RULE: If there is ANY educational, platform-related, or help-seeking intent (even implied), DO NOT classify as conversation_based.**

**CRITICAL RULE: If the message suggests the person is a student or user of the platform, classify based on their actual intent, not the greeting.**

**KEY INDICATOR:** Is this PURELY social interaction with ABSOLUTELY NO educational, platform, or help-seeking intent? If there's ANY doubt, classify in the appropriate functional category.

---

**6. exam_related_info**
INTENT: Student is requesting information about examinations themselves, their structure, schedule, eligibility requirements, preparation strategies, or academic guidance related to exams. THIS ALSO INCLUDES ALL REQUESTS FOR PYQ (PREVIOUS YEAR QUESTIONS) AND FILL IN THE BLANKS OF ANY KIND.

Included Query Types:

1. ALL PYQ (Previous Year Questions) requests (e.g., "mujhe pyq chahiye electric charge kee", "solution ke mcq chahiye PYQ ke", "Physics ka PYQ do", "Chemistry ke previous year questions")
2. ALL FILL IN THE BLANKS requests (e.g., "mujhe fill in the blanks chahiye", "mujhe electric charge ke fill in the blanks chahiye", "mujhe janan swasth ke fill in the blanks chahiye")
3. Official exam patterns and formats (e.g., "JEE ka pattern kya hai?")
4. Official examination schedules and dates (e.g., "Board exam kab hai?")
5. General syllabus coverage and important topics with high weightage (e.g., "JEE ke liye kaunsa chapter sabse important hai?")
6. Exam eligibility criteria and requirements (e.g., "JEE ke liye qualification kya chahiye?")
7. Book recommendations for specific exams (e.g., "MPSC ke liye konsa book lu?", "Hindi mai konsa book accha hai maths ke liye?")
8. Exam-specific preparation strategies and important topics
9. Subject-wise important chapters/topics for specific competitive exams
10. Study material recommendations for particular examinations
11. Important questions for any exam (e.g., "Physics ke important questions batao", "Chemistry ke important questions kya hai?")
12. Exam syllabus and curriculum queries (e.g., "mp board ka full syllabus ka pdf chahiye?, "physics ka syllabus chahiye"")

**SPECIAL RULE - QUESTION REQUESTS:**
ANY request for questions, MCQs, or practice materials should ALWAYS be classified as exam_related_info, regardless of other context:

- "chapter 3 questions" → exam_related_info
- "chapter 3 important questions" → exam_related_info
- "chapter 3 mcq" → exam_related_info
- "solution mcq" → exam_related_info
- "physics questions chahiye" → exam_related_info
- "maths ke questions send karo" → exam_related_info
- "chemistry mcq de do" → exam_related_info
- "practice questions" → exam_related_info
- "exercise questions" → exam_related_info

**EXCEPTION FOR TEST REQUESTS:**
HOWEVER, when someone is asking for TESTS (not questions about tests), classify as app_related:
- "test chahiye" → app_related (wants to ACCESS test)
- "physics ka test do" → app_related (wants to GET test)
- "chapterwise test kaha milege" → app_related (wants to FIND test location)
- "mock test dena hai" → app_related (wants to TAKE test)
- BUT "test me kya questions aate hain" → exam_related_info (asking ABOUT test content)

This rule overrides all other classification logic for question/MCQ requests.
**CRITICAL DISTINCTION:**

1. exam_related_info: "JEE ke liye kaunsa chapter important hai?" (asking about exam-specific academic guidance)
2. app_related: "JEE questions kb aayenge app par?" (asking about app content timeline)
3. exam_related_info: "MPSC ke liye book recommend karo" (asking for exam preparation guidance)
4. exam_related_info: "Mp board class 12th previous year paper" (ANY PYQ request goes here)
5. exam_related_info: "Chemistry ke important questions batao" (asking for important questions as exam guidance)
6. exam_related_info: "mujhe fill in the blanks chahiye" (ANY fill in the blanks request)
7. exam_related_info: "mujhe electric charge ke fill in the blanks chahiye" (topic-specific fill in the blanks request)
8. app_related: "Pre board ke liye important questions kaise milege app se?" (asking how to access important questions from the platform)
9. app_related: "Mujhe vidhyut aavesh ka pyq lecture chahiye" (ANY LECTURE request)
10. app_related: "physics ke chapterwise test kaha milege" (asking WHERE to ACCESS tests from platform)
11. app_related: "test chahiye physics ka" (wants to GET test content)
12. app_related: "mock test dena hai" (wants to TAKE/ATTEMPT test)
13. exam_related_info: "test me kitne marks ka paper hota hai" (asking ABOUT test structure)

**IMPORTANT RULE:** ANY request for PYQ (Previous Year Questions), previous year papers, or past exam questions should ALWAYS be classified as exam_related_info, regardless of context.
**IMPORTANT RULE:** Distinguish between two types of fill-in-the-blank queries:
- **Direct factual questions with blanks** (asking for the actual answer): classify as subject_related
  - Examples: "हमारी आकाशगंगा का नाम ______ है।", "The capital of India is ______", "H2O is called ______"
- **Requests for fill-in-the-blank worksheets/materials**: classify as exam_related_info
  - Examples: "mujhe fill in the blanks chahiye", "fill in the blanks worksheets send karo"
**IMPORTANT RULE:** ANY request for LECTURES should ALWAYS be classified as app_related, regardless of context.
**IMPORTANT RULE:** ANY request to ACCESS/GET/TAKE TESTS should ALWAYS be classified as app_related, NOT exam_related_info.

**KEY INDICATOR:**
Is the student asking for EXAM-SPECIFIC ACADEMIC GUIDANCE, preparation strategies, important topics, book recommendations, important questions for exam preparation, ANY KIND OF PYQ/PREVIOUS YEAR QUESTIONS, OR ANY KIND OF FILL IN THE BLANKS — BUT NOT asking to access/get/take tests, lectures, or other platform content?

-------------------------

**REMEMBER: conversation_based should be EXTREMELY RARE. Most student interactions have educational or platform-related intent and should be classified accordingly.**

INSTRUCTION: Classify this query into ONE of these categories: subject_related, app_related, complaint, guidance_based, conversation_based, exam_related_info

Q: {question}

Return ONLY the category name:"""


        response = self.llm.invoke(prompt).content.strip().lower()
        for category in self.valid_categories:
            if category in response:
                return category

        # If response doesn't match exactly, check for partial matches
        category_keywords = {
            'subject_related': ['subject', 'academic', 'topic', 'concept'],
            'app_related': ['app', 'feature', 'batch', 'platform', 'navigation', 'subscription', 'pricing', 'payment', 'discount', 'scholarship'],
            'complaint': ['complaint', 'problem', 'issue', 'frustration'],
            'guidance_based': ['guidance', 'study', 'planning', 'advice'],
            'conversation_based': ['conversation', 'casual', 'greeting'],
            'exam_related_info': ['exam', 'examination', 'pattern', 'schedule']
        }

        for category, keywords in category_keywords.items():
            if any(keyword in response for keyword in keywords):
                return category

        # Default fallback - analyze the response more carefully
        if 'subject' in response or 'academic' in response:
            return 'subject_related'
        elif 'app' in response or 'feature' in response or 'subscription' in response or 'pricing' in response:
            return 'app_related'
        elif 'complaint' in response or 'problem' in response:
            return 'complaint'
        elif 'guidance' in response or 'study' in response:
            return 'guidance_based'
        elif 'exam' in response:
            return 'exam_related_info'
        else:
            return 'conversation_based'


class SupervisorAgent:
    """Supervisor agent that wraps the classifier."""

    def __init__(self, classifier_agent):
        self.classifier_agent = classifier_agent

    def handle_doubt(self, question):
        """Handle a question by classifying it."""
        classification = self.classifier_agent.classify(question)
        return classification


def create_classifier():
    """Create and return a configured classifier instance."""
    llm = ChatOpenAI(
        model=settings.openai_model,
        openai_api_key=settings.openai_api_key,
        openai_organization=settings.openai_org_id,
        temperature=settings.openai_temperature
    )
    classifier_agent = ClassifierAgent(llm)
    supervisor_agent = SupervisorAgent(classifier_agent)
    return supervisor_agent


def initial_main_classifier(question: str) -> str:
    """
    Main entry point for classification.

    Args:
        question: The user query to classify

    Returns:
        Classification category as a string

    Raises:
        ClassificationError: If classification fails
    """
    try:
        logger.info(f"[Classifier Main] Question: {question}")
        start_time = time.time()

        supervisor = create_classifier()
        classification = supervisor.handle_doubt(question)

        elapsed_time = time.time() - start_time
        logger.info(f"[Classifier Main] Classification: {classification} (time: {elapsed_time:.3f}s)")

        return classification
    except (AuthenticationError, APIStatusError) as e:
        logger.error(f"OpenAI API error during classification: {e}")
        raise ClassificationError(f"OpenAI API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during classification: {e}")
        raise ClassificationError(f"Classification failed: {e}")
