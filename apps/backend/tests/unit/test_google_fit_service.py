"""Tests for Google Fit service."""
import pytest
from app.services.google_fit_service import GoogleFitService

@pytest.mark.asyncio
async def test_google_fit_service_init():
    service = GoogleFitService()
    assert service is not None

@pytest.mark.asyncio
async def test_fetch_weight_data():
    service = GoogleFitService()
    # Without real tokens, should handle gracefully
    result = await service.fetch_weight("fake_token")
    assert result is None  # returns None without real token

@pytest.mark.asyncio
async def test_token_encryption():
    service = GoogleFitService()
    assert hasattr(service, 'encrypt_token')
    assert hasattr(service, 'decrypt_token')
