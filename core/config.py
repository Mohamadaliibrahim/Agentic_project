"""
Application Configuration
Centralized configuration management
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings"""
    
    # Server Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8010
    RELOAD: bool = True
    LOG_LEVEL: str = "info"
    
    # Database Configuration
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "bot_database")
    DATABASE_TYPE: str = os.getenv("DATABASE_TYPE", "mongodb")
    
    # Application Configuration
    TITLE: str = "Bot API"
    DESCRIPTION: str = "A well-structured FastAPI bot backend"
    VERSION: str = "1.0.0"
    
    # CORS Configuration
    CORS_ORIGINS: list = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]

# Global settings instance
settings = Settings()
