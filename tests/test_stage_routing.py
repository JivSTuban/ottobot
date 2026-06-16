"""
AGENT-01: LangGraph stage transition tests — updated for GAP plan routing redesign.

Design change (GAP plan): route_next_stage is now a pure end-check that returns
"agent" or END. All stage progression logic moved to _compute_next_stage (called
by agent_node). Tests now target _compute_next_stage for stage transitions and
route_next_stage for the end-check only.

State format:
  messages: list of dicts {"role": ..., "content": ...} — _extract_content handles both
             dict and object (SimpleNamespace/LangChain message) forms.
  escalation_scorer only fires on messages with .content attribute (objects),
  NOT plain dicts — so routing tests using dict messages isolate routing logic only.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from langgraph.graph import END

from agent.graph import route_next_stage, _compute_next_stage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(
    stage: str = "intro",
    last_content: str = "",
    visit_count: dict | None = None,
    message_role: str = "user",
) -> dict:
    """
    Build a minimal ConversationState dict for routing tests.

    Using plain dicts for messages so escalation_scorer (which checks .content
    attribute) does NOT fire spuriously — isolates routing logic under test.
    """
    return {
        "messages": [{"role": message_role, "content": last_content}],
        "stage": stage,
        "thread_id": "test",
        "escalated": False,
        "visit_count": visit_count or {},
        "message_timestamps": [],
        "system_alert": "",
    }


# ---------------------------------------------------------------------------
# Linear progression tests (now via _compute_next_stage)
# ---------------------------------------------------------------------------


def test_intro_to_qualify():
    """AGENT-01: intro stage transitions to qualify after lead provides name."""
    state = _make_state(stage="intro", last_content="Hi po")
    next_s, escalated, _ = _compute_next_stage(state)
    assert next_s == "qualify"
    assert escalated is False


def test_qualify_to_pitch():
    """AGENT-01: qualify stage transitions to pitch after lead confirms interest."""
    state = _make_state(stage="qualify", last_content="interesado ako")
    next_s, escalated, _ = _compute_next_stage(state)
    assert next_s == "pitch"
    assert escalated is False


def test_pitch_to_objection_handling():
    """AGENT-01: pitch stage transitions to objection_handling on price objection."""
    state = _make_state(stage="pitch", last_content="medyo mahal naman")
    next_s, escalated, _ = _compute_next_stage(state)
    assert next_s == "objection_handling"
    assert escalated is False


# ---------------------------------------------------------------------------
# Bidirectional edge tests (D-08)
# ---------------------------------------------------------------------------


def test_objection_back_to_pitch():
    """AGENT-01: objection_handling can route back to pitch on positive sentiment (D-08 bidirectional edge)."""
    # 'sige' is in POSITIVE_SENTIMENT_PHRASES, pitch visit_count < 3
    state = _make_state(
        stage="objection_handling",
        last_content="sige",
        visit_count={"pitch": 1},
    )
    next_s, escalated, _ = _compute_next_stage(state)
    assert next_s == "pitch"
    assert escalated is False


def test_visit_count_guard_breaks_loop():
    """AGENT-01: visit_count >= 3 on pitch prevents infinite backward edge loop (Pitfall 4)."""
    # pitch visited 3 times already + positive sentiment -> still go to propose_appointment
    state = _make_state(
        stage="objection_handling",
        last_content="sige",
        visit_count={"pitch": 3},
    )
    next_s, escalated, _ = _compute_next_stage(state)
    assert next_s == "propose_appointment"
    assert escalated is False


# ---------------------------------------------------------------------------
# Fast rule escalation tests
# ---------------------------------------------------------------------------


def test_explicit_booking_phrase_escalates():
    """AGENT-01: explicit Taglish booking phrase triggers escalate via fast rule (D-07)."""
    # 'gusto ko mag-book' is in BOOKING_PHRASES_FAST
    state = _make_state(
        stage="pitch",
        last_content="gusto ko mag-book bukas",
    )
    next_s, escalated, alert = _compute_next_stage(state)
    assert next_s == "escalate"
    assert escalated is True
    assert "Hot lead" in alert


def test_escalation_scorer_overrides_progression():
    """AGENT-01: escalation_scorer (2-of-3 signals) escalates regardless of stage."""
    import types
    import time

    # Use SimpleNamespace (has .content) so escalation_scorer fires
    now = time.time()
    msg1 = types.SimpleNamespace(content="gusto ko mag-book")  # booking phrase signal_1
    msg2 = types.SimpleNamespace(content="sige ok")             # positive sentiment signal_2
    # Fast cadence: msg2 arrived 10 seconds after msg1 -> signal_3
    state = {
        "messages": [msg1, msg2],
        "stage": "qualify",
        "thread_id": "test",
        "escalated": False,
        "visit_count": {},
        "message_timestamps": [now - 10, now],  # 10 seconds apart -> signal_3
        "system_alert": "",
    }
    next_s, escalated, alert = _compute_next_stage(state)
    assert next_s == "escalate"
    assert escalated is True


# ---------------------------------------------------------------------------
# route_next_stage end-check tests
# ---------------------------------------------------------------------------


def test_route_next_stage_non_terminal_returns_agent():
    """AGENT-01 (GAP): route_next_stage returns 'agent' for non-escalate stages."""
    for stage in ["intro", "qualify", "pitch", "objection_handling", "propose_appointment", "confirm"]:
        state = _make_state(stage=stage)
        result = route_next_stage(state)
        assert result == "agent", f"Expected 'agent' for stage={stage!r}"


def test_route_next_stage_escalate_returns_end():
    """AGENT-01 (GAP): route_next_stage returns END when stage == 'escalate'."""
    state = _make_state(stage="escalate")
    result = route_next_stage(state)
    assert result is END


# ---------------------------------------------------------------------------
# agent_node tests (require mock_router)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_agent_node_appends_stage_instruction(monkeypatch):
    """Messages list passed to router.acompletion ends with system message containing 'Current stage:'."""
    # Set up mock router response
    mock_message = MagicMock()
    mock_message.content = "MOCK_REPLY"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_acompletion = AsyncMock(return_value=mock_response)

    import agent.graph as graph_module
    monkeypatch.setattr(graph_module.router, "acompletion", mock_acompletion)

    from agent.graph import agent_node

    state = {
        "messages": [{"role": "user", "content": "Magkano po?"}],
        "stage": "pitch",
        "thread_id": "test",
        "escalated": False,
        "visit_count": {},
        "message_timestamps": [],
        "industry": "dental",
    }

    await agent_node(state)

    # Inspect call args
    call_args = mock_acompletion.call_args
    messages_sent = call_args.kwargs.get("messages") or call_args.args[0]
    # Last message must be stage instruction
    last = messages_sent[-1]
    content = last.get("content") if hasattr(last, "get") else last.content
    assert "Current stage:" in content


@pytest.mark.asyncio
async def test_agent_node_updates_visit_count(monkeypatch):
    """After one agent_node call, returned dict's visit_count[stage] is 1."""
    mock_message = MagicMock()
    mock_message.content = "MOCK_REPLY"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_acompletion = AsyncMock(return_value=mock_response)

    import agent.graph as graph_module
    monkeypatch.setattr(graph_module.router, "acompletion", mock_acompletion)

    from agent.graph import agent_node

    state = {
        "messages": [{"role": "user", "content": "Hello"}],
        "stage": "intro",
        "thread_id": "test",
        "escalated": False,
        "visit_count": {},
        "message_timestamps": [],
        "industry": "dental",
    }

    result = await agent_node(state)

    assert result["visit_count"]["intro"] == 1
