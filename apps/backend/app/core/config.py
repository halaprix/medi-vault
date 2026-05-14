"""Core configuration — Pydantic Settings loaded from environment/.env."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://medi-vault:medi-vault@postgres:5432/medi-vault"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # ChromaDB
    chromadb_url: str = "http://chromadb:8000"

    # Ollama
    ollama_base_url: str = "http://ollama:11434"
    ollama_model_name: str = "llama3:8b"

    # Encryption
    encryption_key: str = "change-me"

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost/api/v1/auth/google/callback"

    # App
    auto_delete_pdfs: bool = False
    max_upload_size_mb: int = 50
    sync_interval_hours: int = 6

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
