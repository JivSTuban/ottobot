"""
DEMO-03: LangGraph AsyncPostgresSaver persistence tests.
Wave 0 stubs — all fail intentionally to drive implementation in plan 04.
"""

import pytest


def test_state_resumes_after_reconnect():
    """DEMO-03: Conversation state is recoverable from AsyncPostgresSaver using thread_id after WebSocket reconnect."""
    pytest.fail("Pending: DEMO-03 implementation in plan 04")


def test_async_postgres_saver_setup_idempotent():
    """DEMO-03: checkpointer.setup() is idempotent — safe to call on every startup (Pitfall 2 prevention)."""
    pytest.fail("Pending: DEMO-03 implementation in plan 04")
