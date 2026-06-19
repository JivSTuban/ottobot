"""
tests/test_channels.py — Unit tests for Phase 4 real channels.

Covers:
- api/channels.py: send_sms, send_facebook_message, deterministic_thread_id
- api/main.py: /webhook/sms, GET/POST /webhook/facebook, /leads/upload, /webhook/lead-form
"""

import io
import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Set required env vars before importing api modules
os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault("MISTRAL_API_KEY", "test")

from httpx import AsyncClient, ASGITransport


# ---------------------------------------------------------------------------
# deterministic_thread_id
# ---------------------------------------------------------------------------

def test_deterministic_thread_id_is_stable():
    """Same phone + business_id always returns the same uuid5."""
    from api.channels import deterministic_thread_id

    tid1 = deterministic_thread_id("+63917000000", "biz-abc")
    tid2 = deterministic_thread_id("+63917000000", "biz-abc")
    assert tid1 == tid2


def test_deterministic_thread_id_differs_by_phone():
    """Different phones produce different thread IDs."""
    from api.channels import deterministic_thread_id

    tid1 = deterministic_thread_id("+63917000001", "biz-abc")
    tid2 = deterministic_thread_id("+63917000002", "biz-abc")
    assert tid1 != tid2


def test_deterministic_thread_id_differs_by_business():
    """Same phone, different business → different thread ID."""
    from api.channels import deterministic_thread_id

    tid1 = deterministic_thread_id("+63917000000", "biz-abc")
    tid2 = deterministic_thread_id("+63917000000", "biz-xyz")
    assert tid1 != tid2


def test_deterministic_thread_id_is_valid_uuid():
    """Output is a valid UUID string."""
    from api.channels import deterministic_thread_id

    tid = deterministic_thread_id("+63917000000", "biz-abc")
    parsed = uuid.UUID(tid)
    assert parsed.version == 5


# ---------------------------------------------------------------------------
# send_sms
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_sms_no_key(monkeypatch):
    """No-op when SEMAPHORE_API_KEY is absent."""
    monkeypatch.delenv("SEMAPHORE_API_KEY", raising=False)
    from api.channels import send_sms

    with patch("httpx.AsyncClient") as mock_client:
        await send_sms("+63917000000", "Hello")
        mock_client.assert_not_called()


@pytest.mark.asyncio
async def test_send_sms_posts_correct_payload(monkeypatch):
    """Posts correct form data to Semaphore API when key is set."""
    monkeypatch.setenv("SEMAPHORE_API_KEY", "test_key")
    monkeypatch.setenv("SEMAPHORE_SENDER_NAME", "OttoBot")

    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_post = AsyncMock(return_value=mock_response)
    mock_client_instance = AsyncMock()
    mock_client_instance.post = mock_post
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    from api.channels import send_sms

    with patch("api.channels.httpx.AsyncClient", return_value=mock_client_instance):
        await send_sms("+63917000000", "Magandang araw!")

    call_kwargs = mock_post.call_args
    sent_data = call_kwargs.kwargs["data"]
    assert sent_data["apikey"] == "test_key"
    assert sent_data["number"] == "+63917000000"
    assert "Magandang araw!" in sent_data["message"]
    assert sent_data["sendername"] == "OttoBot"


@pytest.mark.asyncio
async def test_send_sms_handles_api_error(monkeypatch):
    """Logs warning but does not raise on Semaphore 4xx."""
    monkeypatch.setenv("SEMAPHORE_API_KEY", "test_key")

    mock_response = MagicMock()
    mock_response.status_code = 400

    mock_post = AsyncMock(return_value=mock_response)
    mock_client_instance = AsyncMock()
    mock_client_instance.post = mock_post
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    from api.channels import send_sms

    with patch("api.channels.httpx.AsyncClient", return_value=mock_client_instance):
        await send_sms("+63917000000", "test")  # should not raise


# ---------------------------------------------------------------------------
# send_facebook_message
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_facebook_message_no_token(monkeypatch):
    """No-op when META_PAGE_ACCESS_TOKEN is absent."""
    monkeypatch.delenv("META_PAGE_ACCESS_TOKEN", raising=False)
    from api.channels import send_facebook_message

    with patch("httpx.AsyncClient") as mock_client:
        await send_facebook_message("12345", "Hello")
        mock_client.assert_not_called()


@pytest.mark.asyncio
async def test_send_facebook_message_posts_correct_payload(monkeypatch):
    """Posts recipient + message to Graph API when token is set."""
    monkeypatch.setenv("META_PAGE_ACCESS_TOKEN", "test_token")

    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_post = AsyncMock(return_value=mock_response)
    mock_client_instance = AsyncMock()
    mock_client_instance.post = mock_post
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    from api.channels import send_facebook_message

    with patch("api.channels.httpx.AsyncClient", return_value=mock_client_instance):
        await send_facebook_message("fb_user_123", "Kumusta!")

    call_kwargs = mock_post.call_args
    sent_json = call_kwargs.kwargs["json"]
    assert sent_json["recipient"]["id"] == "fb_user_123"
    assert sent_json["message"]["text"] == "Kumusta!"


# ---------------------------------------------------------------------------
# /webhook/sms endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sms_webhook_returns_ok(monkeypatch):
    """POST /webhook/sms returns {status: ok} and thread_id."""
    monkeypatch.setenv("BUSINESS_ID", "")
    monkeypatch.setenv("DEFAULT_INDUSTRY", "dental")

    from api.main import app

    # Patch compiled_graph to return empty update (no agent call needed)
    import api.main as app_state

    async def fake_astream(*args, **kwargs):
        return
        yield  # make it an async generator

    fake_compiled = MagicMock()
    fake_compiled.astream = fake_astream
    monkeypatch.setattr(app_state, "compiled_graph", fake_compiled)

    # Patch send_sms so no real API call happens
    with patch("api.channels.send_sms", new_callable=AsyncMock):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/webhook/sms",
                json={
                    "message": "Gusto ko mag-book",
                    "senderNumber": "+63917000000",
                },
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "thread_id" in data


# ---------------------------------------------------------------------------
# /webhook/facebook GET (verify)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_facebook_webhook_verify_success(monkeypatch):
    """GET /webhook/facebook returns hub.challenge when token matches."""
    monkeypatch.setenv("FACEBOOK_VERIFY_TOKEN", "my_secret_token")

    from api.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/webhook/facebook",
            params={
                "hub_mode": "subscribe",
                "hub_challenge": "12345",
                "hub_verify_token": "my_secret_token",
            },
        )

    assert resp.status_code == 200
    assert resp.json() == 12345


@pytest.mark.asyncio
async def test_facebook_webhook_verify_wrong_token(monkeypatch):
    """GET /webhook/facebook returns 403 when token does not match."""
    monkeypatch.setenv("FACEBOOK_VERIFY_TOKEN", "my_secret_token")

    from api.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/webhook/facebook",
            params={
                "hub_mode": "subscribe",
                "hub_challenge": "12345",
                "hub_verify_token": "wrong_token",
            },
        )

    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# /webhook/facebook POST (message routing)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_facebook_webhook_post_routes_message(monkeypatch):
    """POST /webhook/facebook calls send_facebook_message with agent reply."""
    monkeypatch.setenv("BUSINESS_ID", "")
    monkeypatch.setenv("DEFAULT_INDUSTRY", "dental")

    from api.main import app
    import api.main as app_state

    async def fake_astream(*args, **kwargs):
        yield {"agent": {"messages": [{"role": "assistant", "content": "Kumusta!"}]}}

    fake_compiled = MagicMock()
    fake_compiled.astream = fake_astream
    monkeypatch.setattr(app_state, "compiled_graph", fake_compiled)

    send_mock = AsyncMock()
    with patch("api.channels.send_facebook_message", send_mock):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/webhook/facebook",
                json={
                    "object": "page",
                    "entry": [
                        {
                            "messaging": [
                                {
                                    "sender": {"id": "fb_user_123"},
                                    "message": {"text": "Gusto ko mag-book"},
                                }
                            ]
                        }
                    ],
                },
            )

    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    send_mock.assert_awaited_once()
    call_args = send_mock.call_args
    assert call_args.args[0] == "fb_user_123"
    assert "Kumusta!" in call_args.args[1]


# ---------------------------------------------------------------------------
# /leads/upload
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_lead_upload_invalid_business_id(monkeypatch):
    """POST /leads/upload returns 400 for non-UUID business_id."""
    from api.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        csv_content = b"phone,name\n+63917000000,Juan\n"
        resp = await client.post(
            "/leads/upload?business_id=not-a-uuid",
            files={"file": ("leads.csv", io.BytesIO(csv_content), "text/csv")},
        )

    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_lead_upload_sends_greeting_sms(monkeypatch):
    """POST /leads/upload calls send_sms for each valid phone row."""
    monkeypatch.delenv("SUPABASE_DIRECT_URL", raising=False)
    monkeypatch.delenv("SUPABASE_DB_URI", raising=False)
    monkeypatch.setenv("OUTBOUND_GREETING", "Hello test!")

    from api.main import app

    business_id = str(uuid.uuid4())
    csv_content = b"phone,name\n+63917000001,Maria\n+63917000002,Jose\n"

    send_mock = AsyncMock()
    with patch("api.channels.send_sms", send_mock):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                f"/leads/upload?business_id={business_id}",
                files={"file": ("leads.csv", io.BytesIO(csv_content), "text/csv")},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["upserted"] == 2
    assert send_mock.await_count == 2


# ---------------------------------------------------------------------------
# /webhook/lead-form
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_lead_form_webhook_ingests_lead(monkeypatch):
    """POST /webhook/lead-form sends greeting SMS for each inbound lead."""
    monkeypatch.delenv("SUPABASE_DIRECT_URL", raising=False)
    monkeypatch.delenv("SUPABASE_DB_URI", raising=False)
    monkeypatch.setenv("BUSINESS_ID", "")
    monkeypatch.setenv("OUTBOUND_GREETING", "Hi from OttoBot!")

    from api.main import app

    payload = {
        "object": "page",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "leads": [
                                {
                                    "field_data": [
                                        {"name": "phone_number", "values": ["+63917999000"]},
                                        {"name": "full_name", "values": ["Test Lead"]},
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        ],
    }

    send_mock = AsyncMock()
    with patch("api.channels.send_sms", send_mock):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/webhook/lead-form", json=payload)

    assert resp.status_code == 200
    assert resp.json()["ingested"] == 1
    send_mock.assert_awaited_once_with("+63917999000", "Hi from OttoBot!")
