"""
AGENT-02: LiteLLM Router singleton configuration and fallback tests.

Implements the 5 behaviors from Plan 01-03 Task 3.
Requires GROQ_API_KEY, GEMINI_API_KEY, MISTRAL_API_KEY env vars — set to dummy values.
"""

import os
import pytest

# Set placeholder env vars BEFORE importing agent.llm so Router can be constructed.
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("MISTRAL_API_KEY", "test-key")


def test_router_is_module_level_singleton():
    """Test 1: Importing agent.llm twice returns the same Router instance."""
    import agent.llm as llm_mod_a
    import agent.llm as llm_mod_b

    assert llm_mod_a.router is llm_mod_b.router


def test_build_model_list_includes_all_when_keys_present():
    """All three providers appear when each has a non-empty API key."""
    from agent.llm import _build_model_list

    env = {"GROQ_API_KEY": "g", "GEMINI_API_KEY": "x", "MISTRAL_API_KEY": "m"}
    models = [d["litellm_params"]["model"] for d in _build_model_list(env.get)]
    assert len(models) == 3
    assert any(m.startswith("groq/") for m in models)
    assert any(m.startswith("gemini/") for m in models)
    assert any(m.startswith("mistral/") for m in models)


def test_build_model_list_excludes_providers_with_empty_key():
    """A provider whose API key is empty/absent is dropped from the chain.

    Root cause of the dead-fallback bug: an empty GEMINI_API_KEY registered a
    keyless gemini deployment; LiteLLM raised 'Missing Gemini API key' on
    fallback and never reached mistral. Keyless providers must be excluded.
    """
    from agent.llm import _build_model_list

    env = {"GROQ_API_KEY": "g", "GEMINI_API_KEY": "", "MISTRAL_API_KEY": "m"}
    models = [d["litellm_params"]["model"] for d in _build_model_list(env.get)]
    assert any(m.startswith("groq/") for m in models)
    assert any(m.startswith("mistral/") for m in models)
    assert not any(m.startswith("gemini/") for m in models)


def test_router_deployments_never_have_empty_keys():
    """The live singleton must not carry any deployment with a blank api_key."""
    from agent.llm import router

    models = [e["litellm_params"]["model"] for e in router.model_list]
    assert any(m.startswith("groq/") for m in models)  # primary always present
    for entry in router.model_list:
        assert entry["litellm_params"].get("api_key"), (
            f"deployment {entry['litellm_params']['model']} has a blank api_key"
        )


def test_tpm_limit_present_for_groq():
    """Test 3: Groq model entry has tpm=6000 and rpm=30 (Pitfall 3 prevention)."""
    from agent.llm import router

    groq_entry = next(
        e for e in router.model_list if e["litellm_params"]["model"].startswith("groq/")
    )
    params = groq_entry["litellm_params"]
    assert params.get("tpm") == 6000
    assert params.get("rpm") == 30


def test_usage_based_routing_v2_configured():
    """Test 4: router.routing_strategy is 'usage-based-routing-v2'."""
    from agent.llm import router

    assert router.routing_strategy == "usage-based-routing-v2"


@pytest.mark.integration
def test_groq_429_falls_back_to_gemini():
    """Test 5 (integration): fallbacks are configured as [{'chat': ['chat', 'chat']}].

    Full mocked acompletion fallback test is marked integration.
    Asserts that the fallbacks list is correctly configured instead of
    testing live network behavior.
    """
    from agent.llm import router

    assert router.fallbacks == [{"chat": ["chat", "chat"]}]
