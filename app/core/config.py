from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    PROJECT_NAME: str = "AI Concierge"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 30
    
    # ChromaDB
    CHROMA_HOST: str = "chroma"
    CHROMA_PORT: int = 8000

    class Config:
        case_sensitive = True

settings = Settings()
