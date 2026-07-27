"""
agent/llm.py — Module-level LiteLLM Router singleton (AGENT-02).

Router is instantiated ONCE at module import. Never instantiate per-request —
that loses rate-limit tracking across calls (Anti-pattern, PATTERNS.md).

Providers (fallback priority order):
  1. Groq Llama 3.3 70B (primary) — rpm=30, tpm=6000 per free tier limits
  2. Gemini Flash (fallback)       — rpm=15
  3. Mistral Small (fallback)      — no explicit RPM limit on free tier

Only providers with a non-empty API key are registered. A keyless deployment
(e.g. an unset GEMINI_API_KEY) raises "Missing <provider> API key" the moment
the Router falls back to it, aborting the chain before it can reach a provider
that IS configured. Excluding keyless providers keeps the fallback chain live.

Routing: usage-based-routing-v2 routes away from models near their RPM/TPM limits.
Fallback chain: any configured provider -> the next configured provider.
"""

import os

from litellm import Router

# Deployment specs in fallback priority order. `key_env` names the env var that
# must hold a non-empty key for the deployment to be registered.
_PROVIDERS = [
    {
        "key_env": "GROQ_API_KEY",
        "params": {
            "model": "groq/llama-3.3-70b-versatile",
            "rpm": 30,
            "tpm": 6000,  # MUST set tpm — Router uses this to pre-empt 429 (Pitfall 3)
        },
    },
    {
        "key_env": "GEMINI_API_KEY",
        "params": {
            "model": "gemini/gemini-1.5-flash",
            "rpm": 15,
        },
    },
    {
        "key_env": "MISTRAL_API_KEY",
        "params": {
            "model": "mistral/mistral-small-latest",
        },
    },
]


def _build_model_list(getenv=os.environ.get):
    """Return litellm model_list entries for providers that have a non-empty API key.

    Keyless providers are excluded so every deployment in the fallback chain can
    actually authenticate. `getenv` is injectable for testing.
    """
    model_list = []
    for provider in _PROVIDERS:
        api_key = (getenv(provider["key_env"], "") or "").strip()
        if not api_key:
            continue
        model_list.append(
            {
                "model_name": "chat",
                "litellm_params": {**provider["params"], "api_key": api_key},
            }
        )
    return model_list


router = Router(
    model_list=_build_model_list(),
    fallbacks=[{"chat": ["chat", "chat"]}],
    num_retries=2,
    retry_after=1,
    routing_strategy="usage-based-routing-v2",
    cache_responses=True,  # free exact-match caching for common greetings (Section 4b.5)
)
