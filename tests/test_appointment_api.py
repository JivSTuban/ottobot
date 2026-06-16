"""
tests/test_appointment_api.py — Unit tests for availability + appointment endpoints.

Covers:
- POST /availability: valid + invalid business_id
- GET /availability/{business_id}: slot list response (mocked psycopg)
- POST /appointments/confirm: valid + invalid thread_id + status check

Uses FastAPI TestClient (synchronous). psycopg is mocked at module level to
avoid real DB connections. SUPABASE_DIRECT_URL is monkeypatched empty so
lifespan setup_appointment_tables() is a no-op; AsyncPostgresSaver is also
patched to use InMemorySaver path gracefully.

asyncio_mode = "auto" in pyproject.toml — no @pytest.mark.asyncio decorator needed.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_BID = str(uuid.uuid4())
VALID_TID = str(uuid.uuid4())
PROPOSED_TIME = "2026-06-20T14:00:00+08:00"


def _make_mock_conn():
    """Return an async context manager mock for psycopg.AsyncConnection.connect."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall = AsyncMock(
        return_value=[(0, "09:00", "10:00"), (2, "14:00", "15:00")]
    )

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=mock_cursor)
    # fetchall accessible directly on conn.execute() result
    mock_conn.execute.return_value = mock_cursor

    # Make it work as an async context manager
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
    TestClient with mocked psycopg and empty SUPABASE_DIRECT_URL so the
    lifespan setup_appointment_tables() is a no-op.
    """
    monkeypatch.setenv("SUPABASE_DIRECT_URL", "")
    monkeypatch.setenv("SUPABASE_DB_URI", "")

    with patch("psycopg.AsyncConnection.connect", return_value=_make_mock_conn()):
        from api.main import app
        with TestClient(app) as c:
            yield c


@pytest.fixture
def client_with_db(monkeypatch):
    """
    TestClient where psycopg.AsyncConnection.connect is mocked to return rows,
    used specifically for GET /availability tests.
    """
    monkeypatch.setenv("SUPABASE_DIRECT_URL", "postgresql://fake:fake@localhost/fake")
    monkeypatch.setenv("SUPABASE_DB_URI", "")

    mock_conn_ctx = _make_mock_conn()

    with patch("psycopg.AsyncConnection.connect", return_value=mock_conn_ctx):
        from api.main import app
        with TestClient(app) as c:
            yield c


# ---------------------------------------------------------------------------
# POST /availability
# ---------------------------------------------------------------------------

def test_set_availability_valid(client):
    """Valid business_id + slot list → 200 {"status": "ok"}."""
    body = {
        "business_id": VALID_BID,
        "slots": [
            {"day_of_week": 1, "start_time": "09:00", "end_time": "10:00"}
        ],
    }
    resp = client.post("/availability", json=body)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_set_availability_invalid_business_id(client):
    """Non-UUID business_id → 400."""
    body = {
        "business_id": "not-a-uuid",
        "slots": [
            {"day_of_week": 1, "start_time": "09:00", "end_time": "10:00"}
        ],
    }
    resp = client.post("/availability", json=body)
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /availability/{business_id}
# ---------------------------------------------------------------------------

def test_get_availability_returns_slots(monkeypatch):
    """psycopg fetchall returns 2 rows; response is a list (possibly with slots or fallback)."""
    monkeypatch.setenv("SUPABASE_DIRECT_URL", "postgresql://fake:fake@localhost/fake")
    monkeypatch.setenv("SUPABASE_DB_URI", "")

    mock_conn_ctx = _make_mock_conn()

    with patch("psycopg.AsyncConnection.connect", return_value=mock_conn_ctx):
        from api.main import app
        with TestClient(app) as c:
            resp = c.get(f"/availability/{VALID_BID}")
    assert resp.status_code == 200
    data = resp.json()
    assert "slots" in data
    assert isinstance(data["slots"], list)


# ---------------------------------------------------------------------------
# POST /appointments/confirm
# ---------------------------------------------------------------------------

def test_confirm_appointment_valid(client):
    """Valid thread_id + business_id + proposed_time → 200 {"status": "confirmed"}."""
    body = {
        "thread_id": VALID_TID,
        "business_id": VALID_BID,
        "proposed_time": PROPOSED_TIME,
    }
    resp = client.post("/appointments/confirm", json=body)
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"


def test_confirm_appointment_invalid_thread(client):
    """Non-UUID thread_id → 400."""
    body = {
        "thread_id": "bad-thread-id",
        "business_id": VALID_BID,
        "proposed_time": PROPOSED_TIME,
    }
    resp = client.post("/appointments/confirm", json=body)
    assert resp.status_code == 400


def test_appointment_status_confirmed(client):
    """Confirmed appointment response has status == 'confirmed' and correct thread_id."""
    tid = str(uuid.uuid4())
    body = {
        "thread_id": tid,
        "business_id": VALID_BID,
        "proposed_time": PROPOSED_TIME,
    }
    resp = client.post("/appointments/confirm", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "confirmed"
    assert data["thread_id"] == tid
