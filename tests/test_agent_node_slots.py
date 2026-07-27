"""
tests/test_agent_node_slots.py — TDD tests for agent_node slot injection (Plan 02-03 Task 1).

Covers:
- When stage == "propose_appointment" and slots available:
    proposed_appointment is set to ISO datetime string in returned state
    assistant message contains "Mayroon kaming bakante sa"
- When stage == "propose_appointment" and no slots (empty list):
    assistant message contains FALLBACK_PHRASE
- When stage != "propose_appointment":
    get_available_slots is NOT called; proposed_appointment not in returned dict

asyncio_mode = "auto" in pytest.ini — no @pytest.mark.asyncio decorator needed.
"""

import datetime
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

PH_TZ = datetime.timezone(datetime.timedelta(hours=8))

# A fixed Monday at 10:00 PH — slot at 14:00 qualifies (4h gap > 2h buffer)
_NOW = datetime.datetime(2026, 6, 15, 10, 0, 0, tzinfo=PH_TZ)
_SLOT_DT = datetime.datetime(2026, 6, 15, 14, 0, 0, tzinfo=PH_TZ)


def _make_state(**overrides) -> dict:
    """Return a minimal ConversationState-compatible dict."""
    base = {
        "messages": [{"role": "user", "content": "Pwede ba mag-book?"}],
        "stage": "propose_appointment",
        "thread_id": str(uuid.uuid4()),
        "escalated": False,
        "visit_count": {},
        "message_timestamps": [],
        "industry": "dental",
        "system_alert": "",
        "proposed_appointment": None,
    }
    base.update(overrides)
    return base


def _fake_completion(content: str = "Test reply"):
    """Return a fake LiteLLM completion response."""
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


# ---------------------------------------------------------------------------
# Task 1 — Test: slot injection when slots available
# ---------------------------------------------------------------------------


async def test_agent_node_sets_proposed_appointment_when_slots_available(monkeypatch):
    """When stage == propose_appointment and slots exist, proposed_appointment is ISO datetime string."""
    # Stub: get_available_slots returns one availability row
    availability_row = {
        "day_of_week": 0,  # Monday
        "start_time": datetime.time(14, 0),
        "end_time": datetime.time(15, 0),
    }
    mock_get_slots = AsyncMock(return_value=[availability_row])

    # Stub compute_next_slots to return our fixed slot
    mock_compute = MagicMock(return_value=[_SLOT_DT])

    # Stub router.acompletion
    mock_router = AsyncMock(return_value=_fake_completion("Sige, may bakante kami!"))

    import os
    monkeypatch.setenv("BUSINESS_ID", "biz-001")

    with (
        patch("agent.graph.get_available_slots", mock_get_slots),
        patch("agent.graph.compute_next_slots", mock_compute),
        patch("agent.llm.router.acompletion", mock_router),
    ):
        from agent.graph import agent_node
        state = _make_state(stage="propose_appointment")
        result = await agent_node(state)

    assert "proposed_appointment" in result
    assert result["proposed_appointment"] is not None
    # Should be an ISO format string
    iso_str = result["proposed_appointment"]
    parsed = datetime.datetime.fromisoformat(iso_str)
    assert parsed.hour == 14


async def test_agent_node_reply_contains_tagalog_slot_text(monkeypatch):
    """When stage == propose_appointment and slots exist, LLM context contains 'Mayroon kaming bakante sa'."""
    availability_row = {
        "day_of_week": 0,
        "start_time": datetime.time(14, 0),
        "end_time": datetime.time(15, 0),
    }
    mock_get_slots = AsyncMock(return_value=[availability_row])
    mock_compute = MagicMock(return_value=[_SLOT_DT])

    captured_messages = []

    async def capture_completion(**kwargs):
        captured_messages.extend(kwargs.get("messages", []))
        return _fake_completion("May bakante kami sa Lunes!")

    import os
    monkeypatch.setenv("BUSINESS_ID", "biz-001")

    with (
        patch("agent.graph.get_available_slots", mock_get_slots),
        patch("agent.graph.compute_next_slots", mock_compute),
        patch("agent.llm.router.acompletion", capture_completion),
    ):
        from agent.graph import agent_node
        state = _make_state(stage="propose_appointment")
        await agent_node(state)

    # The stage_instruction system message should contain Tagalog slot text
    all_content = " ".join(
        m.get("content", "") if isinstance(m, dict) else getattr(m, "content", "")
        for m in captured_messages
    )
    assert "Mayroon kaming bakante sa" in all_content


async def test_agent_node_reply_contains_fallback_when_no_slots(monkeypatch):
    """When stage == propose_appointment and no slots, LLM context contains FALLBACK_PHRASE."""
    mock_get_slots = AsyncMock(return_value=[])  # empty — no availability
    mock_compute = MagicMock(return_value=[])

    captured_messages = []

    async def capture_completion(**kwargs):
        captured_messages.extend(kwargs.get("messages", []))
        return _fake_completion("Tawagan ka namin!")

    import os
    monkeypatch.setenv("BUSINESS_ID", "biz-001")

    with (
        patch("agent.graph.get_available_slots", mock_get_slots),
        patch("agent.graph.compute_next_slots", mock_compute),
        patch("agent.llm.router.acompletion", capture_completion),
    ):
        from agent.graph import agent_node
        state = _make_state(stage="propose_appointment")
        await agent_node(state)

    all_content = " ".join(
        m.get("content", "") if isinstance(m, dict) else getattr(m, "content", "")
        for m in captured_messages
    )
    from agent.slots import FALLBACK_PHRASE
    assert FALLBACK_PHRASE in all_content


async def test_agent_node_suppresses_ai_disclosure_on_outbound_start():
    """Outbound-start first turn: system prompt must NOT contain the AI-disclosure block."""
    from agent.graph import OUTBOUND_START_MARKER

    captured_messages = []

    async def capture_completion(*args, **kwargs):
        captured_messages.extend(kwargs.get("messages", []))
        return _fake_completion("Kumusta! Ako si Rica ng Bright Smile Dental.")

    with patch("agent.llm.router.acompletion", capture_completion):
        from agent.graph import agent_node
        state = _make_state(
            stage="intro",
            messages=[{"role": "user", "content": f"{OUTBOUND_START_MARKER} unang mensahe"}],
        )
        await agent_node(state)

    system_text = " ".join(
        m.get("content", "") for m in captured_messages if m.get("role") == "system"
    )
    assert "transparency" not in system_text
    assert "AI assistant" not in system_text


async def test_agent_node_includes_ai_disclosure_on_normal_intro():
    """Normal inbound first turn: system prompt MUST contain the AI-disclosure block."""
    captured_messages = []

    async def capture_completion(*args, **kwargs):
        captured_messages.extend(kwargs.get("messages", []))
        return _fake_completion("Kumusta po!")

    with patch("agent.llm.router.acompletion", capture_completion):
        from agent.graph import agent_node
        state = _make_state(
            stage="intro",
            messages=[{"role": "user", "content": "Kumusta, may tanong ako"}],
        )
        await agent_node(state)

    system_text = " ".join(
        m.get("content", "") for m in captured_messages if m.get("role") == "system"
    )
    assert "transparency" in system_text


async def test_agent_node_does_not_call_slots_on_other_stages(monkeypatch):
    """When stage != propose_appointment, get_available_slots is NOT called."""
    mock_get_slots = AsyncMock(return_value=[])
    mock_router = AsyncMock(return_value=_fake_completion("Kumusta!"))

    with (
        patch("agent.graph.get_available_slots", mock_get_slots),
        patch("agent.llm.router.acompletion", mock_router),
    ):
        from agent.graph import agent_node
        state = _make_state(stage="intro")
        result = await agent_node(state)

    mock_get_slots.assert_not_called()
    # proposed_appointment not set (or None) for non-propose_appointment stages
    assert result.get("proposed_appointment") is None
