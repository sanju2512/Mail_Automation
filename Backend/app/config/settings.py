import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base Directory of Project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application Configuration
    APP_NAME: str = "Agentic Document Automation"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/data/app.db"

    # GroqCloud LLM Configuration
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "qwen/qwen3.8-27b"
    GROQ_TIMEOUT: int = 60
    GROQ_TEMPERATURE: float = 0.1
    GROQ_MAX_TOKENS: int = 4096

    # ChromaDB & Embeddings
    CHROMA_PERSIST_DIRECTORY: str = str(BASE_DIR / "data" / "chroma")
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    USE_LIGHTWEIGHT_EMBEDDINGS: bool = False
    RAG_TOP_K: int = 4

    # Storage Paths
    INPUT_DIR: str = str(BASE_DIR / "data" / "input")
    OUTPUT_DIR: str = str(BASE_DIR / "data" / "output")
    TEMPLATE_DIR: str = str(BASE_DIR / "data" / "templates")
    KNOWLEDGE_BASE_DIR: str = str(BASE_DIR / "data" / "knowledge_base")

    # Email Automation
    EMAIL_IMAP_SERVER: str = "imap.gmail.com"
    EMAIL_IMAP_PORT: int = 993
    EMAIL_SMTP_SERVER: str = "smtp.gmail.com"
    EMAIL_SMTP_PORT: int = 587
    EMAIL_USER: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    EMAIL_CHECK_INTERVAL_SECONDS: int = 60

    def ensure_directories(self) -> None:
        """Ensure that all runtime storage directories exist."""
        for path_str in [self.INPUT_DIR, self.OUTPUT_DIR, self.TEMPLATE_DIR, self.KNOWLEDGE_BASE_DIR, self.CHROMA_PERSIST_DIRECTORY]:
            Path(path_str).mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories()
