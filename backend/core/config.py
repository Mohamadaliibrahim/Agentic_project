import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings - All configurable values in one place"""
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8011"))
    RELOAD: bool = os.getenv("RELOAD", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    
    # Logging configuration
    DEBUG_THIRD_PARTY: bool = os.getenv("DEBUG_THIRD_PARTY", "false").lower() == "true"
    MINIMAL_LOGGING: bool = os.getenv("MINIMAL_LOGGING", "true").lower() == "true"
    
    # Database Configuration
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "bot_database")
    DATABASE_TYPE: str = os.getenv("DATABASE_TYPE", "mongodb")
    DATABASE_TIMEOUT_MS: int = int(os.getenv("DATABASE_TIMEOUT_MS", "5000"))
    
    # API Metadata
    TITLE: str = "Bot API"
    DESCRIPTION: str = "A well-structured FastAPI bot backend"
    VERSION: str = "1.0.0"
    
    # CORS Configuration
    CORS_ORIGINS: list = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]
    
    # Mistral AI Configuration
    MISTRAL_API_ENDPOINT: str = os.getenv("MISTRAL_API_ENDPOINT", "https://api.mistral.ai/v1/chat/completions")
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    MISTRAL_MODEL: str = os.getenv("MISTRAL_MODEL", "mistral-small-2503")
    MISTRAL_API_EMBEDDING: str = os.getenv("MISTRAL_API_EMBEDDING", "https://api.mistral.ai/v1/embeddings")
    MISTRAL_EMBEDDING_MODEL: str = os.getenv("MISTRAL_EMBEDDING_MODEL", "codestral-embed")
    MISTRAL_TEMPERATURE: float = float(os.getenv("MISTRAL_TEMPERATURE", "0.7"))
    MISTRAL_MAX_TOKENS: int = int(os.getenv("MISTRAL_MAX_TOKENS", "500"))
    MISTRAL_MAX_CONTEXT_TOKENS: int = int(os.getenv("MISTRAL_MAX_CONTEXT_TOKENS", "10000"))
    MISTRAL_API_TIMEOUT: float = float(os.getenv("MISTRAL_API_TIMEOUT", "60.0"))
    MISTRAL_EMBEDDING_TIMEOUT: float = float(os.getenv("MISTRAL_EMBEDDING_TIMEOUT", "120.0"))
    MISTRAL_STARTUP_TIMEOUT: float = float(os.getenv("MISTRAL_STARTUP_TIMEOUT", "10.0"))
    MISTRAL_STARTUP_MAX_TOKENS: int = int(os.getenv("MISTRAL_STARTUP_MAX_TOKENS", "10"))
    MISTRAL_MAX_RETRIES: int = int(os.getenv("MISTRAL_MAX_RETRIES", "3"))
    MISTRAL_EMBEDDING_BATCH_SIZE_SMALL: int = int(os.getenv("MISTRAL_EMBEDDING_BATCH_SIZE_SMALL", "5"))
    MISTRAL_EMBEDDING_BATCH_SIZE_LARGE: int = int(os.getenv("MISTRAL_EMBEDDING_BATCH_SIZE_LARGE", "10"))
    MISTRAL_EMBEDDING_BATCH_THRESHOLD: int = int(os.getenv("MISTRAL_EMBEDDING_BATCH_THRESHOLD", "50"))
    
    # Weather API Configuration
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    OPENWEATHER_API_URL: str = os.getenv("OPENWEATHER_API_URL", "https://api.openweathermap.org/data/2.5/weather")
    OPENWEATHER_API_TIMEOUT: float = float(os.getenv("OPENWEATHER_API_TIMEOUT", "30.0"))
    
    # RAG Configuration
    RAG_MAX_CONTEXT_CHUNKS: int = int(os.getenv("RAG_MAX_CONTEXT_CHUNKS", "5"))
    RAG_MAX_CONTEXT_LENGTH: int = int(os.getenv("RAG_MAX_CONTEXT_LENGTH", "2000"))
    RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "500"))
    RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))
    
    # Document Upload Configuration
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    MAX_UPLOAD_SIZE_BYTES: int = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    # Network Configuration
    SOCKET_TIMEOUT: float = float(os.getenv("SOCKET_TIMEOUT", "1.0"))
    
    # Token Estimation
    CHARS_PER_TOKEN: int = int(os.getenv("CHARS_PER_TOKEN", "4"))
    
    # Orchestrator Configuration
    STRICT_TOOL_MATCHING: bool = os.getenv("STRICT_TOOL_MATCHING", "true").lower() == "true"  # Prevents hallucination by requiring exact tool matches

settings = Settings()

