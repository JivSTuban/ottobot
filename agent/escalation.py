"""
agent/escalation.py — 2-of-3 composite escalation scorer (D-09).

Signals:
  signal_1 — booking phrase detected in last message
  signal_2 — positive sentiment phrase in last two messages
  signal_3 — fast cadence: last message arrived within 30 seconds of previous

Returns True iff at least 2 of the 3 signals fire.
"""

BOOKING_PHRASES = [
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
    "gusto ko na mag-book",
    "mag-schedule",
    "i-set na",
    "reserve na",
    "kelan libre",
    "book na",
]

POSITIVE_SENTIMENT_PHRASES = [
    "ok",
    "sige",
    "sure",
    "oo",
    "opo",
    "tara",
    "pwede",
    "gusto",
    "interesado",
    "maganda",
    "nice",
    "sounds good",
    "i'll go",
    "yes",
    "go na",
    "ayos",
    "tama",
    "agree",
    "ganun ba",
    "sali na ako",
]


def escalation_scorer(state: dict) -> bool:
    """
    Return True iff at least 2 of 3 escalation signals fire.

    Args:
        state: dict with 'messages' (list of objects with .content)
               and 'message_timestamps' (list of float epoch seconds).
    """
    messages = state.get("messages", [])
    if not messages:
        return False

    last_msg = messages[-1].content.lower() if hasattr(messages[-1], "content") else ""
    last_two = [m.content.lower() for m in messages[-2:] if hasattr(m, "content")]

    signal_1 = any(p in last_msg for p in BOOKING_PHRASES)
    signal_2 = sum(1 for m in last_two if any(p in m for p in POSITIVE_SENTIMENT_PHRASES)) >= 1

    timestamps = state.get("message_timestamps", [])
    signal_3 = False
    if len(timestamps) >= 2:
        signal_3 = (timestamps[-1] - timestamps[-2]) < 30  # seconds

    return sum([signal_1, signal_2, signal_3]) >= 2
