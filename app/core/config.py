"""
Configuration management using Pydantic Settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI Configuration
    openai_api_key: str
    openai_org_id: Optional[str] = None

    # Application Configuration
    log_level: str = "INFO"
    environment: str = "development"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "Educational Query Classifier API"
    api_version: str = "1.0.0"
    api_description: str = "FastAPI service for classifying educational queries from WhatsApp"

    # OpenAI Model Configuration
    openai_model: str = "gpt-4.1-mini"
    openai_temperature: float = 0.0
    openai_max_tokens: int = 500

    # External Classifier API Configuration
    external_api_base_url: str = "http://0.0.0.0:5002"
    external_api_access_token: str = "DBkYaMoQ4zkN"
    external_api_user_id: str = "2c9f8050989969d101989e75c6407d7c"
    external_api_timeout: int = 30  # seconds

    # Guidance Processor Configuration
    parquet_file_path: Optional[str] = None
    vector_store_id: Optional[str] = None

    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

    # DynamoDB Configuration
    dynamodb_table_name: str = "whatsapp_conversation_history"
    history_retention_days: int = 90
    history_messages_limit: int = 5
    history_window_hours: int = 24

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
