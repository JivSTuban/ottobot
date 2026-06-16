"""
agent/state.py — ConversationState TypedDict and STAGES Literal.

Required by all LangGraph graph nodes and the escalation scorer.
"""

from langgraph.graph.message import add_messages
from typing import Annotated, Literal, TypedDict

STAGES = Literal[
    "intro",
    "qualify",
    "pitch",
    "objection_handling",
    "propose_appointment",
    "confirm",
    "escalate",
]


def _append_list(existing: list, new: list) -> list:
    """Reducer: append new timestamps to existing list rather than replace (D-09)."""
    return (existing or []) + (new or [])


class ConversationState(TypedDict):
    messages: Annotated[list, add_messages]
    stage: STAGES
    thread_id: str
    escalated: bool
    visit_count: dict[str, int]  # guards bidirectional edge infinite loops (D-08)
    message_timestamps: Annotated[list[float], _append_list]  # supports 2-of-3 escalation cadence signal (D-09)
    industry: str  # persona selection — persisted across turns (WR-01)
    system_alert: str  # populated by agent_node when escalated=True; consumed by ws_handler state event
    proposed_appointment: str | None  # ISO 8601 datetime string of proposed slot, or None (scalar; last-write-wins)
