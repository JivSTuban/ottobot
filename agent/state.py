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


class ConversationState(TypedDict):
    messages: Annotated[list, add_messages]
    stage: STAGES
    thread_id: str
    escalated: bool
    visit_count: dict[str, int]  # guards bidirectional edge infinite loops (D-08)
    message_timestamps: list[float]  # supports 2-of-3 escalation cadence signal (D-09)
    system_alert: str  # populated by agent_node when escalated=True; consumed by ws_handler state event
