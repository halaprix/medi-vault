"""EncryptedString — SQLAlchemy type that auto-encrypts/decrypts at the DB layer."""

from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

from app.core.security import decrypt, encrypt


class EncryptedString(TypeDecorator):
    """SQLAlchemy type for transparent Fernet encryption of string columns.

    Usage in models:
        google_oauth_token = Column(EncryptedString, nullable=True)

    Encryption happens on INSERT/UPDATE; decryption on SELECT.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        """Encrypt value before writing to DB."""
        if value is None:
            return None
        if not value:
            return ""
        return encrypt(value)

    def process_result_value(self, value: str | None, dialect) -> str | None:
        """Decrypt value after reading from DB."""
        if value is None:
            return None
        if not value:
            return ""
        return decrypt(value)
