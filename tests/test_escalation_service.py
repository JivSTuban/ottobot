"""
tests/test_escalation_service.py — Unit tests for api/escalation_service.py.

Uses pytest-anyio and mocked httpx / psycopg to verify behavior without
real API keys or database connections.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# send_escalation_email
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_escalation_email_no_key(monkeypatch):
    """No-op when RESEND_API_KEY is absent."""
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    from api.escalation_service import send_escalation_email
    # Should complete without error and without making any HTTP request
    with patch("httpx.AsyncClient") as mock_client:
        await send_escalation_email("owner@example.com", "+63917000000", "test summary")
        mock_client.assert_not_called()


@pytest.mark.asyncio
async def test_send_escalation_email_sends_correct_payload(monkeypatch):
    """Posts correct JSON payload to Resend API when key is set."""
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    monkeypatch.setenv("RESEND_TO_EMAIL", "owner@example.com")
    monkeypatch.setenv("RESEND_FROM_EMAIL", "bot@test.app")

    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_post = AsyncMock(return_value=mock_response)
    mock_client_instance = AsyncMock()
    mock_client_instance.post = mock_post
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    from api.escalation_service import send_escalation_email

    with patch("api.escalation_service.httpx.AsyncClient", return_value=mock_client_instance):
        await send_escalation_email("owner@example.com", "+63917000000", "Gusto ko mag-book")

    call_kwargs = mock_post.call_args
    sent_json = call_kwargs.kwargs["json"]
    assert "+63917000000" in sent_json["subject"]
    assert "+63917000000" in sent_json["text"]
    assert "Gusto ko mag-book" in sent_json["text"]
    assert sent_json["to"] == ["owner@example.com"]
    assert sent_json["from"] == "bot@test.app"


@pytest.mark.asyncio
async def test_send_escalation_email_handles_api_error(monkeypatch):
    """Logs warning but does not raise on Resend API 4xx response."""
    monkeypatch.setenv("RESEND_API_KEY", "re_bad_key")

    mock_response = MagicMock()
    mock_response.status_code = 403

    mock_post = AsyncMock(return_value=mock_response)
    mock_client_instance = AsyncMock()
    mock_client_instance.post = mock_post
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    from api.escalation_service import send_escalation_email

    with patch("api.escalation_service.httpx.AsyncClient", return_value=mock_client_instance):
        # Should not raise even on 403
        await send_escalation_email("owner@example.com", "+63917000000", "summary")


@pytest.mark.asyncio
async def test_send_escalation_email_handles_network_error(monkeypatch):
    """Logs warning but does not raise on httpx network errors."""
    import httpx as _httpx
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")

    mock_post = AsyncMock(side_effect=_httpx.ConnectError("connection refused"))
    mock_client_instance = AsyncMock()
    mock_client_instance.post = mock_post
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    from api.escalation_service import send_escalation_email

    with patch("api.escalation_service.httpx.AsyncClient", return_value=mock_client_instance):
        await send_escalation_email("owner@example.com", "+63917000000", "summary")


# ---------------------------------------------------------------------------
# store_escalation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_store_escalation_no_db(monkeypatch):
    """No-op when no DB URI is configured."""
    monkeypatch.delenv("SUPABASE_DIRECT_URL", raising=False)
    monkeypatch.delenv("SUPABASE_DB_URI", raising=False)

    from api.escalation_service import store_escalation

    with patch("psycopg.AsyncConnection.connect") as mock_connect:
        await store_escalation("thread-1", "biz-1", "+63917000000", "summary")
        mock_connect.assert_not_called()


@pytest.mark.asyncio
async def test_store_escalation_inserts_row(monkeypatch):
    """Executes INSERT when DB URI is set."""
    monkeypatch.setenv("SUPABASE_DIRECT_URL", "postgresql://test:test@localhost/test")

    mock_conn = AsyncMock()
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=False)

    from api.escalation_service import store_escalation

    with patch("psycopg.AsyncConnection.connect", return_value=mock_conn):
        await store_escalation("thread-1", "biz-1", "+63917000000", "last 3 messages")

    mock_conn.execute.assert_called_once()
    call_args = mock_conn.execute.call_args
    sql = call_args.args[0]
    params = call_args.args[1]
    assert "INSERT INTO escalations" in sql
    assert params[0] == "thread-1"
    assert params[1] == "biz-1"
    assert params[2] == "+63917000000"
    assert "last 3 messages" in params[3]
