"""Tests for RAG service."""
import pytest
from app.services.rag_service import RAGService

@pytest.mark.asyncio
async def test_rag_service_init():
    service = RAGService()
    assert service is not None

@pytest.mark.asyncio
async def test_rag_retrieve():
    service = RAGService()
    results = await service.retrieve("cholesterol")
    assert isinstance(results, list)

@pytest.mark.asyncio
async def test_rag_generate_recommendation():
    service = RAGService()
    rec = await service.generate_recommendation({"biomarker": "LDL", "value": 160})
    assert rec is not None
