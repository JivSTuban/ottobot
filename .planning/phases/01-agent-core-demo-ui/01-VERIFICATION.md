---
phase: 01-agent-core-demo-ui
verified: 2026-06-15T12:00:00Z
status: human_needed
score: 16/16 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Run the full demo end-to-end: start uvicorn api.main:app with real SUPABASE_DB_URI + LLM API keys; open frontend dev server; select Dental (Ate Ana); send a Taglish message; observe token stream in LeadChat and stage badge update in OwnerPanel"
    expected: "Tokens stream into a blinking agent bubble; stage badge advances from 'Bago' to 'Tinatasa'; after 2-3 turns escalation logic can fire and HOT LEAD alert appears with role=alert"
    why_human: "Requires live Supabase Postgres connection, live LLM API keys, and a running browser to verify real-time WebSocket streaming, token accumulation, and stage badge visual updates"
  - test: "Verify that conversation state persists across WebSocket reconnect: send 3 messages, close the browser tab, reopen to the same /ws/{threadId} URL, and send another message"
    expected: "The conversation resumes from where it left off — the agent's next response is contextually aware of prior messages"
    why_human: "DEMO-03 persistence via AsyncPostgresSaver requires a live Supabase connection; MemorySaver unit tests prove the pattern but not the real Postgres path"
  - test: "Verify NPC 2024-04 AI disclosure appears in the very first agent message for each of the three personas (Ate Ana / Ate Bea / Kuya Marco)"
    expected: "First response contains 'AI assistant' phrase per base.j2 template; visible in LeadChat bubble"
    why_human: "check_ai_disclosure guardrail is unit-tested but the rendered intro prompt being injected as the first system message in a live LLM call cannot be verified without a real API call"
  - test: "Verify all three persona industry backgrounds (dental / aesthetics / real_estate) render as subtle panel backgrounds in IndustrySelector cards and split-screen panels"
    expected: "Each card shows an industry background image at ~15% opacity; selected industry background appears in both LeadChat and OwnerPanel headers"
    why_human: "Image rendering requires a browser; paths depend on frontend/public/images/ assets produced by Plan 02 (Gemini MCP) which is outside this verification scope"
  - test: "Verify escalation alert UX: trigger a 2-of-3 escalation signal sequence (booking phrase + positive sentiment) and observe OwnerPanel behavior"
    expected: "Red banner slides down with 'HOT LEAD — Tawagan na!' text; role=alert attribute is set; banner is visually prominent with destructive (#ef4444) background"
    why_human: "Visual animation (CSS slideDown, 200ms ease-in), color rendering, and screen-reader alert announcement require a browser with accessibility tooling"
---

# Phase 01: Agent Core + Demo UI — Verification Report

**Phase Goal:** Build the agent core (LangGraph + LiteLLM + FastAPI WebSocket) and a split-screen Vite + React demo UI demonstrating all three AI personas (Ate Ana / Ate Bea / Kuya Marco) with real-time Taglish conversation, stage progression, escalation alerts, and Supabase persistence.
**Verified:** 2026-06-15T12:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Python 3.12+ active; langgraph/litellm/fastapi pinned in pyproject.toml | VERIFIED | `pyproject.toml`: `requires-python = ">=3.12"`; exact pins langgraph==0.6.11, litellm==1.83.9, fastapi[standard]==0.128.8 |
| 2 | AsyncPostgresSaver import path resolves (`langgraph.checkpoint.postgres.aio`) | VERIFIED | `api/main.py` line 80: `from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver` inside lifespan; SUMMARY confirms import verified at install |
| 3 | ConversationState TypedDict with add_messages reducer and 7-stage STAGES Literal | VERIFIED | `agent/state.py`: `Annotated[list, add_messages]`, `STAGES = Literal["intro","qualify","pitch","objection_handling","propose_appointment","confirm","escalate"]` |
| 4 | BusinessProfile Pydantic model + DEMO_PROFILES with Ate Ana/Ate Bea/Kuya Marco (D-12) | VERIFIED | `agent/models.py`: BusinessProfile with pricing validator; DEMO_PROFILES dict with all three personas confirmed in code |
| 5 | Three Jinja2 persona templates extend base.j2 with NPC 2024-04 AI disclosure phrase | VERIFIED | `base.j2` line 3: "ako ay AI assistant"; dental/aesthetics/real_estate.j2 all exist and contain persona-specific content |
| 6 | LiteLLM Router singleton with Groq(rpm=30,tpm=6000)/Gemini(rpm=15)/Mistral + usage-based-routing-v2 | VERIFIED | `agent/llm.py`: rpm=30, tpm=6000 for Groq; `litellm_config.yaml`: routing_strategy=usage-based-routing-v2, rpm=30, tpm=6000 |
| 7 | escalation_scorer returns True iff 2-of-3 signals fire (BOOKING_PHRASES, POSITIVE_SENTIMENT_PHRASES, cadence) | VERIFIED | `agent/escalation.py`: 18 BOOKING_PHRASES, 20 POSITIVE_SENTIMENT_PHRASES, `sum([signal_1, signal_2, signal_3]) >= 2` logic present |
| 8 | StateGraph builder (AGENT-01) with agent_node + route_next_stage conditional edge; escalation checked first | VERIFIED | `agent/graph.py` 198 lines: StateGraph(ConversationState), agent_node async, route_next_stage sync, escalation_scorer called first at line 162, visit_count guard, D-08 bidirectional, MAX_HISTORY=20 |
| 9 | FastAPI app with @asynccontextmanager lifespan; AsyncPostgresSaver + checkpointer.setup() inside lifespan | VERIFIED | `api/main.py`: `@asynccontextmanager async def lifespan`, `async with AsyncPostgresSaver.from_conn_string(...)`, `await checkpointer.setup()` at line 85 |
| 10 | WebSocket /ws/{thread_id} route; thread_id validated as uuid4; non-uuid4 rejected | VERIFIED | `api/main.py`: `validate_thread_id` helper, close code 1008 for non-uuid4; `api/ws_handler.py`: handle_ws streams tokens via `astream(stream_mode="messages")` |
| 11 | type:token, type:state, type:system_alert events emitted over WebSocket | VERIFIED | `api/ws_handler.py`: `send_json({"type":"token"...})`, `send_json({"type":"state","stage","escalated"})`, `holding_message_429()` returns `{"type":"system_alert"}` |
| 12 | ConnectionManager + online guardrails (AI disclosure, BusinessProfile validation, 429 holding) | VERIFIED | `api/connection_manager.py` 26 lines; `api/guardrails.py` 69 lines with check_ai_disclosure, validate_business_profile_or_fallback, holding_message_429 |
| 13 | useWebSocket hook consumes token/state/system_alert; sends {text,industry} to /ws/{thread_id} | VERIFIED | `frontend/src/useWebSocket.ts`: discriminated union WsMessage, token appends, state finalizes streaming, system_alert 8s timer, send serializes {text,industry} |
| 14 | IndustrySelector with 3 persona cards + "Simulan" button; split-screen layout on selection | VERIFIED | `frontend/src/App.tsx`: crypto.randomUUID() threadId, IndustrySelector/LeadChat/OwnerPanel imported; IndustrySelector renders "Piliin ang Industry", 3 cards with avatarSrc/industrySrc/cardLabel |
| 15 | OwnerPanel stage badge with Tagalog labels + escalation alert role="alert" | VERIFIED | `frontend/src/OwnerPanel.tsx`: `role="alert"`, `className="escalation-alert"`, "HOT LEAD — Tawagan na!"; `frontend/src/types.ts`: stageToLeadStatus maps to "Bago"/"Tinatasa"/"HOT"/"Naka-book" |
| 16 | .env.example, litellm_config.yaml, pytest.ini, pyproject.toml all committed with required content | VERIFIED | .env.example: SUPABASE_DB_URI present; litellm_config.yaml: usage-based-routing-v2; pytest.ini: asyncio_mode=auto; pyproject.toml: packages=["agent","api"] |

**Score:** 16/16 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `agent/state.py` | ConversationState + STAGES | VERIFIED | 27 lines, exports both |
| `agent/models.py` | BusinessProfile + DEMO_PROFILES + make_env | VERIFIED | 94 lines, Ate Ana/Bea/Kuya Marco |
| `agent/llm.py` | LiteLLM Router singleton | VERIFIED | 52 lines, module-level `router` |
| `agent/escalation.py` | escalation_scorer + phrase lists | VERIFIED | 80 lines, 2-of-3 scorer |
| `agent/graph.py` | StateGraph builder + routing | VERIFIED | 198 lines, exported not compiled |
| `agent/stage_detection.py` | LLM stage classifier | VERIFIED | Exists, async functions |
| `agent/prompts/base.j2` | AI disclosure + Taglish instruction | VERIFIED | "ako ay AI assistant" confirmed |
| `agent/prompts/dental.j2` | Ate Ana dental template | VERIFIED | Extends base.j2 |
| `agent/prompts/aesthetics.j2` | Ate Bea aesthetics template | VERIFIED | Exists |
| `agent/prompts/real_estate.j2` | Kuya Marco real estate template | VERIFIED | Exists |
| `api/main.py` | FastAPI + lifespan + WebSocket route | VERIFIED | 121 lines, all key patterns |
| `api/ws_handler.py` | handle_ws streaming handler | VERIFIED | 132 lines, all 3 event types |
| `api/connection_manager.py` | ConnectionManager | VERIFIED | 26 lines |
| `api/guardrails.py` | 3 online guardrails | VERIFIED | 69 lines |
| `frontend/src/types.ts` | Stage/LeadStatus/Message/stageToLeadStatus | VERIFIED | All 4 exports present |
| `frontend/src/useWebSocket.ts` | WebSocket hook | VERIFIED | WsMessage discriminated union, all handlers |
| `frontend/src/IndustrySelector.tsx` | 3-card industry chooser | VERIFIED | Piliin ang Industry, Simulan, avatarSrc, industrySrc |
| `frontend/src/OwnerPanel.tsx` | Conv mirror + stage badge + escalation alert | VERIFIED | role=alert, HOT LEAD banner |
| `frontend/src/LeadChat.tsx` | Streaming chat + input | VERIFIED | .streaming-cursor, Send button |
| `frontend/src/App.tsx` | Top-level layout | VERIFIED | 40+ lines, crypto.randomUUID, split layout |
| `frontend/dist/index.html` | Production build | VERIFIED | Exists (63.56 KB gzip per SUMMARY) |
| `pyproject.toml` | Python project with pinned deps | VERIFIED | requires-python>=3.12, packages=["agent","api"] |
| `litellm_config.yaml` | Router YAML with usage-based-routing-v2 | VERIFIED | rpm=30, tpm=6000, routing_strategy confirmed |
| `pytest.ini` | asyncio_mode=auto | VERIFIED | Line 2: asyncio_mode=auto |
| `.env.example` | All env var templates | VERIFIED | SUPABASE_DB_URI, GROQ/GEMINI/MISTRAL/PHOENIX keys |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `api/main.py lifespan` | `agent/graph.py builder` | `builder.compile(checkpointer=checkpointer)` | WIRED | Line 86 of api/main.py |
| `api/main.py lifespan` | `os.environ["SUPABASE_DB_URI"]` | `AsyncPostgresSaver.from_conn_string` | WIRED | Line 82-83 of api/main.py |
| `api/ws_handler.py` | `api.main.compiled_graph` | `app_state.compiled_graph.astream` | WIRED | `import api.main as app_state` + `.astream(stream_mode="messages")` |
| `api/ws_handler.py` | `ws.send_json(type:token/state)` | WebSocket protocol | WIRED | Lines 84-86, 126-129 of ws_handler.py |
| `agent/graph.py` | `agent/llm.py router` | `from agent.llm import router` | WIRED | Confirmed in graph.py imports |
| `agent/graph.py` | `agent/escalation.py escalation_scorer` | `escalation_scorer(state)` at route_next_stage line 162 | WIRED | Checked first per T-04-03 |
| `agent/models.py` | `agent/prompts/{industry}.j2` | `env.get_template(f"{industry}.j2").render()` | WIRED | render_system_prompt in models.py |
| `frontend/src/useWebSocket.ts` | `api WebSocket /ws/{thread_id}` | `new WebSocket(url)` with url containing `/ws/` | WIRED | useWebSocket.ts confirmed |
| `frontend/src/App.tsx` | `frontend/src/assets/personas.ts PERSONA_ASSETS` | industry key lookup | WIRED | avatarSrc/industrySrc/cardLabel used in IndustrySelector |

---

### Behavioral Spot-Checks

| Behavior | Evidence | Status |
|----------|----------|--------|
| route_next_stage calls escalation_scorer first | `agent/graph.py` line 162: `if escalation_scorer(state): return "escalate"` before any other logic | PASS |
| visit_count guard prevents pitch/objection_handling loop | Conditional at vc["pitch"]>=3 + stage=="objection_handling" -> "propose_appointment" | PASS |
| uuid4 validation rejects non-uuid strings | `validate_thread_id` helper extracts uuid.UUID(str, version=4); ws close 1008 | PASS |
| 429 backoff dict prevents retry storm | `_429_backoff[thread_id] = time.time() + 30` in ws_handler.py | PASS |
| AI disclosure phrase present in base.j2 | `base.j2`: "ako ay AI assistant ni {{ agent_name }}" | PASS |
| Frontend build produces dist/index.html | `frontend/dist/index.html` exists | PASS |

---

### Requirements Coverage

| Requirement | Plans | Description | Status | Evidence |
|-------------|-------|-------------|--------|----------|
| AGENT-01 | 01-04 | LangGraph state machine 7 stages + bidirectional edges | SATISFIED | agent/graph.py StateGraph builder, route_next_stage, D-08 bidirectional, 9 tests GREEN |
| AGENT-02 | 01-03 | LiteLLM Router with Groq/Gemini/Mistral + usage-based routing | SATISFIED | agent/llm.py module-level Router, litellm_config.yaml, 5 tests GREEN |
| AGENT-03 | 01-03 | Taglish system prompt + AI disclosure | SATISFIED | base.j2 NPC 2024-04 phrase + Taglish code-switch instruction confirmed |
| AGENT-04 | 01-03 | Industry persona templates dental/aesthetics/real_estate | SATISFIED | 3 .j2 templates extend base.j2; DEMO_PROFILES with D-12 names |
| AGENT-05 | 01-03, 01-04, 01-05 | Goal-directed escalation scoring + routing + state event | SATISFIED | escalation_scorer 2-of-3 wired in route_next_stage first; type:state event sends `escalated` bool |
| DEMO-01 | 01-05, 01-06 | FastAPI WebSocket ConnectionManager + real-time bidirectional chat | SATISFIED | api/main.py WebSocket route, ConnectionManager, useWebSocket hook wired |
| DEMO-02 | 01-06 | Split-screen UI: LeadChat + OwnerPanel + stage badge + escalation alert | SATISFIED | All components implemented; 26 frontend tests GREEN; production build exists |
| DEMO-03 | 01-05 | AsyncPostgresSaver -> Supabase Postgres persistence | SATISFIED (unit) | lifespan pattern wired; MemorySaver unit tests pass; live Supabase path requires human verification |

---

### Anti-Patterns Found

| File | Pattern | Severity | Assessment |
|------|---------|----------|------------|
| `agent/models.py` lines 62/70/78 | `phone="+63917XXXXXXX"` placeholder values | Info | Intentional demo data — DEMO_PROFILES are hardcoded demo fixtures, not production data; not a stub |
| `api/main.py` line 89 | Comment: "compiled_graph becomes invalid after this point" | Info | Informational comment noting lifespan constraint; not a debt marker |

No TBD, FIXME, or XXX markers found in any phase-modified files.

---

### Human Verification Required

#### 1. End-to-end live demo with real API keys

**Test:** Start `uvicorn api.main:app` with SUPABASE_DB_URI + LLM keys; open frontend dev server; select Dental; send a Taglish message.
**Expected:** Tokens stream into a blinking agent bubble in LeadChat; stage badge in OwnerPanel advances from "Bago"; after booking-phrase trigger HOT LEAD alert appears.
**Why human:** Requires live Supabase Postgres, live LLM API keys, and a browser to verify real-time WebSocket token streaming and visual stage badge transitions.

#### 2. Supabase persistence across reconnect (DEMO-03 live path)

**Test:** Send 3 messages with a specific threadId; close tab; reconnect to same /ws/{threadId}; send another message.
**Expected:** Agent response is contextually aware of prior conversation history loaded from Supabase checkpointer.
**Why human:** AsyncPostgresSaver lifespan pattern is unit-tested with MemorySaver shim; real Postgres path requires a live Supabase project.

#### 3. NPC 2024-04 AI disclosure in live first message

**Test:** Trigger first turn for each persona (Ate Ana / Ate Bea / Kuya Marco) and read the first agent response.
**Expected:** Each intro response includes "AI assistant" phrase in visible text.
**Why human:** check_ai_disclosure guardrail is unit-tested; verifying the phrase appears in the actual LLM output requires a live API call.

#### 4. Persona images visual rendering

**Test:** Open IndustrySelector in browser; check that dental/aesthetics/real_estate cards show the industry background images and persona avatars.
**Expected:** Images load from `/images/personas/*.png` and `/images/industries/*.png`; subtle opacity overlay visible.
**Why human:** Image rendering requires a browser; public/ image assets are produced by Plan 02 (Gemini MCP) and not part of this code verification scope.

#### 5. Escalation alert visual UX

**Test:** Trigger 2-of-3 escalation signals (booking phrase + positive sentiment) in a live conversation.
**Expected:** Red (#ef4444) banner slides down in OwnerPanel with "HOT LEAD — Tawagan na!"; CSS slideDown animation is smooth (200ms ease-in); role="alert" fires screen reader.
**Why human:** CSS animation and accessibility announcement require a browser with accessibility tooling.

---

### Gaps Summary

No automated gaps found. All 16 must-have truths are VERIFIED in the codebase. All 8 requirement IDs (AGENT-01 through AGENT-05, DEMO-01 through DEMO-03) have substantive, wired implementation. Five items require human verification with a live environment (Supabase + API keys + browser).

---

_Verified: 2026-06-15T12:00:00Z_
_Verifier: Claude (gsd-verifier)_
