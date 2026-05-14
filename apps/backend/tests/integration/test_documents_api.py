"""Integration tests — Documents API."""
import io

import pytest


@pytest.mark.asyncio
async def test_upload_document(client, auth_headers):
    pdf = io.BytesIO(b"%PDF-1.4 fake lab report content")
    resp = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("lab.pdf", pdf, "application/pdf")},
        headers=auth_headers,
    )
    assert resp.status_code == 202
    data = resp.json()
    assert "document_id" in data
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_upload_invalid_type(client, auth_headers):
    txt = io.BytesIO(b"not a pdf")
    resp = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("doc.txt", txt, "text/plain")},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_documents_empty(client, auth_headers):
    resp = await client.get("/api/v1/documents/", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_nonexistent_document(client, auth_headers):
    resp = await client.get("/api/v1/documents/nonexistent-id", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_document_status_nonexistent(client, auth_headers):
    resp = await client.get("/api/v1/documents/nonexistent-id/status", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_auth_flow(client):
    # Status before setup
    resp = await client.get("/api/v1/auth/status")
    assert resp.json()["is_setup"] is False

    # Setup
    resp = await client.post("/api/v1/auth/setup", json={"pin": "5678"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    # Status after setup
    resp = await client.get("/api/v1/auth/status")
    assert resp.json()["is_setup"] is True

    # Login
    resp = await client.post("/api/v1/auth/login", json={"pin": "5678"})
    assert resp.status_code == 200

    # Protected endpoint
    resp = await client.get("/api/v1/documents/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    # Bad token
    resp = await client.get("/api/v1/documents/", headers={"Authorization": "Bearer bad.token.here"})
    assert resp.status_code == 401
