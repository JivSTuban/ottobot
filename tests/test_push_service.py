"""
tests/test_push_service.py — Unit tests for send_push_notification() in api/escalation_service.py.

Uses pytest-asyncio and mocked httpx to verify behavior without real Expo API calls.
Follows the exact mock pattern from tests/test_escalation_service.py.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx as _httpx


# ---------------------------------------------------------------------------
# send_push_notification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_push_no_token():
    """No-op when expo_token is empty string — AsyncClient never instantiated."""
    from api.escalation_service import send_push_notification

    with patch("api.escalation_service.httpx.AsyncClient") as mock_client:
        await send_push_notification("", "Hot lead — tumawag na!", "Call now", {})
        mock_client.assert_not_called()


@pytest.mark.asyncio
async def test_send_push_sends_correct_payload():
    """Posts correct JSON payload to Expo Push API; no Authorization header."""
    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_post = AsyncMock(return_value=mock_response)
    mock_client_instance = AsyncMock()
    mock_client_instance.post = mock_post
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    from api.escalation_service import send_push_notification

    with patch("api.escalation_service.httpx.AsyncClient", return_value=mock_client_instance):
        await send_push_notification(
            "ExponentPushToken[test]",
            "Hot lead — tumawag na!",
            "Call now",
            {},
        )

    call_kwargs = mock_post.call_args
    sent_json = call_kwargs.kwargs["json"]
    assert sent_json["to"] == "ExponentPushToken[test]"
    assert sent_json["title"] == "Hot lead — tumawag na!"
    assert sent_json["body"] == "Call now"
    assert sent_json["sound"] == "default"
    assert sent_json["channelId"] == "default"
    # Expo Push API must NOT receive an Authorization header
    headers = call_kwargs.kwargs.get("headers", {})
    assert "Authorization" not in headers


@pytest.mark.asyncio
async def test_send_push_http_error():
    """Logs warning but does not raise on httpx.RequestError."""
    mock_post = AsyncMock(side_effect=_httpx.ConnectError("connection refused"))
    mock_client_instance = AsyncMock()
    mock_client_instance.post = mock_post
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    from api.escalation_service import send_push_notification

    with patch("api.escalation_service.httpx.AsyncClient", return_value=mock_client_instance):
        # Must not raise
        await send_push_notification(
            "ExponentPushToken[test]",
            "Hot lead — tumawag na!",
            "Call now",
            {},
        )


@pytest.mark.asyncio
async def test_send_push_4xx_response():
    """Logs warning but does not raise on 4xx response from Expo Push API."""
    mock_response = MagicMock()
    mock_response.status_code = 400

    mock_post = AsyncMock(return_value=mock_response)
    mock_client_instance = AsyncMock()
    mock_client_instance.post = mock_post
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    from api.escalation_service import send_push_notification

    with patch("api.escalation_service.httpx.AsyncClient", return_value=mock_client_instance):
        # Must not raise
        await send_push_notification(
            "ExponentPushToken[test]",
            "Hot lead — tumawag na!",
            "Call now",
            {},
        )
