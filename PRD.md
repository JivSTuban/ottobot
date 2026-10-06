# OttoBot x Filipinohomes: MVP PRD (combined)

**Version:** 3.0 (2026-10-06). Merges `docs/PRD-filipinohomes-mvp.md` v2.0 (Jiv/Gabe split, evidence-graded claims C1-C9) with the GHL record layer, nurture plays, controls, provisioning, and scouting status from the Mini session (MCP probe, Context7-checked GHL docs, Crowdsnare handoff docs). v2.0 sections are kept intact; additions are marked **[v3 new]**.
**Owners:** Jiv Tuban (agent, channels, compliance) and Gabe (surfaces, auth, data). Split in section 7.

---

## 1. Brief (one screen)

**What:** Pilot OttoBot as a Taglish first-responder and lead qualifier for Filipinohomes. A buyer inquiry gets a reply in seconds, is qualified on the fields a real-estate agent actually needs, and is handed to the right human agent with a summary and a proposed site-viewing slot.

**Why Filipinohomes:** they are a beta tester and potential partner, and their own agent directory publishes an "Inquiry Reply" time per agent. The fastest agents sit at about 10 to 48 minutes and the list falls to hours below that (C4, live page checked 2026-10-06, 12 of about 1,737 agents, method unstated). That is a public, measurable gap and our beta metric.

**What we ship:** one tenant (Filipinohomes), text only, three lead sources, two reply channels, handoff to human agents, an ops dashboard that proves the reply-time win. **[v3 new]** Plus a GHL record layer: every lead, thread state, booking, and handoff mirrored to one FH GHL subaccount, which doubles as the fallback send path and the source for outcome correlation.

**What we do not ship:** voice calls, a second customer, billing, agency multi-account (old Phase 7), the autoresearch loop (old Phase 8), calendar integrations, a built-in CRM (GHL is the record, not the product).

**Done means:** a real lead from a Filipinohomes source gets an AI first reply under 60 seconds (target, not researched), is qualified, and lands with an assigned agent who confirms a viewing, with every step visible in the dashboard and in GHL, and a consent and opt-out trail on record.

---

## 2. Who Filipinohomes is (verified vs not)

| Fact | Status |
|---|---|
| filipinohomes.com is a Cebu-based real-estate company led by founder and CEO Anthony Gerard O. Leuterio, active July 2026 | Confirmed (C1). Source is their own news site. Confirm it is your contact's company. |
| Hybrid: nationwide network of property specialists plus listings search and an agent directory. No legal entity named on the about page | Confirmed medium (C2). Portal vs brokerage is contested. |
| Size: "144 branches, 35,000 agents" (their news) vs "52 offices in 40 cities" (press, per verifier) | **Unverified, conflicting** (C3). Do not quote either. |
| Per-agent "Inquiry Reply" time and a "Sort by Fastest reply" | Confirmed medium (C4). |

Do not assume the agent base is a long tail of solo agents; that claim was refuted 0-3.

---

## 3. Users and jobs

| User | Job | MVP surface |
|---|---|---|
| Buyer or inquirer (Taglish, sometimes English, Bisaya **[unverified]**) | Get an answer now, without waiting for an agent | Messenger and SMS |
| Filipinohomes agent | Receive a qualified lead with context, confirm a viewing | Mobile app + push, web inbox |
| Filipinohomes ops/admin | See reply time, funnel, who is slow; control assignment | Web dashboard |
| Jiv and Gabe | Prove the win with numbers and keep the pilot safe | Metrics, audit log |

---

## 4. Current state (verified in the repo 2026-10-06)

- 144 backend tests pass on `feat/neon-clerk-mvp`. Phases 1 to 6 of v1 shipped.
- Real-estate persona exists but is thin: `agent/prompts/real_estate.j2` is 14 lines, with no qualification fields.
- Channels exist: Semaphore SMS (`/webhook/sms`, `api/main.py:556`), Messenger (`/webhook/facebook`, `:583`, `:600`), lead upload (`:633`), lead form (`:695`).
- **Single-tenant by environment variable:** all three webhooks read `BUSINESS_ID` and `DEFAULT_INDUSTRY` from env (`api/main.py:567`, `:609`, `:705`). One deployment serves one business.
- **Lead form handler will not work on real Meta traffic.** `/webhook/lead-form` reads `value.leads[].field_data` from the webhook body (`api/main.py:715`). Meta's leadgen webhook delivers a `leadgen_id`, and the lead data is fetched with a separate retrieval call (Meta doc, updated 2026-05-21, C8). Needs rework.
- **Escalation targets one owner** (push to a single token plus Resend email). Filipinohomes needs routing to a specific agent.
- AI disclosure: `agent/prompts/base.j2:2-8` discloses AI on inbound conversations and skips it on the outbound first message. This is the behavior fixed on 2026-07-27, and it is a decision to revisit (section 8, D3).
- Migration leftovers still on Supabase: `mobile/lib/supabase.ts` (stub), `mobile/app/(tabs)/settings.tsx`, `frontend/src/OnboardingWizard.tsx`, `tests/conftest.py`. Tasks 7 to 10 of `docs/superpowers/plans/2026-07-29-supabase-to-neon-clerk.md` cover them.
- Login design: the restrained redesign is not confirmed wired into `mobile/app/login.tsx`. Re-verify before Gabe starts G6.
- Design system (signal green, accent discipline) is defined in `docs/design/guardrails.md` and applies to every new screen.

**[v3 new]** GHL wiring status (verified live 2026-10-06): project `opencode.json` registers `ghl-mcp` (remote `https://services.leadconnectorhq.com/mcp/`, 36 tools). Handshake and `tools/list` succeed. The FH PIT at hand returns `Invalid Private Integration token` on all data calls, so no GHL read or write works yet. The repo has no GHL write-back path; agent outcomes currently land only in Neon. Sections 5 (GHL-01..06) and 9 (Q9) cover closing this.

**[v3 new]** Dealership pattern source (Crowdsnare handoff docs, verified 2026-10-06): the 13 scout locations are Crowdsnare client GHL subaccounts (Applewood x7, Bannister x2, Braby, Crowdsnare Canada, CS DBR, Gloria Cooper). Each carries its own PIT. Transferable patterns, not transcripts: speed-to-lead SMS, dormant reactivation with safe stops, outbound triage (interested / not / wrong-person / bought), Messenger qualify-and-route, outcome-triggered call follow-up. These shape NURT-01..06 and CTRL-01..04 below. Raw threads are still unscouted (section 9, Q9/Q10).

---

## 5. MVP scope

### P0 (pilot cannot start without these)

| ID | Requirement | Acceptance |
|---|---|---|
| RE-01 | Real-estate qualification: capture budget, preferred location, property type, pre-selling vs ready-for-occupancy, financing route (cash, bank, Pag-IBIG, in-house), OFW status, timeline, viewing availability | Fields stored per lead, shown in inbox, agent asks only what is missing, no field asked twice |
| RE-02 | Taglish and English replies that match the lead's register; "po/opo" mirroring kept | Eval set of 30 scripted conversations, pass rate recorded per model |
| LEAD-01 | Lead sources: Facebook Lead Ads (leadgen_id plus Graph fetch), inbound Messenger, inbound SMS, CSV upload | Each creates one deduped lead with `source` set |
| CH-01 | Tenant routing replaces `BUSINESS_ID` env: webhook resolves business from page id, number, or token | Two test tenants cannot see each other's leads |
| CH-02 | Messenger and SMS send/receive with Meta messaging-window rules respected | Out-of-window sends are blocked and logged, not silently dropped |
| HAND-01 | Handoff to the assigned human agent with summary, qualification card and proposed viewing slots | Agent gets push and sees the card; lead is told who follows up |
| HAND-02 | Agent roster and assignment rule (round robin or by location) | Admin imports agents from CSV and edits the rule |
| CONS-01 | Consent and notice: privacy notice in the first message or form, STOP/opt-out honored on every channel, audit log of consent and opt-out | Opt-out stops all sends within one turn; log is queryable |
| MET-01 | Metrics events: inquiry received, first AI reply, qualified, handed off, human first reply, viewing confirmed | Dashboard shows median first reply (AI vs human), funnel, per-agent table |
| AUTH-01 | Neon plus Clerk cutover finished, Supabase fully removed | `git grep -i supabase` returns docs and archive only |
| UI-01 | Web inbox, conversation view, agent roster, pilot dashboard; mobile pipeline and push | Follow `docs/design/guardrails.md`; reduced-motion safe |
| GHL-01 **[v3 new]** | FH subaccount PIT minted with `conversations.readonly`, `conversations/message.readonly`, `contacts.readonly`, `opportunities.readonly`, `locations.readonly`, `calendars.readonly` plus write scopes for send, tag, stage moves. Token in env only | MCP `conversations_search-conversation` returns live threads |
| GHL-02 **[v3 new]** | Agent outcomes written back to GHL: contact fields, tags, conversation status, opportunity stage; booking creates the calendar event within 60 s | Every Neon booking has a matching GHL event and stage |
| GHL-03 **[v3 new]** | Agent reads the full GHL thread before deciding, so it never asks twice | Spot-check: zero repeated qualification questions over 20 threads |
| GHL-04 **[v3 new]** | Manual takeover, stop/no-bump, booked cleanup, and triage tags enforced in both directions (GHL tag freezes agent; agent terminal state halts GHL follow-ups) | Takeover and terminal-state test sets pass 100% |

### P1 (build if P0 is green with time left)

- Viber Business sender (cost model in C5; needs a Philippines-registered sending entity or the rate is about 14x to 29x higher).
- Bisaya support, tested on a separate eval set.
- English admin copy pass for CRM (Task 10), keep agent-facing Tagalog.
- Weekly pilot report export (CSV).
- NURT-06 **[v3 new]**: dormant reactivation at 3/7/21 days with a fresh hook each time; never the same bump twice; terminal states halt it.
- GHL-05 **[v3 new]**: weekly outcome correlation joining booked viewings to originating threads; feeds the nurture framework with what actually worked.

### Out of scope for the MVP

Voice calling (unresearched, text first), WhatsApp, second tenant, billing, calendar sync, listing-aware recommendations from the portal catalog, auto-optimization loop, email channel.

---

## 6. Success metrics (pilot)

Baseline first, targets second. Targets below are design goals, not researched benchmarks.

| Metric | Baseline source | Pilot target |
|---|---|---|
| Median first reply time | Filipinohomes data, to be requested (public per-agent figures are 10 minutes to 15 hours, method unknown) | AI first reply under 60 s, measured by MET-01 |
| Inquiry to qualified rate | Not known | Report only in week 1, set target after |
| Qualified to viewing confirmed | Not known | Report only in week 1, set target after |
| Opt-out and complaint rate | None | Zero un-honored opt-outs |
| Agent handoff acceptance | None | Agents act on handoff within their stated SLA |
| GHL mirror lag **[v3 new]** | None | Booking to GHL event plus stage under 60 s |

---

## 7. Work split: Jiv 15+2 (proposal), Gabe 15

Sizing: S=1, M=2, L=3. Split follows the code boundary so the two streams rarely touch the same files. Assumption: Gabe's strengths are not yet confirmed; swap items if needed but keep the point balance. **[v3 new]** J8 is proposed at 2 pts for the GHL record layer; fold it into J3/J6 or accept 17/15 by agreement, do not silently inflate.

### Jiv: agent, channels, compliance (backend core)

| ID | Item | Pts | Files |
|---|---|---|---|
| J1 | Real-estate agent v2: qualification state, prompt, stage detection (RE-01, RE-02) | 3 | `agent/prompts/real_estate.j2`, `agent/state.py`, `agent/stage_detection.py`, `agent/graph.py` |
| J2 | Lead ingestion: Lead Ads leadgen fetch, CSV, dedupe (LEAD-01) | 2 | `api/main.py` webhooks, `api/channels.py` |
| J3 | Tenant routing, Messenger and SMS hardening, window rules (CH-01, CH-02) | 3 | `api/main.py`, `api/channels.py`, `api/db.py` |
| J4 | Handoff service: assignment, summary, push/SMS to agent (HAND-01 backend) | 2 | `api/escalation_service.py`, `api/main.py` |
| J5 | Consent, notice, opt-out, audit log (CONS-01) | 2 | `api/`, `agent/prompts/base.j2` |
| J6 | Metrics events table and `/metrics` endpoint (MET-01 backend) | 2 | `api/`, new migration |
| J7 | Model bake-off on the Taglish eval set (Llama 3.3 70B vs alternatives) | 1 | `evals/`, `litellm_config.yaml` |
| J8 **[v3 new]** | GHL record layer: PIT bootstrap, ingest webhook, write-back, thread read, takeover/tag sync (GHL-01..04) | 2 | `api/ghl.py` (new), `api/main.py`, `opencode.json` |

### Gabe: surfaces, auth, data

| ID | Item | Pts | Files |
|---|---|---|---|
| G1 | Finish Neon+Clerk code: plan Tasks 7, 8, 10 (settings to `/me/business`, `lib/api.ts` bearer helper, delete supabase stub, onboarding signup, English copy) | 3 | `mobile/`, `frontend/src/OnboardingWizard.tsx` |
| G2 | Provision Neon and Clerk, deploy, cutover (plan Task 9, AUTH-01) | 2 | infra, env, `scripts/` |
| G3 | Web inbox and conversation view with qualification card (UI-01) | 3 | `frontend/src/dashboard/`, new inbox |
| G4 | Agent roster import and assignment rule UI (HAND-02) | 2 | `frontend/src/` |
| G5 | Pilot dashboard: reply-time AI vs human, funnel, per-agent table, CSV (MET-01 UI) | 2 | `frontend/src/dashboard/` |
| G6 | Mobile: login, pipeline with new fields, push on handoff (UI-01) | 3 | `mobile/app/` |

### Contract between the two streams

Agree these in week 1 and freeze them in `docs/api-contract.md`: lead object (with the qualification fields), conversation message object, handoff payload, metrics event names, `/leads`, `/metrics` and `/agents` response shapes. Gabe builds against fixtures until the real endpoints land. **[v3 new]** Add the GHL write-back payload (contact fields, tags, stage, calendar event) to the same contract.

### Dependencies

- G2 (deploy) before J3 can be tested against a real tenant.
- J6 feeds G5. J4 feeds the push in G6.
- J1 and J7 are independent of everything else; start there.
- J8 needs the fresh PIT (section 9, Q9) before live verification, but builds against fixtures meanwhile.

### Proposed sequence (proposal, not researched)

| Week | Jiv | Gabe |
|---|---|---|
| 0 | Discovery call with the Filipinohomes contact (section 9) | Freeze contract, start G1 |
| 1 to 2 | J1, J7, J2 | G1, G2 |
| 3 to 4 | J3, J5, J6, J8 (fixtures) | G3, G4 |
| 5 | J4, J8 live verification | G5, G6 |
| 6 | Pilot on a small agent group, shadow mode first (AI drafts, human sends) | Same |

Shadow mode first is a deliberate safety choice: it produces reply-time and quality data before any real lead sees an AI message.

---

## 8. Decisions needed (with a default so work does not stall)

| # | Decision | Default until decided | Why it is open |
|---|---|---|---|
| D1 | Model for Taglish | Keep `groq/llama-3.3-70b-versatile`, bake off in J7 | FilBench and Batayan are NLP benchmarks on older models, not sales dialogue (C6). SEA-LION scored about 11 points below GPT-4o. Test, do not assume. |
| D2 | Text first, voice later | Text only | Voice was not researched. |
| D3 | AI disclosure policy | Disclose on inbound (current), send privacy notice and opt-out in the first outbound message, never claim to be human | NPC Advisory 2024-04 requires transparency about AI processing, not a "bot must announce itself" line (C7). Meta and Viber bot rules are unresearched. This conflicts with the earlier "never reveal AI" preference, so Jiv decides after the compliance check. |
| D4 | Reply channel priority | Messenger and SMS | Channel mix for PH buyers is **[unverified]**; Filipinohomes contact will tell us. |
| D5 | Tenant model | One business (Filipinohomes), many agents as handoff targets | Depends on whether each agent wants their own persona or number. |
| D6 | Sending entity | Filipinohomes brand, sent through our accounts | Viber domestic rate needs a PH-headquartered sender (C5). |
| D7 **[v3 new]** | GHL as record layer | Add the GHL mirror; direct send stays primary | Crowdsnare runs this exact loop in production across 13 subaccounts; the MCP is already wired and only the PIT is missing. Revisit if the FH contact forbids a third-party record. |

---

## 9. What still needs research

### A. Ask the Filipinohomes contact (web search cannot answer these)

| # | Question | Blocks |
|---|---|---|
| Q1 | How do leads reach agents today (on-site message, email, Lead Ads, calls)? Can they expose a webhook, API or email forward? | J2, LEAD-01 |
| Q2 | Monthly lead volume, and real inquiry-to-first-reply times across agents. Is the "Inquiry Reply" metric computed by the platform? | Section 6 baseline |
| Q3 | Which channels do their buyers actually use (Messenger, Viber, SMS, calls)? | D4 |
| Q4 | Who owns the Facebook Page and ad accounts, and can we get an app installed with `ADVERTISE` access (needs `lead_retrieval`, `pages_manage_metadata` and others, C8)? | J2 |
| Q5 | Which agents join the pilot, and how should assignment work? | HAND-02 |
| Q6 | Existing privacy notice and consent wording on their forms | CONS-01 |
| Q7 | Are leads handled on behalf of licensed brokers, and who supervises? | Section 9C |
| Q8 | Commercial terms: pilot free, paid, revenue share, partner path | Business model |
| Q9 **[v3 new]** | Fresh FH subaccount PIT (current token invalid); plus fresh per-subaccount PITs for any dealership threads we want to scout | J8, GHL-01, thread scouting |
| Q10 **[v3 new]** | Which dashboard minted the per-location JWT table (location_id, version, iat, sub)? Needed to query those 13 locations without per-subaccount PITs | Thread scouting |

### B. Run another deep-research pass (web can answer)

| # | Topic | Blocks |
|---|---|---|
| R1 | Meta Messenger policy for AI bots, 24-hour window and human-agent tag, outbound template rules | CH-02, D3 |
| R2 | Philippine SMS rules (NTC, telco registration, sender ID, Semaphore terms), consent for marketing SMS | CH-02, CONS-01 |
| R3 | Competitors and prior art: Lamudi, Dot Property and developer chat tools. No competitor price survived verification, and the Lamudi and botsatwork.ph price claims were refuted | Pricing, positioning |
| R4 | PH buyer qualification facts (Pag-IBIG rules, pre-selling terms, OFW process) from primary sources. The blog figures in the research file are unverified | RE-01 content |
| R5 | Current Taglish quality of Claude, Gemini, GPT and Llama on a sales-dialogue test, ideally our own eval | D1 |
| R6 **[v3 new]** | GHL conversation scouting method once Q9/Q10 land: search sort options, message paging, won-opportunity correlation for the 13 locations | NURT-01..06 content |

### C. Needs a lawyer or regulator source

- Does an AI qualifying and booking leads for licensed agents create PRC or DHSUD broker-licensing exposure? No usable source found (the DHSUD FAQ page was judged unreliable). Frame OttoBot as a tool acting for the licensed broker until told otherwise.

---

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| AI says something wrong about price or availability | Trust and legal | Agent never quotes a final price or availability; refers to the assigned agent. Shadow mode first. |
| Taglish quality below bar | Bad first impression | J7 bake-off, human handoff on low confidence, guardrails in `api/guardrails.py` |
| Messaging window or platform policy violation | Page or number banned | R1 and R2 before CH-02 goes live; block out-of-window sends |
| Single-tenant env config reaches production | Cross-tenant data leak | CH-01 is P0; add the two-tenant test |
| Lead Ads webhook design wrong | No leads arrive | J2 first, verified against a test form |
| Groq model IDs rot | Outage | Keep `_build_model_list` check; verify `/v1/models` before release (see FAILURES.md) |
| Partner expectations outrun a text-only MVP | Relationship | Section 1 non-goals shared with the contact in week 0 |
| PIT rotation kills the GHL layer **[v3 new]** | Silent mirror gap | Health check on GHL auth in J8; alert on 401, never fail the direct send path because the mirror is down |
| Duplicate runtimes on one account **[v3 new]** | Double replies | Shutdown plan per branch before pilot traffic; audit webhook targets |

---

## 11. Docs to update when this ships

`CLAUDE.md` (current state), `README.md` (env and run steps), `.env.example`, `docs/api-contract.md` (new), `docs/design/guardrails.md` (any new screen patterns). Obsidian `Projects/ottobot/` gets a pointer to this file and the decisions D1 to D7, not a copy.

## 12. Changelog

- v2.0 (2026-10-06, MacBook): MVP PRD with evidence grades C1-C9, 50/50 Jiv/Gabe split, decisions D1-D6.
- v3.0 (2026-10-06, Mini): merged GHL record layer (GHL-01..05, J8 proposal, D7), dealership-derived nurture and controls (NURT-01..06, GHL-04), provisioning notes, scouting status (Q9, Q10, R6), mirror-lag metric, rotation and duplicate risks. No thread content added; nothing unverified presented as fact.
