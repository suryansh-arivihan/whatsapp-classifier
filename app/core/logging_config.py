"""
Centralized logging configuration for the application.
"""
import logging
import sys
from app.core.config import settings


def setup_logging():
    """Configure logging for the application."""

    # Create logger
    logger = logging.getLogger("whatsapp_classifier")
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Add formatter to handler
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    return logger


# Global logger instance
logger = setup_logging()
