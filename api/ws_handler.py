"""
api/ws_handler.py — WebSocket message handler: token streaming + state events.

Anti-pattern: NEVER call asyncio.run() inside this handler.
Calling asyncio.run() inside a running FastAPI event loop raises
RuntimeError: This event loop is already running (AI-SPEC Section 4b.2 / Pitfall).

Imports compiled_graph from api.main via module reference to pick up the value
set during lifespan startup (not at import time when it is still None).
"""

import time

import litellm
from fastapi import WebSocket

import api.main as app_state
from agent.models import DEMO_PROFILES
from api.guardrails import (
    check_ai_disclosure,
    holding_message_429,
    validate_business_profile_or_fallback,
)

# In-memory 429 backoff tracker: thread_id -> retry-after epoch (float).
# If the current time is before the stored epoch, the 30s hold is still active.
_429_backoff: dict[str, float] = {}


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
    config = {"configurable": {"thread_id": thread_id}}

    async for ws_message in websocket.iter_json():
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
        try:
            async for chunk, metadata in app_state.compiled_graph.astream(
                initial_state,
                config=config,
                stream_mode="messages",
            ):
                if hasattr(chunk, "content") and chunk.content:
                    await websocket.send_json(
                        {
                            "type": "token",
                            "content": chunk.content,
                            "node": metadata.get("langgraph_node", ""),
                        }
                    )
        except litellm.RateLimitError:
            _429_backoff[thread_id] = time.time() + 30
            await websocket.send_json(holding_message_429())
            continue

        # --- Post-stream state event (DEMO-02 / AGENT-05) ---
        final_state = await app_state.compiled_graph.aget_state(config)
        values = final_state.values if final_state else {}
        stage = values.get("stage", "intro")

        # --- Guardrail 3: AI disclosure check on intro stage first turn ---
        if stage == "intro" and profile is not None:
            from agent.models import make_env

            env = make_env()
            rendered_system = profile.render_system_prompt(env)
            if not check_ai_disclosure(rendered_system):
                import logging

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

        await websocket.send_json(
            {
                "type": "state",
                "stage": stage,
                "escalated": values.get("escalated", False),
            }
        )
