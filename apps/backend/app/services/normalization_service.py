"""Normalization engine — biomarker matching, unit conversion, reference range parsing."""
import json
import re
from pathlib import Path
from typing import Optional, Tuple

# ── Reference Range Parsing ──────────────────────────


def parse_ref_range(ref_text: str) -> Tuple[Optional[float], Optional[float]]:
    """Parse reference range text into (low, high) numeric bounds.
    
    Patterns handled:
    - "3.5 - 5.0" → (3.5, 5.0)
    - "< 5.0" → (None, 5.0)
    - "> 40" → (40, None)
    - "Negative" → (None, None)
    """
    if not ref_text or not isinstance(ref_text, str):
        return None, None

    text = ref_text.strip()

    if text.lower() in ("negative", "positive", "normal", "abnormal", "indeterminate"):
        return None, None

    # Pattern "< 5.0" or "<5.0"
    lt_match = re.match(r"<\s*([\d.]+)", text)
    if lt_match:
        return None, float(lt_match.group(1))

    # Pattern "> 40" or ">40"
    gt_match = re.match(r">\s*([\d.]+)", text)
    if gt_match:
        return float(gt_match.group(1)), None

    # Pattern "3.5 - 5.0"
    range_match = re.match(r"([\d.]+)\s*-\s*([\d.]+)", text)
    if range_match:
        return float(range_match.group(1)), float(range_match.group(2))

    return None, None


# ── Out of Range Computation ─────────────────────────


def compute_out_of_range(
    value: float,
    ref_low: Optional[float],
    ref_high: Optional[float],
) -> Tuple[bool, str]:
    """Determine if value is out of range and direction."""
    if ref_low is not None and value < ref_low:
        return True, "low"
    if ref_high is not None and value > ref_high:
        return True, "high"
    return False, "normal"


# ── Unit Conversion ──────────────────────────────────


def _load_conversions() -> dict:
    path = Path(__file__).parent.parent.parent.parent / "scripts" / "unit_conversions.json"
    if not path.exists():
        return {}
    with open(path) as f:
        data = json.load(f)
    return {
        c["loinc_code"]: c
        for c in data.get("conversions", [])
    }


UNIT_CONVERSIONS = _load_conversions()


def convert_unit(value: float, from_unit: str, to_unit: str, loinc_code: str) -> float:
    """Convert biomarker value between units using predefined conversion factors."""
    if from_unit == to_unit:
        return value

    conv = UNIT_CONVERSIONS.get(loinc_code)
    if conv and conv["from"] == from_unit and conv["to"] == to_unit:
        return value * conv["factor"]
    if conv and conv["from"] == to_unit and conv["to"] == from_unit:
        return value / conv["factor"]

    return value  # no conversion available


# ── Biomarker Matching ───────────────────────────────


def match_biomarker(raw_name: str, biomarkers: list[dict]) -> Optional[str]:
    """Match raw_name to biomarker ID using exact/fuzzy matching."""
    # Exact match (case-insensitive)
    raw_lower = raw_name.lower().strip()
    for b in biomarkers:
        if raw_lower == b["display_name"].lower():
            return b["id"]
        for alias in b.get("aliases", []):
            if raw_lower == alias.lower():
                return b["id"]

    # Fuzzy match via rapidfuzz (optional)
    try:
        from rapidfuzz import fuzz
        best_score = 0
        best_id = None
        for b in biomarkers:
            score = max(
                fuzz.ratio(raw_lower, b["display_name"].lower()),
                max((fuzz.ratio(raw_lower, a.lower()) for a in b.get("aliases", [])), default=0),
            )
            if score > best_score and score >= 85:
                best_score = score
                best_id = b["id"]
        if best_id:
            return best_id
    except ImportError:
        pass

    return None
