# PRD: OttoBot Lead Nurture for Filipino Homes (with GHL)

- Status: Draft v1, generated 2026-10-06
- Sources: ottobot `.planning-archive` (REQUIREMENTS, AI-SPEC, RESEARCH), `JivSTuban/crowdsnare-handoff-docs` (02 through 06), live GHL MCP probe (`opencode.json`, 36 tools), official GHL API docs via Context7
- Note: no raw dealership threads were available at draft time (credentials dead, see section 9). All nurture content below is structural. Real thread examples get appended once scouting unblocks.

## 1. Problem

Filipino Homes brokers lose warm leads to slow follow-up. Inquiry comes in through Messenger or SMS, nobody replies in minutes, qualification is ad hoc, site viewings are proposed over long threads, and dormant leads are never reactivated. The proven fix in automotive (Crowdsnare dealership subaccounts: speed-to-lead SMS, reactivation, outbound triage, Messenger routing) has no Filipino-market equivalent: Taglish register matching, phone-confirmation culture, and zero calendar-app adoption.

## 2. Users

- Leads: Filipino property seekers (ages 20-45) writing in Tagalog, Taglish, or English over Messenger or SMS.
- Brokers: Filipino Homes agents who want booked site viewings and clean handoffs, no new tool to learn.
- Operator (Jiv/agency): provisions one GHL subaccount per branch or team, monitors, QA before live traffic.

## 3. Goals and non-goals

Goals:
- Sub-5-minute first response to every new property inquiry, in the lead's own register.
- Qualification (budget, location, timeline, financing) completed by the agent before human time is spent.
- Site viewing booked with max 2 slot choices, confirmed, reminded, and cleaned up after booking.
- Dormant leads reactivated on a schedule with safe stop states.
- Every booking and handoff mirrored in GHL (contacts, conversations, opportunities, calendars).

Non-goals (v1): agent-placed voice calls (human-initiated escalation only), Google Calendar or Calendly integration (reconciler pattern instead), email channel, industries beyond the current three templates, built-in CRM (GHL stays the system of record).

## 4. System overview

OttoBot remains the conversation layer; GHL becomes the record and delivery layer for Filipino Homes, following the Crowdsnare message loop adapted to one subaccount:

1. Lead message or lead event enters the FH GHL subaccount.
2. A GHL workflow updates context fields and calls the OttoBot webhook with contact plus conversation IDs.
3. OttoBot loads branch config, nurture rules, availability, and thread state, then decides: respond, book, transfer, tag, stop, or escalate.
4. OttoBot writes the outcome back to GHL fields and pipeline stage.
5. GHL sends the customer-facing SMS or Messenger reply.
6. Follow-up automations continue or stop based on tags, stage, and agent state.

Data isolation follows the Crowdsnare model: one subaccount, one PIT, its own pipelines, calendars, numbers, workflows, and config row.

## 5. Requirements

### 5.1 Nurture plays (new)

- [ ] **NURT-01 Speed-to-lead**: first response to a new inquiry within 5 minutes, 24/7. Detects appointment intent in the first two turns and routes to qualification, not small talk.
- [ ] **NURT-02 Qualification**: collects budget band, target location, move-in timeline, and financing position (cash, bank pre-qual, Pag-IBIG) before pitching. Accepts partial answers and resumes across sessions.
- [ ] **NURT-03 Pitch**: presents at most 2 matching units with payment terms when qualification is sufficient. Never invents prices, availability, or terms.
- [ ] **NURT-04 Objection handling**: recovers price, reservation-fee, and financing objections with one clarifying response each, then re-asks. Treats Filipino politeness deflection ("pag-iisipan ko muna") as a soft close, not a rejection.
- [ ] **NURT-05 Viewing booking**: proposes max 2 slots from branch availability, takes the lead's pick, confirms, sends a reminder, and marks no-show for recovery.
- [ ] **NURT-06 Reactivation**: re-engages dormant threads (no reply 3, 7, 21 days) with a new hook each time, never the same bump twice. Stops permanently on stop, wrong-person, already-bought, or broker-takeover states.

### 5.2 Controls (new, from Crowdsnare cross-product rules)

- [ ] **CTRL-01 Manual takeover**: any broker reply in the thread freezes the agent until the broker releases it.
- [ ] **CTRL-02 Stop handling**: STOP, negative consent, wrong-person, and already-bought each move the contact to a terminal state and halt all follow-ups.
- [ ] **CTRL-03 Booked cleanup**: a confirmed viewing cancels pending bumps and reminders for that thread.
- [ ] **CTRL-04 Triage tags**: every outbound or reactivation contact ends in exactly one state: interested, not-interested, wrong-person, already-bought, or booked.
- [ ] **CTRL-05 Config lookup**: all copy, slots, financing options, and escalation numbers resolve from branch config, never hardcoded.
- [ ] **CTRL-06 Safe QA**: synthetic thread per play per channel passes before live traffic; results logged.

### 5.3 GHL integration (new)

- [ ] **GHL-01 Subaccount and PIT**: FH branch subaccount provisioned; PIT minted with `conversations.readonly`, `conversations/message.readonly`, `contacts.readonly`, `opportunities.readonly`, `locations.readonly`, `calendars.readonly` (plus write scopes for send, tag, and stage moves). Token stored as env, never in git. Project MCP already configured in `opencode.json`.
- [ ] **GHL-02 Ingest**: inbound message and new-lead events reach OttoBot via workflow webhook with contact and conversation IDs.
- [ ] **GHL-03 Write-back**: agent outcomes update contact fields, tags, conversation status, and opportunity stage. Booking creates the calendar event.
- [ ] **GHL-04 Thread read**: agent fetches full thread via `conversations_get-messages` before deciding, so it never asks twice.
- [ ] **GHL-05 Outcome correlation**: weekly job joins booked viewings to originating threads to refresh the nurture framework with what actually worked.
- [ ] **GHL-06 Dashboard**: broker sees leads by stage (new, qualifying, viewing-proposed, booked, escalated, closed) reusing the existing pipeline panel.

### 5.4 Agent core (as built, keep)

AGENT-01 through AGENT-05, DEMO-01 through DEMO-03, APPT-01 through APPT-04, ESC-01 through ESC-03, CHAN-01 through CHAN-03, ONB-01 through ONB-04, APP-01 through APP-05, AGY-01 through AGY-03 all stand. Cross-reference `.planning-archive/REQUIREMENTS.md`. New work must not regress the 7-stage state machine, Taglish register matching, or escalation timing.

### 5.5 Provisioning (new)

- [ ] **PROV-01**: one-command branch setup: verify subaccount, mint PIT, apply snapshot (pipelines, tags, custom fields, calendars, workflows), insert config row, rewrite webhook paths, run synthetic QA, log deployment report.
- [ ] **PROV-02**: golden-source gate: a snapshot is used only after stage completeness, stop handling, calendar cleanup, bump audit, and QA pass.

## 6. Acceptance criteria (sample, each requirement gets one before build)

- NURT-01: 95% of test inquiries answered within 5 minutes across 50 synthetic threads.
- NURT-05: booking completes in at most 6 turns from first slot proposal; never more than 2 slots per message.
- CTRL-01: agent sends zero messages while broker-takeover tag is present (100% over test set).
- CTRL-02: all four terminal states halt follow-ups within one cycle.
- GHL-03: every booked viewing in OttoBot has a matching GHL calendar event and opportunity stage within 60 seconds.
- Taglish: register match judged by the existing Filipino sales-manager rubric, pass bar 85%.

## 7. Constraints

- Taglish register matching and honorific consistency per AI-SPEC section 1b.
- Max 2 slots per proposal; phone confirmation pattern, no calendar invites.
- No high-pressure urgency copy without broker authorization.
- PII minimization: raw lead data stays in GHL and Supabase; docs and FINDINGS carry patterns and paraphrases only.
- Secrets in env and managed stores only; `.mcp.json` and `.env` stay gitignored.

## 8. Phase mapping

- Done (per repo state): phases 1-6 (agent core, reconciler, escalation, channels, onboarding, mobile).
- Next: Phase 7 agency (AGY-01..03, multi-branch isolation) runs together with NURT-01..06, CTRL-01..06, GHL-01..06, PROV-01..02 as the Filipino Homes pilot track. GHL-05 (outcome correlation) is the recurring loop that turns live threads into framework updates.

## 9. Open items and risks

1. FH PIT in the current snippet is invalid; mint a fresh one with section 5.3 scopes.
2. Dealership thread scouting is pending: need fresh per-subaccount PITs or the dashboard behind the JWT table. The nurture plays above encode structure only; real openers, question order, recovery pairs, and cadences get appended from threads (FINDINGS.md sections 4-5 hold the query plan and template).
3. Duplicate-runtime risk on any account that runs old and new workflows side by side; PROV-02 plus a shutdown plan per branch.
4. Webhook pointing at the wrong runtime silently breaks replies; QA gate CTRL-06 covers it.
