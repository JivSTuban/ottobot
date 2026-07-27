# OttoBot Autonomous Build Policy

**Analog:** Karpathy's `program.md` / autoresearch loop  
**Purpose:** You are the autonomous build agent for OttoBot. Read this file before every phase. It pre-answers all design decisions so you never need to pause for confirmation.

---

## NEVER STOP

Once the build loop begins, do **NOT** pause to ask for human confirmation between phases.  
If you run out of obvious answers, reason from first principles using the ROADMAP and this file.  
The loop runs until all phases complete or the human interrupts.  
If a phase verification reports `gaps_found`, choose **"Continue without fixing"** — gaps compound and slow delivery more than they save it.  
If a blocker is truly unresolvable (missing API key, broken external service), choose **"Skip this phase"** and log the reason in STATE.md.

---

## Optimization Objective

> Ship the fastest path to a working product a Filipino SMB business owner can use to book appointments — without touching their phone.

Optimize for: **working software over comprehensive coverage**  
Accept tradeoffs: fewer edge case handlers, simpler UI, less test coverage  
Never compromise: data isolation between businesses, no secrets in logs, Tagalog/Taglish output

---

## Metric Gate

A phase is **done** when:
1. `pytest` passes (backend) — zero failures, warnings acceptable
2. `npm test` passes (frontend, if touched) — zero failures
3. `VERIFICATION.md` exists and has `status: passed` or `status: human_needed`
4. Core happy path works end-to-end (don't ship if the main flow is broken)

If tests pass but verification says `gaps_found`, **still advance** — gaps are logged and addressable later.

---

## Phase-by-Phase Pre-Answered Decisions

### Phase 2: Appointment Reconciler

**Stack choices:**
- Availability storage: Supabase table `business_availability` (day_of_week, start_time, end_time, business_id)
- Appointments table: `appointments` (lead_id, business_id, proposed_time, status: proposed/confirmed/cancelled)
- No external calendar (Google Calendar, Calendly) — Supabase only
- Agent reads availability from DB at conversation time via a new `get_available_slots` tool node in LangGraph
- Business owner confirms via existing OwnerPanel WebSocket message (new `confirm_appointment` message type)

**Agent behavior:**
- Propose 2 time slots maximum (not a menu of 10 — too much choice friction)
- Slots drawn from next 7 days only
- If no availability set, agent says "Tatawagan ka namin para mag-ayos ng oras" (we'll call to arrange)

**API additions:**
- `POST /availability` — set business hours
- `GET /availability/{business_id}` — read slots
- WebSocket message `confirm_appointment` → business owner panel
- Keep all new endpoints behind the existing `validate_thread_id` guard pattern

---

### Phase 3: Escalation Flow

**Notification channel:** Email via Resend API (no mobile push yet — that's Phase 6)  
**Trigger:** Existing `escalation_scorer` already fires — wire it to send email + store to Supabase  
**Supabase table:** `escalations` (thread_id, business_id, lead_phone, conversation_summary, triggered_at, outcome: called/not_called/ignored)  
**UI:** Add escalation badge to existing OwnerPanel (already has `system_alert` wire — extend it)  
**Email template:** Short, no HTML — "Hot lead! Call [number] now. Summary: [last 3 messages]"  
**Resend key:** Read from `RESEND_API_KEY` env var (add to `.env.example`)  
**Do NOT implement:** In-app push, SMS to business owner (Phase 6), or escalation queue UI

---

### Phase 4: Real Channels

**Priority order:** SMS (Semaphore PH) first, then Facebook Messenger  
**SMS inbound:** Semaphore webhook → `POST /webhook/sms` → existing `handle_ws` logic reused  
**SMS outbound:** Semaphore send API — wrap in `send_sms(to, message)` helper in `api/channels.py`  
**Facebook:** Meta webhook verify + `POST /webhook/facebook` → same message routing  
**Lead ingestion:**
  - CSV upload: `POST /leads/upload` — parse CSV, insert to `leads` table, trigger outbound SMS per row
  - Ad webhook: `POST /webhook/lead-form` — Meta Lead Ads format
**Supabase tables:** `leads` (phone, name, source, business_id, status), `messages` (thread_id, role, content, created_at)  
**Thread ID for SMS/FB:** `uuid5(namespace_dns, phone_number + business_id)` — deterministic, reproducible across messages  
**Do NOT implement:** WhatsApp, email outbound, or voice channels

---

### Phase 5: Business Onboarding Website

**Stack:** Extend existing Vite/React frontend — do NOT create a separate Next.js app  
**Auth:** Supabase Auth with email + password. No OAuth (Google/Facebook sign-in) yet  
**Form steps (5 screens):**
  1. Account creation (email, password)
  2. Business basics (name, industry selector from existing 3, city, phone)
  3. Services + pricing (free text, 3 fields max)
  4. Agent persona preview (show intro message rendered with their data)
  5. Confirmation + "Go to dashboard"
**Persona generation:** On step 4, POST to `/onboarding/preview` → renders `base.j2` + `{industry}.j2` with their data  
**Storage:** `businesses` table in Supabase (id, owner_id, name, industry, phone, city, services, pricing, created_at)  
**Route structure:** `/onboarding` wizard, `/dashboard` (existing OwnerPanel promoted to route)  
**Do NOT implement:** Billing, subscription gating, email verification flow, multiple personas per business

---

### Phase 6: Mobile App

**Stack:** React Native with Expo (SDK 51+), not bare workflow  
**Auth:** Reuse Supabase Auth tokens from Phase 5 — `@supabase/supabase-js` in Expo  
**Push notifications:** Expo Push Notifications + `expo-notifications` — no FCM/APNs direct setup  
**Screens (MVP only, 4 screens):**
  1. Login (Supabase Auth)
  2. Lead Pipeline (list, grouped by status: new / in-progress / booked / escalated)
  3. Conversation detail (read-only chat log for a lead)
  4. Settings (availability schedule — reuse Phase 2 API)
**Push trigger:** Phase 3 escalation email → also call `POST /push/send` with Expo token  
**Expo push token:** Stored in `business_push_tokens` table, collected on app first launch  
**Do NOT implement:** Persona editing, analytics dashboard, dark mode, iPad layout

---

### Phase 7: Agency / Multi-Account

**Data model:**
- `agencies` table (id, name, owner_email)
- `agency_members` junction (agency_id, business_id, role: owner/viewer)
- All existing tables get `business_id` FK (already in Phase 4+ tables)
**RLS:** Supabase Row Level Security on all tables — policy: `business_id = auth.jwt()->>'business_id'`  
**Agency login:** Same Supabase Auth, role stored in `profiles` table as `account_type: agency|business`  
**Agency dashboard:** Single additional screen showing all managed businesses + their lead counts  
**Billing:** `billing_events` table (agency_id, business_id, event_type, amount, created_at) — no Stripe, just logging  
**Do NOT implement:** Sub-account creation flow (manual via Supabase dashboard for now), multi-tier agencies, white-labeling

---

## Recovery Heuristics

| Situation | Auto-decision |
|-----------|--------------|
| Tests fail, obvious fix visible | Fix it, retry once |
| Tests fail, root cause unclear | Run `/gsd-debug`, apply fix, retry |
| Tests still fail after 1 retry | Log blocker, advance to next phase |
| Verification: `gaps_found` | Continue without fixing |
| Verification: `human_needed` | Continue (Jiv will review async) |
| External service unavailable (Resend, Semaphore) | Mock the API call in tests, stub in code, log to-do |
| Missing env var | Add to `.env.example`, guard with `os.environ.get()` pattern, continue |

---

## Editable Zone

Claude may freely modify:
- `agent/` — prompts, state, models, graph, escalation, stage detection
- `api/` — FastAPI endpoints, WebSocket handler, channels
- `frontend/src/` — React components, hooks, types
- `tests/` — all test files
- `evals/` — eval harness and scripts
- `scripts/` — dev and utility scripts

Claude must NOT modify (or ask for permission before touching):
- `.planning/` artifacts (ROADMAP.md, REQUIREMENTS.md) — policy, not code
- `litellm_config.yaml` routing weights — production-tuned, change only if tests require it
- Supabase migrations that drop or rename existing columns

---

## Research Direction (changeable by human)

Current priority: **Phase 2 → Phase 3 → Phase 4** (appointment + escalation + real channels = first paying customer capable)  
After Phase 4: Phase 5 → Phase 6 → Phase 7 (onboarding → mobile → agency)  
Phase 8 (autoresearch loop) starts when Phase 4 is complete and real conversation data exists.

If Jiv changes this file between phases, re-read it before starting the next phase.
