"""
AGENT-03/04: BusinessProfile, Jinja2 render, and StageDetectionOutput tests.
Wave 0 stubs — all fail intentionally to drive implementation in plan 03.
"""

import pytest


def test_business_profile_renders_dental():
    """AGENT-04: BusinessProfile renders correct Jinja2 system prompt for dental persona (Ate Ana)."""
    pytest.fail("Pending: AGENT-03/04 implementation in plan 03")


def test_business_profile_renders_aesthetics():
    """AGENT-04: BusinessProfile renders correct Jinja2 system prompt for aesthetics persona (Ate Bea)."""
    pytest.fail("Pending: AGENT-03/04 implementation in plan 03")


def test_business_profile_renders_real_estate():
    """AGENT-04: BusinessProfile renders correct Jinja2 system prompt for real_estate persona (Kuya Marco)."""
    pytest.fail("Pending: AGENT-03/04 implementation in plan 03")


def test_pricing_none_raises():
    """AGENT-04: BusinessProfile raises ValidationError at instantiation when pricing=None (Pitfall 5 prevention)."""
    pytest.fail("Pending: AGENT-03/04 implementation in plan 03")


def test_stage_detection_confidence_range():
    """AGENT-03: StageDetectionOutput rejects confidence outside [0.0, 1.0]."""
    pytest.fail("Pending: AGENT-03 implementation in plan 03")


def test_render_strict_undefined_raises_on_missing():
    """AGENT-04: Jinja2 StrictUndefined raises UndefinedError when BusinessProfile field is missing (not silent)."""
    pytest.fail("Pending: AGENT-03/04 implementation in plan 03")
