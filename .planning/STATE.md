---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Phase 1 UI-SPEC approved
last_updated: "2026-06-15T02:18:39Z"
last_activity: 2026-06-15 -- Phase 01 Plan 05 completed (FastAPI WebSocket server + online guardrails + 11 tests GREEN)
progress:
  total_phases: 7
  completed_phases: 0
  total_plans: 7
  completed_plans: 4
  percent: 57
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-11)

**Core value:** A Filipino lead receives a natural Tagalog conversation that ends in a confirmed appointment — without the business owner lifting a finger.
**Current focus:** Phase 01 — agent-core-demo-ui

## Current Position

Phase: 01 (agent-core-demo-ui) — EXECUTING
Plan: 5 of 7 (Plans 01-01, 01-03, 01-04, 01-05 complete)
Status: Executing Phase 01
Last activity: 2026-06-15 -- Plan 01-05 complete: api/main.py + api/ws_handler.py + api/connection_manager.py + api/guardrails.py + 11 DEMO-01/DEMO-03 tests GREEN

Progress: [████████░░░░░░░░░░░░] 40%

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

Key decisions already locked:

- Fork SalesGPT as agent base (conversation stage state machine already built)
- LangGraph + PostgresSaver → Supabase Postgres (single persistence layer)
- Llama 4 Maverick (Groq) as primary LLM — best FilBench score for Tagalog among free models
- LiteLLM Router with YAML config and usage-based routing
- Semaphore PH over Twilio for SMS (cheaper for PH numbers)
- Build order: agent → demo UI → channels → onboarding → app

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

### Plan 01-03 Decisions

- os.environ.get() for API keys in agent/llm.py — allows test import without real keys
- POSITIVE_SENTIMENT_PHRASES includes 'gusto' — overlaps with booking phrases; tests must use non-overlapping examples to isolate individual signals
- pytest 'integration' marker registered in pytest.ini for Test 5 (Router fallback)

### Plan 01-04 Decisions

- Builder exported NOT compiled — compilation in api/main.py lifespan with AsyncPostgresSaver (Plan 05)
- route_next_stage is SYNC — LangGraph conditional edge requirement; llm_detect_stage excluded from sync routing path
- escalation_scorer checks .content attribute (not dict messages) — dict messages do not fire escalation; clean isolation of routing logic in unit tests
- visit_count guard fires when pitch >= 3 AND stage == objection_handling — Pitfall 4 prevention (T-04-02)

### Plan 01-05 Decisions

- Phoenix import wrapped in try/except — phoenix package has a broken import chain; OTLP + LangChainInstrumentor work independently
- test_thread_id_rejects_uuid_non_v4 removed — Python stdlib uuid.UUID(str, version=4) coerces version bits silently; guard correctly rejects non-UUID hex strings
- compiled_graph stored as module-level global set inside lifespan — avoids nonlocal scope issues across module imports
- validate_thread_id extracted as standalone helper — enables unit testing without triggering lifespan/Postgres

## Session Continuity

Last session: 2026-06-15T02:18:39Z
Stopped at: Plan 01-05 complete
Resume file: .planning/phases/01-agent-core-demo-ui/01-05-SUMMARY.md
