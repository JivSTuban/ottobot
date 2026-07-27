"""
agent/graph.py — LangGraph StateGraph builder for the OttoBot conversation agent.

Compilation happens in api/main.py lifespan with AsyncPostgresSaver.
In tests, compile with MemorySaver:

    from langgraph.checkpoint.memory import MemorySaver
    graph = builder.compile(checkpointer=MemorySaver())

Exports: builder, agent_node, route_next_stage, _compute_next_stage, jinja_env,
         MAX_HISTORY, BOOKING_PHRASES_FAST

Design: Single-node looping graph.
  - agent_node computes next_stage via _compute_next_stage and writes it into state.
  - route_next_stage (conditional edge) ONLY decides whether to continue ("agent") or END.
    It returns "agent" for any stage != "escalate", and END when stage == "escalate".
  - This avoids the LangGraph pitfall of returning unregistered node names from a
    conditional edge (which silently routes to END and logs "wrote to unknown channel").

Stage routing priority in _compute_next_stage:
  1. escalation_scorer(state)          — 2-of-3 composite signal (D-09)
  2. BOOKING_PHRASES_FAST fast rule    — explicit Taglish booking phrase in last lead msg
  3. visit_count guard                 — pitch >= 3 AND objection_handling -> propose_appointment
  4. D-08 bidirectional edge           — objection_handling + positive sentiment + pitch<3 -> pitch
  5. Deterministic linear progression  — default

NOTE: Do NOT call llm_detect_stage from inside route_next_stage in an async context
(asyncio.run() inside running loop raises RuntimeError). LLM stage detection is
surfaced as a separate node step in future iterations.
"""

import os

from langgraph.graph import StateGraph, END

from agent.escalation import escalation_scorer, POSITIVE_SENTIMENT_PHRASES
from agent.llm import router
from agent.models import make_env, DEMO_PROFILES
from agent.slots import get_available_slots, compute_next_slots, format_slot_tagalog, FALLBACK_PHRASE
from agent.state import ConversationState

# ---------------------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------------------

MAX_HISTORY = 20

# Marker prefixed onto the synthetic first user message when the agent fires the
# opening outbound message (see api/ws_handler.py). On this turn we suppress the
# AI-disclosure block in the system prompt — we don't announce AI upfront.
OUTBOUND_START_MARKER = "[OUTBOUND_START]"

jinja_env = make_env()


def _is_outbound_start(messages: list) -> bool:
    """True if any user message on this turn carries the outbound-start marker."""
    for m in messages:
        role = m.get("role") if hasattr(m, "get") else getattr(m, "role", "")
        if role != "user":
            continue
        content = m.get("content") if hasattr(m, "get") else getattr(m, "content", "")
        if isinstance(content, str) and content.lstrip().startswith(OUTBOUND_START_MARKER):
            return True
    return False

BOOKING_PHRASES_FAST = [
    "gusto ko mag-book",
    "i-book na",
    "puwede ba bukas",
    "anong available",
    "schedule na",
    "mag-set ng appointment",
    "kelan pwede",
    "book na tayo",
    "gusto ko na",
    "punta na ko",
    "magkano",
    "presyo",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STAGE_PROGRESSION: dict = {
    "intro": "qualify",
    "qualify": "pitch",
    "pitch": "objection_handling",
    "objection_handling": "propose_appointment",
    "propose_appointment": "confirm",
    "confirm": "escalate",
    "escalate": END,
}


def _extract_content(msg) -> str:
    """
    Return the lower-cased content string from a message.

    Handles:
    - dict-like: msg.get("content") or msg["content"]
    - object-like: msg.content attribute
    """
    if hasattr(msg, "get"):
        content = msg.get("content") or msg.get("content", "")
    elif hasattr(msg, "content"):
        content = msg.content
    else:
        content = ""
    return (content or "").lower()


def _normalize_message(msg) -> dict:
    """
    Strip checkpoint-restored LangChain message objects down to {role, content}.

    LangChain messages (HumanMessage, AIMessage, etc.) carry extra fields like
    additional_kwargs, response_metadata, type, and id. Mistral's API rejects
    any extra fields. Always normalise before passing to router.acompletion.
    """
    if isinstance(msg, dict):
        return {"role": msg.get("role", "user"), "content": msg.get("content", "")}
    role = getattr(msg, "role", None)
    if role is None:
        # Map LangChain type attr to OpenAI role
        _type = getattr(msg, "type", "human")
        role = {"human": "user", "ai": "assistant", "system": "system"}.get(_type, "user")
    return {"role": role, "content": getattr(msg, "content", "")}


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------


def _compute_next_stage(state: ConversationState) -> tuple[str, bool, str]:
    """
    Compute next stage, escalated flag, and system_alert string.

    Called by agent_node to determine state updates before returning.
    Does NOT read from state["stage"] directly for routing — reads the current stage
    from state to apply the priority rules.

    Returns:
        (next_stage, escalated, system_alert)

    Priority:
    1. escalation_scorer (2-of-3 signals D-09)
    2. BOOKING_PHRASES_FAST explicit fast rule
    3. visit_count guard (pitch >= 3 + objection_handling -> propose_appointment)
    4. D-08 bidirectional: objection_handling + positive sentiment + pitch<3 -> pitch
    5. Deterministic linear progression
    """
    current: str = state.get("stage", "intro")

    # 1. Escalation scorer checks first (T-04-03 mitigation)
    if escalation_scorer(state):
        alert = f"Hot lead detected. Contact the lead now. Stage: {current}"
        return "escalate", True, alert

    messages: list = state.get("messages", [])
    last_msg: str = _extract_content(messages[-1]) if messages else ""

    # 2. Explicit booking phrase fast rule
    if any(p in last_msg for p in BOOKING_PHRASES_FAST):
        alert = f"Hot lead detected. Contact the lead now. Stage: {current}"
        return "escalate", True, alert

    vc: dict = state.get("visit_count") or {}

    # 3. visit_count guard — prevents pitch <-> objection_handling infinite loop (T-04-02)
    if vc.get("pitch", 0) >= 3 and current == "objection_handling":
        return "propose_appointment", False, ""

    # 4. D-08 bidirectional: objection_handling -> pitch on positive sentiment when vc<3
    if (
        current == "objection_handling"
        and any(p in last_msg for p in POSITIVE_SENTIMENT_PHRASES)
        and vc.get("pitch", 0) < 3
    ):
        return "pitch", False, ""

    # 5. Default deterministic linear progression
    next_s = _STAGE_PROGRESSION.get(current, "escalate")
    # _STAGE_PROGRESSION["escalate"] == END (sentinel) — treat as escalate terminal
    if next_s is END:
        next_s = "escalate"
        alert = f"Hot lead detected. Contact the lead now. Stage: {current}"
        return next_s, True, alert
    return next_s, False, ""


async def agent_node(state: ConversationState) -> dict:
    """
    Core agent node — calls LiteLLM Router and returns assistant reply + updated stage/visit_count.

    Prepends persona system prompt on intro stage if no system message exists yet.
    Appends a per-turn stage instruction as the final system message.

    After computing the LLM reply, calls _compute_next_stage to derive next stage
    and writes {"stage", "escalated", "system_alert"} into the returned state dict.
    The conditional edge (route_next_stage) only checks whether stage == "escalate"
    to decide END or loop back to "agent".
    """
    stage: str = state.get("stage", "intro")
    industry: str = state.get("industry", "dental")  # type: ignore[arg-type]
    messages: list = state.get("messages", [])

    # Build prefix: persona system prompt on first turn of intro
    has_system = any(
        (m.get("role") if hasattr(m, "get") else getattr(m, "role", "")) == "system"
        for m in messages
    )
    system_prefix: list = []
    if stage == "intro" and not has_system:
        profile = DEMO_PROFILES.get(industry, DEMO_PROFILES["dental"])
        rendered = profile.render_system_prompt(
            jinja_env, outbound_start=_is_outbound_start(messages)
        )
        system_prefix = [{"role": "system", "content": rendered}]

    # Stage instruction appended as final system message per-turn
    stage_instruction = {
        "role": "system",
        "content": f"Current stage: {stage}. Goal: advance the conversation appropriately.",
    }

    # --- Slot injection for propose_appointment stage ---
    slot_context = ""
    proposed_appointment_iso: str | None = None
    if stage == "propose_appointment":
        business_id = os.environ.get("BUSINESS_ID", "")
        raw_rows = await get_available_slots(business_id)
        next_slots = compute_next_slots(raw_rows)
        if next_slots:
            slot_lines = [format_slot_tagalog(dt) for dt in next_slots]
            slot_context = "\n".join(slot_lines)
            proposed_appointment_iso = next_slots[0].isoformat()
        else:
            slot_context = FALLBACK_PHRASE

    if slot_context:
        stage_instruction = {
            "role": "system",
            "content": stage_instruction["content"] + f"\n\nAvailable slots:\n{slot_context}",
        }

    messages_to_send = (
        system_prefix
        + [_normalize_message(m) for m in messages[-MAX_HISTORY:]]
        + [stage_instruction]
    )

    response = await router.acompletion(
        model="chat",
        messages=messages_to_send,
        max_tokens=512,
        temperature=0.7,
    )

    reply: str = response.choices[0].message.content

    # Update visit_count for current stage
    vc = dict(state.get("visit_count") or {})
    vc[stage] = vc.get(stage, 0) + 1

    # Compute next stage AFTER incrementing visit_count (vc guard depends on updated count)
    # Pass updated vc into a temporary state snapshot for _compute_next_stage
    state_snapshot = dict(state)
    state_snapshot["visit_count"] = vc
    next_stage, escalated, system_alert = _compute_next_stage(state_snapshot)  # type: ignore[arg-type]

    return {
        "messages": [{"role": "assistant", "content": reply}],
        "visit_count": vc,
        "stage": next_stage,
        "escalated": escalated,
        "system_alert": system_alert,
        "proposed_appointment": proposed_appointment_iso,
    }


# ---------------------------------------------------------------------------
# Conditional edge (sync — LangGraph requirement)
# ---------------------------------------------------------------------------


def route_next_stage(state: ConversationState) -> str:
    """
    Pure end-check conditional edge.

    Returns "agent" to loop back for all non-terminal stages.
    Returns END only when stage == "escalate" (terminal stage).

    Stage progression logic lives in agent_node/_compute_next_stage.
    This function never returns an unregistered node name — only "agent" or END.
    """
    current: str = state.get("stage", "intro")
    if current == "escalate":
        return END
    return "agent"


# ---------------------------------------------------------------------------
# Build graph (NOT compiled — compilation happens in api/main.py lifespan)
# ---------------------------------------------------------------------------

builder = StateGraph(ConversationState)
builder.add_node("agent", agent_node)
builder.add_conditional_edges("agent", route_next_stage, {"agent": "agent", END: END})
builder.set_entry_point("agent")
