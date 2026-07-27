# Phase 1: Agent Core & Demo UI - Context

**Gathered:** 2026-06-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 delivers a working Tagalog/Taglish AI sales agent running on LangGraph + LiteLLM, plus a split-screen demo web UI that shows a live conversation from both the lead's and business owner's perspectives. This is the proof-of-concept that validates conversation quality before any real channels (Messenger, SMS) are wired.

**Delivers:**
- LangGraph state machine with 7 conversation stages (intro → qualify → pitch → objection handling → propose appointment → confirm → escalate)
- LiteLLM Router: Groq/Llama 4 Maverick primary, Gemini Flash + Mistral fallbacks, YAML config with usage-based routing
- Tagalog system prompt with Taglish code-switching (mirrors the lead's language)
- Industry persona templates for dental, aesthetics, real estate — injected at runtime via Pydantic model + Jinja2
- Goal-directed escalation logic with hybrid signal detection
- FastAPI WebSocket server (ConnectionManager pattern)
- Vite + React split-screen demo UI with industry selector
- LangGraph PostgresSaver → Supabase Postgres (single persistence layer)

**Does NOT deliver:** real channels (Phase 4), business onboarding (Phase 5), appointment reconciler (Phase 2), mobile app (Phase 6).

</domain>

<decisions>
## Implementation Decisions

### SalesGPT Adoption Strategy
- **D-01:** Fork SalesGPT's repo structure and reuse its prompts, templates, and LiteLLM wiring — but rip out its internal stage detection state machine and replace with LangGraph from the ground up. ("Fork SalesGPT, replace internals")
- **D-02:** Keep as much SalesGPT Python code as still compiles after swapping the state machine. Evaluate each piece during implementation — no pre-commitment to keeping or discarding specific modules.
- **D-03:** SalesGPT source lives inside this repo in an `/agent` subdirectory. No git submodule.

### Demo UI Tech Stack
- **D-04:** Vite + React SPA in a `/frontend` directory. Connects to FastAPI exclusively via WebSocket (no REST API calls from the demo UI). Lightweight, no SSR complexity.
- **D-05:** Business owner panel (right side) shows: full conversation mirror (read-only), current lead status badge (new / qualifying / hot / booked), and escalation alert flash when triggered. Matches DEMO-02 spec exactly.
- **D-06:** Demo UI has an industry selector at startup. Choosing dental / aesthetics / real estate loads the corresponding persona (name, tone, system prompt template). Simulates the Phase 5 onboarding flow.

### Stage Transition Mechanism
- **D-07:** Hybrid transition model: explicit signals (booking intent phrases, escalation keywords) trigger state transitions via fast rules. Ambiguous transitions use an LLM stage-detection call. Balances cost vs correctness on Groq free tier rate limits.
- **D-08:** Bidirectional stage graph — LangGraph edges allow backward routing (e.g., `objection_handling` can route back to `pitch` after resolving, or back to `propose_appointment`). More natural Filipino conversation patterns.
- **D-09:** Escalation signals: explicit Taglish booking/price-inquiry phrases fire escalation immediately (rule). Ambiguous positive engagement uses a composite score: 2-of-3 required — (1) intent phrase, (2) positive sentiment in last 2 messages, (3) fast response cadence (<30s).

### Taglish Prompt + Persona Structure
- **D-10:** Industry persona uses a `BusinessProfile` Pydantic model (fields: `agent_name`, `business_name`, `industry`, `services`, `pricing`, `phone`). A Jinja2 template per industry renders the full system prompt at conversation start. Clean, testable, directly reusable in Phase 5 onboarding.
- **D-11:** Taglish code-switching handled via prompt instruction: "Respond in the same mix of Tagalog and English the lead uses. If they write in pure English, reply in English. If Taglish, match their register." LLM handles natively — no language detection library required.
- **D-12:** Each industry has a preset demo persona: dental → Ate Ana, aesthetics → Ate Bea, real estate → Kuya Marco. Selected via the demo UI industry dropdown. No hardcoded env-only config needed.

### Claude's Discretion
- Specific Taglish phrase list for escalation keywords — planner/implementer defines based on SalesGPT's existing signal list and common Filipino sales conversation patterns.
- Exact LangGraph edge map (which stages can transition to which) — implementer derives from SalesGPT's stage graph and the bidirectional constraint above.
- Vite + React project structure (component layout, folder conventions) — standard patterns apply.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — full project context, key decisions table, dependency versions (Context7-verified), LiteLLM YAML config, stack constraints
- `.planning/REQUIREMENTS.md` — v1 requirements with traceability to phases; AGENT-01 through DEMO-03 define Phase 1 scope

### External Libraries (verify via Context7 before installing)
- LangGraph (Python): Context7 ID `/websites/langchain_oss_python_langgraph` — state graph, PostgresSaver, conditional edges
- LiteLLM: Context7 ID `/websites/litellm_ai` — usage-based routing, YAML config, fallback chains
- FastAPI: Context7 ID `/websites/fastapi_tiangolo` — WebSocket, ConnectionManager pattern
- Supabase: Context7 ID `/supabase/supabase` — Postgres connection string for PostgresSaver

### SalesGPT Reference
- GitHub: `https://github.com/filip-michalsky/SalesGPT` — fork source; reuse prompts, stage definitions, LiteLLM wiring; replace state machine with LangGraph

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None yet — brand new project, no existing code.

### Established Patterns
- None yet — this phase establishes the foundational patterns.

### Integration Points
- Phase 1 establishes the baseline: LangGraph graph + FastAPI WebSocket + Supabase Postgres. All future phases wire into these three integration points.

</code_context>

<specifics>
## Specific Ideas

- **Persona names:** Ate Ana (dental), Ate Bea (aesthetics), Kuya Marco (real estate) — Filipino honorifics that feel natural for a sales agent persona.
- **SalesGPT adoption:** "Keep as much as compiles" — pragmatic, not prescriptive. The researcher should evaluate which SalesGPT classes survive the state machine swap.
- **Escalation scoring:** 2-of-3 composite (intent phrase + positive sentiment + fast cadence) — gives the agent room to escalate even when a lead doesn't say the exact booking phrase.
- **Demo UI industry selector:** designed to foreshadow Phase 5 onboarding UX — user picks industry, persona loads. Not just a demo convenience.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-Agent Core & Demo UI*
*Context gathered: 2026-06-11*
