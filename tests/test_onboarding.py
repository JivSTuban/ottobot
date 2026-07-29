"""tests/test_onboarding.py — Unit tests for Phase 5 onboarding API endpoints."""

import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault("MISTRAL_API_KEY", "test")

from httpx import AsyncClient, ASGITransport


VALID_DATA = {
    "owner_email": "owner@example.com",
    "name": "Smile Dental",
    "industry": "dental",
    "phone": "+63917000000",
    "city": "Cebu",
    "services": "cleaning, whitening",
    "pricing": "P500-P2500",
    "agent_name": "Ate Ana",
}


@pytest.mark.asyncio
async def test_onboarding_preview_returns_text():
    """POST /onboarding/preview returns a non-empty preview string."""
    from api.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/onboarding/preview", json=VALID_DATA)

    assert resp.status_code == 200
    data = resp.json()
    assert "preview" in data
    assert len(data["preview"]) > 50
    assert "Smile Dental" in data["preview"] or "dental" in data["preview"].lower()


@pytest.mark.asyncio
async def test_onboarding_preview_invalid_industry():
    """POST /onboarding/preview returns 400 for unknown industry."""
    from api.main import app

    payload = {**VALID_DATA, "industry": "plumbing"}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/onboarding/preview", json=payload)

    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_onboarding_submit_no_db(monkeypatch):
    """POST /onboarding/submit returns ok with mock business_id when no DB."""
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from api.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/onboarding/submit", json=VALID_DATA)

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "business_id" in data


@pytest.mark.asyncio
async def test_onboarding_submit_invalid_industry():
    """POST /onboarding/submit returns 400 for invalid industry."""
    from api.main import app

    payload = {**VALID_DATA, "industry": "unknown"}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/onboarding/submit", json=payload)

    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_onboarding_submit_invalid_email():
    """POST /onboarding/submit returns 400 for missing @ in email."""
    from api.main import app

    payload = {**VALID_DATA, "owner_email": "not-an-email"}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/onboarding/submit", json=payload)

    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_onboarding_submit_stores_to_db(monkeypatch):
    """POST /onboarding/submit executes INSERT when DB URI is set."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")

    mock_id = uuid.uuid4()
    mock_cursor = AsyncMock()
    mock_cursor.fetchone = AsyncMock(return_value=(mock_id,))
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=mock_cursor)
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=False)

    from api.main import app

    with patch("psycopg.AsyncConnection.connect", return_value=mock_conn):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/onboarding/submit", json=VALID_DATA)

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["business_id"] == str(mock_id)
    mock_conn.execute.assert_called_once()
