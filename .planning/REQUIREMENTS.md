# Requirements: OttoBot

**Defined:** 2026-06-11
**Core Value:** A Filipino lead receives a natural Tagalog conversation that ends in a confirmed appointment — without the business owner lifting a finger and without requiring anyone to adopt a new tool.

## v1 Requirements

### Agent Core

- [ ] **AGENT-01**: LangGraph state machine with conversation stages (intro → qualify → pitch → objection handling → propose appointment → confirm → escalate)
- [ ] **AGENT-02**: LiteLLM Router with Groq/Llama 4 Maverick as primary, Gemini Flash fallback, Mistral fallback — YAML config with usage-based routing and auto-retry
- [ ] **AGENT-03**: Tagalog system prompt with Taglish (code-switching) support — agent responds in the language the lead uses
- [ ] **AGENT-04**: Industry persona templates for dental, aesthetics, real estate — injected at runtime from business profile
- [ ] **AGENT-05**: Goal-directed escalation logic — detects hot lead signals, triggers escalation state

### Demo UI

- [ ] **DEMO-01**: FastAPI WebSocket server using ConnectionManager pattern for real-time bidirectional chat
- [ ] **DEMO-02**: Split-screen web UI — left: lead chat interface, right: simulated business owner panel (conversation summary, lead status, escalation alerts)
- [ ] **DEMO-03**: LangGraph PostgresSaver pointing at Supabase Postgres — single persistence layer for agent state and conversation history

### Appointments

- [x] **APPT-01**: Business owner sets weekly availability schedule (days + hours) during onboarding
- [x] **APPT-02**: Agent proposes time windows from available slots; lead states preference
- [x] **APPT-03**: Business owner confirms or counter-proposes via app — no calendar integration required
- [x] **APPT-04**: Confirmed appointments stored in Supabase with lead, business, time, and status

### Escalation

- [ ] **ESC-01**: App push notification to business owner: "Hot lead — call [number] now" with conversation summary
- [ ] **ESC-02**: Agent provides business phone number to lead as part of escalation message
- [ ] **ESC-03**: Escalation state logged in Supabase; business owner marks outcome in app

### Channels

- [ ] **CHAN-01**: Meta Business API integration — agent sends/receives via Facebook Messenger
- [ ] **CHAN-02**: Semaphore PH SMS integration — agent sends/receives via text
- [ ] **CHAN-03**: Lead source ingestion — uploaded contact list, inbound message trigger, ad lead form webhook

### Onboarding

- [ ] **ONB-01**: Multi-step onboarding form — business name, industry, location, phone, website, services, pricing
- [ ] **ONB-02**: Industry template selection (dental / aesthetics / real estate) with preview of agent persona
- [ ] **ONB-03**: Supabase Auth — business owner account creation and session management
- [ ] **ONB-04**: Agent persona generated from onboarding data; stored and injected into LangGraph state

### Mobile App

- [ ] **APP-01**: Push notifications — hot lead alert, appointment booked, conversation summary
- [ ] **APP-02**: Conversation history per lead — full chat log readable by business owner
- [ ] **APP-03**: Pipeline dashboard — leads by status (new, in-progress, booked, escalated, closed)
- [ ] **APP-04**: Agent persona management — edit name, tone, script, offers post-onboarding
- [ ] **APP-05**: Availability calendar-lite — mark open/blocked days; no external calendar integration

### Agency

- [ ] **AGY-01**: Agency account type — manage multiple business owner sub-accounts from one login
- [ ] **AGY-02**: Per-client agent isolation — each business gets their own agent, leads, and data
- [ ] **AGY-03**: Agency billing aggregate — one invoice for all managed accounts

## v2 Requirements

*(None defined yet — all requirements are in v1 scope)*

## Out of Scope

| Feature | Reason |
|---------|--------|
| Voice AI calling | Agent does not call leads autonomously; escalation is human-initiated — future milestone |
| Calendar app integration (Google Calendar, Calendly) | Filipino leads don't use these; reconciler pattern replaces it |
| SEA-LION / SeaLLM fine-tuning | Llama 4 Maverick outperforms SEA-specific models on FilBench; fine-tuning deferred |
| Beyond 3 industries in v1 | Dental, aesthetics, real estate are initial templates; others added in v2 |
| Email channel | Filipinos don't use email for consumer comms; not in MVP |
| Built-in CRM | GHL is the reference, not the target; OttoBot surfaces lead data, not replaces CRM |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AGENT-01 | Phase 1 | Pending |
| AGENT-02 | Phase 1 | Pending |
| AGENT-03 | Phase 1 | Pending |
| AGENT-04 | Phase 1 | Pending |
| AGENT-05 | Phase 1 | Pending |
| DEMO-01 | Phase 1 | Pending |
| DEMO-02 | Phase 1 | Pending |
| DEMO-03 | Phase 1 | Pending |
| APPT-01 | Phase 2 | Complete |
| APPT-02 | Phase 2 | Complete |
| APPT-03 | Phase 2 | Complete |
| APPT-04 | Phase 2 | Complete |
| ESC-01 | Phase 3 | Pending |
| ESC-02 | Phase 3 | Pending |
| ESC-03 | Phase 3 | Pending |
| CHAN-01 | Phase 4 | Pending |
| CHAN-02 | Phase 4 | Pending |
| CHAN-03 | Phase 4 | Pending |
| ONB-01 | Phase 5 | Pending |
| ONB-02 | Phase 5 | Pending |
| ONB-03 | Phase 5 | Pending |
| ONB-04 | Phase 5 | Pending |
| APP-01 | Phase 6 | Pending |
| APP-02 | Phase 6 | Pending |
| APP-03 | Phase 6 | Pending |
| APP-04 | Phase 6 | Pending |
| APP-05 | Phase 6 | Pending |
| AGY-01 | Phase 7 | Pending |
| AGY-02 | Phase 7 | Pending |
| AGY-03 | Phase 7 | Pending |

**Coverage:**

- v1 requirements: 30 total
- Mapped to phases: 30
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-11*
*Last updated: 2026-06-11 after initialization*
