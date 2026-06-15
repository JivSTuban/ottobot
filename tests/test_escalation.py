"""
AGENT-05: Goal-directed escalation logic tests (2-of-3 composite scorer).

Implements the 6 behaviors from Plan 01-03 Task 2.
Uses types.SimpleNamespace(content="...") to mimic LangChain Message objects.
"""

import types
import pytest


def make_msg(content: str):
    """Create a message object with .content attribute (mimics LangChain HumanMessage/AIMessage)."""
    return types.SimpleNamespace(content=content)


def test_two_of_three_signals_escalates():
    """Test 1: All 3 signals present — booking phrase + positive sentiment + fast cadence."""
    from agent.escalation import escalation_scorer

    import time

    t1 = time.time()
    state = {
        "messages": [
            make_msg("kumusta ka?"),
            make_msg("oo sige"),  # signal_2: positive sentiment
            make_msg("gusto ko na mag-book bukas"),  # signal_1: booking phrase
        ],
        "message_timestamps": [t1, t1 + 10],  # signal_3: fast cadence (<30s)
    }
    assert escalation_scorer(state) is True


def test_one_signal_does_not_escalate():
    """Test 2: Only booking phrase present — 1-of-3 is not enough."""
    from agent.escalation import escalation_scorer

    import time

    t1 = time.time()
    state = {
        "messages": [
            make_msg("anong oras kayo bukas?"),
            make_msg("gusto ko mag-book"),  # signal_1 only
        ],
        "message_timestamps": [t1, t1 + 60],  # NOT fast cadence
    }
    result = escalation_scorer(state)
    assert result is False


def test_low_intent_query_does_not_escalate():
    """Test 3: Purely informational query — no signals fire."""
    from agent.escalation import escalation_scorer

    import time

    t1 = time.time()
    state = {
        "messages": [make_msg("may parking ba kayo?")],
        "message_timestamps": [t1],
    }
    assert escalation_scorer(state) is False


def test_booking_phrase_plus_positive_sentiment_escalates():
    """Test 4: Signals 1 and 2 present, slow cadence — still 2-of-3 returns True."""
    from agent.escalation import escalation_scorer

    import time

    t1 = time.time()
    state = {
        "messages": [
            make_msg("opo pwede"),  # signal_2: positive sentiment in last_two
            make_msg("gusto ko mag-book"),  # signal_1: booking phrase
        ],
        "message_timestamps": [t1, t1 + 120],  # slow cadence — signal_3=False
    }
    assert escalation_scorer(state) is True


def test_empty_messages_returns_false():
    """Test 5: Empty messages list returns False immediately."""
    from agent.escalation import escalation_scorer

    state = {"messages": [], "message_timestamps": []}
    assert escalation_scorer(state) is False


def test_pure_object_message_form():
    """Test 6: Messages provided as objects with .content attribute work correctly."""
    from agent.escalation import escalation_scorer

    import time

    t1 = time.time()

    class MsgObj:
        def __init__(self, content: str):
            self.content = content

    state = {
        "messages": [
            MsgObj("oo sige"),  # signal_2: positive sentiment
            MsgObj("i-book na"),  # signal_1: booking phrase
        ],
        "message_timestamps": [t1, t1 + 5],  # signal_3: fast cadence
    }
    assert escalation_scorer(state) is True
