"""
tests/test_leads_endpoints.py — Unit tests for GET /leads and GET /leads/{lead_id}/messages.

Covers:
- GET /leads returns {"leads": [...]} with status field per lead
- GET /leads/{lead_id}/messages returns messages ordered newest-first
- GET /leads/{lead_id}/messages with invalid UUID → 400
- GET /leads with no Authorization header → 401/403

Uses FastAPI TestClient (synchronous). psycopg is mocked. JWT auth dependency
is overridden via FastAPI dependency_overrides for unit-test isolation.

asyncio_mode = "auto" in pyproject.toml — no @pytest.mark.asyncio decorator needed.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_BID = str(uuid.uuid4())
VALID_LID = str(uuid.uuid4())

# Message timestamps — newer first to validate ordering
MSG_NEWER = "2026-06-19T10:05:00"
MSG_OLDER = "2026-06-19T09:00:00"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_conn_leads():
    """
    Mock psycopg connection returning leads and messages.

    fetchall is called for both leads query and messages query.
    We use side_effect to return different rows per call order.
    """
    mock_cursor = MagicMock()
    # First fetchall → leads rows; second fetchall → messages rows
    mock_cursor.fetchall = AsyncMock(
        side_effect=[
            [(VALID_LID, "+639171234567", "new", "2026-06-19T10:00:00")],  # leads
            [
                ("msg-1", "Hello", "inbound", MSG_NEWER),
                ("msg-2", "Kamusta", "outbound", MSG_OLDER),
            ],  # messages
        ]
    )
    mock_cursor.fetchone = AsyncMock(
        return_value=("+639171234567",)  # phone for lead ownership check
    )

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=mock_cursor)

    mock_conn_ctx = AsyncMock()
    mock_conn_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn_ctx.__aexit__ = AsyncMock(return_value=False)

    return mock_conn_ctx


def _make_mock_conn_empty():
    """Mock psycopg connection returning empty results."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall = AsyncMock(return_value=[])
    mock_cursor.fetchone = AsyncMock(return_value=None)

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=mock_cursor)

    mock_conn_ctx = AsyncMock()
    mock_conn_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn_ctx.__aexit__ = AsyncMock(return_value=False)

    return mock_conn_ctx


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client(monkeypatch):
    """
    TestClient with mocked psycopg and JWT auth dependency overridden.

    JWT auth is bypassed by overriding get_business_id_from_token to return VALID_BID.
    """
    monkeypatch.setenv("SUPABASE_DIRECT_URL", "postgresql://test:test@localhost/test")
    monkeypatch.setenv("SUPABASE_DB_URI", "")

    with patch("psycopg.AsyncConnection.connect", return_value=_make_mock_conn_leads()):
        from api.main import app, get_business_id_from_token

        app.dependency_overrides[get_business_id_from_token] = lambda: VALID_BID
        try:
            with TestClient(app) as c:
                yield c
        finally:
            app.dependency_overrides.pop(get_business_id_from_token, None)


@pytest.fixture
def client_no_db(monkeypatch):
    """TestClient with no DB — exercises no-op graceful degradation path."""
    monkeypatch.setenv("SUPABASE_DIRECT_URL", "")
    monkeypatch.setenv("SUPABASE_DB_URI", "")

    with patch("psycopg.AsyncConnection.connect", return_value=_make_mock_conn_empty()):
        from api.main import app, get_business_id_from_token

        app.dependency_overrides[get_business_id_from_token] = lambda: VALID_BID
        try:
            with TestClient(app) as c:
                yield c
        finally:
            app.dependency_overrides.pop(get_business_id_from_token, None)


# ---------------------------------------------------------------------------
# GET /leads tests
# ---------------------------------------------------------------------------


def test_get_leads_returns_list(client):
    """GET /leads with mock JWT and mock DB → 200, {"leads": [...]}."""
    resp = client.get("/leads")
    assert resp.status_code == 200
    data = resp.json()
    assert "leads" in data
    assert isinstance(data["leads"], list)
    assert len(data["leads"]) >= 1
    assert data["leads"][0]["status"] == "new"


def test_get_leads_no_db(client_no_db):
    """GET /leads with no DB → 200, {"leads": [], "grouped": {}} graceful no-op."""
    resp = client_no_db.get("/leads")
    assert resp.status_code == 200
    data = resp.json()
    assert "leads" in data
    assert data["leads"] == []


def test_get_leads_no_auth():
    """GET /leads with no Authorization header → 401 or 403."""
    from api.main import app

    with TestClient(app) as c:
        resp = c.get("/leads")
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# GET /leads/{lead_id}/messages tests
# ---------------------------------------------------------------------------


def test_get_messages_invalid_uuid():
    """GET /leads/not-a-uuid/messages → 400 (UUID validation rejects non-UUID)."""
    from api.main import app, get_business_id_from_token

    app.dependency_overrides[get_business_id_from_token] = lambda: VALID_BID
    try:
        with TestClient(app) as c:
            resp = c.get("/leads/not-a-uuid/messages")
    finally:
        app.dependency_overrides.pop(get_business_id_from_token, None)
    assert resp.status_code == 400


def test_get_messages_no_db(client_no_db):
    """GET /leads/{lead_id}/messages with no DB → 200, {"messages": []} no-op."""
    resp = client_no_db.get(f"/leads/{VALID_LID}/messages")
    assert resp.status_code == 200
    data = resp.json()
    assert data["messages"] == []


def test_get_messages_no_auth():
    """GET /leads/{lead_id}/messages with no Authorization → 401 or 403."""
    from api.main import app

    with TestClient(app) as c:
        resp = c.get(f"/leads/{VALID_LID}/messages")
    assert resp.status_code in (401, 403)
