"""
tests/test_stage_detection.py — RED stubs for agent/stage_detection.py (Task 1 of plan 01-04).

TDD: all tests fail intentionally to drive implementation.
"""

import pytest


def test_llm_detect_stage_is_coroutine():
    """llm_detect_stage must be an async function."""
    from agent.stage_detection import llm_detect_stage
    import inspect
    assert inspect.iscoroutinefunction(llm_detect_stage)


def test_detect_stage_structured_is_coroutine():
    """detect_stage_structured must be an async function."""
    from agent.stage_detection import detect_stage_structured
    import inspect
    assert inspect.iscoroutinefunction(detect_stage_structured)


@pytest.mark.asyncio
async def test_stage_detection_fallback_on_exhaustion(monkeypatch):
    """On 3-attempt exhaustion, returns StageDetectionOutput with current_stage and confidence=0.0."""
    import agent.stage_detection as sd
    # Force json-mode path by removing patched_router
    monkeypatch.setattr(sd, "patched_router", None)

    # Make router.acompletion always raise
    from unittest.mock import AsyncMock
    monkeypatch.setattr(sd.router, "acompletion", AsyncMock(side_effect=Exception("fail")))

    result = await sd.detect_stage_structured([], "qualify")
    from agent.models import StageDetectionOutput
    assert isinstance(result, StageDetectionOutput)
    assert result.next_stage == "qualify"
    assert result.confidence == 0.0
    assert result.reasoning == "fallback"


def test_stage_detection_module_imports():
    """Module imports cleanly with placeholder env vars."""
    import agent.stage_detection as sd  # noqa: F401
    assert hasattr(sd, "llm_detect_stage")
    assert hasattr(sd, "detect_stage_structured")
