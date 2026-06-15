"""
tests/test_graph_module.py — GREEN tests for agent/graph.py (Task 2 of plan 01-04).
"""

import inspect

import pytest

from agent.graph import (
    BOOKING_PHRASES_FAST,
    MAX_HISTORY,
    agent_node,
    builder,
    jinja_env,
    route_next_stage,
)


def test_graph_imports():
    """agent/graph.py must export builder, agent_node, route_next_stage, jinja_env, MAX_HISTORY."""
    assert builder is not None
    assert agent_node is not None
    assert route_next_stage is not None
    assert jinja_env is not None
    assert MAX_HISTORY is not None


def test_max_history_is_20():
    """MAX_HISTORY == 20."""
    assert MAX_HISTORY == 20


def test_agent_node_is_async():
    """agent_node must be an async coroutine function."""
    assert inspect.iscoroutinefunction(agent_node)


def test_route_next_stage_is_callable():
    """route_next_stage must be a sync callable."""
    assert callable(route_next_stage)
    assert not inspect.iscoroutinefunction(route_next_stage)


def test_booking_phrases_fast_contains_required_phrases():
    """BOOKING_PHRASES_FAST must contain 'magkano', 'gusto ko mag-book', 'i-book na'."""
    assert "magkano" in BOOKING_PHRASES_FAST
    assert "gusto ko mag-book" in BOOKING_PHRASES_FAST
    assert "i-book na" in BOOKING_PHRASES_FAST
