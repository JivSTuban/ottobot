"""
agent/graph.py — LangGraph StateGraph builder for the OttoBot conversation agent.

Compilation happens in api/main.py lifespan with AsyncPostgresSaver.
In tests, compile with MemorySaver:

    from langgraph.checkpoint.memory import MemorySaver
    graph = builder.compile(checkpointer=MemorySaver())

Exports: builder, agent_node, route_next_stage, jinja_env, MAX_HISTORY, BOOKING_PHRASES_FAST

Stage routing priority in route_next_stage (sync — LangGraph conditional edge):
  1. escalation_scorer(state)          — 2-of-3 composite signal (D-09)
  2. BOOKING_PHRASES_FAST fast rule    — explicit Taglish booking phrase in last lead msg
  3. visit_count guard                 — pitch >= 3 AND objection_handling -> propose_appointment
  4. D-08 bidirectional edge           — objection_handling + positive sentiment + pitch<3 -> pitch
  5. Deterministic linear progression  — default

NOTE: Do NOT call llm_detect_stage from inside route_next_stage in an async context
(asyncio.run() inside running loop raises RuntimeError). LLM stage detection is
surfaced as a separate node step in future iterations.
"""

from langgraph.graph import StateGraph, END

from agent.escalation import escalation_scorer, POSITIVE_SENTIMENT_PHRASES
from agent.llm import router
from agent.models import make_env, DEMO_PROFILES
from agent.state import ConversationState

# ---------------------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------------------

MAX_HISTORY = 20

jinja_env = make_env()

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


async def agent_node(state: ConversationState) -> dict:
    """
    Core agent node — calls LiteLLM Router and returns assistant reply + updated visit_count.

    Prepends persona system prompt on intro stage if no system message exists yet.
    Appends a per-turn stage instruction as the final system message.
    """
    stage: str = state.get("stage", "intro")
    industry: str = state.get("industry", "dental")  # type: ignore[arg-type]
    messages: list = state.get("messages", [])

    # Build prefix: persona system prompt on first turn of intro
    system_prefix: list = []
    existing_roles = [_extract_content(m) for m in messages]
    has_system = any(
        (m.get("role") if hasattr(m, "get") else getattr(m, "role", "")) == "system"
        for m in messages
    )
    if stage == "intro" and not has_system:
        profile = DEMO_PROFILES.get(industry, DEMO_PROFILES["dental"])
        rendered = profile.render_system_prompt(jinja_env)
        system_prefix = [{"role": "system", "content": rendered}]

    # Stage instruction appended as final system message per-turn
    stage_instruction = {
        "role": "system",
        "content": f"Current stage: {stage}. Goal: advance the conversation appropriately.",
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

    return {
        "messages": [{"role": "assistant", "content": reply}],
        "visit_count": vc,
    }


# ---------------------------------------------------------------------------
# Conditional edge (sync — LangGraph requirement)
# ---------------------------------------------------------------------------


def route_next_stage(state: ConversationState) -> str:
    """
    Determine next stage synchronously.

    Priority:
    1. escalation_scorer (2-of-3 signals D-09)
    2. BOOKING_PHRASES_FAST explicit fast rule
    3. visit_count guard (pitch >= 3 + objection_handling -> propose_appointment)
    4. D-08 bidirectional: objection_handling + positive sentiment + pitch<3 -> pitch
    5. Deterministic linear progression
    """
    # 1. Escalation scorer checks first (T-04-03 mitigation)
    if escalation_scorer(state):
        return "escalate"

    messages: list = state.get("messages", [])
    last_msg: str = _extract_content(messages[-1]) if messages else ""

    # 2. Explicit booking phrase fast rule
    if any(p in last_msg for p in BOOKING_PHRASES_FAST):
        return "escalate"

    vc: dict = state.get("visit_count") or {}
    current: str = state.get("stage", "intro")

    # 3. visit_count guard — prevents pitch <-> objection_handling infinite loop (T-04-02)
    if vc.get("pitch", 0) >= 3 and current == "objection_handling":
        return "propose_appointment"

    # 4. D-08 bidirectional: objection_handling -> pitch on positive sentiment when vc<3
    if (
        current == "objection_handling"
        and any(p in last_msg for p in POSITIVE_SENTIMENT_PHRASES)
        and vc.get("pitch", 0) < 3
    ):
        return "pitch"

    # 5. Default deterministic linear progression
    return _STAGE_PROGRESSION.get(current, END)


# ---------------------------------------------------------------------------
# Build graph (NOT compiled — compilation happens in api/main.py lifespan)
# ---------------------------------------------------------------------------

builder = StateGraph(ConversationState)
builder.add_node("agent", agent_node)
builder.add_conditional_edges("agent", route_next_stage)
builder.set_entry_point("agent")
