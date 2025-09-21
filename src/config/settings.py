import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Database Configuration
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "rag_investigation_db"
    
    # SOP Configuration
    SOP_DIRECTORY: str = "data/sop_documents"
    SOP_DOCUMENT_URLS: str = ""  # Comma-separated URLs
    SOP_INDEX_PATH: str = "data/sop_index"
    
    # RAG Configuration
    EMBEDDING_MODEL: str = "paraphrase-MiniLM-L3-v2"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100
    MAX_RETRIEVAL_RESULTS: int = 7
    
    # API Configuration
    API_TITLE: str = "GP Hackathon - Investigation Management System"
    API_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Gemini API Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    
    # Additional environment variables causing validation errors
    CHROMA_PERSIST_PATH: Optional[str] = None
    TRANSFORMERS_CACHE: Optional[str] = None
    SENTENCE_TRANSFORMERS_HOME: Optional[str] = None
    MONGO_URI: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings
