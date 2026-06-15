---
phase: 01-agent-core-demo-ui
plan: "03"
subsystem: agent-core
tags: [python, pydantic, jinja2, litellm, langgraph, tdd]

requires:
  - 01-01 (Python venv + Wave 0 stubs)

provides:
  - ConversationState TypedDict with add_messages reducer
  - BusinessProfile + Industry enum + StageDetectionOutput Pydantic models
  - DEMO_PROFILES for D-12 personas (Ate Ana/Ate Bea/Kuya Marco)
  - Jinja2 prompt templates with NPC 2024-04 AI disclosure + Taglish D-11 instruction
  - LiteLLM Router singleton with usage-based-routing-v2 + Groq/Gemini/Mistral
  - 2-of-3 escalation_scorer (D-09) with BOOKING_PHRASES and POSITIVE_SENTIMENT_PHRASES

affects:
  - 01-04 (LangGraph graph wiring — consumes ConversationState, agent.llm.router, escalation_scorer)
  - 01-05 (FastAPI WebSocket — consumes agent.llm.router, ConversationState)
  - 01-06 (persistence — consumes ConversationState)

tech-stack:
  added:
    - jinja2>=3.1.0 (StrictUndefined environment for safe template rendering)
  patterns:
    - TDD RED/GREEN per task (test stubs committed before implementation)
    - Pydantic field_validator for business rule enforcement (pricing not empty)
    - Jinja2 template inheritance (base.j2 -> dental/aesthetics/real_estate)
    - Module-level Router singleton (never per-request instantiation)

key-files:
  created:
    - agent/state.py
    - agent/models.py
    - agent/llm.py
    - agent/escalation.py
    - agent/prompts/base.j2
    - agent/prompts/dental.j2
    - agent/prompts/aesthetics.j2
    - agent/prompts/real_estate.j2
  modified:
    - tests/test_models.py
    - tests/test_escalation.py
    - tests/test_llm_router.py
    - pytest.ini

key-decisions:
  - "os.environ.get() used instead of os.environ[] in agent/llm.py — allows test import without real keys; tests set dummy values via setdefault()"
  - "POSITIVE_SENTIMENT_PHRASES includes 'gusto' which overlaps with booking phrases — test_one_signal_does_not_escalate uses 'magkano' (price inquiry) to isolate signal_1 only"
  - "pytest.ini 'integration' marker registered to suppress PytestUnknownMarkWarning for Test 5"

requirements-completed: [AGENT-02, AGENT-03, AGENT-04, AGENT-05]

duration: ~35m
completed: "2026-06-15"
---

# Phase 01 Plan 03: Agent Core Models + Prompts + LLM Layer Summary

**Pydantic BusinessProfile + Jinja2 persona templates + LiteLLM Router singleton + 2-of-3 escalation scorer that together turn 18 Wave 0 failing stubs GREEN**

## Performance

- **Duration:** ~35 minutes
- **Started:** 2026-06-15T02:01Z
- **Completed:** 2026-06-15T02:36Z
- **Tasks:** 3 (all TDD)
- **Files created:** 11 (4 Python modules + 4 Jinja2 templates + 3 test replacements)
- **Files modified:** 4 (3 tests + pytest.ini)

## Accomplishments

- `agent/state.py`: ConversationState TypedDict with `Annotated[list, add_messages]` reducer, 7-stage STAGES Literal, visit_count and message_timestamps fields required by downstream graph and escalation logic
- `agent/models.py`: BusinessProfile with Pydantic pricing validator, render_system_prompt Jinja2 method, make_env() StrictUndefined factory, DEMO_PROFILES (Ate Ana/Ate Bea/Kuya Marco per D-12), StageDetectionOutput with confidence [0,1] ge/le constraints
- Jinja2 templates: base.j2 with NPC 2024-04 AI disclosure phrase ("ako ay AI assistant") and D-11 Taglish code-switching instruction; dental/aesthetics/real_estate.j2 extend base.j2 and render all 5 required BusinessProfile fields via StrictUndefined env
- `agent/escalation.py`: 18 BOOKING_PHRASES + 20 POSITIVE_SENTIMENT_PHRASES; 2-of-3 composite scorer per D-09 with cadence signal_3 checking 30-second threshold
- `agent/llm.py`: Module-level Router singleton with Groq (rpm=30, tpm=6000), Gemini Flash (rpm=15), Mistral Small; usage-based-routing-v2; fallbacks=[{chat:[chat,chat]}]; cache_responses=True

## Task Commits

1. **Task 1 RED** — `a639e60`: test stubs for agent models + state (7 behaviors)
2. **Task 1 GREEN** — `075454c`: agent/state.py + agent/models.py + 4 Jinja2 templates
3. **Task 2 RED** — `e3c4f41`: failing escalation scorer tests (6 behaviors)
4. **Task 2 GREEN** — `061e7c5`: agent/escalation.py 2-of-3 composite scorer
5. **Task 3 RED** — `e701b13`: failing LiteLLM Router tests (5 behaviors)
6. **Task 3 GREEN** — `8e32260`: agent/llm.py Router singleton + pytest.ini integration mark

## Verification Results

```
18 passed, 1 warning in 0.95s
```

All three test files pass:
- `tests/test_models.py`: 7 tests GREEN
- `tests/test_escalation.py`: 6 tests GREEN
- `tests/test_llm_router.py`: 5 tests GREEN

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Config] Register 'integration' pytest mark**
- **Found during:** Task 3 — `@pytest.mark.integration` caused PytestUnknownMarkWarning
- **Fix:** Added `markers = integration: ...` to pytest.ini
- **Files modified:** `pytest.ini`
- **Commit:** `8e32260`

**2. [Rule 1 - Bug] test_one_signal_does_not_escalate test message overlap**
- **Found during:** Task 2 GREEN — "gusto ko mag-book" fires both signal_1 (booking phrase) AND signal_2 ("gusto" in POSITIVE_SENTIMENT_PHRASES), making the test assertion incorrect
- **Fix:** Changed test message to "magkano ang presyo?" which has signal_1 (price inquiry/booking) but no positive sentiment overlap and slow cadence. Added explanation comment in test
- **Files modified:** `tests/test_escalation.py`
- **Commit:** `061e7c5` (included in GREEN commit)

## TDD Gate Compliance

All three tasks followed RED -> GREEN cycle:
- RED commits exist for each task before implementation
- GREEN commits follow with minimal implementation to pass
- No REFACTOR pass needed (code was clean at GREEN)

## Known Stubs

None. All BusinessProfile fields render correctly. DEMO_PROFILES produce 1457–1521 character outputs including persona names and AI disclosure phrases.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: template-rendering | agent/models.py | render_system_prompt uses model_dump() — only internally-defined DEMO_PROFILES data reaches templates in Phase 1; user-supplied lead text NEVER passes through Jinja2 (T-03-04 mitigation confirmed) |

T-03-01 through T-03-05 from plan threat register are all addressed:
- T-03-01: Lead text not interpolated into system prompt — only BusinessProfile fields
- T-03-02: "ako ay AI assistant" phrase verified in base.j2 and in test_demo_profile_dental_render_system_prompt assertion
- T-03-03: os.environ.get() with empty-string default; no key logging
- T-03-04: StrictUndefined catches missing fields; Pydantic validates types before render
- T-03-05: Groq rpm=30, tpm=6000 enforced in Router; fallback chain to Gemini/Mistral confirmed

## Self-Check: PASSED

All created files verified on disk. All 6 task commits verified in git log:
- a639e60 (test RED models), 075454c (feat GREEN models)
- e3c4f41 (test RED escalation), 061e7c5 (feat GREEN escalation)
- e701b13 (test RED llm_router), 8e32260 (feat GREEN llm_router)

Final suite: 18 passed, 0 failed.
