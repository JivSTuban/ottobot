---
phase: 04-real-channels
status: complete
completed_at: 2026-06-19
plans_executed: 3
tests_before: 95 backend / 32 frontend
tests_after: 111 backend / 32 frontend
---

# Phase 4: Real Channels — Summary

## Goal Achieved

Agent sends and receives SMS via Semaphore PH, replies via Facebook Messenger, and ingests leads from CSV uploads and Meta Lead Ads webhooks.

## What Was Built

### Plan 04-01: SMS Channel + Lead/Messages Tables
- `api/channels.py` — `send_sms()`, `send_facebook_message()`, `deterministic_thread_id()`
- `api/main.py` — `setup_channel_tables()` creates `leads` + `messages` tables; `POST /webhook/sms` endpoint; `process_channel_message()` shared helper
- 9 new backend tests

### Plan 04-02: Facebook Messenger Webhook
- `api/main.py` — `GET /webhook/facebook` (Meta verify challenge) + `POST /webhook/facebook` (message routing via process_channel_message)
- 3 new backend tests

### Plan 04-03: Lead Ingestion
- `api/main.py` — `POST /leads/upload` (CSV → leads table + outbound SMS) + `POST /webhook/lead-form` (Meta Lead Ads → leads table + outbound SMS)
- 4 new backend tests (including 400 guard on invalid business_id)

## Success Criteria Verification

| Criterion | Status |
|-----------|--------|
| CHAN-01: Agent receives Facebook Messenger message and replies via Meta Business API | ✅ GET verify + POST handler with send_facebook_message() |
| CHAN-02: Agent receives SMS and replies via Semaphore PH | ✅ POST /webhook/sms + send_sms() |
| CHAN-03: Business owner can upload CSV; ad lead form webhook ingests leads | ✅ /leads/upload + /webhook/lead-form |

## Key Decisions

- `deterministic_thread_id(phone, business_id)` = uuid5(NAMESPACE_DNS, phone:business_id) — stable thread identity for multi-message SMS/FB conversations
- `process_channel_message()` shares compiled_graph with WebSocket path — no code duplication
- `BUSINESS_ID` env var for Phase 4; Phase 5 auth replaces it with auth-gated validation
- `leads` table source column: csv_upload | lead_form | sms_inbound | fb_messenger
- `ON CONFLICT (phone, business_id) DO NOTHING` on all lead upserts — idempotent ingestion
