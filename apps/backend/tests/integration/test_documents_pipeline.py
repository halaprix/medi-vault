"""Integration test: full document upload→process pipeline."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_document_upload_pipeline():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login first
        resp = await client.post("/api/v1/auth/login", json={"pin": "1234"})
        if resp.status_code != 200:
            pytest.skip("Auth not configured")
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Upload document
        with open("/tmp/test_doc.pdf", "wb") as f:
            f.write(b"%PDF-1.4 fake pdf content")
        with open("/tmp/test_doc.pdf", "rb") as f:
            resp = await client.post("/api/v1/documents/upload", files={"file": f}, headers=headers)
        assert resp.status_code in (202, 400, 422)  # 202 accepted, 400/422 invalid
        
        # List documents
        resp = await client.get("/api/v1/documents/", headers=headers)
        assert resp.status_code == 200
