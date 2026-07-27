---
phase: 06-mobile-app
plan: "03"
subsystem: push-notifications
tags: [push, expo, escalation, backend, APP-01]
dependency_graph:
  requires: [06-01]
  provides: [send_push_notification, push-wiring]
  affects: [api/escalation_service.py, api/ws_handler.py]
tech_stack:
  added: []
  patterns: [httpx-async-client, expo-push-http-api, try-except-no-reraise]
key_files:
  created: [tests/test_push_service.py]
  modified: [api/escalation_service.py, api/ws_handler.py]
decisions:
  - "No Authorization header for Expo Push API — device identified via 'to' field token"
  - "Push failure wrapped in try/except in both escalation_service and ws_handler — never crashes escalation"
  - "expo_token lookup uses parameterized psycopg query to mitigate SQLi (T-06-11)"
  - "lead_phone used as lead identifier in push body since lead name unavailable at escalation point"
metrics:
  duration: "15 minutes"
  completed: "2026-06-19T07:57:39Z"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 2
---

# Phase 06 Plan 03: Push Notification Backend Summary

Backend push notification delivery via Expo Push HTTP API — `send_push_notification()` added to `escalation_service.py` and wired into `ws_handler.py` escalation path alongside existing email notification.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add send_push_notification() to escalation_service.py | 9a67586 | api/escalation_service.py, tests/test_push_service.py |
| 2 | Wire send_push_notification() into ws_handler.py escalation path | 64fbb4c | api/ws_handler.py |

## What Was Built

**Task 1 (TDD — RED/GREEN):**
- Added `EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"` constant
- Implemented `send_push_notification(expo_token, title, body, data)` in `api/escalation_service.py`:
  - No-op on empty `expo_token`
  - `httpx.AsyncClient(timeout=10.0)` matching `send_escalation_email()` pattern exactly
  - No `Authorization` header — Expo identifies device via the `"to"` field
  - JSON payload: `to`, `title`, `body`, `data`, `sound="default"`, `channelId="default"`
  - Graceful error handling: logs warning on 4xx or `httpx.RequestError`, never re-raises
- Created `tests/test_push_service.py` with 4 tests: no-op, correct payload, 4xx response, RequestError

**Task 2:**
- Added `send_push_notification` to the import from `api.escalation_service` in `ws_handler.py`
- After `send_escalation_email()` fires, looks up `expo_token` from `business_push_tokens` table using parameterized query
- Calls `send_push_notification` with UI-SPEC copy: title `"Hot lead — tumawag na!"`, body `"[lead_phone] ay handa nang mag-book. Tawagan siya ngayon."`, data `{"leadId": thread_id}`
- Entire push block wrapped in outer `try/except Exception` — push never crashes escalation flow
- Existing `send_escalation_email` and `store_escalation` calls untouched (additive change)

## Test Results

- `pytest tests/test_push_service.py`: 4 passed
- `pytest tests/test_escalation_service.py`: 6 passed (no regressions)
- `pytest tests/`: 132 passed, 0 failed

## Decisions Made

1. No Authorization header for Expo Push API — Expo uses the `"to"` field (the `ExponentPushToken`) to route notifications; an Authorization header would be rejected
2. Push block wrapped in `try/except Exception` in `ws_handler.py` as defense-in-depth — `send_push_notification` already handles its own errors but ws_handler outer guard ensures DB lookup errors also cannot crash escalation
3. Used `lead_phone` as lead identifier in push body because lead name is not guaranteed to be available at escalation trigger point

## Deviations from Plan

None - plan executed exactly as written.

## Threat Model Compliance

| Threat ID | Mitigation Applied |
|-----------|-------------------|
| T-06-09 | expo_token looked up server-side by business_id from ws_handler session; client cannot inject token |
| T-06-10 | httpx timeout=10.0; entire push block in try/except; email still fires regardless |
| T-06-11 | Parameterized psycopg query `(%s, tuple)` — no f-string interpolation |
| T-06-SC | No new packages installed; httpx already in pyproject.toml |

## Self-Check: PASSED

- [x] `api/escalation_service.py` — exists, has `send_push_notification()` and `EXPO_PUSH_URL`
- [x] `tests/test_push_service.py` — exists, 4 tests, all pass
- [x] `api/ws_handler.py` — imports `send_push_notification`, calls it in escalation path
- [x] Commits 9a67586 and 64fbb4c exist in git log
- [x] 132 tests pass, 0 regressions
