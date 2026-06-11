# OttoBot

## What This Is

OttoBot is a B2B SaaS platform that gives Philippine SMBs (dental, aesthetics, real estate) a Tagalog-speaking AI outbound sales agent that converts leads into booked appointments via Facebook Messenger and SMS. Business owners onboard through a website, personalize their agent with business info and industry templates, and receive real-time notifications through a mobile app when leads are hot or appointments are booked.

## Core Value

A Filipino lead receives a natural Tagalog conversation that ends in a confirmed appointment — without the business owner lifting a finger and without requiring anyone to adopt a new tool.

## Requirements

### Validated

(None yet — ship to validate)

### Active

**Phase 1 — Agent Core & Demo UI**
- [ ] **AGENT-01**: LangGraph state machine with conversation stages (intro → qualify → pitch → objection handling → propose appointment → confirm → escalate)
- [ ] **AGENT-02**: LiteLLM Router with Groq/Llama 4 Maverick as primary, Gemini Flash fallback, Mistral fallback — YAML config with usage-based routing and auto-retry
- [ ] **AGENT-03**: Tagalog system prompt with Taglish (code-switching) support — agent responds in the language the lead uses
- [ ] **AGENT-04**: Industry persona templates for dental, aesthetics, real estate — injected at runtime from business profile
- [ ] **AGENT-05**: Goal-directed escalation logic — detects hot lead signals, triggers escalation state
- [ ] **DEMO-01**: FastAPI WebSocket server using ConnectionManager pattern for real-time bidirectional chat
- [ ] **DEMO-02**: Split-screen web UI — left: lead chat interface, right: simulated business owner panel (conversation summary, lead status, escalation alerts)
- [ ] **DEMO-03**: LangGraph PostgresSaver pointing at Supabase Postgres — single persistence layer for agent state and conversation history

**Phase 2 — Appointment Reconciler**
- [ ] **APPT-01**: Business owner sets weekly availability schedule (days + hours) during onboarding
- [ ] **APPT-02**: Agent proposes time windows from available slots; lead states preference
- [ ] **APPT-03**: Business owner confirms or counter-proposes via app — no calendar integration required
- [ ] **APPT-04**: Confirmed appointments stored in Supabase with lead, business, time, and status

**Phase 3 — Escalation Flow**
- [ ] **ESC-01**: App push notification to business owner: "Hot lead — call [number] now" with conversation summary
- [ ] **ESC-02**: Agent provides business phone number to lead as part of escalation message
- [ ] **ESC-03**: Escalation state logged in Supabase; business owner marks outcome in app

**Phase 4 — Real Channels**
- [ ] **CHAN-01**: Meta Business API integration — agent sends/receives via Facebook Messenger
- [ ] **CHAN-02**: Semaphore PH SMS integration — agent sends/receives via text
- [ ] **CHAN-03**: Lead source ingestion — uploaded contact list, inbound message trigger, ad lead form webhook

**Phase 5 — Business Onboarding Website**
- [ ] **ONB-01**: Multi-step onboarding form — business name, industry, location, phone, website, services, pricing
- [ ] **ONB-02**: Industry template selection (dental / aesthetics / real estate) with preview of agent persona
- [ ] **ONB-03**: Supabase Auth — business owner account creation and session management
- [ ] **ONB-04**: Agent persona generated from onboarding data; stored and injected into LangGraph state

**Phase 6 — Mobile App**
- [ ] **APP-01**: Push notifications — hot lead alert, appointment booked, conversation summary
- [ ] **APP-02**: Conversation history per lead — full chat log readable by business owner
- [ ] **APP-03**: Pipeline dashboard — leads by status (new, in-progress, booked, escalated, closed)
- [ ] **APP-04**: Agent persona management — edit name, tone, script, offers post-onboarding
- [ ] **APP-05**: Availability calendar-lite — mark open/blocked days; no external calendar integration

**Phase 7 — Agency / Multi-Account**
- [ ] **AGY-01**: Agency account type — manage multiple business owner sub-accounts from one login
- [ ] **AGY-02**: Per-client agent isolation — each business gets their own agent, leads, and data
- [ ] **AGY-03**: Agency billing aggregate — one invoice for all managed accounts

### Out of Scope

- **Voice AI calling** — agent does not call leads autonomously; escalation is human-initiated (future milestone)
- **Calendar app integration** (Google Calendar, Calendly, etc.) — Filipino leads don't use these; reconciler pattern replaces it
- **SEA-LION / SeaLLM fine-tuning** — Llama 4 Maverick outperforms SEA-specific models on FilBench; fine-tuning deferred
- **Beyond 3 industries in v1** — dental, aesthetics, real estate are the initial templates; others added in v2
- **Email channel** — Filipinos don't use email for consumer comms; not in MVP
- **Built-in CRM** — GHL is the reference, not the target; OttoBot surfaces lead data, not replaces CRM

## Context

**Market insight:** Filipinos rank 4th globally in ChatGPT usage but have low calendar app adoption and lower average incomes — requires cost-efficient, zero-adoption-friction tooling.

**Communication channels:** FB Messenger and SMS dominate Philippine consumer comms. WhatsApp and Viber are secondary. Email is not used for lead follow-up.

**Language:** Taglish (mixed Tagalog/English) is the natural register for Filipino consumer conversations — the agent must handle code-switching gracefully, not enforce pure Tagalog.

**Reference product:** GoHighLevel (GHL) — OttoBot is GHL's pipeline + automation layer with a Filipino-market-specific AI conversation layer on top.

**FilBench finding (Aug 2025):** Llama 4 Maverick is the best free/open-weight model for Filipino/Tagalog, outperforming SEA-specific models. Available on Groq for fast inference.

**SalesGPT base:** Fork of github.com/filip-michalsky/SalesGPT (2.6k stars) — provides conversation stage detection, LiteLLM integration, and a React frontend. Saves 2–3 weeks vs building the agent state machine from scratch.

**LangGraph + Supabase:** LangGraph's `PostgresSaver` checkpointer connects directly to Supabase Postgres via connection string — no separate state store needed. Each lead conversation maps to a `thread_id`.

**Supabase Realtime:** RLS-protected broadcast channel pushes live conversation updates to the business owner dashboard. Business owner only sees their own leads.

## Constraints

- **Budget**: Zero LLM API cost at MVP — Groq free tier (Llama 4 Maverick), Gemini free tier, Mistral free tier routed via LiteLLM
- **Hosting**: Free tiers at MVP — Railway (FastAPI agent), Vercel (Next.js frontend), Supabase (DB + auth + realtime)
- **Language**: Agent must handle Taglish — pure Tagalog-only prompts will feel unnatural and reduce conversion
- **No calendar dependency**: Appointment flow must work without any external calendar integration
- **Stack**: Python (agent/backend), Next.js (web), React Native or PWA (mobile) — matches SalesGPT's existing codebase

## Key Decisions

| Decision | Rationale | Outcome |
|---|---|---|
| Fork SalesGPT as agent base | Conversation stage state machine + LiteLLM integration already built; saves 2–3 weeks | — Pending |
| LangGraph for state machine | Explicit graph control over conversation stages + escalation; `PostgresSaver` integrates with Supabase | — Pending |
| LangGraph `PostgresSaver` → Supabase Postgres | Single persistence layer for both agent state and app data; no Redis or separate store needed | — Pending |
| Llama 4 Maverick (Groq) as primary LLM | Best FilBench score among free models for Tagalog; Groq provides fastest inference | — Pending |
| LiteLLM Router (not OpenRouter) | YAML-configurable, self-hosted, `usage-based-routing` with per-model RPM/TPM limits; better control than managed router | — Pending |
| Semaphore PH over Twilio for SMS | Local Philippine gateway — significantly cheaper per message for PH numbers | — Pending |
| Appointment reconciler (no calendar) | Eliminates adoption friction; business owner confirms via app, not external calendar | — Pending |
| Build order: agent → demo UI → channels → onboarding → app | Validates conversation quality before wiring real channels; prevents rework | — Pending |
| FastAPI WebSocket `ConnectionManager` pattern | Official FastAPI pattern for multi-client real-time chat; directly applicable to demo split-screen UI | — Pending |
| Supabase RLS on messages and leads | Each business owner sees only their data; row-level security enforced at DB layer | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:**
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone:**
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-11 after initialization*
