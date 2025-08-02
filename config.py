from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Telegram Bot Configuration
    bot_token: str = Field(..., env="BOT_TOKEN")
    
    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")
    
    # DeepSeek API Configuration
    deepseek_api_key: str = Field(..., env="DEEPSEEK_API_KEY")
    deepseek_api_url: str = Field(
        default="https://api.deepseek.com/v1/chat/completions",
        env="DEEPSEEK_API_URL"
    )
    
    # Payment Configuration
    payment_card_number: str = Field(..., env="PAYMENT_CARD_NUMBER")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings() 