"""
api/guardrails.py — Online guardrails for the OttoBot WebSocket server.

Three guardrails implemented here:
1. AI disclosure check (NPC 2024-04 — Philippine data privacy regulation)
2. BusinessProfile validation gate (cascades to fallback on Pydantic ValidationError)
3. 429 holding message (returned when all LLM providers are rate-limited)

Exports: check_ai_disclosure, validate_business_profile_or_fallback, holding_message_429,
         AI_DISCLOSURE_PHRASE
"""

from pydantic import ValidationError

from agent.models import DEMO_PROFILES, BusinessProfile

# The exact phrase that the intro template (base.j2) must render.
# Must match the literal string in base.j2 so the guardrail test is unambiguous.
AI_DISCLOSURE_PHRASE = "AI assistant"


def check_ai_disclosure(rendered_intro: str) -> bool:
    """
    Return True iff the rendered intro system prompt contains the NPC 2024-04
    AI disclosure phrase.

    Args:
        rendered_intro: The fully-rendered Jinja2 system prompt string.

    Returns:
        True if AI_DISCLOSURE_PHRASE is present, False otherwise.
    """
    return AI_DISCLOSURE_PHRASE in rendered_intro


def validate_business_profile_or_fallback(
    industry: str,
) -> tuple[BusinessProfile | None, str | None]:
    """
    Resolve and re-validate a BusinessProfile for the given industry.

    Looks up DEMO_PROFILES[industry], falling back to "dental" if the key is
    absent. Re-validates with Pydantic to catch any runtime corruption.

    Returns:
        (BusinessProfile, None) on success.
        (None, holding_message_str) on ValidationError.
    """
    try:
        profile = DEMO_PROFILES.get(industry) or DEMO_PROFILES["dental"]
        # Re-validate to catch any runtime corruption (belt-and-suspenders)
        profile = BusinessProfile.model_validate(profile.model_dump())
        return (profile, None)
    except ValidationError:
        return (None, "Sandali lang po, may technical issue. Subukan ulit mamaya.")


def holding_message_429() -> dict:
    """
    Return the holding message dict sent to the client when all LLM providers
    are rate-limited (cascading 429).

    Returns:
        dict with type "system_alert" and a Tagalog holding message.
    """
    return {
        "type": "system_alert",
        "content": "Sandali lang po, may technical issue kami.",
    }
