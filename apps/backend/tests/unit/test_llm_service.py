"""Tests for LLM service."""
import pytest
from app.services.llm_service import LLMService

@pytest.mark.asyncio
async def test_llm_service_init():
    service = LLMService()
    assert service is not None

@pytest.mark.asyncio
async def test_llm_json_extraction():
    service = LLMService()
    result = await service.extract_json("Total cholesterol: 200 mg/dL")
    assert result is not None

@pytest.mark.asyncio
async def test_llm_retry_logic():
    service = LLMService()
    # Verify retry configuration exists
    assert hasattr(service, 'max_retries')
