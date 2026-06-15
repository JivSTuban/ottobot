"""
agent/stage_detection.py — LLM stage classifier with structured output (D-07).

IMPORTANT: route_next_stage is sync (LangGraph conditional edge). Do NOT call
llm_detect_stage from inside route_next_stage in FastAPI context —
asyncio.run() inside running loop raises RuntimeError. Use the deterministic
progression as the default; surface LLM detection only as a separate node
update step if needed in future.

Exports:
  - detect_stage_structured(messages, current_stage) -> StageDetectionOutput
  - llm_detect_stage(state) -> str (one of the 7 STAGES)
"""

import logging

from agent.llm import router
from agent.models import StageDetectionOutput

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# instructor.patch compatibility — try patching, fall back to JSON-mode
# ---------------------------------------------------------------------------

patched_router = None

try:
    import instructor  # type: ignore

    patched_router = instructor.patch(router)
    logger.debug("instructor.patch(router) succeeded — using structured output mode")
except Exception:
    patched_router = None
    logger.warning(
        "instructor.patch(router) failed; using JSON-mode fallback for stage detection"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_STAGE_SYSTEM_TEMPLATE = (
    "Current stage: {current_stage}. "
    "Classify the conversation's next stage. "
    "Return JSON: next_stage (one of intro/qualify/pitch/objection_handling/"
    "propose_appointment/confirm/escalate), confidence (0.0-1.0), "
    "reasoning (<=200 chars)."
)

_MAX_ATTEMPTS = 3


async def detect_stage_structured(
    messages: list, current_stage: str
) -> StageDetectionOutput:
    """
    Call the LLM to classify the next stage using structured output.

    Args:
        messages: list of message dicts (or objects with .content)
        current_stage: the currently active stage string

    Returns:
        StageDetectionOutput — never None. Falls back gracefully on failure.
    """
    sys_msg = {
        "role": "system",
        "content": _STAGE_SYSTEM_TEMPLATE.format(current_stage=current_stage),
    }
    full_messages = list(messages) + [sys_msg]

    if patched_router is not None:
        # instructor-patched path — structured output
        for attempt in range(_MAX_ATTEMPTS):
            try:
                result = await patched_router.chat.completions.create(
                    model="chat",
                    messages=full_messages,
                    response_model=StageDetectionOutput,
                    max_tokens=100,
                    temperature=0.0,
                )
                return result
            except Exception as exc:
                # catches InstructorRetryException and any other error
                logger.warning(
                    "detect_stage_structured attempt %d/%d failed: %s",
                    attempt + 1,
                    _MAX_ATTEMPTS,
                    exc,
                )
    else:
        # JSON-mode fallback path
        for attempt in range(_MAX_ATTEMPTS):
            try:
                response = await router.acompletion(
                    model="chat",
                    messages=full_messages,
                    response_format={"type": "json_object"},
                    max_tokens=100,
                    temperature=0.0,
                )
                content = response.choices[0].message.content
                return StageDetectionOutput.model_validate_json(content)
            except Exception as exc:
                logger.warning(
                    "detect_stage_structured (json-mode) attempt %d/%d failed: %s",
                    attempt + 1,
                    _MAX_ATTEMPTS,
                    exc,
                )

    # Exhausted all attempts
    logger.error("stage detection failed after %d attempts", _MAX_ATTEMPTS)
    return StageDetectionOutput(
        next_stage=current_stage,  # type: ignore[arg-type]
        confidence=0.0,
        reasoning="fallback",
    )


async def llm_detect_stage(state: dict) -> str:
    """
    Convenience wrapper: returns the next stage string from detect_stage_structured.

    Falls back to state['stage'] (or 'intro') on any unexpected error.
    """
    current = state.get("stage", "intro")
    result = await detect_stage_structured(
        state.get("messages", []), current
    )
    return result.next_stage
