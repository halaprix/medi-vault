"""Security utilities — Fernet encryption, JWT, password hashing, key generation."""

import base64
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Fernet Encryption ────────────────────────────────

_fernet: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    """Lazy-init Fernet instance from configured encryption key."""
    global _fernet
    if _fernet is not None:
        return _fernet
    key = settings.encryption_key
    if not key or key == "change-me":
        raise RuntimeError(
            "ENCRYPTION_KEY is not configured. Run 'make generate-key' or set "
            "ENCRYPTION_KEY to a valid Fernet key in your .env file."
        )
    # Fernet keys must be 32 url-safe base64-encoded bytes
    try:
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as e:
        raise RuntimeError(
            f"Invalid ENCRYPTION_KEY: {e}. Generate a new key with 'make generate-key'."
        )
    return _fernet


def generate_key() -> str:
    """Generate a new Fernet key suitable for ENCRYPTION_KEY."""
    return Fernet.generate_key().decode()


def encrypt(plaintext: str) -> str:
    """Encrypt a string value using Fernet symmetric encryption."""
    if not plaintext:
        return ""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a Fernet-encrypted string value."""
    if not ciphertext:
        return ""
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()


# ── Password / PIN Hashing ───────────────────────────

def hash_pin(pin: str) -> str:
    return pwd_context.hash(pin)


def verify_pin(pin: str, pin_hash: str) -> bool:
    return pwd_context.verify(pin, pin_hash)


# ── JWT ──────────────────────────────────────────────

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.encryption_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.encryption_key, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
