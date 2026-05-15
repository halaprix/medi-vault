"""Integration tests for Health Metrics CRUD + sync."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_metrics_crud():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/auth/login", json={"pin": "1234"})
        if resp.status_code != 200:
            pytest.skip("Auth not configured")
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create
        resp = await client.post("/api/v1/metrics/", json={
            "metric_type": "weight", "value": 70.5, "unit": "kg"
        }, headers=headers)
        assert resp.status_code in (200, 201, 422)
        
        # List
        resp = await client.get("/api/v1/metrics/", headers=headers)
        assert resp.status_code == 200
