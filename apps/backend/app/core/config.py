# TEST_MODE
"""Core configuration — Pydantic Settings loaded from environment/.env."""

import math
from typing import Optional

from pydantic import field_validator
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

    # Security
    allowed_hosts: str = "localhost,127.0.0.1,frontend"
    backend_port: int = 8000

    # Audit logging
    audit_log_enabled: bool = True
    audit_log_file: str = "/var/log/medi-vault/audit.log"

    # ── Validators ─────────────────────────────────────

    @field_validator("max_upload_size_mb")
    @classmethod
    def validate_max_upload(cls, v: int) -> int:
        if v < 1 or v > 500:
            raise ValueError("max_upload_size_mb must be between 1 and 500")
        return v

    @field_validator("sync_interval_hours")
    @classmethod
    def validate_sync_interval(cls, v: int) -> int:
        if v < 1 or v > 168:
            raise ValueError("sync_interval_hours must be between 1 and 168 (1 week)")
        return v

    @field_validator("backend_port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if v < 1 or v > 65535:
            raise ValueError("backend_port must be between 1 and 65535")
        return v

    @field_validator("ollama_base_url", "chromadb_url", "redis_url")
    @classmethod
    def validate_urls(cls, v: str) -> str:
        if v and not (v.startswith("http://") or v.startswith("https://") or v.startswith("redis://")):
            raise ValueError(f"URL must start with http://, https://, or redis://: {v}")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
