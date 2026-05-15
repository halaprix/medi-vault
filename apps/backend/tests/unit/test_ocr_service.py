"""Tests for OCR service."""
import pytest
from app.services.ocr_service import OCRService

@pytest.mark.asyncio
async def test_ocr_service_initialization():
    service = OCRService()
    assert service is not None

@pytest.mark.asyncio
async def test_ocr_extract_empty():
    service = OCRService()
    with pytest.raises(ValueError):
        await service.extract(b"")

@pytest.mark.asyncio
async def test_ocr_pdf_conversion():
    service = OCRService()
    assert hasattr(service, 'convert_pdf_to_images')
