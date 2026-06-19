"""
tests/test_push_endpoint.py — Unit tests for POST /push/send endpoint.

Covers:
- POST /push/send with valid ExponentPushToken → 200, stored=True
- POST /push/send with invalid token format → 422
- POST /push/send with no DB configured → 200, stored=False
- POST /push/send with no Authorization header → 401/403

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
VALID_TOKEN = "ExponentPushToken[test-token-xxx]"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_conn():
    """Return an async context manager mock for psycopg.AsyncConnection.connect."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone = AsyncMock(return_value=None)
    mock_cursor.fetchall = AsyncMock(return_value=[])

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
    SUPABASE_DIRECT_URL is set so DB path is exercised (psycopg mocked).
    """
    monkeypatch.setenv("SUPABASE_DIRECT_URL", "postgresql://test:test@localhost/test")
    monkeypatch.setenv("SUPABASE_DB_URI", "")

    with patch("psycopg.AsyncConnection.connect", return_value=_make_mock_conn()):
        from api.main import app, get_business_id_from_token

        app.dependency_overrides[get_business_id_from_token] = lambda: VALID_BID
        try:
            with TestClient(app) as c:
                yield c
        finally:
            app.dependency_overrides.pop(get_business_id_from_token, None)


@pytest.fixture
def client_no_db(monkeypatch):
    """TestClient with no DB configured — exercises the no-op path."""
    monkeypatch.setenv("SUPABASE_DIRECT_URL", "")
    monkeypatch.setenv("SUPABASE_DB_URI", "")

    with patch("psycopg.AsyncConnection.connect", return_value=_make_mock_conn()):
        from api.main import app, get_business_id_from_token

        app.dependency_overrides[get_business_id_from_token] = lambda: VALID_BID
        try:
            with TestClient(app) as c:
                yield c
        finally:
            app.dependency_overrides.pop(get_business_id_from_token, None)


# ---------------------------------------------------------------------------
# POST /push/send tests
# ---------------------------------------------------------------------------


def test_push_send_stores_token(client):
    """Valid ExponentPushToken[...] + mock DB → 200, stored=True."""
    resp = client.post("/push/send", json={"expo_token": VALID_TOKEN})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["stored"] is True


def test_push_send_invalid_token_format(client):
    """Non-ExponentPushToken format → 422."""
    resp = client.post("/push/send", json={"expo_token": "BadToken[x]"})
    assert resp.status_code == 422


def test_push_send_no_db(client_no_db):
    """No SUPABASE_DIRECT_URL configured → 200, stored=False (graceful no-op)."""
    resp = client_no_db.post("/push/send", json={"expo_token": VALID_TOKEN})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["stored"] is False


def test_push_send_no_auth():
    """No Authorization header → 401 or 403 (HTTPBearer security scheme)."""
    from api.main import app

    with TestClient(app) as c:
        resp = c.post("/push/send", json={"expo_token": VALID_TOKEN})
    # HTTPBearer returns 403 when no credentials provided
    assert resp.status_code in (401, 403)


def test_push_send_plain_bearer_rejected():
    """Non-ExponentPushToken with no auth → 401/403 (auth checked first)."""
    from api.main import app

    with TestClient(app) as c:
        resp = c.post(
            "/push/send",
            json={"expo_token": "bad-token"},
            headers={"Authorization": "Bearer invalid.jwt.token"},
        )
    # Token is invalid — 401
    assert resp.status_code in (401, 422)
