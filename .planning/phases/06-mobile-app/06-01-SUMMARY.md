---
phase: "06-mobile-app"
plan: "01"
subsystem: "api"
tags: ["fastapi", "jwt", "mobile", "endpoints", "push-notifications", "leads"]
dependency_graph:
  requires: []
  provides:
    - "GET /leads — JWT-gated leads pipeline endpoint"
    - "GET /leads/{lead_id}/messages — JWT-gated chat log endpoint"
    - "POST /push/send — Expo push token registration endpoint"
    - "get_business_id_from_token — FastAPI Depends JWT helper"
  affects:
    - "api/main.py"
    - "tests/test_push_endpoint.py"
    - "tests/test_leads_endpoints.py"
tech_stack:
  added:
    - "PyJWT>=2.8.0 — HS256 JWT decode for Supabase Bearer tokens"
    - "FastAPI HTTPBearer — standard security scheme for Authorization header"
  patterns:
    - "JWT sub → businesses table join (never trust client-supplied business_id)"
    - "FastAPI dependency_overrides for JWT auth bypass in unit tests"
    - "DB no-op pattern (return empty when SUPABASE_DIRECT_URL unset)"
    - "Parameterized psycopg queries throughout (no f-string SQL)"
key_files:
  created:
    - "tests/test_push_endpoint.py — 5 tests for POST /push/send"
    - "tests/test_leads_endpoints.py — 6 tests for GET /leads and GET /leads/{id}/messages"
  modified:
    - "api/main.py — JWT helper + 3 new endpoints + PushTokenRequest model + setup_push_token_table"
    - "pyproject.toml — added PyJWT>=2.8.0 dependency"
    - ".env.example — added SUPABASE_JWT_SECRET documentation"
decisions:
  - "PyJWT used instead of python-jose (python-jose not in pyproject.toml; PyJWT is lighter and sufficient)"
  - "Messages retrieved via phone→thread_id lookup (actual schema uses thread_id in messages table, not lead_id FK)"
  - "messages table uses role field (not direction) — endpoint returns role key to match schema"
  - "Lead ownership verified by SELECT phone FROM leads WHERE id=%s AND business_id=%s before fetching messages"
  - "setup_push_token_table added to lifespan call chain for idempotent table creation"
metrics:
  duration: "~25 minutes"
  completed_date: "2026-06-19"
  tasks_completed: 2
  files_modified: 5
---

# Phase 06 Plan 01: Mobile App API Endpoints Summary

**One-liner:** JWT auth dependency + GET /leads, GET /leads/{lead_id}/messages, POST /push/send endpoints with PyJWT HS256 decode and parameterized DB queries.

## What Was Built

Three new FastAPI endpoints for the Expo mobile app backend layer:

1. **`GET /leads`** — Returns all leads for the authenticated business owner. `business_id` is extracted from the JWT Bearer token (never from request body). Returns `{"leads": [...]}` with `id`, `phone`, `status`, `created_at` per lead.

2. **`GET /leads/{lead_id}/messages`** — Returns messages for a specific lead, newest-first (for `FlatList inverted` on mobile). Ownership verified via DB: lead must belong to the authenticated business. Uses `phone → thread_id` join since the messages table links via `thread_id`, not `lead_id` FK.

3. **`POST /push/send`** — Registers or updates an Expo push token for the authenticated business. Validates `ExponentPushToken[...]` format before upsert. One token per business (UPSERT on `business_id`).

**JWT helper `get_business_id_from_token`:**
- Decodes Supabase JWT using `SUPABASE_JWT_SECRET` (HS256, no audience verification)
- Extracts `sub` (owner_email), looks up `id` from `businesses` table
- Raises `HTTPException(401)` on invalid token, missing secret, or no business found

## Test Coverage

| File | Tests | Coverage |
|------|-------|----------|
| `tests/test_push_endpoint.py` | 5 | POST /push/send happy path, invalid format, no DB, no auth, invalid JWT |
| `tests/test_leads_endpoints.py` | 6 | GET /leads happy path, no DB, no auth; messages invalid UUID, no DB, no auth |

All 128 tests passing (11 new + 117 existing, 0 regressions).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Schema Mismatch] messages table has no lead_id FK or direction column**
- **Found during:** Task 1 implementation
- **Issue:** Plan assumed messages table has `lead_id` (FK to leads) and `direction` (inbound/outbound). Actual schema (created in Phase 4) has `thread_id` (TEXT) and `role` (user/assistant/system).
- **Fix:** Rewrote `GET /leads/{lead_id}/messages` to do: `SELECT phone FROM leads WHERE id=%s AND business_id=%s` → compute `thread_id = deterministic_thread_id(phone, business_id)` → `SELECT id, content, role, created_at FROM messages WHERE thread_id=%s`. Endpoint returns `role` key instead of `direction`.
- **Files modified:** `api/main.py` (get_lead_messages function)
- **Impact:** Functionally identical — mobile app gets messages in newest-first order; field name is `role` not `direction`

**2. [Rule 2 - Missing infrastructure] business_push_tokens table not created in lifespan**
- **Found during:** Task 1 implementation
- **Issue:** Plan described UPSERT into `business_push_tokens` but didn't include table creation in lifespan.
- **Fix:** Added `setup_push_token_table()` async helper and called it in lifespan after `setup_onboarding_tables()`.
- **Files modified:** `api/main.py`

**3. [Rule 3 - Dependency not installed] python-jose absent; PyJWT used instead**
- **Found during:** Task 1 (import check)
- **Issue:** Plan said "check pyproject.toml for python-jose; if not present, use PyJWT." Neither was installed.
- **Fix:** Installed PyJWT 2.13.0, added `PyJWT>=2.8.0` to pyproject.toml, used `import jwt as pyjwt` with `pyjwt.decode()` and `pyjwt.PyJWTError`.
- **Files modified:** `pyproject.toml`

## Threat Surface Scan

All three STRIDE mitigations from the plan's threat model are implemented:

| Threat ID | Mitigation Applied |
|-----------|-------------------|
| T-06-01 | `business_id` from JWT sub → `businesses` join; never from request body |
| T-06-02 | `SELECT phone FROM leads WHERE id=%s AND business_id=%s` ownership check before message fetch |
| T-06-03 | `business_id` from JWT only; `PushTokenRequest.business_id` field is ignored |
| T-06-04 | All queries use `%s` parameterized placeholders via psycopg |
| T-06-05 | `expo_token.startswith("ExponentPushToken[")` format check before upsert |

No new unplanned threat surfaces introduced.

## Self-Check: PASSED

- [x] `api/main.py` — exists and has `/leads`, `/leads/{lead_id}/messages`, `/push/send` routes
- [x] `tests/test_push_endpoint.py` — 5 tests, all passing
- [x] `tests/test_leads_endpoints.py` — 6 tests, all passing
- [x] Commit `adba1ba` — verified in git log
- [x] Full pytest suite: 128 passed, 0 failures
