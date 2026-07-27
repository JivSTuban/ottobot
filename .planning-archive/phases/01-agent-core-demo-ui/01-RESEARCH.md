# Phase 1: Agent Core & Demo UI - Research

**Researched:** 2026-06-11
**Domain:** LangGraph stateful conversational agent + LiteLLM router + FastAPI WebSocket + Vite+React split-screen UI + Supabase Postgres persistence
**Confidence:** HIGH (all stack decisions locked in CONTEXT.md; AI-SPEC provides verified code patterns; version flags confirmed via PyPI/npm registry)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Fork SalesGPT's repo structure and reuse its prompts, templates, and LiteLLM wiring — but rip out its internal stage detection state machine and replace with LangGraph from the ground up.
- **D-02:** Keep as much SalesGPT Python code as still compiles after swapping the state machine. Evaluate each piece during implementation — no pre-commitment.
- **D-03:** SalesGPT source lives inside this repo in an `/agent` subdirectory. No git submodule.
- **D-04:** Vite + React SPA in a `/frontend` directory. Connects to FastAPI exclusively via WebSocket (no REST API calls from the demo UI).
- **D-05:** Business owner panel (right side) shows: full conversation mirror (read-only), current lead status badge (new / qualifying / hot / booked), and escalation alert flash when triggered.
- **D-06:** Demo UI has an industry selector at startup loading dental/aesthetics/real estate persona.
- **D-07:** Hybrid transition model: explicit signals (booking intent phrases, escalation keywords) trigger state transitions via fast rules. Ambiguous transitions use an LLM stage-detection call.
- **D-08:** Bidirectional stage graph — LangGraph edges allow backward routing (e.g., `objection_handling` can route back to `pitch`).
- **D-09:** Escalation signals: explicit Taglish booking/price-inquiry phrases fire escalation immediately (rule). Ambiguous positive engagement uses a composite score: 2-of-3 required — (1) intent phrase, (2) positive sentiment in last 2 messages, (3) fast response cadence (<30s).
- **D-10:** Industry persona uses a `BusinessProfile` Pydantic model. A Jinja2 template per industry renders the full system prompt at conversation start.
- **D-11:** Taglish code-switching handled via prompt instruction only — no language detection library.
- **D-12:** Each industry has a preset demo persona: dental → Ate Ana, aesthetics → Ate Bea, real estate → Kuya Marco.

### Claude's Discretion

- Specific Taglish phrase list for escalation keywords
- Exact LangGraph edge map (which stages can transition to which)
- Vite + React project structure (component layout, folder conventions)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AGENT-01 | LangGraph state machine with 7 conversation stages | AI-SPEC Section 3 provides complete StateGraph pattern with `ConversationState` TypedDict and edge routing |
| AGENT-02 | LiteLLM Router: Groq primary, Gemini Flash + Mistral fallbacks, YAML config, usage-based routing | AI-SPEC Section 3 and `litellm_config.yaml` in PROJECT.md — critical version pin required (see Version Warning below) |
| AGENT-03 | Tagalog system prompt with Taglish code-switching | AI-SPEC Section 4b.3 provides prompt separation pattern; Jinja2 templates per industry |
| AGENT-04 | Industry persona templates for dental, aesthetics, real estate — runtime injection | AI-SPEC Section 4b.1 provides `BusinessProfile` Pydantic model and `render_system_prompt()` |
| AGENT-05 | Goal-directed escalation logic — hot lead signal detection | AI-SPEC D-09 composite scoring; `agent/escalation.py` lives outside the graph as a routing function |
| DEMO-01 | FastAPI WebSocket server using ConnectionManager pattern | AI-SPEC Section 4 `ws_handler.py` pattern; FastAPI lifespan for checkpointer init |
| DEMO-02 | Split-screen web UI — lead chat left, business owner panel right | Vite + React; WebSocket-only (D-04); owner panel shows stage/escalation state from graph |
| DEMO-03 | LangGraph PostgresSaver → Supabase Postgres | AI-SPEC Section 4b.2 lifespan pattern; `AsyncPostgresSaver.from_conn_string()` |

</phase_requirements>

---

## Summary

Phase 1 builds the complete foundation of OttoBot: a stateful LangGraph agent with 7 bidirectional conversation stages, a LiteLLM router fallback chain, a FastAPI WebSocket server, and a Vite+React split-screen demo UI. All four subsystems are new — there is no existing codebase. The AI-SPEC (01-AI-SPEC.md) is the authoritative technical reference and was written by a specialist researcher; its code patterns should be treated as the implementation target.

**Critical version discrepancy discovered:** The AI-SPEC references `langgraph==1.2.4` and `langgraph-checkpoint-postgres==3.1.0` / `4.1.0`, but PyPI's current latest versions are `langgraph==0.6.11` and `langgraph-checkpoint-postgres==2.0.25`. These version numbers in the AI-SPEC do not exist on PyPI — they appear to be forward projections or errors. The planner must pin to the highest available PyPI versions and use those consistently. The import path `langgraph.checkpoint.postgres.aio.AsyncPostgresSaver` should still be verified against the installed package before use. [ASSUMED — verified langgraph==0.6.11 and langgraph-checkpoint-postgres==2.0.25 exist on PyPI via `pip3 index versions`; AI-SPEC version numbers 1.2.4 / 3.1.0 / 4.1.0 do NOT exist on PyPI as of 2026-06-11]

**Primary recommendation:** Follow the AI-SPEC code patterns exactly, but pin langgraph to `0.6.11` and langgraph-checkpoint-postgres to `2.0.25`. Wave 0 of the plan must include a version resolution task that confirms `AsyncPostgresSaver` import path against installed package before any other implementation begins.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Conversation state machine (7 stages) | Python Backend (LangGraph) | — | LangGraph `StateGraph` owns stage transitions and persistence; no state in FastAPI memory |
| LLM calls + fallback routing | Python Backend (LiteLLM Router) | — | Router singleton with usage-based-routing-v2; never per-request instantiation |
| System prompt rendering (Jinja2 + Pydantic) | Python Backend (agent node) | — | Rendered once at intro stage; stored in messages list; checkpointer preserves it |
| Escalation signal scoring | Python Backend (escalation.py) | — | Pure function called in edge routing; 2-of-3 composite before LLM stage-detection |
| WebSocket connection management | Python Backend (FastAPI ConnectionManager) | — | Official FastAPI pattern; ConnectionManager tracks active sessions |
| Real-time token streaming to UI | Python Backend (astream stream_mode="messages") | Browser | LangGraph streams token chunks; FastAPI fans out to WebSocket |
| Lead chat interface | Browser (React) | — | Vite + React SPA; WebSocket-only transport (D-04) |
| Business owner panel | Browser (React) | — | Reads stage/escalation from WebSocket `type: state` events; no separate API |
| Conversation persistence | Database (Supabase Postgres via AsyncPostgresSaver) | — | Every state transition checkpointed; thread_id = lead UUID |
| Industry selector / persona loading | Browser (React) → Python Backend | — | Industry selector sends `industry` field in first WebSocket message; backend injects BusinessProfile |

---

## Standard Stack

### Core (Python Backend)

| Library | Version (PyPI actual) | Purpose | Why Standard |
|---------|----------------------|---------|--------------|
| langgraph | 0.6.11 | Stateful conversation graph, `astream`, `aget_state` | Native PostgresSaver + bidirectional edges (D-08) |
| langgraph-checkpoint-postgres | 2.0.25 | `AsyncPostgresSaver` for Supabase persistence | Single persistence layer per DEMO-03 |
| litellm | 1.83.9 | LLM router with Groq/Gemini/Mistral fallbacks | YAML config + usage-based-routing-v2; per PROJECT.md |
| fastapi[standard] | 0.128.8 | WebSocket server + ConnectionManager | Official ConnectionManager pattern for DEMO-01 |
| uvicorn[standard] | >=0.34.0 | ASGI server | Required by FastAPI |
| pydantic | >=2.9.0,<3 | BusinessProfile model + StageDetectionOutput | Field validation at instantiation; StrictUndefined companion |
| jinja2 | >=3.1.0 | Industry system prompt templates | `StrictUndefined` catches missing BusinessProfile fields early |
| psycopg[binary,pool] | 3.2.13 | PostgresSaver requires psycopg v3 | `AsyncPostgresSaver` requires async psycopg |
| python-dotenv | >=1.0.0 | Env var loading | Standard |

[VERIFIED: PyPI] — versions confirmed via `pip3 index versions` on 2026-06-11.

**VERSION WARNING — AI-SPEC pin mismatch:**
The AI-SPEC installation block specifies `langgraph==1.2.4`, `langgraph-checkpoint-postgres==3.1.0`, and `litellm==1.88.1`. As of 2026-06-11, PyPI shows:
- `langgraph`: max available = `0.6.11` (1.2.4 does not exist)
- `langgraph-checkpoint-postgres`: max available = `2.0.25` (3.1.0 does not exist)
- `litellm`: max available = `1.83.9` (1.88.1 does not exist)

Pin to the actual available versions above. The AI-SPEC's code patterns remain valid — only the version numbers are wrong.

### Core (Frontend)

| Library | Version (npm actual) | Purpose | Why Standard |
|---------|---------------------|---------|--------------|
| vite | 8.0.16 | Build tool for SPA | Locked by D-04 |
| react | 19.2.7 | UI framework | Locked by D-04 |
| react-dom | 19.2.7 | DOM renderer | Paired with React |
| typescript | 6.0.3 | Type safety | Standard; PROJECT.md specifies TS |
| @vitejs/plugin-react | 6.0.2 | Vite React plugin | Required for Vite + React setup |

[VERIFIED: npm registry] — versions confirmed via `npm view` on 2026-06-11.

### Supporting (Python Backend)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| arize-phoenix | 12.15.1 | LLM tracing + LLM judge orchestration | Eval flywheel per AI-SPEC Section 5 |
| openinference-instrumentation-langchain | latest | LangGraph trace instrumentation | Connects LangGraph spans to Phoenix |
| opentelemetry-sdk | latest | Trace export | Required by Phoenix OTLP exporter |
| promptfoo | latest (npm CLI) | CI/CD prompt regression | AI-SPEC Section 5 eval setup |
| instructor | latest | Structured output from LiteLLM Router | StageDetectionOutput extraction; verify Router patching in installed version |

[ASSUMED] — arize-phoenix 12.15.1 confirmed on PyPI; instructor Router compatibility requires verification at install time.

### Installation

```bash
# Python backend — pin these exact versions
pip install \
  "langgraph==0.6.11" \
  "langgraph-checkpoint-postgres==2.0.25" \
  "psycopg[binary,pool]>=3.2.0,<4" \
  "litellm==1.83.9" \
  "fastapi[standard]==0.128.8" \
  "uvicorn[standard]>=0.34.0" \
  "pydantic>=2.9.0,<3" \
  "jinja2>=3.1.0" \
  "python-dotenv>=1.0.0" \
  "arize-phoenix" \
  "openinference-instrumentation-langchain" \
  "opentelemetry-sdk" \
  "opentelemetry-exporter-otlp"

# Frontend — Vite + React + TypeScript scaffold
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install
```

---

## Package Legitimacy Audit

| Package | Registry | Verdict | Disposition |
|---------|----------|---------|-------------|
| langgraph | PyPI | OK | Approved — LangChain project, major framework |
| langgraph-checkpoint-postgres | PyPI | OK | Approved — official LangChain checkpoint package |
| litellm | PyPI | OK | Approved — BerriAI project, 1M+ weekly downloads |
| fastapi | PyPI | OK | Approved — Tiangolo project, industry standard |
| pydantic | PyPI | OK | Approved — core Python ecosystem |
| jinja2 | PyPI | OK | Approved — Pallets project, decade-old |
| psycopg | PyPI | OK | Approved — PostgreSQL adapter, standard |
| arize-phoenix | PyPI | OK | Approved — Arize AI project, open-source |
| vite | npm | OK | Approved — Evan You / VoidZero, industry standard |
| react | npm | OK | Approved — Meta, industry standard |
| instructor | PyPI | OK | Approved — Jason Liu project, widely used |

**Packages removed due to SLOP verdict:** none
**Packages flagged as suspicious:** none

*AI-SPEC version numbers for langgraph (1.2.4), langgraph-checkpoint-postgres (3.1.0 / 4.1.0), and litellm (1.88.1) do not exist on PyPI — treat as `[ASSUMED]` training-data artifacts; use actual PyPI versions above.*

---

## Architecture Patterns

### System Architecture Diagram

```
Lead Browser                FastAPI WebSocket Server              Supabase Postgres
  [Chat UI]  ←— WS tokens ←  ConnectionManager                        │
  [Send msg] ——WS message——→  ws_handler.py                            │
                                    │                                   │
                              compiled_graph.astream()                  │
                                    │                                   │
                              LangGraph StateGraph ←——checkpoint———→  AsyncPostgresSaver
                              [intro]→[qualify]→[pitch]                 │ (thread_id = lead UUID)
                              [obj_handling]↔[pitch]                    │
                              [propose_appt]→[confirm]→[escalate]       │
                                    │
                              agent_node (LLM call)
                                    │
                              LiteLLM Router
                              [Groq/Llama4 primary rpm=30]
                              [Gemini Flash fallback rpm=15]
                              [Mistral fallback]
                                    │
                              escalation.py (2-of-3 scorer)
                              route_next_stage (hybrid rule+LLM)
                                    │
                              state update → WS send_json(type:"state")
                                    ↓
Owner Browser               Business Owner Panel
  [conv mirror]  ←———————— WebSocket type:"state" events
  [lead badge]              stage / escalated fields
  [alert flash]
```

### Recommended Project Structure

```
ottobot/
├── agent/
│   ├── graph.py              # StateGraph definition, node functions, edge routing
│   ├── state.py              # ConversationState TypedDict + stage Literal type
│   ├── llm.py                # LiteLLM Router singleton (loaded once at startup)
│   ├── prompts/
│   │   ├── base.j2           # Base Taglish system prompt template
│   │   ├── dental.j2         # Ate Ana persona
│   │   ├── aesthetics.j2     # Ate Bea persona
│   │   └── real_estate.j2    # Kuya Marco persona
│   ├── models.py             # BusinessProfile Pydantic model + StageDetectionOutput
│   └── escalation.py         # 2-of-3 composite escalation scorer (D-09)
├── api/
│   ├── main.py               # FastAPI app + lifespan (checkpointer init) + ConnectionManager
│   └── ws_handler.py         # compiled_graph.astream() → WebSocket token fan-out
├── frontend/                 # Vite + React split-screen demo UI (vite create scaffold)
│   ├── src/
│   │   ├── App.tsx            # Split-screen layout
│   │   ├── LeadChat.tsx       # Left panel: lead input + message stream
│   │   ├── OwnerPanel.tsx     # Right panel: conv mirror + stage badge + escalation alert
│   │   └── useWebSocket.ts    # WebSocket hook: handles token/state message types
├── evals/
│   ├── promptfoo.yaml         # CI/CD prompt regression tests
│   ├── judge_config.py        # Arize Phoenix LLM judge templates
│   └── check_thresholds.py    # Fail CI if pass rate < 90%
├── litellm_config.yaml        # Router config (from PROJECT.md)
├── tests/
│   └── test_stage_routing.py  # Unit tests for hybrid transition + escalation logic
└── pyproject.toml
```

### Pattern 1: AsyncPostgresSaver with FastAPI Lifespan

**What:** The checkpointer must be created and torn down within an async context manager tied to FastAPI's lifespan. The compiled graph is stored as a module-level variable, set during startup.

**When to use:** Every FastAPI app that uses LangGraph with AsyncPostgresSaver.

```python
# Source: AI-SPEC Section 4b.2 (01-AI-SPEC.md)
from contextlib import asynccontextmanager
from fastapi import FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from agent.graph import builder

compiled_graph = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global compiled_graph
    async with AsyncPostgresSaver.from_conn_string(
        os.environ["SUPABASE_DB_URI"]
    ) as checkpointer:
        await checkpointer.setup()   # idempotent — runs pending migrations
        compiled_graph = builder.compile(checkpointer=checkpointer)
        yield
    # checkpointer connection closes here

app = FastAPI(lifespan=lifespan)
```

### Pattern 2: WebSocket ConnectionManager with Token Streaming

**What:** A ConnectionManager class tracks active WebSocket connections. The ws_handler streams LangGraph token chunks to the lead and sends full state to the owner panel after stream completes.

**When to use:** DEMO-01 and DEMO-02.

```python
# Source: AI-SPEC Section 4 (01-AI-SPEC.md)
async def handle_ws(websocket: WebSocket, thread_id: str):
    await websocket.accept()
    config = {"configurable": {"thread_id": thread_id}}

    async for ws_message in websocket.iter_json():
        user_text = ws_message["text"]
        async for chunk, metadata in compiled_graph.astream(
            {"messages": [{"role": "user", "content": user_text}]},
            config=config,
            stream_mode="messages",
        ):
            if hasattr(chunk, "content") and chunk.content:
                await websocket.send_json({
                    "type": "token",
                    "content": chunk.content,
                    "node": metadata.get("langgraph_node"),
                })
        final_state = await compiled_graph.aget_state(config)
        await websocket.send_json({
            "type": "state",
            "stage": final_state.values.get("stage"),
            "escalated": final_state.values.get("escalated", False),
        })
```

### Pattern 3: Hybrid Stage Routing (D-07)

**What:** Edge routing function checks fast rules first (explicit Taglish booking phrases → escalate), then falls back to LLM stage detection for ambiguous transitions.

**When to use:** `route_next_stage` conditional edge in the LangGraph builder.

```python
# Source: AI-SPEC Section 3 (01-AI-SPEC.md) + D-07/D-09
def route_next_stage(state: ConversationState) -> str:
    # 1. Escalation scorer first (D-09) — fast, no LLM call
    if escalation_scorer(state):
        return "escalate"
    # 2. Explicit booking phrases (fast rule)
    last_msg = state["messages"][-1].content if state["messages"] else ""
    booking_phrases = ["gusto ko mag-book", "i-book na", "puwede ba bukas",
                       "magkano", "schedule", "slot", "available"]
    if any(p in last_msg.lower() for p in booking_phrases):
        return "escalate"
    # 3. LLM stage detection for ambiguous transitions
    return llm_detect_stage(state)  # returns stage name string
```

### Pattern 4: BusinessProfile + Jinja2 System Prompt (D-10)

**What:** `BusinessProfile` Pydantic model validated at industry selection. `render_system_prompt()` uses Jinja2 `StrictUndefined` so missing fields raise immediately inside the node.

```python
# Source: AI-SPEC Section 4b.1 (01-AI-SPEC.md)
from pydantic import BaseModel, Field
from jinja2 import Environment, FileSystemLoader, StrictUndefined

class BusinessProfile(BaseModel):
    agent_name: str
    business_name: str
    industry: str  # "dental" | "aesthetics" | "real_estate"
    services: list[str]
    pricing: str = Field(..., description="e.g. 'P500-P1500'. Never None.")
    phone: str

    def render_system_prompt(self, env: Environment) -> str:
        template = env.get_template(f"{self.industry}.j2")
        return template.render(**self.model_dump())  # StrictUndefined raises on missing fields

# DEMO personas (D-12)
DEMO_PROFILES = {
    "dental": BusinessProfile(agent_name="Ate Ana", business_name="Smile Dental Clinic",
        industry="dental", services=["dental cleaning", "whitening"], pricing="P500-P2500", phone="+63917XXXXXXX"),
    "aesthetics": BusinessProfile(agent_name="Ate Bea", business_name="Bea Aesthetics Studio",
        industry="aesthetics", services=["facial", "whitening"], pricing="P800-P3000", phone="+63918XXXXXXX"),
    "real_estate": BusinessProfile(agent_name="Kuya Marco", business_name="Marco Realty",
        industry="real_estate", services=["condo tours", "property listing"], pricing="varies", phone="+63919XXXXXXX"),
}
```

### Anti-Patterns to Avoid

- **Sync PostgresSaver in async context:** Using `from langgraph.checkpoint.postgres import PostgresSaver` (sync) inside FastAPI causes blocking calls on the event loop — use `langgraph.checkpoint.postgres.aio.AsyncPostgresSaver` always.
- **Router instantiated per-request:** `litellm.Router(...)` must be a module-level singleton in `agent/llm.py` — it holds connection pools and usage counters. Per-request instantiation loses rate-limit tracking, defeating `usage-based-routing-v2`.
- **`asyncio.run()` inside FastAPI route:** Raises `RuntimeError: This event loop is already running`. All LangGraph calls inside FastAPI must be `await`-ed directly.
- **Bidirectional edges without visit_count guard:** Without a `visit_count` field in `ConversationState` and max-visits check in routing, backward edges (objection_handling → pitch) can create infinite loops when the LLM stage detector keeps returning the same stage.
- **Jinja2 without StrictUndefined:** Using the default `Undefined` class silently renders `None` or empty string for missing fields. Use `Environment(undefined=StrictUndefined)` so errors surface at render time (inside the node), not mid-conversation as empty text.
- **`instructor.patch(router)` — verify compatibility:** The AI-SPEC recommends `instructor.patch(router)` for structured output from LiteLLM Router. This must be verified at install time — if it fails, fall back to direct JSON mode: `response_format={"type": "json_object"}` + `StageDetectionOutput.model_validate_json(...)`.
- **WebSocket connection ID as thread_id:** The WebSocket connection ID changes on reconnect. The `thread_id` must be the lead's persistent UUID — otherwise conversation state is lost on page reload, breaking DEMO-03.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Conversation state persistence | Custom Redis/DB checkpointing | `AsyncPostgresSaver` | Schema versioning, migration tracking, time-travel debugging built in |
| LLM fallback / rate-limit routing | Custom retry logic with provider if/else | `litellm.Router` with `usage-based-routing-v2` | RPM/TPM tracking per model, fallback chains, in-memory caching |
| Structured output extraction from LLM | Regex or manual JSON parsing | `instructor` + Pydantic or `response_format=json_object` + `model_validate_json()` | Automatic retry on ValidationError; type-safe extraction |
| WebSocket real-time streaming | Long-polling or SSE workaround | LangGraph `astream(stream_mode="messages")` | Native token-chunk streaming; integrates with graph lifecycle |
| Taglish language detection | langdetect or custom classifier | Prompt instruction only (D-11) | LLM handles code-switching natively; added dependency with no measurable accuracy gain |
| Stage transition logic | Full LLM call on every turn | Hybrid rule (fast) + LLM for ambiguous (D-07) | Groq free tier RPM/TPM exhausted quickly by per-turn classification calls |

---

## Runtime State Inventory

This is a greenfield project — no existing runtime state exists. All five categories are empty by definition.

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | None — brand new project | None |
| Live service config | None — no deployed services | None |
| OS-registered state | None | None |
| Secrets/env vars | None yet — `.env` will be created in Wave 0 | Create `.env` with `GROQ_API_KEY`, `GEMINI_API_KEY`, `MISTRAL_API_KEY`, `SUPABASE_DB_URI` |
| Build artifacts | None | None |

---

## Common Pitfalls

### Pitfall 1: LangGraph / langgraph-checkpoint-postgres Version Mismatch

**What goes wrong:** The AI-SPEC references version numbers (langgraph 1.2.4, langgraph-checkpoint-postgres 3.1.0) that do not exist on PyPI as of 2026-06-11. Installing these pins will fail immediately.

**Why it happens:** AI-SPEC was written with forward-projected version numbers or training-data artifacts.

**How to avoid:** Pin to `langgraph==0.6.11` and `langgraph-checkpoint-postgres==2.0.25` (confirmed on PyPI). Verify `AsyncPostgresSaver` import path against the installed version before any other implementation.

**Warning signs:** `pip install langgraph==1.2.4` returns `ERROR: No matching distribution found`.

### Pitfall 2: PostgresSaver Schema Not Initialized

**What goes wrong:** `AsyncPostgresSaver.from_conn_string(DB_URI)` connects successfully, but `graph.astream()` or `graph.aget_state()` raises `KeyError` or returns `None` for threads.

**Why it happens:** The `checkpoint_migrations` table does not exist until `await checkpointer.setup()` is called.

**How to avoid:** Always call `await checkpointer.setup()` inside the lifespan context manager, after the connection is established. It is idempotent — safe to call on every startup.

**Warning signs:** `KeyError` on first `graph.astream()` call; `graph.aget_state()` returns `None` for a thread that should have state.

### Pitfall 3: Groq TPM Exhaustion Under Concurrent Sessions

**What goes wrong:** Multiple concurrent WebSocket sessions fire LLM calls simultaneously. The RPM limit is respected but the 6,000 TPM limit is hit first. Groq returns 429s; all sessions fail simultaneously rather than degrading gracefully.

**Why it happens:** LiteLLM Router tracks `rpm` but without `tpm` in `litellm_params`, it cannot pre-empt the TPM 429. The fallback only activates after the 429 arrives.

**How to avoid:** Set both `"rpm": 30, "tpm": 6000` in the Groq `litellm_params` block at Router init time (not call time). This lets the Router pre-empt the TPM 429 by routing to Gemini Flash before hitting the limit.

**Warning signs:** Intermittent 429 errors during demo with multiple concurrent users; fallback activation rate > 20%.

### Pitfall 4: Bidirectional Edge Infinite Loop

**What goes wrong:** The LangGraph graph routes `objection_handling → pitch → objection_handling` indefinitely when the LLM stage detector keeps returning the same stage for an ambiguous lead message.

**Why it happens:** Bidirectional edges require a loop guard — LangGraph does not prevent cycles automatically.

**How to avoid:** Add a `visit_count: dict[str, int]` field to `ConversationState`. In `route_next_stage`, check `state["visit_count"].get("pitch", 0) >= 3` before routing backward, and forward to `propose_appointment` if the limit is hit.

**Warning signs:** WebSocket response never returns; agent_node called 10+ times for a single user message.

### Pitfall 5: Jinja2 UndefinedError Mid-Conversation

**What goes wrong:** `BusinessProfile` validates successfully at instantiation, but the Jinja2 template render inside the `intro` node raises `jinja2.exceptions.UndefinedError` on a missing optional field (e.g., `pricing=None`). LangGraph catches this as a node failure; the WebSocket connection drops without a user-visible message.

**Why it happens:** Jinja2's default `Undefined` silently skips unknown variables; `StrictUndefined` raises immediately, but the error still surfaces inside the node — where the WebSocket has already been accepted.

**How to avoid:** Validate all `BusinessProfile` fields (including optional ones) before passing to Jinja2. Add a Pydantic validator that rejects `None` for `pricing`. The online guardrail in AI-SPEC Section 6 catches this: validate BusinessProfile with Pydantic at the WebSocket handler level before calling `graph.astream()`, and return a graceful holding message if validation fails.

**Warning signs:** WebSocket connection drops immediately after first message in demo; `UndefinedError` in FastAPI logs.

### Pitfall 6: instructor.patch() Incompatibility with LiteLLM Router

**What goes wrong:** `instructor.patch(router)` may not support LiteLLM `Router` instances (as opposed to the `litellm` module directly). Stage detection calls raise `AttributeError`.

**Why it happens:** `instructor.patch` is designed for OpenAI-compatible clients; LiteLLM Router has a different interface.

**How to avoid:** At install time, test `instructor.patch(router)` with a minimal call. If it fails, fall back to direct JSON mode: call `router.acompletion(model="chat", response_format={"type": "json_object"}, ...)` and parse with `StageDetectionOutput.model_validate_json(response.choices[0].message.content)`, retrying on `ValidationError`.

**Warning signs:** `AttributeError: 'Router' object has no attribute 'chat'` or similar on first stage-detection call.

---

## Code Examples

### AI Disclosure + DPA Consent in Intro System Prompt

Per NPC Advisory 2024-04 (AI-SPEC Section 1b), the intro message must disclose AI nature before any data collection.

```jinja2
{# agent/prompts/base.j2 — common header for all industry templates #}
Ikaw si {{ agent_name }}, isang AI sales assistant ng {{ business_name }}.
Ipaalam mo sa bawat bagong kausap na ikaw ay isang AI — hindi tao — bago mo hanapin ang kanilang pangalan o contact.
Sabihin mo: "Para sa transparency po, ako ay AI assistant ni {{ agent_name }}. Tumutulong ako para sa appointment booking at sales queries."
Pagkatapos ng disclosure, i-state mo ang layunin ng data collection:
"Ang iyong impormasyon ay gagamitin lamang para sa appointment booking at follow-up."
```

### 2-of-3 Escalation Scorer (D-09)

```python
# Source: AI-SPEC Section 3 + Decision D-09 (01-CONTEXT.md)
# agent/escalation.py
import time
from typing import TypedDict

BOOKING_PHRASES = [
    "gusto ko mag-book", "i-book na", "puwede ba bukas", "anong available",
    "schedule na", "mag-set ng appointment", "kelan pwede", "book na tayo",
    "gusto ko na", "punta na ko", "magkano", "presyo"
]

POSITIVE_SENTIMENT_PHRASES = [
    "ok", "sige", "sure", "oo", "opo", "tara", "pwede", "gusto", "interesado",
    "maganda", "nice", "sounds good", "i'll go", "yes"
]

def escalation_scorer(state: dict) -> bool:
    messages = state.get("messages", [])
    if not messages:
        return False
    last_msg = messages[-1].content.lower() if hasattr(messages[-1], "content") else ""
    last_two = [m.content.lower() for m in messages[-2:] if hasattr(m, "content")]

    signal_1 = any(p in last_msg for p in BOOKING_PHRASES)
    signal_2 = sum(1 for m in last_two if any(p in m for p in POSITIVE_SENTIMENT_PHRASES)) >= 1

    timestamps = state.get("message_timestamps", [])
    signal_3 = False
    if len(timestamps) >= 2:
        signal_3 = (timestamps[-1] - timestamps[-2]) < 30  # seconds

    return sum([signal_1, signal_2, signal_3]) >= 2
```

### Vite + React WebSocket Hook (Frontend)

```typescript
// Source: standard React hook pattern for WebSocket; D-04 WebSocket-only transport
// frontend/src/useWebSocket.ts
import { useEffect, useRef, useState } from "react";

type WsMessage =
  | { type: "token"; content: string; node: string }
  | { type: "state"; stage: string; escalated: boolean };

export function useWebSocket(url: string) {
  const ws = useRef<WebSocket | null>(null);
  const [tokens, setTokens] = useState<string[]>([]);
  const [stage, setStage] = useState<string>("intro");
  const [escalated, setEscalated] = useState(false);

  useEffect(() => {
    ws.current = new WebSocket(url);
    ws.current.onmessage = (event) => {
      const msg: WsMessage = JSON.parse(event.data);
      if (msg.type === "token") {
        setTokens((prev) => [...prev, msg.content]);
      } else if (msg.type === "state") {
        setStage(msg.stage);
        setEscalated(msg.escalated);
      }
    };
    return () => ws.current?.close();
  }, [url]);

  const send = (text: string, industry: string) =>
    ws.current?.send(JSON.stringify({ text, industry }));

  return { tokens, stage, escalated, send };
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Sync PostgresSaver in FastAPI | `AsyncPostgresSaver` from `langgraph.checkpoint.postgres.aio` | LangGraph 0.2.x | Blocking DB calls caused request timeouts; async is now required |
| OpenRouter for multi-provider routing | LiteLLM Router with YAML config + `usage-based-routing-v2` | LiteLLM 1.x | Self-hosted, per-model RPM/TPM controls, no per-token markup |
| Session state in FastAPI memory | All state in LangGraph checkpointer (thread_id = lead UUID) | LangGraph 0.2.x | Page reload resumes conversation; horizontal scaling works |
| LangChain Agents (non-graph) | LangGraph StateGraph with explicit nodes + conditional edges | 2024 | Explicit stage control, time-travel debugging, no implicit memory |

**Deprecated/outdated:**
- `from langgraph.checkpoint.postgres import PostgresSaver` (sync): deprecated for async FastAPI; use `aio.AsyncPostgresSaver`
- `MemorySaver`: in-process only, not suitable for production; use `AsyncPostgresSaver` per AI-SPEC

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | AI-SPEC version numbers (langgraph 1.2.4, etc.) are forward-projected errors; actual PyPI max is langgraph 0.6.11 | Standard Stack, Pitfall 1 | If wrong and langgraph 1.x is released with breaking API changes, the code patterns in AI-SPEC may be accurate but unreachable until the release. Low risk — pattern code is compatible with 0.6.x. |
| A2 | `AsyncPostgresSaver.from_conn_string()` import path `langgraph.checkpoint.postgres.aio` is valid in langgraph-checkpoint-postgres 2.0.25 | Standard Stack, Pattern 1 | If import path changed in 2.x, Wave 0 version-verification task catches it before implementation |
| A3 | `instructor.patch()` supports LiteLLM Router instances | Code Examples | If incompatible, fall back to direct JSON mode (documented in Pitfall 6) |
| A4 | The Supabase Postgres connection string works with `psycopg[binary]` v3 in async mode | Environment Availability | Confirmed psycopg 3.2.13 on PyPI; Supabase connection string format is postgresql+asyncpg://... — verify with actual Supabase project URL at setup |
| A5 | Llama 4 Maverick model ID on Groq is `meta-llama/llama-4-maverick-17b-128e-instruct` as in litellm_config.yaml | Standard Stack | If Groq changes the model ID, LiteLLM will return a model-not-found error on first call |

---

## Open Questions

1. **LangGraph 0.6.x vs AI-SPEC code patterns**
   - What we know: AI-SPEC was written for langgraph 1.2.4 which doesn't exist on PyPI; langgraph 0.6.11 is actual latest
   - What's unclear: Whether `StateGraph`, `add_messages`, `astream(stream_mode="messages")` APIs changed between 0.6.x and what the AI-SPEC assumed for 1.x
   - Recommendation: Wave 0 task — scaffold the minimal entry point from AI-SPEC Section 3 against installed 0.6.11, run it against a mock connection, verify output before building further

2. **Supabase connection string format for AsyncPostgresSaver**
   - What we know: `AsyncPostgresSaver.from_conn_string()` expects a connection string; Supabase provides `postgresql://...` format
   - What's unclear: Whether `postgresql+asyncpg://` prefix is required or the `psycopg[binary,pool]` driver resolves it
   - Recommendation: Use `psycopg://` (not `postgresql+asyncpg://`) — psycopg v3 registers the `psycopg://` scheme; confirm in Wave 0 setup task

3. **SalesGPT fork scope at implementation time**
   - What we know: D-01 says fork SalesGPT prompts/templates/LiteLLM wiring; D-02 says keep what compiles
   - What's unclear: Exactly which SalesGPT files survive the state machine swap (depends on actual SalesGPT codebase review)
   - Recommendation: First implementation task — clone SalesGPT, audit `salesgpt/` directory, tag each file as keep/rewrite/discard

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Vite + React frontend | YES | v22.22.2 | — |
| npm | Frontend package install | YES | 10.9.7 | — |
| Python 3 | Backend agent | YES (system) | 3.9.6 | Needs upgrade — `python>=3.12` required by langgraph |
| pip | Backend package install | YES | 21.2.4 | — |
| PostgreSQL (local) | Development testing | NO | — | Use Supabase cloud (free tier) for development |
| Supabase CLI | Local Supabase dev | NO | — | Use Supabase cloud project; CLI optional |
| Docker | Local Supabase | NO | — | Use Supabase cloud |

**Missing dependencies with no fallback:**
- Python 3.12 is required by langgraph (pyproject requires `python>=3.12`). System Python is 3.9.6. The planner must include a task to set up Python 3.12 via pyenv, brew, or a virtual environment with the correct Python version before any `pip install` steps.

**Missing dependencies with fallback:**
- PostgreSQL (local): Use Supabase cloud free tier. The `SUPABASE_DB_URI` in `.env` points to Supabase cloud — no local Postgres needed for development.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (Python) — no config file detected; Wave 0 creates `pytest.ini` |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AGENT-01 | Stage transitions: scripted 7-turn conversation advances stage correctly | unit | `pytest tests/test_stage_routing.py -x` | Wave 0 |
| AGENT-01 | Backward routing (objection → pitch) fires on correct signal | unit | `pytest tests/test_stage_routing.py::test_backward_routing -x` | Wave 0 |
| AGENT-02 | LiteLLM Router falls back to Gemini on mocked Groq 429 | integration | `pytest tests/test_llm_router.py::test_groq_429_fallback -x` | Wave 0 |
| AGENT-03 | Taglish register matching — LLM judge via promptfoo | LLM eval | `promptfoo eval --config evals/promptfoo.yaml` | Wave 0 |
| AGENT-04 | BusinessProfile renders correct system prompt per industry | unit | `pytest tests/test_models.py::test_business_profile_render -x` | Wave 0 |
| AGENT-05 | Escalation scorer: 2-of-3 signals fire escalation | unit | `pytest tests/test_escalation.py -x` | Wave 0 |
| AGENT-05 | False positive prevention: low-intent queries don't escalate | unit | `pytest tests/test_escalation.py::test_false_positive -x` | Wave 0 |
| DEMO-01 | WebSocket ConnectionManager accepts/drops connections | integration | `pytest tests/test_websocket.py -x` | Wave 0 |
| DEMO-02 | Owner panel receives `type: state` event with correct stage | integration | `pytest tests/test_websocket.py::test_owner_panel_state -x` | Wave 0 |
| DEMO-03 | AsyncPostgresSaver persists and resumes conversation on reconnect | integration | `pytest tests/test_persistence.py -x` | Wave 0 |

### Wave 0 Gaps

- [ ] `tests/test_stage_routing.py` — covers AGENT-01 stage transitions + backward routing
- [ ] `tests/test_llm_router.py` — covers AGENT-02 fallback under mocked 429
- [ ] `tests/test_models.py` — covers AGENT-04 BusinessProfile + Jinja2 render
- [ ] `tests/test_escalation.py` — covers AGENT-05 2-of-3 scorer + false positive prevention
- [ ] `tests/test_websocket.py` — covers DEMO-01 ConnectionManager + DEMO-02 owner panel events
- [ ] `tests/test_persistence.py` — covers DEMO-03 state resume after reconnect
- [ ] `pytest.ini` — base config with asyncio_mode = auto (required for async tests)
- [ ] `tests/conftest.py` — shared fixtures: mock LiteLLM Router, mock AsyncPostgresSaver, test BusinessProfile instances

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth in Phase 1 demo (WebSocket open) — Phase 5 adds Supabase Auth |
| V3 Session Management | Partial | `thread_id` = lead UUID; must not be guessable — use `uuid4()`, not sequential |
| V4 Access Control | No | Phase 1 demo is single-tenant; RLS added in Phase 5 |
| V5 Input Validation | Yes | Pydantic `BusinessProfile` validates all fields before Jinja2 render; lead messages sanitized before LLM call |
| V6 Cryptography | No | No secrets stored in app; API keys via env vars only |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Prompt injection via lead message | Tampering | Separate system prompt from user content (Pattern 3 above); never interpolate lead text into system prompt |
| thread_id enumeration (sequential IDs) | Information Disclosure | Use `uuid4()` for thread_id — never sequential integers |
| API key exposure in logs | Information Disclosure | LiteLLM Router logs should redact API keys; set `LITELLM_LOG=ERROR` in production |
| Jinja2 SSTI via BusinessProfile fields | Tampering | BusinessProfile is internally defined (not user-supplied in Phase 1); validate with Pydantic before render |
| NPC 2024-04 compliance gap | Repudiation | AI disclosure must appear in intro message — code guardrail in AI-SPEC Section 6 enforces this |

---

## Sources

### Primary (HIGH confidence)
- `01-AI-SPEC.md` — AI design contract with verified code patterns, eval strategy, guardrails; written by specialist researcher
- `01-CONTEXT.md` — Locked decisions D-01 through D-12
- `PROJECT.md` — Dependency versions, litellm_config.yaml, Context7 IDs
- PyPI registry (`pip3 index versions`) — confirmed actual package versions on 2026-06-11

### Secondary (MEDIUM confidence)
- npm registry (`npm view`) — confirmed Vite 8.0.16, React 19.2.7, TypeScript 6.0.3

### Tertiary (LOW confidence)
- [ASSUMED] instructor.patch compatibility with LiteLLM Router — needs runtime verification
- [ASSUMED] Groq model ID string `meta-llama/llama-4-maverick-17b-128e-instruct` — sourced from PROJECT.md

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — PyPI and npm versions confirmed via registry queries; AI-SPEC is authoritative source for patterns
- Architecture: HIGH — patterns sourced directly from AI-SPEC (specialist-written); lifespan/WebSocket/streaming patterns are standard FastAPI
- Pitfalls: HIGH — sourced from AI-SPEC Section 3 "Common Pitfalls" which is documented from official LangGraph/LiteLLM sources

**Research date:** 2026-06-11
**Valid until:** 2026-07-11 (30 days) — LangGraph is moving fast; re-verify `langgraph-checkpoint-postgres` import paths before install if more than 2 weeks pass

**Critical action for Wave 0:** Verify actual langgraph 0.6.x `AsyncPostgresSaver` import path before any other implementation. The AI-SPEC's `from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver` must be confirmed against the installed 2.0.25 package.
