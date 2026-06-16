---
phase: 01-agent-core-demo-ui
plan: GAP
subsystem: agent-routing, api-persistence, ws-handler
tags: [gap-closure, langgraph, routing, supabase, websocket, escalation]
dependency_graph:
  requires: [01-01, 01-02, 01-03, 01-04, 01-05, 01-06, 01-07]
  provides: [correct-stage-routing, system_alert-state-event, direct-db-url-fallback]
  affects: [agent/graph.py, agent/state.py, api/main.py, api/ws_handler.py]
tech_stack:
  added: []
  patterns: [single-node-looping-graph, direct-postgres-url-fallback, state-driven-conditional-edge]
key_files:
  created: [tests/test_graph_routing.py]
  modified: [agent/graph.py, agent/state.py, api/main.py, api/ws_handler.py, .env.example, tests/test_stage_routing.py, tests/test_websocket.py]
decisions:
  - "_compute_next_stage helper owns all stage progression logic; route_next_stage is a pure end-check returning 'agent' or END only"
  - "SUPABASE_DIRECT_URL tried before SUPABASE_DB_URI in lifespan to bypass pgbouncer DNS propagation lag"
  - "system_alert populated by agent_node when escalated=True; ws_handler includes it in {type:state} payload"
  - "add_conditional_edges path_map explicit: {'agent': 'agent', END: END} to prevent silent unknown-channel routing"
metrics:
  duration: "25 minutes"
  completed: "2026-06-16"
  tasks_completed: 2
  files_changed: 7
requirements: [AGENT-01, AGENT-04, DEMO-03]
---

# Phase 01 Plan GAP: Gap Closure Summary

**One-liner:** Single-node looping LangGraph with _compute_next_stage state writes and SUPABASE_DIRECT_URL fallback to close UAT tests 2 and 5.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Fix LangGraph routing — loop agent node with stage updates | 387f91c | agent/graph.py, agent/state.py, tests/test_graph_routing.py |
| 2 | Fix ws_handler system_alert + Supabase direct URL fallback | 369c820 | api/ws_handler.py, api/main.py, .env.example, tests/test_stage_routing.py, tests/test_websocket.py |

## What Was Built

### Task 1: LangGraph Routing Redesign

Root cause: `add_conditional_edges("agent", route_next_stage)` returned unregistered node names ("qualify", "pitch", etc.) causing LangGraph to silently route to END on every turn. Stage never advanced.

Fix:
- Introduced `_compute_next_stage(state)` — carries all priority routing logic (escalation scorer, booking phrases, visit_count guard, D-08 bidirectional, linear progression). Returns `(next_stage, escalated, system_alert)`.
- `agent_node` now calls `_compute_next_stage` and writes `stage`, `escalated`, `system_alert` into its return dict each turn.
- `route_next_stage` simplified to a pure end-check: returns `"agent"` for all non-escalate stages, `END` when `stage == "escalate"`.
- `add_conditional_edges` updated with explicit path_map `{"agent": "agent", END: END}`.
- `system_alert` field added to `ConversationState` TypedDict.

### Task 2: Supabase Direct URL Fallback + system_alert State Event

- `api/main.py`: Tries `SUPABASE_DIRECT_URL` (port 5432, direct connection) before `SUPABASE_DB_URI` (port 6543, pooler). Direct connection bypasses pgbouncer DNS propagation lag on projects <24h old. URL truncated to 40 chars in log (T-GAP-01 mitigation).
- `api/ws_handler.py`: `{type:"state"}` JSON payload now includes `system_alert` key — React OwnerPanel can display hot lead alert without frontend changes.
- `.env.example`: Documents `SUPABASE_DIRECT_URL` with port 5432 direct connection format.

## Test Results

```
68 passed, 1 warning in 1.04s
```

- `tests/test_graph_routing.py`: 12 new tests all pass (routing, escalation, agent_node return dict)
- `tests/test_stage_routing.py`: Updated to call `_compute_next_stage` (routing logic moved); 10 tests pass
- `tests/test_websocket.py`: Fixed fake_astream mock to yield `{node_name: state_delta}` dicts; added `system_alert` assertion

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pre-existing test_stage_routing.py — tested old route_next_stage API**
- **Found during:** Task 2 full suite run
- **Issue:** All 6 linear/escalation tests in test_stage_routing.py called `route_next_stage` expecting stage names like "qualify". After GAP redesign, route_next_stage only returns "agent" or END.
- **Fix:** Updated tests to call `_compute_next_stage` for stage transition assertions; added two new tests for the end-check behavior.
- **Files modified:** tests/test_stage_routing.py
- **Commit:** 369c820

**2. [Rule 1 - Bug] Fixed pre-existing test_websocket.py — fake_astream yielded tuples**
- **Found during:** Task 2 full suite run
- **Issue:** `test_token_event_emitted` and `test_owner_panel_state_event_emitted` used `async def fake_astream` that yielded `(chunk, metadata)` tuples. ws_handler expects `{node_name: state_delta}` dicts (stream_mode="updates" format). This caused `AttributeError: 'tuple' object has no attribute 'items'`.
- **Fix:** Updated both fake_astream generators to yield proper update dicts. Added `system_alert` assertion to state event test.
- **Files modified:** tests/test_websocket.py
- **Commit:** 369c820

## Known Stubs

None — all state fields are wired end-to-end.

## Threat Flags

No new security-relevant surface introduced beyond what is in the threat model.

| Flag | File | Description |
|------|------|-------------|
| T-GAP-01 mitigated | api/main.py | SUPABASE_DIRECT_URL log line truncated to 40 chars — password never logged |

## Self-Check: PASSED

- agent/graph.py: exists, _compute_next_stage exported, route_next_stage is pure end-check
- agent/state.py: system_alert field added
- api/main.py: SUPABASE_DIRECT_URL tried first
- api/ws_handler.py: system_alert in state event
- tests/test_graph_routing.py: created, 12 tests
- Commit 387f91c: exists (Task 1)
- Commit 369c820: exists (Task 2)
- Full suite: 68 passed, 0 failed
