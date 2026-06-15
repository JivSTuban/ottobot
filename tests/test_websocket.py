"""
DEMO-01/02: FastAPI WebSocket ConnectionManager and owner panel event tests.

Tests cover:
- ConnectionManager connect/disconnect lifecycle
- thread_id uuid4 validation (validate_thread_id helper)
- Token event emitted from astream chunks
- State event emitted after astream completes (owner panel D-05)
- 429 holding message on litellm.RateLimitError
"""

import os
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Set required env vars before importing api modules
os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault("MISTRAL_API_KEY", "test")
os.environ.setdefault("SUPABASE_DB_URI", "postgresql://test")


# ---------------------------------------------------------------------------
# ConnectionManager tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connection_manager_accepts():
    """DEMO-01: ConnectionManager.connect() calls ws.accept() and appends to active_connections."""
    from api.connection_manager import ConnectionManager

    cm = ConnectionManager()
    mock_ws = AsyncMock()
    await cm.connect(mock_ws)

    mock_ws.accept.assert_awaited_once()
    assert mock_ws in cm.active_connections


@pytest.mark.asyncio
async def test_connection_manager_disconnects():
    """DEMO-01: disconnect() removes the WebSocket; double-disconnect is idempotent."""
    from api.connection_manager import ConnectionManager

    cm = ConnectionManager()
    mock_ws = AsyncMock()
    await cm.connect(mock_ws)
    assert len(cm.active_connections) == 1

    cm.disconnect(mock_ws)
    assert len(cm.active_connections) == 0

    # Second disconnect should not raise
    cm.disconnect(mock_ws)
    assert len(cm.active_connections) == 0


# ---------------------------------------------------------------------------
# thread_id validation
# ---------------------------------------------------------------------------


def test_thread_id_must_be_uuid4_rejects_invalid():
    """DEMO-01: validate_thread_id returns False for non-uuid4 strings."""
    from api.main import validate_thread_id

    assert not validate_thread_id("not-a-uuid")
    assert not validate_thread_id("abc")
    assert not validate_thread_id("12345")
    assert not validate_thread_id("")


def test_thread_id_must_be_uuid4_accepts_valid():
    """DEMO-01: validate_thread_id returns True for valid uuid4."""
    from api.main import validate_thread_id

    assert validate_thread_id(str(uuid.uuid4()))


def test_thread_id_rejects_non_uuid_strings():
    """DEMO-01: validate_thread_id rejects strings that are not valid UUID hex formats."""
    from api.main import validate_thread_id

    # These are definitively not UUIDs
    assert not validate_thread_id("not-a-uuid-at-all")
    assert not validate_thread_id("hello world")
    assert not validate_thread_id("1234")
    # Completely invalid hex
    assert not validate_thread_id("zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz")


# ---------------------------------------------------------------------------
# Fake WebSocket helper
# ---------------------------------------------------------------------------


class FakeWebSocket:
    """Minimal fake WebSocket that records send_json calls."""

    def __init__(self, messages: list):
        """
        Args:
            messages: list of dicts yielded one by one by iter_json().
        """
        self._messages = messages
        self.sent: list = []

    async def iter_json(self):
        for msg in self._messages:
            yield msg

    async def send_json(self, data: dict) -> None:
        self.sent.append(data)

    async def accept(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Token event test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_token_event_emitted(monkeypatch):
    """DEMO-01/02: handle_ws sends at least one type='token' event per astream chunk."""
    import api.main as app_state

    # Fake astream async generator yielding one token chunk
    async def fake_astream(initial_state, config, stream_mode):
        chunk = SimpleNamespace(content="hello")
        metadata = {"langgraph_node": "agent"}
        yield chunk, metadata

    # Fake aget_state returns a state with stage=qualify, escalated=False
    fake_state = MagicMock()
    fake_state.values = {"stage": "qualify", "escalated": False}
    fake_compiled = MagicMock()
    fake_compiled.astream = fake_astream
    fake_compiled.aget_state = AsyncMock(return_value=fake_state)

    monkeypatch.setattr(app_state, "compiled_graph", fake_compiled)

    from api.ws_handler import handle_ws

    ws = FakeWebSocket([{"text": "hello", "industry": "dental"}])
    await handle_ws(ws, str(uuid.uuid4()))

    token_events = [m for m in ws.sent if m.get("type") == "token"]
    assert len(token_events) >= 1
    assert token_events[0]["content"] == "hello"


# ---------------------------------------------------------------------------
# State event test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_owner_panel_state_event_emitted(monkeypatch):
    """DEMO-02: After astream completes, handle_ws sends type='state' with stage and escalated."""
    import api.main as app_state

    async def fake_astream(initial_state, config, stream_mode):
        chunk = SimpleNamespace(content="response text")
        yield chunk, {"langgraph_node": "agent"}

    fake_state = MagicMock()
    fake_state.values = {"stage": "qualify", "escalated": False}
    fake_compiled = MagicMock()
    fake_compiled.astream = fake_astream
    fake_compiled.aget_state = AsyncMock(return_value=fake_state)

    monkeypatch.setattr(app_state, "compiled_graph", fake_compiled)

    from api.ws_handler import handle_ws

    ws = FakeWebSocket([{"text": "tell me more", "industry": "dental"}])
    await handle_ws(ws, str(uuid.uuid4()))

    state_events = [m for m in ws.sent if m.get("type") == "state"]
    assert len(state_events) >= 1
    assert state_events[0]["stage"] == "qualify"
    assert state_events[0]["escalated"] is False


# ---------------------------------------------------------------------------
# 429 holding message test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_429_holding_message(monkeypatch):
    """DEMO-01: On litellm.RateLimitError, handle_ws sends the holding_message_429 shape."""
    import litellm

    import api.main as app_state
    from api.ws_handler import _429_backoff

    # Clear any stale backoff entries
    _429_backoff.clear()

    async def raise_rate_limit(initial_state, config, stream_mode):
        raise litellm.RateLimitError(
            message="Rate limit exceeded",
            llm_provider="groq",
            model="llama-4-maverick",
        )
        # unreachable but satisfies async generator protocol
        yield  # pragma: no cover

    fake_compiled = MagicMock()
    fake_compiled.astream = raise_rate_limit
    fake_compiled.aget_state = AsyncMock(return_value=None)

    monkeypatch.setattr(app_state, "compiled_graph", fake_compiled)

    from api.ws_handler import handle_ws

    ws = FakeWebSocket([{"text": "gusto ko mag-book", "industry": "dental"}])
    thread_id = str(uuid.uuid4())
    await handle_ws(ws, thread_id)

    system_alerts = [m for m in ws.sent if m.get("type") == "system_alert"]
    assert len(system_alerts) >= 1
    assert "content" in system_alerts[0]

    # Backoff should now be set
    import time

    assert _429_backoff.get(thread_id, 0) > time.time()
