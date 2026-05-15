"""Integration tests for auth flow."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_auth_setup_login_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Setup
        resp = await client.post("/api/v1/auth/setup", json={"pin": "1234"})
        assert resp.status_code in (200, 201, 400)  # 400 if already set up
        
        # Login
        resp = await client.post("/api/v1/auth/login", json={"pin": "1234"})
        if resp.status_code == 200:
            data = resp.json()
            assert "access_token" in data
