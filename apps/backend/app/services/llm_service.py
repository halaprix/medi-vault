"""LLM Service — parses OCR text into structured biomarker data via Ollama."""

import json
import re
import time
from typing import Any, Optional

import httpx
from pydantic import BaseModel, Field, field_validator

from app.core.config import settings
from structlog import get_logger

logger = get_logger()


# ── Pydantic Validation Schema ────────────────────────

class LabResultItem(BaseModel):
    raw_name: str = ""
    value: Optional[float] = None
    raw_value_string: str = ""
    unit: Optional[str] = None
    ref_range_low: Optional[float] = None
    ref_range_high: Optional[float] = None
    ref_range_text: Optional[str] = None
    is_out_of_range: Optional[bool] = None
    out_of_range_flag: Optional[str] = None

    @field_validator("value", mode="before")
    @classmethod
    def coerce_nan_none(cls, v):
        if v is None:
            return None
        if isinstance(v, float) and (v != v):  # NaN check
            return None
        return v


class LabReportSchema(BaseModel):
    lab_name: Optional[str] = None
    report_date: Optional[str] = None
    patient_info_present: bool = False
    results: list[LabResultItem] = []

    @field_validator("report_date")
    @classmethod
    def validate_date(cls, v):
        if v and isinstance(v, str):
            # Accept YYYY-MM-DD format
            if re.match(r"^\d{4}-\d{2}-\d{2}$", v):
                return v
        return None


# ── System Prompt ─────────────────────────────────────

SYSTEM_PROMPT = """You are a medical lab report parser. Extract ALL biomarker results from the provided OCR text.
Return ONLY a valid JSON object. No explanation, no preamble.

Schema:
{
  "lab_name": "string or null",
  "report_date": "YYYY-MM-DD or null",
  "patient_info_present": boolean,
  "results": [
    {
      "raw_name": "exact name as it appears in the document",
      "value": number or null,
      "raw_value_string": "exact value string as appears (e.g., '>100', '<0.5', '3.2H')",
      "unit": "unit as appears or null",
      "ref_range_low": number or null,
      "ref_range_high": number or null,
      "ref_range_text": "raw reference range string or null",
      "is_out_of_range": boolean or null,
      "out_of_range_flag": "H, L, HH, LL, or null as shown in document"
    }
  ]
}

Rules:
- Include ALL rows, even if value is absent (mark value as null)
- Preserve raw strings exactly
- Do not invent values not present in the text
- Date format must be YYYY-MM-DD"""


# ── Service ───────────────────────────────────────────

class LLMService:
    """Parses OCR text using Ollama into structured lab report JSON."""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model_name = settings.ollama_model_name

    async def parse(self, ocr_text: str, max_retries: int = 3) -> dict[str, Any]:
        prompt = f"{SYSTEM_PROMPT}\n\nOCR Text:\n{ocr_text}"
        last_error = None

        for attempt in range(max_retries):
            try:
                t0 = time.monotonic()
                response_text = await self._call_ollama(prompt, attempt > 0)
                elapsed_ms = (time.monotonic() - t0) * 1000

                raw_result = self._extract_json(response_text)

                # Validate with Pydantic
                validated = LabReportSchema(**raw_result)
                result_dict = validated.model_dump()

                # Log metrics
                results_count = len(result_dict.get("results", []))
                null_fields = sum(
                    1 for r in result_dict.get("results", [])
                    if r.get("value") is None
                )
                logger.info(
                    "llm_parse",
                    model=self.model_name,
                    results_extracted=results_count,
                    null_value_fields=null_fields,
                    response_time_ms=round(elapsed_ms, 1),
                    attempt=attempt + 1,
                )

                return result_dict

            except (json.JSONDecodeError, ValueError) as e:
                last_error = str(e)
                logger.warning(
                    "llm_parse_retry",
                    attempt=attempt + 1,
                    error=last_error,
                )
                if attempt < max_retries - 1:
                    prompt = (
                        f"Your previous response was not valid JSON. "
                        f"Return ONLY the JSON object, nothing else.\n\n"
                        f"Error: {last_error}\n\nHere was the text to parse:\n{ocr_text}"
                    )

        raise ValueError(f"LLM parsing failed after {max_retries} attempts: {last_error}")

    async def _call_ollama(self, prompt: str, is_retry: bool = False) -> str:
        timeout = httpx.Timeout(120.0)
        backoff = 2 ** min(is_retry * 2, 3) if is_retry else 1

        async with httpx.AsyncClient(timeout=timeout) as client:
            for retry in range(3):
                try:
                    resp = await client.post(
                        f"{self.base_url}/api/generate",
                        json={
                            "model": self.model_name,
                            "prompt": prompt,
                            "stream": False,
                            "options": {"temperature": 0.1},
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return data.get("response", "")
                except httpx.HTTPError as e:
                    if retry < 2:
                        import asyncio
                        await asyncio.sleep(backoff)
                        backoff *= 2
                    else:
                        raise

    def _extract_json(self, text: str) -> dict[str, Any]:
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try regex: find first JSON object
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError("Could not extract valid JSON from LLM response")


def chunk_ocr_text(text: str, max_chars: int = 24000) -> list[str]:
    """Chunk OCR text by page markers if too long (~6000 tokens at 4 chars/token)."""
    if len(text) <= max_chars:
        return [text]

    pages = re.split(r"--- PAGE \d+ ---", text)
    chunks = []
    current = ""
    for page in pages:
        page = page.strip()
        if not page:
            continue
        if len(current) + len(page) > max_chars and current:
            chunks.append(current)
            current = page
        else:
            current += "\n" + page if current else page
    if current:
        chunks.append(current)
    return chunks or [text]
