---
phase: 02-appointment-reconciler
plan: 02
subsystem: api
tags: [fastapi, psycopg, supabase, availability, appointments, tdd]
dependency_graph:
  requires:
    - 02-01 (agent/slots.py — compute_next_slots, format_slot_tagalog, FALLBACK_PHRASE)
  provides:
    - POST /availability endpoint
    - GET /availability/{business_id} endpoint
    - POST /appointments/confirm endpoint
    - validate_business_id() helper
    - setup_appointment_tables() lifespan hook
  affects:
    - 02-03 (LangGraph reads GET /availability in slot tool node)
tech_stack:
  added: []
  patterns:
    - FastAPI HTTPException 400 for UUID validation
    - psycopg AsyncConnection.connect with %s parameterized queries
    - Pydantic BaseModel request bodies (AvailabilityRequest, ConfirmAppointmentRequest)
    - CREATE TABLE IF NOT EXISTS in lifespan for idempotent schema setup
key_files:
  created:
    - tests/test_appointment_api.py
  modified:
    - api/main.py
decisions:
  - validate_business_id() mirrors validate_thread_id() pattern — UUID v4 check via uuid.UUID().version == 4
  - setup_appointment_tables() is a no-op when SUPABASE_DIRECT_URL and SUPABASE_DB_URI are both empty — enables test environments without real DB
  - GET /availability calls agent.slots.compute_next_slots() to apply the 2-hour buffer and 2-slot cap already implemented in Plan 02-01
  - POST /appointments/confirm no-ops DB write when URI is empty — returns confirmed status for integration test simplicity
metrics:
  duration: 12 minutes
  completed: "2026-06-16"
  tasks_completed: 2
  files_changed: 2
---

# Phase 02 Plan 02: Availability + Appointment Endpoints Summary

**One-liner:** REST availability management and appointment confirmation endpoints with psycopg parameterized upserts, UUID validation, and IF NOT EXISTS table setup in FastAPI lifespan.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write test_appointment_api.py stubs (RED) | ace6d47 | tests/test_appointment_api.py |
| 2 | Add availability + appointment endpoints to api/main.py | e615de9 | api/main.py |

## What Was Built

### New: `tests/test_appointment_api.py`

6 unit tests covering all three endpoints:
- `test_set_availability_valid` — POST /availability with valid UUID → 200 {"status":"ok"}
- `test_set_availability_invalid_business_id` — non-UUID business_id → 400
- `test_get_availability_returns_slots` — GET /availability/{id} with mocked psycopg rows → 200 with slots list
- `test_confirm_appointment_valid` — POST /appointments/confirm with valid UUIDs → 200 {"status":"confirmed"}
- `test_confirm_appointment_invalid_thread` — non-UUID thread_id → 400
- `test_appointment_status_confirmed` — confirms response has status=="confirmed" and correct thread_id

### Modified: `api/main.py`

Added in order:
1. `psycopg` and `pydantic.BaseModel`, `fastapi.HTTPException` imports
2. `validate_business_id()` — UUID v4 check (mirrors existing `validate_thread_id()`)
3. `setup_appointment_tables()` — CREATE TABLE IF NOT EXISTS for `business_availability` and `appointments`; called from lifespan after `checkpointer.setup()`
4. Pydantic models: `AvailabilitySlotIn`, `AvailabilityRequest`, `ConfirmAppointmentRequest`
5. `POST /availability` — validates business_id + day_of_week range, upserts via ON CONFLICT
6. `GET /availability/{business_id}` — fetches rows, calls `compute_next_slots()`, returns formatted Tagalog slots
7. `POST /appointments/confirm` — validates thread_id + business_id, inserts confirmed appointment

## Test Results

- `pytest tests/test_appointment_api.py -v` → 6 passed
- `pytest` (full suite) → 83 passed, 0 failures (was 77 before this plan)

## TDD Gate Compliance

- RED gate: `test(02-02)` commit ace6d47 — 6 tests collected, all failing (endpoints 404)
- GREEN gate: `feat(02-02)` commit e615de9 — all 6 tests pass

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all endpoints are functionally wired. GET /availability calls `compute_next_slots()` from Plan 02-01 which performs real time math. POST /appointments/confirm writes to DB when URI is present; no-ops gracefully in tests.

## Threat Flags

None — no new trust boundaries introduced beyond those listed in the plan's threat model. All STRIDE mitigations applied:
- T-02-03: `validate_thread_id()` on `/appointments/confirm`
- T-02-04: `validate_business_id()` on all three endpoints; day_of_week range check
- T-02-05: all SQL queries use `%s` parameterized placeholders
- T-02-06: db_uri never logged; only partial redaction in existing lifespan log

## Self-Check: PASSED

- `tests/test_appointment_api.py` exists: FOUND
- `api/main.py` modified: FOUND
- Commit ace6d47 (RED): FOUND
- Commit e615de9 (GREEN): FOUND
- `validate_business_id` in api/main.py: FOUND (line 31)
- `setup_appointment_tables` in api/main.py: FOUND (line 60, 170)
- `POST /availability` in api/main.py: FOUND (line 203)
- `GET /availability/{business_id}` in api/main.py: FOUND (line 238)
- `POST /appointments/confirm` in api/main.py: FOUND (line 284)
