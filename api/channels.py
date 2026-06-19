"""
api/channels.py — Outbound channel helpers: SMS via Semaphore PH, Facebook Messenger reply.

Design:
- send_sms(to, message): POST to Semaphore API. No-op if SEMAPHORE_API_KEY absent.
- send_facebook_message(recipient_id, message): POST to Meta Graph API. No-op if token absent.
- deterministic_thread_id(phone, business_id): uuid5(NAMESPACE_DNS, phone+business_id) — stable
  across messages from the same lead to the same business. Matches POLICY.md Phase 4 spec.

Never logs API keys, phone numbers, or message content (T-02-06).
"""

import logging
import os
import uuid

import httpx

logger = logging.getLogger(__name__)

SEMAPHORE_API_URL = "https://api.semaphore.co/api/v4/messages"
FACEBOOK_GRAPH_URL = "https://graph.facebook.com/v19.0/me/messages"


def deterministic_thread_id(phone: str, business_id: str) -> str:
    """
    Return a stable UUID v5 string for a (phone, business_id) pair.

    Same lead messaging the same business always maps to the same thread_id,
    so conversation checkpointing in Postgres persists correctly across messages.
    """
    seed = f"{phone}:{business_id}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, seed))


async def send_sms(to: str, message: str) -> None:
    """
    Send an outbound SMS via Semaphore PH.

    No-ops if SEMAPHORE_API_KEY is absent (safe for test environments).
    """
    api_key = os.environ.get("SEMAPHORE_API_KEY", "")
    if not api_key:
        logger.debug("SEMAPHORE_API_KEY not set — skipping SMS send")
        return

    sender_name = os.environ.get("SEMAPHORE_SENDER_NAME", "OttoBot")
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(
                SEMAPHORE_API_URL,
                data={
                    "apikey": api_key,
                    "number": to,
                    "message": message,
                    "sendername": sender_name,
                },
            )
            if resp.status_code >= 400:
                logger.warning(
                    "Semaphore API returned %s (recipient redacted)", resp.status_code
                )
        except httpx.RequestError as exc:
            logger.warning("Semaphore API request failed: %s", type(exc).__name__)


async def send_facebook_message(recipient_id: str, message: str) -> None:
    """
    Send a reply via Meta Messenger Graph API.

    No-ops if META_PAGE_ACCESS_TOKEN is absent.
    """
    token = os.environ.get("META_PAGE_ACCESS_TOKEN", "")
    if not token:
        logger.debug("META_PAGE_ACCESS_TOKEN not set — skipping Facebook reply")
        return

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.post(
                FACEBOOK_GRAPH_URL,
                params={"access_token": token},
                json={
                    "recipient": {"id": recipient_id},
                    "message": {"text": message},
                },
            )
            if resp.status_code >= 400:
                logger.warning(
                    "Meta Graph API returned %s (recipient redacted)", resp.status_code
                )
        except httpx.RequestError as exc:
            logger.warning("Meta Graph API request failed: %s", type(exc).__name__)
