"""
Base handler class for response generation.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseResponseHandler(ABC):
    """Base class for all response handlers."""

    @abstractmethod
    def handle(self, query: str, classification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate response for a classified query.

        Args:
            query: The user's query (translated if needed)
            classification_data: Dict containing classification details
                - classification: main classification type
                - sub_classification: sub-classification if applicable
                - subject: detected subject
                - language: detected language
                - original_message: original user message
                - translated_message: translated message if applicable

        Returns:
            Dict with response data in format:
            {
                "status": "success" | "error",
                "data": {...},  # Response content
                "message": "...",  # Optional message
                "metadata": {...}  # Optional metadata
            }
        """
        pass
