"""
Exam-related query sub-classification service.
Classifies exam-related queries into 5 sub-categories:
- faq
- pyq_pdf
- asking_PYQ_question
- asking_test
- asking_important_question
"""
import time
import re
from openai import OpenAI
from app.core.config import settings
from app.core.logging_config import logger
from app.utils.exceptions import ClassificationError


class ExamClassifierAgent:
    """Agent responsible for sub-classifying exam-related queries."""

    def __init__(self, client):
        self.client = client
        self.categories = {
            'faq': 'Frequently asked questions about syllabus, exam format, important chapters, weightage, study materials, exam dates, admit cards, centers, results, forms, rules, eligibility, announcements, procedures, preboards, supplementary exams, and general exam-related queries.',
            'asking_PYQ_question': 'Students asking for previous year questions, past exam questions, sample questions, or question papers from specific topics, chapters, or subjects.',
            'asking_important_question': 'Students asking for important questions, expected questions, or questions that are likely to come in upcoming exams without specifically mentioning previous years.',
            'pyq_pdf': 'Students asking for complete previous year exam papers, full paper PDFs, complete paper solutions, or entire exam papers without topic-specific requests.',
            'asking_test': 'Students asking for tests, test series, mock tests, practice tests, or test activities that they can take/attempt.'
        }
        self.valid_categories = set(self.categories.keys())

    def classify(self, question):
        """Classify an exam-related question into one of 5 sub-categories."""
        system_prompt = f"""You are an assistant that classifies exam-related student queries into five categories:

1. **faq** → Use this for all general exam-related queries and frequently asked questions:
   - **Syllabus related questions** (e.g., "Physics ka syllabus kya hai?", "Light chapter ke important topics?", "Kaunse chapters cut ho gaye hain?")
   - **Important chapters and topics** (e.g., "Physics me kaunse chapters important hain?", "Gauss Pramey important hai kya?")
   - **Exam format and logistics** (e.g., "Physics ka paper kitne marks ka h?", "1 marker kitne hote hain?", "Kya NCERT se hi aata hai?")
   - **Study materials and books** (e.g., "Kaunsi book follow karni chahiye?", "NCERT ke bahar ka aata hai kya?")
   - **Exam dates, admit cards, centers, results, forms** (e.g., "Exam kab start hoga?", "Admit card kaise download kare?")
   - **Rules, eligibility, announcements, procedures** (e.g., "Eligibility criteria kya hai?", "Form kaise fill kare?")
   - **Preparation strategy questions** (e.g., "NCERT numericals chor dun to theek rahega?", "Weightage kis chapter ka zyada hai?")

2. **pyq_pdf** → Use this for complete previous year exam papers and full paper solutions:
   - **Complete exam papers** (e.g., "Pichle saal ka paper dedo", "Last year ka physics paper chahiye")
   - **Full paper PDFs** (e.g., "Pichle saal ka paper ka pdf dedo", "2023 ka complete paper pdf")
   - **Complete paper solutions** (e.g., "Pichle saal ka physics ke paper ka solution", "Last year paper with solutions")
   - **Entire exam papers** (e.g., "Full physics paper 2023", "Complete chemistry paper with answers")
   - **Year-specific full papers** (e.g., "2022 ka pura paper", "Last 3 years ke complete papers")

3. **asking_PYQ_question** → Use this ONLY when students are asking for topic/chapter-specific previous year questions:
   - **Previous year questions from specific topics/chapters** (e.g., "Electric charge ke pichle saal ke question dedo", "Optics ke last 5 year ke questions")
   - **Topic-specific past questions** (e.g., "Light chapter ke previous year questions", "Thermodynamics ke pyq questions")
   - **Chapter-wise previous questions** (e.g., "Organic chemistry ke last year ke questions", "Mechanics ke pyq batao")
   - **Fill in the blanks from previous years** (e.g., "Electric charge ke previous year ke fill in the blanks")

4. **asking_test** → Use this HIGHEST PRIORITY when students are asking for tests, test activities, or want to take tests:
   - **General test requests** (e.g., "Mujhe physics ke test chhaiye", "Test chahiye", "Physics ka test dedo")
   - **Chapter-wise test requests** (e.g., "Electric charge ke chapter ka test chahiye", "Chapter 1 ka test dedo")
   - **Test series requests** (e.g., "Test series chahiye", "Mock test chahiye", "Practice test dedo")
   - **Subject-specific test requests** (e.g., "Chemistry ke test chahiye", "Maths ka test series")
   - **Full-length test requests** (e.g., "Full length test chahiye", "Complete physics test")
   - **ANY request where user wants to TAKE/ATTEMPT a test or test activity**

5. **asking_important_question** → Use this as DEFAULT when students are asking for any kind of questions:
   - **Important questions for upcoming exams** (e.g., "Physics ke important questions batao", "Chemistry ke expected questions kya hain?")
   - **Questions likely to come in exam** (e.g., "Kya questions aa sakte hain exam me?", "Important numerical questions batao")
   - **Expected questions from topics** (e.g., "Light chapter se kya questions aa sakte hain?", "Thermodynamics ke important questions")
   - **Questions for practice without year reference** (e.g., "Practice ke liye questions chahiye", "Important MCQs batao")
   - **General question requests** (e.g., "Questions chahiye", "Physics ke questions dedo", "Chemistry ke questions batao")
   - **Fill in the blanks (general)** (e.g., "Fill in the blanks chahiye", "Electric charge ke fill in the blanks dedo")
   - **ANY request for questions that doesn't specifically mention previous years or complete papers**

📌 Key Rules (Priority Order):
- **HIGHEST PRIORITY**: If asking for **tests, test series, mock tests, practice tests, or wanting to TAKE/ATTEMPT a test** → **asking_test**
- If asking about **any exam-related information, syllabus, preparation, or general queries** → **faq**
- If asking for **complete exam papers, full PDFs, or complete paper solutions** → **pyq_pdf**
- If asking for **topic/chapter-specific previous year questions** → **asking_PYQ_question**
- If asking for **ANY KIND OF QUESTIONS (including general, important, expected, fill in the blanks, etc.) without mentioning previous years or tests** → **asking_important_question**
- **DEFAULT: When in doubt about question requests, always choose asking_important_question**

✅ Examples:
- "Physics ka syllabus kya hai?" → faq
- "Light chapter ke important topics kya hain?" → faq
- "Physics me kaunse chapters important hain?" → faq
- "Physics ka paper kitne marks ka h?" → faq
- "NCERT ke bahar ka aata hai kya?" → faq
- "Pichle saal ka paper dedo" → pyq_pdf
- "Pichle saal ka paper ka pdf dedo" → pyq_pdf
- "Pichle saal ka physics ke paper ka solution" → pyq_pdf
- "2023 ka complete paper chahiye" → pyq_pdf
- "Last year ka full physics paper" → pyq_pdf
- "Electric charge ke pichle saal ke question dedo" → asking_PYQ_question
- "Light chapter ke previous year questions" → asking_PYQ_question
- "Thermodynamics ke pyq questions" → asking_PYQ_question
- "Electric charge ke previous year ke fill in the blanks" → asking_PYQ_question
- "Mujhe physics ke test chhaiye" → asking_test
- "Physics ka test dedo" → asking_test
- "Test chahiye" → asking_test
- "Electric charge ke chapter ka test chahiye" → asking_test
- "Chapter 1 ka test chahiye" → asking_test
- "Mock test chahiye" → asking_test
- "Test series dedo" → asking_test
- "Chemistry ke test chahiye" → asking_test
- "Full length test chahiye" → asking_test
- "Physics ke important questions batao" → asking_important_question
- "Chemistry ke expected questions kya hain?" → asking_important_question
- "Light chapter se kya questions aa sakte hain?" → asking_important_question
- "Questions chahiye" → asking_important_question
- "Physics ke questions dedo" → asking_important_question
- "Chemistry ke questions batao" → asking_important_question
- "Fill in the blanks chahiye" → asking_important_question
- "Electric charge ke fill in the blanks dedo" → asking_important_question
- "Maths ke questions send karo" → asking_important_question
- "Biology ke MCQ chahiye" → asking_important_question
- "kya vidyut avesh or kshetra se objective qustion ate h" → faq

🎯 **CRITICAL DECISION RULE:**
- If the query contains words like **"test", "tests", "mock test", "practice test", "test series"** → **asking_test**
- If asking for **"important topics"** or **"important chapters"** → **faq**
- If asking for **"important questions"** → **asking_important_question**
- If the query contains words like "questions", "MCQ", "fill in the blanks" WITHOUT specifically mentioning "previous year", "last year", "pyq", "complete paper", or "test" → **asking_important_question**
- When unsure between categories for question requests → **ALWAYS choose asking_important_question**

INSTRUCTION: Classify this query into ONE of these categories: faq, pyq_pdf, asking_PYQ_question, asking_test, asking_important_question

Q: {question}

Return ONLY the category name:"""

        user_prompt = system_prompt.format(question=question)

        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                temperature=settings.openai_temperature,
                max_tokens=50
            )

            raw_response = response.choices[0].message.content.strip().lower()
            return raw_response

        except Exception as e:
            logger.info(f"[Classifier Exam] Error in classification: {str(e)}")
            return 'faq'  # Default fallback


def create_exam_classifier():
    """Create and return a configured exam classifier instance."""
    client = OpenAI(
        api_key=settings.openai_api_key,
        organization=settings.openai_org_id
    )
    classifier_agent = ExamClassifierAgent(client)
    return classifier_agent


def _normalize_exam_classification(raw_classification: str) -> str:
    """
    Normalize exam classification to match schema enum values.

    Args:
        raw_classification: Raw classification from the classifier (may be lowercase)

    Returns:
        Normalized classification matching the enum
    """
    # Map lowercase variations to correct enum values
    normalization_map = {
        'faq': 'faq',
        'pyq_pdf': 'pyq_pdf',
        'asking_pyq_question': 'asking_PYQ_question',  # Fix case
        'asking_test': 'asking_test',
        'asking_important_question': 'asking_important_question'
    }

    normalized = normalization_map.get(raw_classification.lower())
    if normalized:
        return normalized

    # If not found, return as-is and let validation catch it
    logger.warning(f"Unknown exam classification: {raw_classification}")
    return raw_classification


def exam_related_main_classifier(question: str) -> str:
    """
    Main entry point for exam sub-classification.

    Args:
        question: The exam-related query to sub-classify

    Returns:
        Exam sub-classification category as a string

    Raises:
        ClassificationError: If classification fails
    """
    try:
        logger.info(f"[Classifier Exam] Question: {question}")
        start_time = time.time()

        classifier = create_exam_classifier()
        raw_classification = classifier.classify(question)

        # Normalize to match schema enum
        classification = _normalize_exam_classification(raw_classification)

        elapsed_time = time.time() - start_time
        logger.info(f"[Classifier Exam] Classification: {classification} (time: {elapsed_time:.3f}s)")

        return classification
    except Exception as e:
        logger.error(f"Unexpected error during exam classification: {e}")
        raise ClassificationError(f"Exam classification failed: {e}")
