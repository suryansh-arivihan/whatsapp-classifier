"""
Custom exceptions for the application.
"""


class ClassifierException(Exception):
    """Base exception for all classifier-related errors."""
    pass


class ClassificationError(ClassifierException):
    """Raised when classification fails."""
    pass


class TranslationError(ClassifierException):
    """Raised when translation fails."""
    pass


class SubjectDetectionError(ClassifierException):
    """Raised when subject detection fails."""
    pass


class LanguageDetectionError(ClassifierException):
    """Raised when language detection fails."""
    pass


class OpenAIAPIError(ClassifierException):
    """Raised when OpenAI API call fails."""
    pass


class InvalidInputError(ClassifierException):
    """Raised when input validation fails."""
    pass
