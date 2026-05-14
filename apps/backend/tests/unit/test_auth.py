"""Tests for auth routes."""
import pytest


@pytest.mark.asyncio
async def test_auth_status_not_setup(client):
    resp = await client.get("/api/v1/auth/status")
    assert resp.status_code == 200
    assert resp.json()["is_setup"] is False


@pytest.mark.asyncio
async def test_auth_setup(client):
    resp = await client.post("/api/v1/auth/setup", json={"pin": "1234"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_auth_setup_twice_fails(client):
    await client.post("/api/v1/auth/setup", json={"pin": "1234"})
    resp = await client.post("/api/v1/auth/setup", json={"pin": "5678"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_auth_login_success(client):
    await client.post("/api/v1/auth/setup", json={"pin": "1234"})
    resp = await client.post("/api/v1/auth/login", json={"pin": "1234"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_auth_login_wrong_pin(client):
    await client.post("/api/v1/auth/setup", json={"pin": "1234"})
    resp = await client.post("/api/v1/auth/login", json={"pin": "0000"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_without_token(client):
    resp = await client.get("/api/v1/documents/")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_token(client, auth_headers):
    resp = await client.get("/api/v1/documents/", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_auth_status_after_setup(client):
    await client.post("/api/v1/auth/setup", json={"pin": "1234"})
    resp = await client.get("/api/v1/auth/status")
    assert resp.status_code == 200
    assert resp.json()["is_setup"] is True


@pytest.mark.asyncio
async def test_invalid_pin_too_short(client):
    resp = await client.post("/api/v1/auth/setup", json={"pin": "12"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_invalid_pin_non_numeric(client):
    resp = await client.post("/api/v1/auth/setup", json={"pin": "abcd"})
    assert resp.status_code == 422
