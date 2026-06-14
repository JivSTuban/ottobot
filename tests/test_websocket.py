"""
DEMO-01/02: FastAPI WebSocket ConnectionManager and owner panel event tests.
Wave 0 stubs — all fail intentionally to drive implementation in plan 04.
"""

import pytest


def test_connection_manager_accepts():
    """DEMO-01: ConnectionManager.connect() accepts WebSocket and appends to active_connections."""
    pytest.fail("Pending: DEMO-01 implementation in plan 04")


def test_connection_manager_disconnects():
    """DEMO-01: ConnectionManager.disconnect() removes WebSocket from active_connections."""
    pytest.fail("Pending: DEMO-01 implementation in plan 04")


def test_owner_panel_state_event_emitted():
    """DEMO-02: After astream completes, ws_handler sends type='state' event with stage and escalated fields."""
    pytest.fail("Pending: DEMO-02 implementation in plan 04")


def test_thread_id_is_uuid():
    """DEMO-01/03: thread_id in WebSocket route must be a valid UUID4 (not sequential int) to prevent state loss on reconnect."""
    pytest.fail("Pending: DEMO-01 implementation in plan 04")
