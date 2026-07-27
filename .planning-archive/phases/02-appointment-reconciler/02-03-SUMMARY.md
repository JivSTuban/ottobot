---
phase: 02-appointment-reconciler
plan: "03"
subsystem: agent-core
tags:
  - langgraph
  - agent_node
  - slots
  - websocket
  - confirm_appointment
dependency_graph:
  requires:
    - 02-01 (agent/slots.py with get_available_slots, compute_next_slots, format_slot_tagalog, FALLBACK_PHRASE)
    - 02-02 (appointments table + REST endpoints)
  provides:
    - agent_node fetches real slots at propose_appointment stage
    - confirm_appointment WebSocket message flow with store_appointment persistence
  affects:
    - api/ws_handler.py
    - agent/graph.py
tech_stack:
  added: []
  patterns:
    - Slot injection inside agent_node (not a new graph node) — avoids unregistered-channel routing pitfall
    - msg_type guard BEFORE user_text extraction — prevents empty LLM call on confirm_appointment messages
    - store_appointment() graceful no-op when DB URI absent — safe for unit tests
key_files:
  created:
    - tests/test_agent_node_slots.py
  modified:
    - agent/graph.py
    - api/ws_handler.py
    - tests/test_persistence.py
decisions:
  - Patch agent.graph.get_available_slots (not agent.slots.get_available_slots) in tests — function imported into graph module namespace
  - Rule 1 fix in test_persistence.py — ainvoke loops until escalate, eventually hits propose_appointment stage and triggers live DB call; patching get_available_slots in the persistence test prevents spurious connection attempt
  - msg_type check placed BEFORE user_text extraction per Pitfall 4 — confirm_appointment messages must not trigger a LangGraph LLM call
  - business_id accepted from WS message body with BUSINESS_ID env var as fallback (Phase 5 will add auth-gated validation)
metrics:
  duration: "~20 minutes"
  completed: "2026-06-16"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 4
  tests_added: 4
  test_suite_before: 74
  test_suite_after: 87
---

# Phase 02 Plan 03: Slot Injection + WebSocket Confirmation Summary

**One-liner:** Wired slot-fetching into agent_node at propose_appointment stage and added confirm_appointment WebSocket branch with psycopg persistence to ws_handler.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extend agent_node to fetch and propose slots (TDD) | 5aabfc2 | agent/graph.py, tests/test_agent_node_slots.py, tests/test_persistence.py |
| 2 | Add confirm_appointment branch to ws_handler | f4b0020 | api/ws_handler.py |

## What Was Built

### Task 1 — agent_node slot injection

`agent/graph.py` now imports `get_available_slots`, `compute_next_slots`, `format_slot_tagalog`, `FALLBACK_PHRASE` from `agent.slots`. Inside `agent_node`, when `stage == "propose_appointment"`:

1. Calls `get_available_slots(business_id)` where `business_id = os.environ.get("BUSINESS_ID", "")`
2. Calls `compute_next_slots(raw_rows)` to get up to 2 qualifying datetimes
3. If slots exist: formats each with `format_slot_tagalog()`, appends slot text to the stage_instruction system message, sets `proposed_appointment_iso = next_slots[0].isoformat()`
4. If no slots: appends `FALLBACK_PHRASE` to stage_instruction
5. Returns `proposed_appointment` in the state dict alongside existing keys

No new graph nodes or conditional edges were added — slot logic is inline in agent_node per RESEARCH.md Open Question 1 recommendation.

### Task 2 — confirm_appointment WebSocket branch

`api/ws_handler.py` now has:

- `store_appointment(thread_id, business_id, confirmed_time)` — async helper that inserts a confirmed appointment row; gracefully no-ops if DB URI is unset
- `msg_type` check at the TOP of the `async for ws_message` loop, BEFORE `user_text` extraction
- `confirm_appointment` branch that: validates `thread_id`, resolves `confirmed_time` (counter_time if action==counter, else proposed_time), calls `store_appointment`, emits `{type: "appointment_confirmed", confirmed_time, thread_id}`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Persistence test triggered live DB call after agent_node extension**
- **Found during:** Task 1 full regression (test_persistence.py::test_state_resumes_after_reconnect)
- **Issue:** `test_state_resumes_after_reconnect` calls `graph.ainvoke()` which loops the graph until escalation. After our changes, `agent_node` calls `get_available_slots` at `propose_appointment` stage. The graph reaches that stage during the multi-loop ainvoke, and `SUPABASE_DB_URI=postgresql://test` (a fake URI set at the top of test_persistence.py) caused psycopg to attempt a real DNS lookup for host `test`, raising OperationalError.
- **Fix:** Added `patch("agent.graph.get_available_slots", AsyncMock(return_value=[]))` to the `with` block in `test_state_resumes_after_reconnect`. This is the correct scope — the function is imported into the `agent.graph` namespace, so it must be patched there.
- **Files modified:** tests/test_persistence.py
- **Commit:** 5aabfc2

**2. [Rule 1 - Bug] Wrong patch namespace in initial TDD tests**
- **Found during:** Task 1 GREEN phase
- **Issue:** Initial failing tests used `patch("agent.slots.get_available_slots")` — but `agent/graph.py` imports the function directly into its own namespace. Patching the origin module (`agent.slots`) does not intercept calls from `agent.graph`.
- **Fix:** Changed all test patches to `patch("agent.graph.get_available_slots")` and `patch("agent.graph.compute_next_slots")`.
- **Files modified:** tests/test_agent_node_slots.py
- **Commit:** 5aabfc2

## Verification Results

```
87 passed, 1 warning in 1.17s
grep -c "propose_appointment" agent/graph.py  → 7
grep -c "confirm_appointment" api/ws_handler.py  → 1
python3 -c "from agent.graph import agent_node; print('OK')"  → OK
```

## Known Stubs

None — all data flows are wired. `store_appointment` gracefully no-ops when DB URI is absent (test safety), but real DB writes occur when `SUPABASE_DIRECT_URL` or `SUPABASE_DB_URI` are set.

## Threat Surface Scan

No new network endpoints or auth paths beyond what the plan's threat model covers.

| Flag | File | Description |
|------|------|-------------|
| Reviewed T-02-07 | api/ws_handler.py | thread_id validated via validate_thread_id() before store_appointment() — mitigated |
| Reviewed T-02-10 | api/ws_handler.py | Never log confirmed_time or business_id values — compliant |

## Self-Check: PASSED

- [x] tests/test_agent_node_slots.py exists (4 tests, all pass)
- [x] agent/graph.py modified — propose_appointment branch present
- [x] api/ws_handler.py modified — confirm_appointment branch present
- [x] Commits 979701d (RED), 5aabfc2 (GREEN + fix), f4b0020 (Task 2) all present
- [x] 87 tests passing, 0 failures
