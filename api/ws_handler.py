"""
api/ws_handler.py — WebSocket message handler: token streaming + state events.

Anti-pattern: NEVER call asyncio.run() inside this handler.
Calling asyncio.run() inside a running FastAPI event loop raises
RuntimeError: This event loop is already running (AI-SPEC Section 4b.2 / Pitfall).

Imports compiled_graph from api.main via module reference to pick up the value
set during lifespan startup (not at import time when it is still None).
"""

import os
import time

import litellm
import psycopg
from fastapi import WebSocket

import api.main as app_state
from agent.models import DEMO_PROFILES
from api.escalation_service import send_escalation_email, store_escalation
from api.guardrails import (
    check_ai_disclosure,
    holding_message_429,
    validate_business_profile_or_fallback,
)
from api.main import validate_thread_id

# In-memory 429 backoff tracker: thread_id -> retry-after epoch (float).
# If the current time is before the stored epoch, the 30s hold is still active.
_429_backoff: dict[str, float] = {}

# De-duplication: track which threads have already fired escalation notification.
# Prevents re-sending on every subsequent message after the escalate stage is reached.
_escalated_threads: set[str] = set()


async def store_appointment(thread_id: str, business_id: str, confirmed_time: str) -> None:
    """Insert a confirmed appointment row into Supabase appointments table."""
    db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
    if not db_uri:
        return  # no-op in test environments
    async with await psycopg.AsyncConnection.connect(db_uri) as conn:
        await conn.execute(
            "INSERT INTO appointments (thread_id, business_id, proposed_time, status) "
            "VALUES (%s, %s, %s::timestamptz, 'confirmed')",
            (thread_id, business_id, confirmed_time)
        )


async def handle_ws(websocket: WebSocket, thread_id: str) -> None:
    """
    Handle all messages for a single WebSocket connection.

    Per message:
    1. Validate BusinessProfile (guardrail).
    2. Check 429 backoff (guardrail).
    3. Stream LangGraph token chunks as {type:"token"} events.
    4. Send {type:"state"} event after stream completes (DEMO-02 / AGENT-05).
    5. On first turn (intro stage): assert AI disclosure present in system prompt;
       if absent, inject hardcoded disclosure message.
    6. On litellm.RateLimitError: record 30s backoff, send holding message.

    Args:
        websocket: The accepted FastAPI WebSocket connection.
        thread_id: A uuid4 string identifying this lead's conversation thread.
    """
    # Guard: reject connections that arrive before lifespan startup completes (CR-03)
    if app_state.compiled_graph is None:
        await websocket.send_json({
            "type": "system_alert",
            "content": "Server is still initializing. Subukan ulit mamaya.",
        })
        return

    config = {"configurable": {"thread_id": thread_id}}

    async for ws_message in websocket.iter_json():
        msg_type = ws_message.get("type", "text")

        if msg_type == "confirm_appointment":
            # Owner panel confirm/counter flow — handled before LLM call (Pitfall 4)
            raw_thread_id = ws_message.get("thread_id", "")
            raw_business_id = ws_message.get("business_id", os.environ.get("BUSINESS_ID", ""))
            if not validate_thread_id(raw_thread_id):
                await websocket.send_json({"type": "error", "content": "Invalid thread_id"})
                continue
            action = ws_message.get("action", "confirm")
            proposed_time = ws_message.get("proposed_time", "")
            counter_time = ws_message.get("counter_time")
            confirmed_time = counter_time if (action == "counter" and counter_time) else proposed_time
            await store_appointment(raw_thread_id, raw_business_id, confirmed_time)
            await websocket.send_json({
                "type": "appointment_confirmed",
                "confirmed_time": confirmed_time,
                "thread_id": raw_thread_id,
            })
            continue

        user_text = ws_message.get("text", "").strip()
        if not user_text:
            continue

        industry = ws_message.get("industry", "dental")

        # --- Guardrail 1: BusinessProfile validation ---
        profile, err = validate_business_profile_or_fallback(industry)
        if err:
            await websocket.send_json(
                {"type": "token", "content": err, "node": "guardrail"}
            )
            continue

        # --- Guardrail 2: 429 backoff ---
        if _429_backoff.get(thread_id, 0.0) > time.time():
            await websocket.send_json(holding_message_429())
            continue

        # Build initial state for this turn; LangGraph merges with checkpointed state.
        initial_state = {
            "messages": [{"role": "user", "content": user_text}],
            "industry": industry,
            "message_timestamps": [time.time()],
        }

        # --- Stream tokens ---
        # stream_mode="updates" works with LiteLLM Router (non-LangChain ChatModel).
        # Each update is {node_name: state_delta}; we extract and send assistant messages.
        try:
            async for update in app_state.compiled_graph.astream(
                initial_state,
                config=config,
                stream_mode="updates",
            ):
                for node_name, node_update in update.items():
                    for msg in node_update.get("messages", []):
                        role = (
                            msg.get("role") if isinstance(msg, dict)
                            else getattr(msg, "role", None)
                            or ({"ai": "assistant"}.get(getattr(msg, "type", ""), "user"))
                        )
                        content = (
                            msg.get("content") if isinstance(msg, dict)
                            else getattr(msg, "content", "")
                        )
                        if role in ("assistant", "ai") and content:
                            await websocket.send_json(
                                {"type": "token", "content": content, "node": node_name}
                            )
        except litellm.RateLimitError:
            _429_backoff[thread_id] = time.time() + 30
            # Prune expired entries to prevent unbounded growth (WR-02)
            now = time.time()
            for k in [k for k, v in _429_backoff.items() if v < now]:
                del _429_backoff[k]
            await websocket.send_json(holding_message_429())
            continue

        # --- Post-stream state event (DEMO-02 / AGENT-05) ---
        final_state = await app_state.compiled_graph.aget_state(config)
        values = final_state.values if final_state else {}
        stage = values.get("stage", "intro")

        # --- Guardrail 3: AI disclosure check on first turn (CR-05, WR-06) ---
        # Key on message count, not post-turn stage (stage is already advanced after agent_node runs).
        # First turn = exactly 2 messages (user + assistant) in post-turn state.
        all_messages = values.get("messages", [])
        is_first_turn = len(all_messages) <= 2
        if is_first_turn and profile is not None:
            import logging
            from agent.graph import jinja_env  # reuse singleton — avoids per-request make_env() (WR-06)

            rendered_system = profile.render_system_prompt(jinja_env)
            if not check_ai_disclosure(rendered_system):
                logging.getLogger(__name__).warning(
                    "AI disclosure missing in rendered system prompt for industry=%s — "
                    "injecting hardcoded disclosure.",
                    industry,
                )
                await websocket.send_json(
                    {
                        "type": "token",
                        "content": (
                            "Para sa transparency po, ako ay AI assistant. "
                            "Tumutulong ako para sa appointment booking at sales queries."
                        ),
                        "node": "guardrail_disclosure",
                    }
                )

        is_escalated = values.get("escalated", False)
        system_alert = values.get("system_alert", "")

        await websocket.send_json(
            {
                "type": "state",
                "stage": stage,
                "escalated": is_escalated,
                "system_alert": system_alert,
            }
        )

        # --- Escalation notification (once per thread) ---
        if is_escalated and thread_id not in _escalated_threads:
            _escalated_threads.add(thread_id)
            lead_phone = ws_message.get("lead_phone", thread_id)
            business_id = ws_message.get("business_id", os.environ.get("BUSINESS_ID", ""))
            to_email = os.environ.get("RESEND_TO_EMAIL", "")
            # Build conversation summary from last 3 messages
            all_msgs = values.get("messages", [])
            last_three = all_msgs[-3:] if len(all_msgs) >= 3 else all_msgs
            summary_lines = []
            for m in last_three:
                role = (m.get("role") if isinstance(m, dict) else getattr(m, "role", ""))
                content = (m.get("content") if isinstance(m, dict) else getattr(m, "content", ""))
                summary_lines.append(f"{role}: {content}")
            conversation_summary = "\n".join(summary_lines)
            await store_escalation(thread_id, business_id, lead_phone, conversation_summary)
            if to_email:
                await send_escalation_email(to_email, lead_phone, conversation_summary)
