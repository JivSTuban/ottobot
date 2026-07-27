---
phase: 03-escalation-flow
status: complete
completed_at: 2026-06-18
plans_executed: 3
tests_before: 87 backend / 30 frontend
tests_after: 95 backend / 32 frontend
---

# Phase 3: Escalation Flow — Summary

## Goal Achieved

Hot lead detection triggers email notification via Resend API, escalation record stored in Supabase, and escalation detail shown in the OwnerPanel UI.

## What Was Built

### Plan 03-01: Escalation Service Backend
- `api/escalation_service.py` — `store_escalation()` inserts into `escalations` Supabase table; `send_escalation_email()` POSTs to Resend API via httpx
- `api/main.py` — `setup_escalation_tables()` creates `escalations` table idempotently on startup
- `.env.example` — Added `RESEND_API_KEY`, `RESEND_TO_EMAIL`, `RESEND_FROM_EMAIL`
- 6 new backend tests

### Plan 03-02: Wire into ws_handler
- `api/ws_handler.py` — After each state event, fires escalation service when `escalated=True` (de-duplicated per thread via `_escalated_threads: set[str]`)
- Extracts `lead_phone` from WS message (falls back to `thread_id`), `business_id` from WS body or env var, last 3 messages as `conversation_summary`
- 2 new backend tests

### Plan 03-03: Frontend Escalation UI
- `frontend/src/useWebSocket.ts` — Parses `system_alert` from `type:state` events, exposes as `escalationAlert`
- `frontend/src/App.tsx` — Passes `escalationAlert` prop to OwnerPanel
- `frontend/src/OwnerPanel.tsx` — Escalation banner shows `system_alert` detail text below "HOT LEAD — Tawagan na!"
- `frontend/src/__tests__/useWebSocket.test.ts` — Fixed pre-existing bug: MockWebSocket.readyState=1 so send() test passes
- 2 new frontend tests

## Success Criteria Verification

| Criterion | Status |
|-----------|--------|
| ESC-01: Hot lead signal triggers escalation state in LangGraph; agent sends business phone number | ✅ Existing escalation_scorer + graph route to escalate stage; agent sends business phone in Tagalog script |
| ESC-02: Business owner receives email "Hot lead — call [number] now" with conversation summary | ✅ send_escalation_email() fires via ws_handler when escalated=True |
| ESC-03: Escalation state and outcome logged in Supabase and visible in app | ✅ store_escalation() inserts to escalations table; OwnerPanel shows escalation banner with detail |

## Key Decisions

- httpx used directly (no resend SDK) — avoids extra dependency
- De-dup via `_escalated_threads: set[str]` in ws_handler module scope — prevents re-sending on every message after escalate stage
- `ON CONFLICT (thread_id) DO NOTHING` on Supabase insert — DB-level idempotency as second safety layer
- `escalationAlert` kept separate from `systemAlert` — system_alert banner is for server init errors; escalationAlert is per-conversation state
