"""
api/escalation_service.py — Escalation notification and persistence helpers.

Sends a plain-text email via the Resend API and stores the escalation event in
the Supabase `escalations` table.

Both helpers are no-ops when the required env vars are absent (safe for unit tests).
Never logs API keys or full db URIs (T-02-06).
"""

import logging
import os

import httpx
import psycopg

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


async def send_push_notification(
    expo_token: str,
    title: str,
    body: str,
    data: dict | None = None,
) -> None:
    """
    Send a push notification via the Expo Push HTTP API.

    No-ops if expo_token is empty (graceful degradation when device has not
    registered a push token). Push failure never crashes the escalation flow.
    No Authorization header — Expo identifies the target device via the "to" field.
    """
    if not expo_token:
        return

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                EXPO_PUSH_URL,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json={
                    "to": expo_token,
                    "title": title,
                    "body": body,
                    "data": data or {},
                    "sound": "default",
                    "channelId": "default",
                },
            )
            if resp.status_code >= 400:
                logger.warning("Expo Push API returned %s", resp.status_code)
        except httpx.RequestError as exc:
            logger.warning("Expo Push API request failed: %s", type(exc).__name__)


async def send_escalation_email(
    to_email: str,
    lead_phone: str,
    conversation_summary: str,
) -> None:
    """
    Send a hot-lead notification email via Resend.

    No-ops if RESEND_API_KEY is not set (graceful degradation for test environments).
    Email is plain-text only — no HTML per POLICY.md Phase 3.
    """
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        logger.debug("RESEND_API_KEY not set — skipping escalation email")
        return

    from_email = os.environ.get("RESEND_FROM_EMAIL", "ottobot@noreply.ottobot.app")
    body = (
        f"Hot lead! Call {lead_phone} now.\n\n"
        f"Conversation summary:\n{conversation_summary}"
    )

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": from_email,
                    "to": [to_email],
                    "subject": f"Hot lead — call {lead_phone} now",
                    "text": body,
                },
            )
            if resp.status_code >= 400:
                logger.warning(
                    "Resend API returned %s for escalation email (lead redacted)",
                    resp.status_code,
                )
        except httpx.RequestError as exc:
            logger.warning("Resend API request failed: %s", type(exc).__name__)


async def store_escalation(
    thread_id: str,
    business_id: str,
    lead_phone: str,
    conversation_summary: str,
) -> None:
    """
    Insert an escalation event into the Supabase `escalations` table.

    No-ops if neither SUPABASE_DIRECT_URL nor SUPABASE_DB_URI is set.
    outcome defaults to 'not_called' — updated by the business owner later.
    """
    db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
    if not db_uri:
        logger.debug("No DB URI — skipping escalation storage")
        return

    # Persisting the escalation is best-effort: the real-time HOT-LEAD alert has
    # already fired via graph state. A dead/unreachable DB must NOT propagate —
    # an uncaught OperationalError here would bubble out of the WebSocket handler
    # and close the live conversation. Log and degrade instead.
    try:
        async with await psycopg.AsyncConnection.connect(db_uri) as conn:
            await conn.execute(
                """
                INSERT INTO escalations
                    (thread_id, business_id, lead_phone, conversation_summary, outcome)
                VALUES (%s, %s, %s, %s, 'not_called')
                ON CONFLICT (thread_id) DO NOTHING
                """,
                (thread_id, business_id, lead_phone, conversation_summary),
            )
    except (psycopg.OperationalError, psycopg.DatabaseError) as exc:
        logger.warning(
            "Escalation DB write failed — alert already sent, continuing without persistence: %s",
            type(exc).__name__,
        )
