"""Shared Pydantic validators — reject NaN, Infinity, negative values, future dates.

These validators should be used on ALL user-facing Pydantic models to prevent
poisoned or nonsensical data from reaching the database or LLM.
"""

import math
from datetime import date, datetime, timezone

from pydantic import field_validator


def validate_finite_float(v: float, field_name: str = "value") -> float:
    """Reject NaN, +Inf, -Inf in float fields."""
    if v is None:
        return v
    if isinstance(v, float):
        if math.isnan(v):
            raise ValueError(f"{field_name} must not be NaN")
        if math.isinf(v):
            raise ValueError(f"{field_name} must not be Infinity")
    return v


def validate_non_negative(v: float, field_name: str = "value") -> float:
    """Reject negative values for fields that should be >= 0."""
    v = validate_finite_float(v, field_name)
    if v is not None and v < 0:
        raise ValueError(f"{field_name} must not be negative")
    return v


def validate_not_future_date(v: str | date | None, field_name: str = "date") -> str | date | None:
    """Reject dates in the future."""
    if v is None:
        return v
    if isinstance(v, str):
        try:
            parsed = date.fromisoformat(v)
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} must be a valid YYYY-MM-DD date")
    else:
        parsed = v
    today = date.today()
    if parsed > today:
        raise ValueError(f"{field_name} must not be in the future: {parsed} > {today}")
    return v


# Pydantic v2 field_validator wrappers for use in @field_validator decorated methods

def finite_float_validator(field_name: str = "value"):
    """Factory for @field_validator that rejects NaN/Infinity."""
    @field_validator(field_name, mode="before")
    @classmethod
    def wrapper(cls, v):
        if v is None:
            return v
        try:
            fv = float(v)
        except (TypeError, ValueError):
            return v  # let Pydantic's type validation handle it
        return validate_finite_float(fv, field_name)
    return wrapper


def non_negative_validator(field_name: str = "value"):
    """Factory for @field_validator that rejects NaN/Infinity/negative."""
    @field_validator(field_name, mode="before")
    @classmethod
    def wrapper(cls, v):
        if v is None:
            return v
        try:
            fv = float(v)
        except (TypeError, ValueError):
            return v
        return validate_non_negative(fv, field_name)
    return wrapper


def not_future_date_validator(field_name: str = "date"):
    """Factory for @field_validator that rejects future dates."""
    @field_validator(field_name)
    @classmethod
    def wrapper(cls, v):
        return validate_not_future_date(v, field_name)
    return wrapper
