---
phase: 01-agent-core-demo-ui
plan: "04"
subsystem: agent-core
tags: [python, langgraph, litellm, tdd, state-machine, routing]

requires:
  - 01-03 (ConversationState, agent.llm.router, escalation_scorer, BusinessProfile)

provides:
  - StateGraph builder with agent_node + conditional route_next_stage edge
  - agent_node: LiteLLM Router call with per-turn stage instruction injection
  - route_next_stage: hybrid escalation -> booking-phrase -> visit_count guard -> D-08 bidirectional -> linear progression
  - agent/stage_detection.py: LLM stage classifier (detect_stage_structured + llm_detect_stage)
  - tests/test_stage_routing.py: 9 passing AGENT-01 tests

affects:
  - 01-05 (FastAPI WebSocket — imports builder and compiles with AsyncPostgresSaver)
  - 01-06 (persistence — ConversationState checkpointed through compiled graph)

tech-stack:
  added:
    - langgraph StateGraph (conditional edges, entry_point)
    - instructor (optional — graceful fallback if patch fails)
  patterns:
    - TDD RED/GREEN per task (failing stubs before implementation)
    - sync route_next_stage (LangGraph conditional edge requirement)
    - async agent_node with per-turn system message injection
    - visit_count guard for infinite loop prevention (T-04-02)
    - escalation_scorer checked FIRST in route_next_stage (T-04-03)

key-files:
  created:
    - agent/graph.py
    - agent/stage_detection.py
    - tests/test_stage_detection.py
    - tests/test_graph_module.py
  modified:
    - tests/test_stage_routing.py (9 stubs -> 9 passing tests)

key-decisions:
  - "Builder exported NOT compiled — compilation in api/main.py lifespan with AsyncPostgresSaver (Plan 05)"
  - "route_next_stage is SYNC — LangGraph conditional edge requirement; llm_detect_stage excluded from sync routing path"
  - "escalation_scorer checks dict messages via hasattr(m,'content') — dict messages do not fire escalation, allowing clean isolation of routing logic in unit tests"
  - "visit_count guard fires when pitch >= 3 AND stage == objection_handling — exact Pitfall 4 prevention"

requirements-completed: [AGENT-01, AGENT-05]

duration: ~4m
completed: "2026-06-15"
---

# Phase 01 Plan 04: LangGraph State Machine + Stage Routing Summary

**StateGraph builder with agent_node (LiteLLM) + route_next_stage (hybrid escalation -> booking-phrase -> visit_count guard -> D-08 bidirectional -> linear progression) + LLM stage classifier, turning all 9 AGENT-01 routing tests GREEN**

## Performance

- **Duration:** ~4 minutes
- **Started:** 2026-06-15T02:08:51Z
- **Completed:** 2026-06-15T02:12:38Z
- **Tasks:** 3 (all TDD)
- **Files created:** 4 (2 Python modules + 2 test files)
- **Files modified:** 1 (test_stage_routing.py)

## Accomplishments

- `agent/stage_detection.py`: `detect_stage_structured` with instructor.patch path + JSON-mode fallback; 3-attempt retry; exhaustion returns `StageDetectionOutput(confidence=0.0, reasoning="fallback")`; `llm_detect_stage` wrapper returning stage string
- `agent/graph.py`: `StateGraph(ConversationState)` with `"agent"` node, `route_next_stage` conditional edge, entry_point set; `MAX_HISTORY=20`; `BOOKING_PHRASES_FAST` list (12 Taglish phrases); `jinja_env` from `make_env()`; builder exported NOT compiled
- `agent_node`: prepends persona system prompt on intro stage (if no existing system message); appends per-turn `"Current stage: {stage}. Goal: ..."` instruction; slices last MAX_HISTORY messages; increments visit_count[stage]
- `route_next_stage` (sync): escalation_scorer first (T-04-03) → BOOKING_PHRASES_FAST fast rule → visit_count guard (pitch>=3 + objection_handling → propose_appointment, T-04-02) → D-08 bidirectional (objection_handling + positive sentiment + pitch<3 → pitch) → linear progression
- `tests/test_stage_routing.py`: all 9 AGENT-01 stubs replaced with real tests; 9 passing

## Task Commits

1. **Task 1 RED** — `2a4e49b`: test stubs for stage_detection module
2. **Task 1 GREEN** — `b6f0815`: agent/stage_detection.py LLM classifier
3. **Task 2 RED** — `4b02027`: failing tests for agent/graph.py module
4. **Task 2 GREEN** — `9250079`: agent/graph.py StateGraph builder + routing
5. **Task 3 GREEN** — `52c6b8e`: test_stage_routing.py stubs -> 9 passing AGENT-01 tests

## Verification Results

```
9 passed, 1 warning in 0.94s
```

Plan verification commands all passed:
- `pytest tests/test_stage_routing.py -x -q` → 9 passed
- `from agent.graph import builder; builder.compile(checkpointer=MemorySaver())` → CompiledStateGraph instance
- visit_count guard test confirms pitch>=3 → propose_appointment (no infinite loop)
- escalation_scorer checked FIRST confirmed by test_escalation_scorer_overrides_progression

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

## TDD Gate Compliance

All three tasks followed RED -> GREEN cycle:

- Task 1: RED commit `2a4e49b` (stage_detection stubs) → GREEN commit `b6f0815` (implementation)
- Task 2: RED commit `4b02027` (graph module stubs) → GREEN commit `9250079` (implementation)
- Task 3: Wave 0 stubs (plan 01) served as RED; GREEN commit `52c6b8e` (9 real tests)

No REFACTOR pass needed — code was clean at GREEN.

## Known Stubs

None. All routing logic is wired. BOOKING_PHRASES_FAST, POSITIVE_SENTIMENT_PHRASES, and visit_count guard are all active. agent_node calls router.acompletion with real message construction logic.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: prompt-injection-guard | agent/graph.py | agent_node stage instruction uses f-string with `stage` from ConversationState — stage is set by route_next_stage (internal), not from user input directly; lead content flows only as role=user messages (T-04-01 mitigation confirmed) |

T-04-01 through T-04-04 all addressed:
- T-04-01: Lead text added as `{"role":"user","content":...}` ONLY; stage instructions are separate `{"role":"system",...}` messages; persona rendered from DEMO_PROFILES (not user input)
- T-04-02: visit_count guard prevents pitch/objection_handling infinite loop; tested in test_visit_count_guard_breaks_loop
- T-04-03: escalation_scorer checked FIRST in route_next_stage before any LLM call; confirmed by test_escalation_scorer_overrides_progression
- T-04-04: accepted — Phoenix tracing in Phase 1 demo; production hardening deferred

## Self-Check: PASSED

Files verified on disk:
- /Users/jivtuban/Desktop/ottobot/agent/graph.py — FOUND
- /Users/jivtuban/Desktop/ottobot/agent/stage_detection.py — FOUND
- /Users/jivtuban/Desktop/ottobot/tests/test_stage_routing.py — FOUND (9 tests)
- /Users/jivtuban/Desktop/ottobot/tests/test_stage_detection.py — FOUND
- /Users/jivtuban/Desktop/ottobot/tests/test_graph_module.py — FOUND

Commits verified:
- 2a4e49b (test RED stage_detection)
- b6f0815 (feat GREEN stage_detection)
- 4b02027 (test RED graph module)
- 9250079 (feat GREEN graph.py)
- 52c6b8e (feat GREEN test_stage_routing)

Final suite: 9 passed, 0 failed.
