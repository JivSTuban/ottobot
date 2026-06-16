"""
agent/llm.py — Module-level LiteLLM Router singleton (AGENT-02).

Router is instantiated ONCE at module import. Never instantiate per-request —
that loses rate-limit tracking across calls (Anti-pattern, PATTERNS.md).

Providers:
  1. Groq Llama 4 Maverick (primary) — rpm=30, tpm=6000 per free tier limits
  2. Gemini Flash (fallback)          — rpm=15
  3. Mistral Small (fallback)         — no explicit RPM limit on free tier

Routing: usage-based-routing-v2 routes away from models near their RPM/TPM limits.
Fallback chain: Groq -> Gemini -> Mistral.
"""

import os

from litellm import Router

router = Router(
    model_list=[
        {
            "model_name": "chat",
            "litellm_params": {
                "model": "groq/meta-llama/llama-4-scout-17b-16e-instruct",
                "api_key": os.environ.get("GROQ_API_KEY", ""),
                "rpm": 30,
                "tpm": 6000,  # MUST set tpm — Router uses this to pre-empt 429 (Pitfall 3)
            },
        },
        {
            "model_name": "chat",
            "litellm_params": {
                "model": "gemini/gemini-1.5-flash",
                "api_key": os.environ.get("GEMINI_API_KEY", ""),
                "rpm": 15,
            },
        },
        {
            "model_name": "chat",
            "litellm_params": {
                "model": "mistral/mistral-small-latest",
                "api_key": os.environ.get("MISTRAL_API_KEY", ""),
            },
        },
    ],
    fallbacks=[{"chat": ["chat", "chat"]}],
    num_retries=2,
    retry_after=1,
    routing_strategy="usage-based-routing-v2",
    cache_responses=True,  # free exact-match caching for common greetings (Section 4b.5)
)
