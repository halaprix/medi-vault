"""Integration tests for Results API."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_results_list_empty():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/auth/login", json={"pin": "1234"})
        if resp.status_code != 200:
            pytest.skip("Auth not configured")
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        resp = await client.get("/api/v1/results/", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
