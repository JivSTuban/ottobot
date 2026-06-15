# Roadmap: OttoBot

## Overview

Build an AI outbound sales agent that speaks Tagalog/Taglish and books appointments for Philippine SMBs — starting with a working demo of the conversation engine, then wiring real channels, onboarding, and a mobile app for business owners.

## Phases

- [ ] **Phase 1: Agent Core & Demo UI** — Working LangGraph agent with Tagalog conversation stages, demo split-screen UI
- [ ] **Phase 2: Appointment Reconciler** — Agent proposes time slots, business owner confirms via app, appointments stored in Supabase
- [ ] **Phase 3: Escalation Flow** — Hot lead detection, push notification to business owner, escalation state tracking
- [ ] **Phase 4: Real Channels** — Facebook Messenger and SMS (Semaphore PH) integration, lead source ingestion
- [ ] **Phase 5: Business Onboarding Website** — Multi-step onboarding form, industry template selection, Supabase Auth
- [ ] **Phase 6: Mobile App** — Push notifications, lead pipeline dashboard, persona management, availability calendar
- [ ] **Phase 7: Agency / Multi-Account** — Agency accounts managing multiple business owner sub-accounts

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
- [ ] 01-05-PLAN.md — FastAPI WebSocket + AsyncPostgresSaver lifespan + online guardrails
- [ ] 01-06-PLAN.md — Vite/React split-screen UI (IndustrySelector, LeadChat, OwnerPanel, useWebSocket)
- [ ] 01-07-PLAN.md — End-to-end dev script + README + manual demo checklist sign-off

### Phase 2: Appointment Reconciler

**Goal**: Agent can propose appointment time windows from the business owner's availability schedule, and confirmed appointments are stored in Supabase — no external calendar needed.
**Depends on**: Phase 1
**Requirements**: APPT-01, APPT-02, APPT-03, APPT-04
**Success Criteria** (what must be TRUE):

  1. Business owner can define weekly availability (days + hours) and it is saved to Supabase
  2. Agent reads available slots and proposes time windows to the lead during conversation
  3. Business owner can confirm or counter-propose an appointment time via the app
  4. Confirmed appointment record (lead, business, time, status) is readable in Supabase

**Plans**: TBD

### Phase 3: Escalation Flow

**Goal**: When the agent detects a hot lead, the business owner receives a push notification with the lead's phone number and conversation summary, and the escalation outcome is tracked.
**Depends on**: Phase 1
**Requirements**: ESC-01, ESC-02, ESC-03
**Success Criteria** (what must be TRUE):

  1. Hot lead signal triggers escalation state in LangGraph; agent sends business phone number to lead
  2. Business owner receives push notification: "Hot lead — call [number] now" with conversation summary
  3. Escalation state and outcome (called / not called) are logged in Supabase and visible in the app

**Plans**: TBD

### Phase 4: Real Channels

**Goal**: Agent sends and receives messages via Facebook Messenger and Semaphore PH SMS, and leads can be ingested from uploaded contact lists, inbound messages, and ad lead form webhooks.
**Depends on**: Phase 1
**Requirements**: CHAN-01, CHAN-02, CHAN-03
**Success Criteria** (what must be TRUE):

  1. Agent receives a Facebook Messenger message and replies via the Meta Business API
  2. Agent receives an SMS and replies via Semaphore PH
  3. Business owner can upload a contact list and trigger outbound campaigns; ad lead form webhook ingests leads automatically

**Plans**: TBD

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
**Requirements**: APP-01, APP-02, APP-03, APP-04, APP-05
**Success Criteria** (what must be TRUE):

  1. Business owner receives push notifications for hot leads, booked appointments, and conversation summaries
  2. Business owner can read the full chat log for any lead
  3. Pipeline dashboard shows all leads grouped by status (new, in-progress, booked, escalated, closed)
  4. Business owner can edit agent name, tone, script, and offers post-onboarding
  5. Business owner can mark days as open or blocked; changes update available slots immediately

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

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Agent Core & Demo UI | 4/7 | In Progress|  |
| 2. Appointment Reconciler | 0/TBD | Not started | - |
| 3. Escalation Flow | 0/TBD | Not started | - |
| 4. Real Channels | 0/TBD | Not started | - |
| 5. Business Onboarding Website | 0/TBD | Not started | - |
| 6. Mobile App | 0/TBD | Not started | - |
| 7. Agency / Multi-Account | 0/TBD | Not started | - |
