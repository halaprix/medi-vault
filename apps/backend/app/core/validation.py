"""Input validation utilities for medi-vault."""
import re
from datetime import datetime, timezone
from typing import Any

def validate_not_nan_inf(value: float) -> float:
    """Reject NaN/Infinity values."""
    import math
    if math.isnan(value) or math.isinf(value):
        raise ValueError(f"Invalid numeric value: {value}")
    return value

def validate_not_negative(value: float) -> float:
    """Reject negative values for medical results."""
    if value < 0:
        raise ValueError(f"Negative value not allowed: {value}")
    return value

def validate_future_date(date_str: str) -> str:
    """Reject future dates for result_date."""
    try:
        dt = datetime.fromisoformat(date_str)
        if dt > datetime.now(timezone.utc):
            raise ValueError(f"Future date not allowed: {date_str}")
        return date_str
    except (ValueError, TypeError):
        raise ValueError(f"Invalid date format: {date_str}")

# MIME type validation for uploaded files
ALLOWED_MIMES = {
    "application/pdf",
    "image/png", "image/jpeg", "image/tiff",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def validate_file_upload(content_type: str | None, size: int) -> None:
    """Validate uploaded file MIME type and size."""
    if content_type and content_type not in ALLOWED_MIMES:
        raise ValueError(f"Unsupported file type: {content_type}")
    if size > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {size} bytes (max {MAX_FILE_SIZE})")
