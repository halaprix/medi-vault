# Adding New Biomarkers

1. Edit `scripts/seed_biomarkers.py`
2. Add a new entry:

```python
{
    "name": "New Biomarker",
    "loinc_code": "XXXXX-X",
    "category": "your_category",
    "unit": "mg/dL",
    "reference_range_low": 10.0,
    "reference_range_high": 20.0,
    "reference_range_unit": "mg/dL",
    "aliases": ["new_bio", "NB"],
    "description": "What this biomarker measures"
}
```

3. Add unit conversions if needed in `scripts/unit_conversions.json`
4. Run: `make seed`
