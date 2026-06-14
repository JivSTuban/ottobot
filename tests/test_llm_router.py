"""
AGENT-02: LiteLLM Router fallback and configuration tests.
Wave 0 stubs — all fail intentionally to drive implementation in plan 03.
"""

import pytest


def test_groq_429_falls_back_to_gemini():
    """AGENT-02: Router falls back to Gemini Flash when Groq returns 429 (mocked)."""
    pytest.fail("Pending: AGENT-02 implementation in plan 03")


def test_router_is_module_level_singleton():
    """AGENT-02: Router is instantiated once at module level, not per-request (anti-pattern prevention)."""
    pytest.fail("Pending: AGENT-02 implementation in plan 03")


def test_tpm_limit_present():
    """AGENT-02: Groq model entry in Router config has tpm=6000 set (Pitfall 3 prevention)."""
    pytest.fail("Pending: AGENT-02 implementation in plan 03")
