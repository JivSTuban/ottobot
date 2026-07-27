---
phase: 02-appointment-reconciler
plan: "01"
subsystem: agent
tags: [slots, tagalog-formatting, state, tdd]
dependency_graph:
  requires: []
  provides: [agent/slots.py, proposed_appointment field in ConversationState]
  affects: [agent/graph.py (Plan 02-03 wires get_available_slots_node)]
tech_stack:
  added: []
  patterns: [psycopg async query, datetime UTC+8 arithmetic, TDD RED/GREEN]
key_files:
  created:
    - agent/slots.py
    - tests/test_appointment_slots.py
  modified:
    - agent/state.py
decisions:
  - asyncio_mode=auto in pytest.ini (not pyproject.toml) — no @pytest.mark.asyncio needed
  - get_available_slots returns [] when SUPABASE_DIRECT_URL and SUPABASE_DB_URI both unset — test-safe graceful degradation
  - compute_next_slots iterates 7 days from today; candidate_dt > now+2h guard per Pitfall 3
  - proposed_appointment is scalar str|None with no Annotated reducer — last-write-wins per CONTEXT.md
metrics:
  duration: "~5 minutes"
  completed_date: "2026-06-16T13:01:01Z"
  tasks_completed: 2
  files_changed: 3
---

# Phase 02 Plan 01: Slot Math Helper and State Extension Summary

**One-liner:** psycopg async slot query + UTC+8 time math + Tagalog formatting in agent/slots.py; ConversationState extended with proposed_appointment scalar field.

## What Was Built

- `agent/slots.py` — four exports: `FALLBACK_PHRASE` constant, `DAYS_PH` weekday list, `format_slot_tagalog(dt)` Tagalog formatter, `compute_next_slots(rows, now, max_count=2)` time-math filter, `get_available_slots(business_id)` async psycopg query.
- `agent/state.py` — added `proposed_appointment: str | None` as plain scalar field after `system_alert`.
- `tests/test_appointment_slots.py` — 9 unit tests; full TDD RED→GREEN cycle.

## Tasks

| # | Name | Commit | Files |
|---|------|--------|-------|
| RED | test stubs (Task 2 order) | acd6ec8 | tests/test_appointment_slots.py |
| GREEN | implementation (Task 1 order) | dcf8f86 | agent/slots.py, agent/state.py |

## Test Results

- New tests: 9 passed, 0 failed
- Full suite: 77 passed (was 68), 0 failures, 0 regressions

## Deviations from Plan

None — plan executed exactly as written.

## TDD Gate Compliance

- RED commit: `acd6ec8` — `test(02-01): add failing tests for slot math and Tagalog formatting`
- GREEN commit: `dcf8f86` — `feat(02-01): create agent/slots.py and extend ConversationState`
- Gate sequence: PASS

## Known Stubs

None — no data is mocked or placeholder-wired. `get_available_slots` returns `[]` when DB URI is absent (intentional, documented behavior).

## Threat Flags

None — no new network endpoints or auth paths introduced in this plan. All SQL uses `%s` parameterized queries. `db_uri` never logged.

## Self-Check: PASSED

- `agent/slots.py` — FOUND
- `agent/state.py` contains `proposed_appointment` — FOUND (line 35)
- `tests/test_appointment_slots.py` — FOUND
- commit `acd6ec8` — FOUND
- commit `dcf8f86` — FOUND
- 77 tests pass — VERIFIED
