"""
Service for detecting subject and language from user queries.
"""
import json
from openai import OpenAI
from typing import Dict, Optional
from app.core.config import settings
from app.core.logging_config import logger
from app.utils.exceptions import SubjectDetectionError, LanguageDetectionError
from app.models.schemas import SubjectType, LanguageType


class SubjectLanguageDetector:
    """Detects academic subject and language from user queries."""

    def __init__(self):
        """Initialize the detector with OpenAI client."""
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            organization=settings.openai_org_id
        )

    def detect(self, query: str) -> Dict[str, Optional[str]]:
        """
        Detect subject and language from the query using structured output.

        Args:
            query: User query text

        Returns:
            Dictionary with 'subject' and 'language' keys

        Raises:
            SubjectDetectionError: If subject detection fails
            LanguageDetectionError: If language detection fails
        """
        try:
            logger.info(f"Detecting subject and language for query: {query[:100]}...")

            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a subject and language classifier for educational queries.

Subject: Classify into Physics, Chemistry, Mathematics, or Biology.

Language Rules:
- "English": Pure English OR casual Hinglish with common English words mixed (like "force kya h", "important questions dedo", "toppersnotes dedo", "chapter one ke lecture chahiye")
- "Hindi":
  * Hindi written in Devanagari script (like "बल क्या है", "इम्पोर्टेन्ट क़ुएस्तिओन्स")
  * Hindi technical/academic terms written in Roman script (like "viduyt avesh ke lecture", "vishuyt dhara", "gatisheel dhara")

Key Distinction:
- If query uses English words mixed with Hindi → English (Hinglish)
- If query uses pure Hindi words (even in Roman script) or Devanagari → Hindi

Examples:
- "what is force" → English
- "force kya h" → English (Hinglish - English word "force")
- "important questions dedo" → English (Hinglish - English words)
- "toppersnotes dedo" → English (Hinglish - English word "toppersnotes")
- "chapter one ke lecture chahiye" → English (Hinglish - English words)
- "viduyt avesh ke lecture milege kya" → Hindi (pure Hindi terms in Roman)
- "vishuyt dhara ke lecture milege kya" → Hindi (pure Hindi terms in Roman)
- "बल क्या है" → Hindi (Devanagari)
- "इम्पोर्टेन्ट क़ुएस्तिओन्स छाहिये" → Hindi (Devanagari)
"""
                    },
                    {
                        "role": "user",
                        "content": f"Classify this question: {query}"
                    }
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "classification",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "subject": {
                                    "type": "string",
                                    "enum": ["Physics", "Chemistry", "Mathematics", "Biology", "null"]
                                },
                                "language": {
                                    "type": "string",
                                    "enum": ["English", "Hindi"]
                                }
                            },
                            "required": ["subject", "language"],
                            "additionalProperties": False
                        }
                    }
                },
                temperature=0
            )

            result = json.loads(response.choices[0].message.content)
            logger.info(f"Detection result: {result}")

            # Validate and normalize
            subject = self._normalize_subject(result.get("subject"))
            language = self._normalize_language(result.get("language"))

            logger.info(f"Detected - Subject: {subject}, Language: {language}")

            return {
                "subject": subject,
                "language": language
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse detection response: {e}")
            raise SubjectDetectionError(f"Failed to parse detection response: {e}")
        except Exception as e:
            logger.error(f"Error during subject/language detection: {e}")
            raise SubjectDetectionError(f"Detection failed: {e}")

    def _build_detection_prompt(self, query: str) -> str:
        """Build the prompt for subject and language detection."""
        return f"""Analyze the following query and detect:
1. The academic subject (if applicable): Physics, Chemistry, Mathematics, Biology, or null if not academic
2. The language: English, Hindi, or english (mix of Hindi and English)

Query: "{query}"

Respond ONLY with a JSON object in this exact format:
{{
    "subject": "Physics|Chemistry|Mathematics|Biology|null",
    "language": "English|Hindi|english"
}}

Guidelines:
- If the query is about general education, app features, complaints, or casual conversation, set subject to null
- For language detection:
  * English: Pure English text
  * Hindi: Pure Hindi/Devanagari script
  * english: Mix of Hindi and English, or Hindi written in Roman script
- Be precise and return ONLY the JSON object, no additional text"""

    def _normalize_subject(self, subject: Optional[str]) -> Optional[str]:
        """Normalize and validate subject."""
        if not subject or subject.lower() == "null" or subject.lower() == "none":
            return None

        subject_map = {
            "physics": SubjectType.PHYSICS.value,
            "chemistry": SubjectType.CHEMISTRY.value,
            "mathematics": SubjectType.MATHEMATICS.value,
            "math": SubjectType.MATHEMATICS.value,
            "maths": SubjectType.MATHEMATICS.value,
            "biology": SubjectType.BIOLOGY.value,
            "bio": SubjectType.BIOLOGY.value
        }

        normalized = subject_map.get(subject.lower())
        if not normalized and subject:
            logger.warning(f"Unknown subject detected: {subject}, setting to None")
            return None

        return normalized

    def _normalize_language(self, language: str) -> str:
        """Normalize and validate language."""
        if not language:
            logger.warning("No language detected, defaulting to English")
            return LanguageType.ENGLISH.value

        language_map = {
            "english": LanguageType.ENGLISH.value,
            "hindi": LanguageType.HINDI.value,
            "hinglish": LanguageType.HINGLISH.value
        }

        normalized = language_map.get(language.lower())
        if not normalized:
            logger.warning(f"Unknown language detected: {language}, defaulting to English")
            return LanguageType.ENGLISH.value

        return normalized
