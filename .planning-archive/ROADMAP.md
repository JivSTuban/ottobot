# Roadmap: OttoBot

## Overview

Build an AI outbound sales agent that speaks Tagalog/Taglish and books appointments for Philippine SMBs — starting with a working demo of the conversation engine, then wiring real channels, onboarding, and a mobile app for business owners.

## Phases

- [x] **Phase 1: Agent Core & Demo UI** — Working LangGraph agent with Tagalog conversation stages, demo split-screen UI (completed 2026-06-15)
- [x] **Phase 2: Appointment Reconciler** — Agent proposes time slots, business owner confirms via app, appointments stored in Supabase (completed 2026-06-16)
- [x] **Phase 3: Escalation Flow** — Hot lead detection, push notification to business owner, escalation state tracking (completed 2026-06-18)
- [x] **Phase 4: Real Channels** — Facebook Messenger and SMS (Semaphore PH) integration, lead source ingestion (completed 2026-06-19)
- [x] **Phase 5: Business Onboarding Website** — Multi-step onboarding form, industry template selection, Supabase Auth (completed 2026-06-19)
- [x] **Phase 6: Mobile App** — Push notifications, lead pipeline dashboard, persona management, availability calendar (completed 2026-06-19)
- [ ] **Phase 7: Agency / Multi-Account** — Agency accounts managing multiple business owner sub-accounts
- [ ] **Phase 8: Autoresearch Loop** — Autonomous overnight prompt/agent optimization via ratchet loop (Karpathy autoresearch pattern adapted for conversation agents)

## Phase Details

### Phase 1: Agent Core & Demo UI

**Goal**: A working Tagalog/Taglish AI sales agent that can carry a full appointment-booking conversation, with a split-screen demo UI showing both the lead's chat and the business owner's panel in real time.
**Depends on**: Nothing (first phase)
**Requirements**: AGENT-01, AGENT-02, AGENT-03, AGENT-04, AGENT-05, DEMO-01, DEMO-02, DEMO-03
**Success Criteria** (what must be TRUE):

  1. Agent moves through conversation stages (intro → qualify → pitch → objection handling → propose appointment → confirm → escalate) without getting stuck
  2. Agent responds in Tagalog or Taglish matching the lead's language, using the correct industry persona (dental / aesthetics / real estate)
  3. LiteLLM Router falls back from Groq to Gemini to Mistral when rate limits are hit
  4. Split-screen demo UI shows live conversation on the left and a real-time business owner panel on the right via WebSocket
  5. Conversation state persists across page reload (PostgresSaver in Supabase)

**Plans**: 7 plans

- [x] 01-01-PLAN.md — Project scaffold (Python 3.12 venv, pyproject.toml, frontend Vite scaffold, Wave 0 test stubs, litellm_config.yaml, .env.example)
- [x] 01-02-PLAN.md — Generate persona + industry images via Gemini MCP and typed asset manifest
- [x] 01-03-PLAN.md — Agent core: state, models, Jinja2 personas, LiteLLM Router, escalation scorer
- [x] 01-04-PLAN.md — LangGraph StateGraph builder, route_next_stage, stage detection
- [x] 01-05-PLAN.md — FastAPI WebSocket + AsyncPostgresSaver lifespan + online guardrails
- [x] 01-06-PLAN.md — Vite/React split-screen UI (IndustrySelector, LeadChat, OwnerPanel, useWebSocket)
- [x] 01-07-PLAN.md — End-to-end dev script + README + manual demo checklist sign-off

### Phase 2: Appointment Reconciler

**Goal**: Agent can propose appointment time windows from the business owner's availability schedule, and confirmed appointments are stored in Supabase — no external calendar needed.
**Depends on**: Phase 1
**Requirements**: APPT-01, APPT-02, APPT-03, APPT-04
**Success Criteria** (what must be TRUE):

  1. Business owner can define weekly availability (days + hours) and it is saved to Supabase
  2. Agent reads available slots and proposes time windows to the lead during conversation
  3. Business owner can confirm or counter-propose an appointment time via the app
  4. Confirmed appointment record (lead, business, time, status) is readable in Supabase

**Plans**: 4 plans
**Wave 1**

- [x] 02-01-PLAN.md — agent/slots.py helper (slot math, Tagalog formatting) + ConversationState.proposed_appointment + test stubs
- [x] 02-02-PLAN.md — FastAPI REST endpoints (POST /availability, GET /availability/{business_id}, POST /appointments/confirm) + Supabase table creation

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-03-PLAN.md — LangGraph agent_node slot injection at propose_appointment stage + ws_handler confirm_appointment branch
- [x] 02-04-PLAN.md — OwnerPanel.tsx Appointments section UI + TypeScript types + frontend tests

### Phase 3: Escalation Flow

**Goal**: When the agent detects a hot lead, the business owner receives a push notification with the lead's phone number and conversation summary, and the escalation outcome is tracked.
**Depends on**: Phase 1
**Requirements**: ESC-01, ESC-02, ESC-03
**Success Criteria** (what must be TRUE):

  1. Hot lead signal triggers escalation state in LangGraph; agent sends business phone number to lead
  2. Business owner receives push notification: "Hot lead — call [number] now" with conversation summary
  3. Escalation state and outcome (called / not called) are logged in Supabase and visible in the app

**Plans**: 3 plans

- [x] 03-01-PLAN.md — Escalation service backend (Resend email + Supabase escalations table)
- [x] 03-02-PLAN.md — Wire escalation into ws_handler (de-dup per thread)
- [x] 03-03-PLAN.md — OwnerPanel escalation UI (show system_alert detail in HOT LEAD banner)

### Phase 4: Real Channels

**Goal**: Agent sends and receives messages via Facebook Messenger and Semaphore PH SMS, and leads can be ingested from uploaded contact lists, inbound messages, and ad lead form webhooks.
**Depends on**: Phase 1
**Requirements**: CHAN-01, CHAN-02, CHAN-03
**Success Criteria** (what must be TRUE):

  1. Agent receives a Facebook Messenger message and replies via the Meta Business API
  2. Agent receives an SMS and replies via Semaphore PH
  3. Business owner can upload a contact list and trigger outbound campaigns; ad lead form webhook ingests leads automatically

**Plans**: 3 plans

- [x] 04-01-PLAN.md — SMS channel + deterministic thread ID + leads/messages tables
- [x] 04-02-PLAN.md — Facebook Messenger webhook (verify + message routing)
- [x] 04-03-PLAN.md — Lead ingestion: CSV upload + Meta Lead Ads webhook

### Phase 5: Business Onboarding Website

**Goal**: A business owner can sign up, complete a multi-step onboarding form, select an industry template, and have a personalized agent persona ready — without any manual setup.
**Depends on**: Phase 1
**Requirements**: ONB-01, ONB-02, ONB-03, ONB-04
**Success Criteria** (what must be TRUE):

  1. Business owner creates an account via Supabase Auth and is authenticated on subsequent visits
  2. Multi-step form collects business name, industry, location, phone, website, services, pricing and saves to Supabase
  3. Business owner previews the agent persona before confirming their industry template selection
  4. Agent persona (generated from onboarding data) is stored in Supabase and injected into LangGraph state when conversations start

**Plans**: TBD

### Phase 6: Mobile App

**Goal**: Business owners can monitor lead activity, read conversation history, manage their agent persona, and set availability — all from a mobile app with push notifications.
**Depends on**: Phase 3, Phase 5
**Requirements**: APP-01, APP-02, APP-03, APP-05
**Success Criteria** (what must be TRUE):

  1. Business owner receives push notifications for hot leads, booked appointments, and conversation summaries
  2. Business owner can read the full chat log for any lead
  3. Pipeline dashboard shows all leads grouped by status (new, in-progress, booked, escalated, closed)
  4. Business owner can mark days as open or blocked; changes update available slots immediately

**Deferred to Phase 7**: APP-04 (agent persona editing in mobile) — per POLICY.md, persona editing is not implemented in Phase 6 mobile app.

**Plans**: TBD

### Phase 7: Agency / Multi-Account

**Goal**: An agency account can manage multiple business owner sub-accounts from a single login, with full data isolation per client and aggregated billing.
**Depends on**: Phase 5, Phase 6
**Requirements**: AGY-01, AGY-02, AGY-03
**Success Criteria** (what must be TRUE):

  1. Agency user can log in and see a list of their managed business owner sub-accounts
  2. Each sub-account's agent, leads, and data are fully isolated — agency user cannot see one client's data from another client's view
  3. Agency receives a single invoice aggregating charges for all managed accounts

**Plans**: TBD

### Phase 8: Autoresearch Loop

**Goal**: An autonomous ratchet loop (inspired by Karpathy's autoresearch) that overnight proposes, tests, and commits prompt/config improvements to the conversation agent — using simulated Taglish conversations as the eval signal, with no human in the loop.
**Depends on**: Phase 3 (full conversation pipeline must be battle-tested), Phase 4 (real conversation data for building labeled eval dataset)
**Requirements**: AUTO-01, AUTO-02, AUTO-03, AUTO-04
**Success Criteria** (what must be TRUE):

  1. A labeled eval dataset of ≥200 simulated Taglish conversations (with ground-truth stage transitions and booking outcomes) is built and versioned
  2. A single scalar optimization metric is defined and computed reliably (weighted F1 across stage transitions + appointment booking rate)
  3. An agent loop autonomously edits the scoped "editable zone" (`agent/prompts.py`, stage detection thresholds, LLM routing weights), runs the eval suite, and keeps or reverts each change based on metric delta
  4. Each accepted change is committed to git with eval score deltas in the commit message — a morning log of N experiments and a measurably better agent

**Editable Zone** (the only files the autoresearch agent may modify):

- `agent/prompts.py` — system prompts, stage-specific instructions, persona templates
- `agent/stage_detection.py` — keyword/pattern thresholds for stage classification
- `litellm_config.yaml` — model routing weights and fallback order

**Fixed / Never Touched**:

- `agent/graph.py` — LangGraph state machine structure
- `agent/models.py` — Pydantic state schemas
- `api/` — FastAPI server
- `evals/` — eval harness and labeled dataset (read-only to the loop)

**Recipe** (adapted from Karpathy autoresearch):

- `evals/program.md` — human sets research direction (e.g., "improve objection-handling in aesthetics industry")
- `evals/run_eval.py` — fixed eval harness, never touched by agent, returns scalar metric
- Ratchet: propose change → run eval → metric improved? keep + commit : revert → repeat
- Target: ~10 experiments/hour overnight on CPU (no GPU needed — LLM API calls, not training)

**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Agent Core & Demo UI | 8/8 | Complete   | 2026-06-16 |
| 2. Appointment Reconciler | 4/4 | Complete    | 2026-06-16 |
| 3. Escalation Flow | 3/3 | Complete | 2026-06-18 |
| 4. Real Channels | 3/3 | Complete | 2026-06-19 |
| 5. Business Onboarding Website | 2/2 | Complete | 2026-06-19 |
| 6. Mobile App | 4/4 | Complete | 2026-06-19 |
| 7. Agency / Multi-Account | 0/TBD | Not started | - |
| 8. Autoresearch Loop | 0/TBD | Not started | - |
