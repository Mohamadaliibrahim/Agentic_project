import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings"""
    
    HOST: str = "127.0.0.1"
    PORT: int = 8011
    RELOAD: bool = True
    LOG_LEVEL: str = "info"
    
    # Logging configuration
    DEBUG_THIRD_PARTY: bool = False  # Set to True to see third-party debug logs
    MINIMAL_LOGGING: bool = True     # Set to False for verbose application logs
    
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "bot_database")
    DATABASE_TYPE: str = os.getenv("DATABASE_TYPE", "mongodb")
    
    TITLE: str = "Bot API"
    DESCRIPTION: str = "A well-structured FastAPI bot backend"
    VERSION: str = "1.0.0"
    
    CORS_ORIGINS: list = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]
    
    MISTRAL_API_ENDPOINT: str = os.getenv("MISTRAL_API_ENDPOINT", "https://api.mistral.ai/v1/chat/completions")
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    MISTRAL_MODEL: str = os.getenv("MISTRAL_MODEL", "mistral-small-2503")
    MISTRAL_API_EMBEDDING: str = os.getenv("MISTRAL_API_EMBEDDING", "https://api.mistral.ai/v1/embeddings")
    MISTRAL_EMBEDDING_MODEL: str = os.getenv("MISTRAL_EMBEDDING_MODEL", "codestral-embed")
    
    # Weather API configuration
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    OPENWEATHER_API_URL: str = "https://api.openweathermap.org/data/2.5/weather"

settings = Settings()
