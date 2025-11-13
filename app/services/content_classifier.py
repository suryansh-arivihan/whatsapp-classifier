"""
Simple content classifier for app-related queries.
Classifies into: lecture, notes, toppers_notes, test_chapterwise, test_full_length
"""
from openai import OpenAI
from app.core.config import settings
from app.core.logging_config import logger


class SimpleContentClassifier:
    """Classifier for educational content requests."""

    def __init__(self, client):
        self.client = client
        self.categories = {
            'lecture': 'Video lectures or teaching content',
            'notes': 'General study notes (PPT notes, lecture notes, written notes)',
            'toppers_notes': 'Notes specifically from toppers/high scorers',
            'test_chapterwise': 'Chapter-wise or topic-specific tests',
            'test_full_length': 'Full-length tests covering complete syllabus'
        }

    def classify(self, question: str) -> str:
        """
        Classify content request into one of 5 categories.

        Args:
            question: User's content request query

        Returns:
            One of: 'lecture', 'notes', 'toppers_notes', 'test_chapterwise', 'test_full_length'
        """
        system_prompt = f"""You are a classifier for educational content requests.
Your ONLY job is to return ONE category from this list:
1. lecture
2. notes
3. toppers_notes
4. test_chapterwise
5. test_full_length

## CLASSIFICATION RULES:

### 1. LECTURE
- User asks for video lectures, teaching content, explanations
- Keywords: "lecture", "video", "samjhao", "padhao", "teaching"
- Examples: "lecture chahiye", "video lecture", "abhishek sir ka lecture"

### 2. NOTES (PPT Notes - ONLY when explicitly mentioned)
- ✅ ONLY when user EXPLICITLY mentions "ppt", "presentation", "slides"
- Keywords: "ppt notes", "presentation notes", "slides chahiye"
- Examples:
  - "ppt notes chahiye" → notes
  - "presentation slides do" → notes
  - "chapter ke ppt notes" → notes

### 3. TOPPERS_NOTES (DEFAULT for all general notes requests)
- 🎯 DEFAULT: When user asks for "notes" WITHOUT mentioning "ppt"
- When user explicitly mentions topper names
- Keywords: "notes chahiye", "notes do", "topper ke notes"
- Examples:
  - "chemistry ke notes do" → toppers_notes (NO ppt mentioned)
  - "notes chahiye physics ke" → toppers_notes (NO ppt mentioned)
  - "chapter 1 ke notes" → toppers_notes (NO ppt mentioned)
  - "priya topper ke notes" → toppers_notes (topper mentioned)
  - "topper notes chahiye" → toppers_notes (topper mentioned)

### 4. TEST_CHAPTERWISE
- User asks for chapter-specific or topic-specific tests
- Mentions specific chapter, topic, or "chapterwise"
- Keywords: "chapter ka test", "topic test", "chapterwise test"
- Examples: "chapter 1 ka test", "electric charge ka test", "chapterwise test"

### 5. TEST_FULL_LENGTH
- User asks for full tests, complete tests, or subject-level tests
- No specific chapter/topic mentioned
- Keywords: "full test", "complete test", "mock test", "subject ka test"
- Examples: "physics ka full test", "complete test chahiye"

## 🚨 CRITICAL NOTES CLASSIFICATION LOGIC:

**Step 1: Check for "ppt" keyword**
- IF query contains "ppt" OR "presentation" OR "slides" → `notes`

**Step 2: Check for "topper" keyword**
- ELSE IF query contains "topper" OR topper names → `toppers_notes`

**Step 3: Default for general notes**
- ELSE IF query contains "notes" → `toppers_notes` (DEFAULT)

## EXAMPLES WITH CORRECT CLASSIFICATION:

✅ "chemistry ke notes do" → toppers_notes (no ppt mentioned)
✅ "notes chahiye" → toppers_notes (no ppt mentioned)
✅ "chapter 1 ke notes" → toppers_notes (no ppt mentioned)
✅ "physics ke ppt notes" → notes (ppt explicitly mentioned)
✅ "ppt notes chahiye" → notes (ppt explicitly mentioned)
✅ "priya topper ke notes" → toppers_notes (topper mentioned)
✅ "topper notes do" → toppers_notes (topper mentioned)

Query: {question}

Return ONLY ONE word from: lecture, notes, toppers_notes, test_chapterwise, test_full_length
"""

        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": system_prompt}],
                temperature=0,
                max_tokens=20
            )

            raw_response = response.choices[0].message.content.strip().lower()

            # Validate response
            if raw_response in self.categories.keys():
                logger.info(f"✅ Content Classification: '{question}' → {raw_response}")
                return raw_response
            else:
                logger.warning(f"⚠️ Invalid response '{raw_response}', defaulting to 'lecture'")
                return 'lecture'

        except Exception as e:
            logger.error(f"❌ Content classification error: {str(e)}")
            return 'lecture'  # Safe default


def simple_classify(user_query: str) -> str:
    """
    Main function to classify user query into one of 5 content categories.

    Args:
        user_query: The user's question/request

    Returns:
        One of: 'lecture', 'notes', 'toppers_notes', 'test_chapterwise', 'test_full_length'
    """
    client = OpenAI(
        api_key=settings.openai_api_key,
        organization=settings.openai_org_id
    )
    classifier = SimpleContentClassifier(client)
    result = classifier.classify(user_query)
    return result
