"""Tests for normalization logic — biomarker matching, unit conversion, ref range parsing."""
import pytest


def test_ref_range_standard():
    """Pattern '3.5 - 5.0' → low=3.5, high=5.0"""
    from app.services.normalization_service import parse_ref_range
    low, high = parse_ref_range("3.5 - 5.0")
    assert low == 3.5
    assert high == 5.0


def test_ref_range_less_than():
    """Pattern '< 5.0' → low=None, high=5.0"""
    from app.services.normalization_service import parse_ref_range
    low, high = parse_ref_range("< 5.0")
    assert low is None
    assert high == 5.0


def test_ref_range_greater_than():
    """Pattern '> 40' → low=40, high=None"""
    from app.services.normalization_service import parse_ref_range
    low, high = parse_ref_range("> 40")
    assert low == 40
    assert high is None


def test_ref_range_negative():
    """Pattern 'Negative' → low=None, high=None"""
    from app.services.normalization_service import parse_ref_range
    low, high = parse_ref_range("Negative")
    assert low is None
    assert high is None


def test_ref_range_with_spaces():
    low, high = parse_ref_range("  2.0  -  6.0  ")
    assert low == 2.0
    assert high == 6.0


def test_compute_out_of_range_high():
    from app.services.normalization_service import compute_out_of_range
    is_oor, direction = compute_out_of_range(6.0, 2.0, 5.0)
    assert is_oor is True
    assert direction == "high"


def test_compute_out_of_range_low():
    from app.services.normalization_service import compute_out_of_range
    is_oor, direction = compute_out_of_range(1.0, 2.0, 5.0)
    assert is_oor is True
    assert direction == "low"


def test_compute_out_of_range_normal():
    from app.services.normalization_service import compute_out_of_range
    is_oor, direction = compute_out_of_range(3.5, 2.0, 5.0)
    assert is_oor is False
    assert direction == "normal"


def test_compute_out_of_range_only_high():
    from app.services.normalization_service import compute_out_of_range
    is_oor, direction = compute_out_of_range(6.0, None, 5.0)
    assert is_oor is True
    assert direction == "high"


def test_compute_out_of_range_only_low():
    from app.services.normalization_service import compute_out_of_range
    is_oor, direction = compute_out_of_range(30.0, 40.0, None)
    assert is_oor is True
    assert direction == "low"


def test_unit_conversion_cholesterol():
    from app.services.normalization_service import convert_unit
    result = convert_unit(200.0, "mg/dL", "mmol/L", "2093-3")
    assert round(result, 4) == 5.172


def test_unit_conversion_glucose():
    from app.services.normalization_service import convert_unit
    result = convert_unit(100.0, "mg/dL", "mmol/L", "2345-7")
    assert round(result, 4) == 5.551


def test_unit_conversion_no_change():
    from app.services.normalization_service import convert_unit
    result = convert_unit(5.0, "mmol/L", "mmol/L", "2093-3")
    assert result == 5.0
