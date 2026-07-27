# Phase 1: Agent Core & Demo UI - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-11
**Phase:** 1-Agent Core & Demo UI
**Areas discussed:** SalesGPT adoption strategy, Demo UI tech stack, Stage transition mechanism, Taglish prompt + persona structure

---

## SalesGPT Adoption Strategy

### Q1: How do we handle the SalesGPT vs LangGraph tension for the agent core?

| Option | Description | Selected |
|--------|-------------|----------|
| LangGraph-first, SalesGPT as reference | Build fresh on LangGraph; SalesGPT as prompts/ideas reference only | |
| Fork SalesGPT, retrofit LangGraph | Copy SalesGPT classes, wrap existing stage machine inside LangGraph nodes | |
| Fork SalesGPT, replace internals | Fork structure + reuse prompts/templates; rip out state machine, replace with LangGraph | ✓ |

**User's choice:** Fork SalesGPT, replace internals
**Notes:** Best of both — proven SalesGPT prompts + clean LangGraph architecture. Avoids maintaining two overlapping state systems.

---

### Q2: Which parts of SalesGPT to keep vs replace?

| Option | Description | Selected |
|--------|-------------|----------|
| Keep: prompts + stage definitions only | Port system prompts, stage names, objection templates only | |
| Keep: prompts, stages, and LiteLLM wiring | Port prompts, stages, and LiteLLM config (SalesGPT already uses LiteLLM) | |
| Keep as much as compiles | Whatever Python code survives the state machine swap; evaluate during implementation | ✓ |

**User's choice:** Keep as much as compiles
**Notes:** Pragmatic — don't pre-commit, evaluate each piece during implementation.

---

### Q3: Where does the SalesGPT fork live?

| Option | Description | Selected |
|--------|-------------|----------|
| Integrated into repo | SalesGPT source in /agent subdirectory of this repo | ✓ |
| Git submodule | Fork on GitHub as submodule | |
| You decide | Let planner pick structure | |

**User's choice:** Integrated into repo
**Notes:** Everything in one place, no submodule complexity.

---

## Demo UI Tech Stack

### Q1: What technology should the Phase 1 demo UI use?

| Option | Description | Selected |
|--------|-------------|----------|
| Vite + React SPA | Lightweight React app in /frontend, WebSocket to FastAPI | ✓ |
| Vanilla HTML + JS | Single HTML file, zero build tooling | |
| Next.js | Start production frontend (Phase 5) early | |

**User's choice:** Vite + React SPA
**Notes:** Lightweight, sets up React patterns for Phase 5 without Next.js overhead at demo stage.

---

### Q2: How should the demo UI connect to FastAPI?

| Option | Description | Selected |
|--------|-------------|----------|
| WebSocket only | All messages through the DEMO-01 WebSocket server | ✓ |
| WebSocket + REST API | WebSocket for chat, REST for status/metadata | |
| You decide | Let planner decide based on demo needs | |

**User's choice:** WebSocket only
**Notes:** Keeps it clean and consistent with the ConnectionManager pattern already decided.

---

### Q3: What should the business owner panel show?

| Option | Description | Selected |
|--------|-------------|----------|
| Live conversation + lead status + escalation badge | Full conversation mirror, status badge, escalation alert flash | ✓ |
| Summary only | AI-generated summary updated per exchange | |
| Both views with toggle | Switch between full conversation and summary | |

**User's choice:** Live conversation + lead status + escalation badge
**Notes:** Exact match to DEMO-02 spec. Demonstrates real-time visibility the business owner gets.

---

## Stage Transition Mechanism

### Q1: What drives stage transitions in the LangGraph conversation graph?

| Option | Description | Selected |
|--------|-------------|----------|
| LLM-based (like SalesGPT) | Separate LLM call classifies stage from conversation history | |
| Rule-based | Python rules: keyword/signal matching per stage | |
| Hybrid: LLM for ambiguous, rules for obvious | Clear signals use rules; ambiguous transitions use LLM | ✓ |

**User's choice:** Hybrid: LLM for ambiguous, rules for obvious
**Notes:** Balances cost (Groq free tier rate limits) vs correctness for Taglish code-switching.

---

### Q2: Can the agent move backward to earlier stages?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — bidirectional stage graph | LangGraph edges allow cycling (e.g., objection → back to pitch) | ✓ |
| No — linear progression only | Stages only advance forward | |
| You decide | Let planner define edge map from SalesGPT's stage graph | |

**User's choice:** Yes — bidirectional stage graph
**Notes:** More natural for Filipino conversation patterns; agent can re-propose after resolving objections.

---

### Q3: What signals trigger escalation (AGENT-05)?

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit booking intent phrases | Taglish phrases: 'gusto ko na mag-book', 'kailan pwede', etc. | |
| Composite score: intent + sentiment + cadence | 2-of-3: intent phrase + positive sentiment + fast cadence | |
| Both — explicit phrases override, score for ambiguous | Explicit phrases fire immediately; ambiguous uses composite score | ✓ |

**User's choice:** Both — explicit phrases override, score for ambiguous
**Notes:** Maps cleanly to the hybrid transition model. Explicit = 0-latency rule; ambiguous = scored.

---

## Taglish Prompt + Persona Structure

### Q1: How should the industry persona be structured and injected?

| Option | Description | Selected |
|--------|-------------|----------|
| Pydantic model → Jinja2 template | BusinessProfile model; industry Jinja2 template renders system prompt | ✓ |
| Flat Python dict → f-string | Simple dict + f-string per industry | |
| YAML persona file per industry | dental.yaml, aesthetics.yaml, etc. loaded at runtime | |

**User's choice:** Pydantic model → Jinja2 template
**Notes:** Clean, testable, directly extensible to Phase 5 onboarding data. Worth the slightly higher setup cost.

---

### Q2: How does the agent handle Taglish code-switching?

| Option | Description | Selected |
|--------|-------------|----------|
| Prompt instruction + mirror lead's language | System prompt instructs LLM to match lead's register | ✓ |
| Language detection per message | langdetect or similar; pass detected language as hint | |
| Always Taglish regardless | Consistent persona, may feel off if lead writes pure English | |

**User's choice:** Prompt instruction + mirror lead's language
**Notes:** LLM handles natively; no additional dependency. Simpler and appropriate.

---

### Q3: Agent persona name — fixed or configurable?

| Option | Description | Selected |
|--------|-------------|----------|
| Hardcoded demo personas per industry | Ate Ana (dental), Ate Bea (aesthetics), Kuya Marco (real estate) | |
| Configurable via env/config | Agent name set via .env or demo config JSON | |
| User picks at demo start (dropdown) | Industry selector in demo UI loads corresponding persona | ✓ |

**User's choice:** User picks at demo start (dropdown in UI)
**Notes:** Industry selector foreshadows Phase 5 onboarding UX — selecting dental/aesthetics/real estate loads the persona. Not just a demo convenience.

---

## Claude's Discretion

- Specific Taglish phrase list for escalation keywords — implementer defines from SalesGPT's signal list + Filipino sales patterns
- Exact LangGraph edge map (which stages can route to which) — derived from SalesGPT's stage graph + bidirectional constraint
- Vite + React project structure — standard conventions apply

## Deferred Ideas

None — discussion stayed within phase scope.
