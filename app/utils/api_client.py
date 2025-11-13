"""
API client for making requests to the external classifier service.
"""
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging_config import logger


def normalize_language(language: str) -> str:
    """
    Normalize language to API format.
    External API only accepts 'english' or 'hindi' (lowercase).
    Converts 'hindlish' to 'hindi'.

    Args:
        language: Input language string

    Returns:
        Normalized language ('english' or 'hindi')
    """
    if not language:
        return "hindi"

    lang_lower = language.lower()

    # Map hindlish to hindi
    if lang_lower == "hindlish":
        return "hindi"

    # Accept english or hindi
    if lang_lower in ["english", "hindi"]:
        return lang_lower

    # Default to hindi for any other value
    return "hindi"


class ExternalAPIClient:
    """Client for making requests to the external classifier API."""

    def __init__(self):
        """Initialize the API client."""
        self.base_url = settings.external_api_base_url
        self.access_token = settings.external_api_access_token
        self.user_id = settings.external_api_user_id
        self.timeout = settings.external_api_timeout

    def get_base_payload(
        self,
        subject: Optional[str] = None,
        user_query: str = "",
        language: str = "hindi",
        class_name: str = "Class 12th",
        course: str = "Board"
    ) -> Dict[str, Any]:
        """
        Get base payload template for API requests.
        Normalizes language to 'english' or 'hindi' (lowercase only).

        Args:
            subject: Academic subject (Physics, Chemistry, Mathematics, Biology)
            user_query: The user's query
            language: Query language (will be normalized)
            class_name: Student's class
            course: Course type

        Returns:
            Dict with base payload structure
        """
        # Normalize language before including in payload
        normalized_language = normalize_language(language)

        return {
            "class": class_name,
            "course": course,
            "language": normalized_language,
            "requestType": "text",
            "subject": subject or "",
            "subscriptionStatus": "",
            "userName": "",
            "userQuery": user_query
        }

    async def call_endpoint(
        self,
        endpoint: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make a POST request to the external API endpoint.

        Args:
            endpoint: API endpoint path (e.g., "/guidance/based/classifier")
            payload: Request payload

        Returns:
            Dict with API response

        Raises:
            Exception: If API call fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            logger.info(f"[ExternalAPI] Calling {url}")
            logger.debug(f"[ExternalAPI] Payload: {payload}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "accept": "application/json",
                        "accessToken": self.access_token,
                        "Content-Type": "application/json"
                    }
                )

                response.raise_for_status()
                result = response.json()

                logger.info(f"[ExternalAPI] Response status: {response.status_code}")
                logger.debug(f"[ExternalAPI] Response: {result}")

                return result

        except httpx.TimeoutException as e:
            logger.error(f"[ExternalAPI] Timeout calling {url}: {e}")
            raise Exception(f"External API timeout: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"[ExternalAPI] HTTP error calling {url}: {e}")
            raise Exception(f"External API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"[ExternalAPI] Error calling {url}: {e}")
            raise Exception(f"External API call failed: {e}")


# Global client instance
external_api_client = ExternalAPIClient()
