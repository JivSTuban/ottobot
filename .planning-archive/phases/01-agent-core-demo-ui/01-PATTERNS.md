# Phase 1: Agent Core & Demo UI - Pattern Map

**Mapped:** 2026-06-11
**Files analyzed:** 18 new files
**Analogs found:** 0 / 18 (brand new project — all patterns sourced from AI-SPEC)

---

## File Classification

| New File | Role | Data Flow | Closest Analog | Match Quality |
|----------|------|-----------|----------------|---------------|
| `agent/state.py` | model | event-driven | NEW (no analog) | — |
| `agent/models.py` | model | request-response | NEW (no analog) | — |
| `agent/llm.py` | service | request-response | NEW (no analog) | — |
| `agent/graph.py` | service | event-driven | NEW (no analog) | — |
| `agent/escalation.py` | utility | event-driven | NEW (no analog) | — |
| `agent/prompts/base.j2` | config | — | NEW (no analog) | — |
| `agent/prompts/dental.j2` | config | — | NEW (no analog) | — |
| `agent/prompts/aesthetics.j2` | config | — | NEW (no analog) | — |
| `agent/prompts/real_estate.j2` | config | — | NEW (no analog) | — |
| `api/main.py` | controller | request-response | NEW (no analog) | — |
| `api/ws_handler.py` | controller | streaming | NEW (no analog) | — |
| `frontend/src/App.tsx` | component | request-response | NEW (no analog) | — |
| `frontend/src/LeadChat.tsx` | component | streaming | NEW (no analog) | — |
| `frontend/src/OwnerPanel.tsx` | component | event-driven | NEW (no analog) | — |
| `frontend/src/useWebSocket.ts` | hook | streaming | NEW (no analog) | — |
| `evals/judge_config.py` | utility | batch | NEW (no analog) | — |
| `evals/promptfoo.yaml` | config | batch | NEW (no analog) | — |
| `evals/check_thresholds.py` | utility | batch | NEW (no analog) | — |
| `tests/test_stage_routing.py` | test | request-response | NEW (no analog) | — |
| `tests/test_escalation.py` | test | request-response | NEW (no analog) | — |
| `tests/test_models.py` | test | request-response | NEW (no analog) | — |
| `tests/test_websocket.py` | test | streaming | NEW (no analog) | — |
| `tests/test_persistence.py` | test | request-response | NEW (no analog) | — |
| `tests/conftest.py` | config | — | NEW (no analog) | — |
| `litellm_config.yaml` | config | — | NEW (no analog) | — |
| `pyproject.toml` | config | — | NEW (no analog) | — |

---

## Pattern Assignments

### `agent/state.py` (model, event-driven)

**Source:** AI-SPEC Section 3 — Entry Point Pattern

**ConversationState TypedDict:**
```python
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing import Annotated, Literal, TypedDict

STAGES = Literal["intro", "qualify", "pitch", "objection_handling",
                 "propose_appointment", "confirm", "escalate"]

class ConversationState(TypedDict):
    messages: Annotated[list, add_messages]
    stage: STAGES
    thread_id: str
    escalated: bool
    visit_count: dict[str, int]   # required — guards bidirectional edge infinite loops (D-08, Pitfall 4)
    message_timestamps: list[float]  # required — supports 2-of-3 escalation cadence signal (D-09)
```

**Anti-pattern to avoid:** `messages: list` without `Annotated[list, add_messages]` — each node call replaces the full message list instead of appending.

---

### `agent/models.py` (model, request-response)

**Source:** AI-SPEC Section 4b.1

**BusinessProfile + StageDetectionOutput:**
```python
from pydantic import BaseModel, Field
from typing import List, Literal
from enum import Enum
import jinja2

class Industry(str, Enum):
    dental = "dental"
    aesthetics = "aesthetics"
    real_estate = "real_estate"

class BusinessProfile(BaseModel):
    agent_name: str = Field(..., description="Persona name, e.g. 'Ate Ana'")
    business_name: str
    industry: Industry
    services: List[str] = Field(..., min_length=1)
    pricing: str = Field(..., description="Price range string, e.g. 'P500-P1500'. Never leave None.")
    phone: str

    def render_system_prompt(self, env: jinja2.Environment) -> str:
        template = env.get_template(f"{self.industry.value}.j2")
        return template.render(**self.model_dump())

# DEMO personas (D-12)
DEMO_PROFILES = {
    "dental": BusinessProfile(agent_name="Ate Ana", business_name="Smile Dental Clinic",
        industry="dental", services=["dental cleaning", "whitening"], pricing="P500-P2500", phone="+63917XXXXXXX"),
    "aesthetics": BusinessProfile(agent_name="Ate Bea", business_name="Bea Aesthetics Studio",
        industry="aesthetics", services=["facial", "whitening"], pricing="P800-P3000", phone="+63918XXXXXXX"),
    "real_estate": BusinessProfile(agent_name="Kuya Marco", business_name="Marco Realty",
        industry="real_estate", services=["condo tours", "property listing"], pricing="varies", phone="+63919XXXXXXX"),
}

class StageDetectionOutput(BaseModel):
    next_stage: Literal[
        "intro", "qualify", "pitch", "objection_handling",
        "propose_appointment", "confirm", "escalate"
    ]
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., max_length=200)
```

---

### `agent/llm.py` (service, request-response)

**Source:** AI-SPEC Section 3 — Entry Point Pattern + Section 4 Implementation Guidance

**LiteLLM Router singleton — module-level, never per-request:**
```python
import os
from litellm import Router

router = Router(
    model_list=[
        {
            "model_name": "chat",
            "litellm_params": {
                "model": "groq/meta-llama/llama-4-maverick-17b-128e-instruct",
                "api_key": os.environ["GROQ_API_KEY"],
                "rpm": 30,
                "tpm": 6000,   # MUST set tpm or Router cannot pre-empt 429 (Pitfall 4 in RESEARCH.md)
            },
        },
        {
            "model_name": "chat",
            "litellm_params": {
                "model": "gemini/gemini-1.5-flash",
                "api_key": os.environ["GEMINI_API_KEY"],
                "rpm": 15,
            },
        },
        {
            "model_name": "chat",
            "litellm_params": {
                "model": "mistral/mistral-small-latest",
                "api_key": os.environ["MISTRAL_API_KEY"],
            },
        },
    ],
    fallbacks=[{"chat": ["chat", "chat"]}],
    num_retries=2,
    retry_after=1,
    routing_strategy="usage-based-routing-v2",
    cache_responses=True,   # free exact-match caching for common greetings (Section 4b.5)
)
```

**Anti-pattern:** Never instantiate `Router(...)` inside a FastAPI route or WebSocket handler — it loses rate-limit tracking across calls.

---

### `agent/graph.py` (service, event-driven)

**Source:** AI-SPEC Section 3 + Section 4 + RESEARCH.md Pattern 3

**StateGraph definition with agent_node + route_next_stage:**
```python
from langgraph.graph import StateGraph, END
from agent.state import ConversationState
from agent.llm import router
from agent.escalation import escalation_scorer
from jinja2 import Environment, FileSystemLoader, StrictUndefined
import os

MAX_HISTORY = 20

jinja_env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "prompts")),
    undefined=StrictUndefined,   # raises on missing fields instead of silently rendering empty string
)

async def agent_node(state: ConversationState) -> dict:
    # Stage instruction appended fresh each turn — keeps it current as context scrolls (Section 4b.3)
    stage_msg = {"role": "system", "content": f"Current stage: {state['stage']}. Goal: ..."}
    messages_to_send = state["messages"][-MAX_HISTORY:] + [stage_msg]
    response = await router.acompletion(
        model="chat",
        messages=messages_to_send,
        max_tokens=512,
        temperature=0.7,
    )
    reply = response.choices[0].message.content
    return {"messages": [{"role": "assistant", "content": reply}]}

def route_next_stage(state: ConversationState) -> str:
    # 1. Escalation scorer first — fast, no LLM call (D-09)
    if escalation_scorer(state):
        return "escalate"
    # 2. Explicit booking phrases fast rule
    last_msg = state["messages"][-1].content if state["messages"] else ""
    booking_phrases = ["gusto ko mag-book", "i-book na", "puwede ba bukas", "anong available",
                       "schedule na", "mag-set ng appointment", "kelan pwede", "book na tayo",
                       "gusto ko na", "punta na ko", "magkano", "presyo"]
    if any(p in last_msg.lower() for p in booking_phrases):
        return "escalate"
    # 3. visit_count guard — prevents infinite backward-edge loop (D-08 + Pitfall 5)
    vc = state.get("visit_count", {})
    if vc.get("pitch", 0) >= 3 and state["stage"] == "objection_handling":
        return "propose_appointment"
    # 4. LLM stage detection for ambiguous transitions
    return llm_detect_stage(state)

# Build graph
builder = StateGraph(ConversationState)
builder.add_node("agent", agent_node)
builder.add_conditional_edges("agent", route_next_stage)
builder.set_entry_point("agent")
# compiled_graph is set in api/main.py lifespan after AsyncPostgresSaver is ready
```

---

### `agent/escalation.py` (utility, event-driven)

**Source:** AI-SPEC Section 3 + Decision D-09 + RESEARCH.md Code Examples

**2-of-3 composite escalation scorer:**
```python
import time

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

---

### `agent/prompts/base.j2` (config)

**Source:** AI-SPEC Section 5 (eval YAML) + RESEARCH.md Code Examples — AI disclosure is a regulatory requirement (NPC 2024-04)

**Required AI disclosure header (must appear before any data collection):**
```jinja2
{# agent/prompts/base.j2 — include at top of every industry template #}
Ikaw si {{ agent_name }}, isang AI sales assistant ng {{ business_name }}.
Ipaalam mo sa bawat bagong kausap na ikaw ay isang AI — hindi tao — bago mo hanapin ang kanilang pangalan o contact.
Sabihin mo: "Para sa transparency po, ako ay AI assistant ni {{ agent_name }}. Tumutulong ako para sa appointment booking at sales queries."
Pagkatapos ng disclosure, i-state mo ang layunin ng data collection:
"Ang iyong impormasyon ay gagamitin lamang para sa appointment booking at follow-up."

Taglish code-switching instruction (D-11):
Respond in the same mix of Tagalog and English the lead uses.
If they write in pure English, reply in English.
If Taglish, match their register exactly — same formality level, same ratio.
Always use "po" and "opo" if the lead uses them. Never use the lead's first name without being given it.
```

**Anti-pattern:** Jinja2 env must be created with `StrictUndefined` — see `agent/graph.py` pattern.

---

### `agent/prompts/dental.j2`, `aesthetics.j2`, `real_estate.j2` (config)

**Source:** AI-SPEC Section 1b domain context + Decision D-12

Each template extends `base.j2` and injects `BusinessProfile` fields. Required variables (all must be present — `StrictUndefined` enforces this):
- `{{ agent_name }}` — e.g., "Ate Ana"
- `{{ business_name }}` — e.g., "Smile Dental Clinic"
- `{{ services }}` — list rendered as comma-separated
- `{{ pricing }}` — e.g., "P500-P2500"
- `{{ phone }}` — for escalation message

---

### `api/main.py` (controller, request-response)

**Source:** AI-SPEC Section 4b.2 + RESEARCH.md Pattern 1 + Pattern 2

**FastAPI lifespan + ConnectionManager + WebSocket route:**
```python
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from agent.graph import builder
# Arize Phoenix instrumentation (AI-SPEC Section 5)
import phoenix as px
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from openinference.instrumentation.langchain import LangChainInstrumentor

compiled_graph = None   # set during lifespan startup

@asynccontextmanager
async def lifespan(app: FastAPI):
    global compiled_graph
    # Phoenix tracing setup — before graph compile
    exporter = OTLPSpanExporter(endpoint="http://localhost:6006/v1/traces")
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    LangChainInstrumentor().instrument()

    async with AsyncPostgresSaver.from_conn_string(
        os.environ["SUPABASE_DB_URI"]
    ) as checkpointer:
        await checkpointer.setup()   # idempotent — runs pending migrations (Pitfall 2)
        compiled_graph = builder.compile(checkpointer=checkpointer)
        yield
    # connection closes here

app = FastAPI(lifespan=lifespan)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

manager = ConnectionManager()

@app.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    await manager.connect(websocket)
    try:
        from api.ws_handler import handle_ws
        await handle_ws(websocket, thread_id)
    finally:
        manager.disconnect(websocket)
```

**Critical:** `thread_id` must be lead UUID (uuid4), NOT the WebSocket connection ID — reconnects would lose state (RESEARCH.md Anti-Patterns).

---

### `api/ws_handler.py` (controller, streaming)

**Source:** AI-SPEC Section 4 — Core Pattern

**graph.astream() → WebSocket token fan-out:**
```python
from fastapi import WebSocket
# compiled_graph imported from api.main after lifespan sets it
import api.main as app_state

async def handle_ws(websocket: WebSocket, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}

    async for ws_message in websocket.iter_json():
        user_text = ws_message["text"]
        industry = ws_message.get("industry", "dental")

        async for chunk, metadata in app_state.compiled_graph.astream(
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

        # After stream completes — send full state for owner panel (D-05)
        final_state = await app_state.compiled_graph.aget_state(config)
        await websocket.send_json({
            "type": "state",
            "stage": final_state.values.get("stage"),
            "escalated": final_state.values.get("escalated", False),
        })
```

**Anti-pattern:** Never call `asyncio.run()` inside this handler — raises `RuntimeError: This event loop is already running` (AI-SPEC Section 4b.2).

---

### `frontend/src/useWebSocket.ts` (hook, streaming)

**Source:** RESEARCH.md Code Examples — Vite + React WebSocket Hook

```typescript
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

### `frontend/src/App.tsx` (component, request-response)

**Source:** RESEARCH.md Architecture + Decision D-04/D-06

Split-screen layout with industry selector:
- Left panel: `<LeadChat />` — lead input + token stream display
- Right panel: `<OwnerPanel />` — conversation mirror + stage badge + escalation alert flash (D-05)
- Top: industry selector dropdown (dental / aesthetics / real_estate) — fires on mount/change, passed to `useWebSocket` send payload (D-06)
- WebSocket URL: `ws://localhost:8000/ws/{threadId}` where `threadId` is a `uuid` generated client-side on page load

---

### `frontend/src/LeadChat.tsx` (component, streaming)

**Source:** Decision D-04 + AI-SPEC system type description

- Consumes `tokens` and `send` from `useWebSocket`
- Renders token stream as a chat bubble (assembling tokens into message strings)
- Input box + send button for lead messages
- Sends `{ text, industry }` JSON over WebSocket (no REST calls per D-04)

---

### `frontend/src/OwnerPanel.tsx` (component, event-driven)

**Source:** Decision D-05

- Consumes `stage` and `escalated` from `useWebSocket`
- Conversation mirror (read-only) — reflects full message stream
- Lead status badge: `new` / `qualifying` / `hot` / `booked` — derived from `stage` value
- Escalation alert flash: triggered when `escalated === true` (WebSocket `type: state` event)

---

### `evals/judge_config.py` (utility, batch)

**Source:** AI-SPEC Section 5 — Eval Tooling

```python
from phoenix.evals import OpenAIModel, llm_classify

REGISTER_MATCH_TEMPLATE = """
You are a Filipino sales manager evaluating an AI sales agent.
Conversation turn:
Lead: {lead_message}
Agent: {agent_message}

Does the agent's reply match the lead's language register (Taglish/Tagalog/English ratio)?
Answer: PASS or FAIL. Then one sentence explaining why.
"""

results = llm_classify(
    dataframe=eval_df,
    template=REGISTER_MATCH_TEMPLATE,
    model=OpenAIModel(model="gpt-4o-mini"),
    rails=["PASS", "FAIL"],
)
```

---

### `evals/promptfoo.yaml` (config, batch)

**Source:** AI-SPEC Section 5

Key test cases required:
- Taglish register match (dental persona)
- AI disclosure present in intro (all 3 personas)
- No price hallucination (dental whitening — assert P1500-P2500 range)
- Soft deflection stays in `objection_handling` stage
- Escalation fires on explicit booking intent ("gusto ko na mag-book bukas")

---

### `evals/check_thresholds.py` (utility, batch)

**Source:** AI-SPEC Section 5

```bash
# Fail CI if critical dimension pass rate < 90%
python evals/check_thresholds.py --results evals/results/latest.json --min-pass-rate 0.90
```

---

### `tests/conftest.py` (config)

**Source:** RESEARCH.md Validation Architecture — Wave 0 Gaps

Required shared fixtures:
- Mock LiteLLM Router (returns deterministic completions)
- Mock `AsyncPostgresSaver` (in-memory; avoids Supabase dependency in unit tests)
- `demo_profile` fixture instances for all 3 industries
- `pytest.ini` with `asyncio_mode = auto` (required for `async def test_*` functions)

---

### `tests/test_stage_routing.py` (test, request-response)

**Source:** RESEARCH.md Validation Architecture — AGENT-01

Tests required:
- 7-turn scripted conversation advances stage correctly at each turn
- Backward routing: `objection_handling → pitch` fires on correct objection signal
- `visit_count` guard prevents infinite backward loop after 3 visits

---

### `tests/test_escalation.py` (test, request-response)

**Source:** RESEARCH.md Validation Architecture — AGENT-05

Tests required:
- 2-of-3 signals all present → `escalation_scorer` returns `True`
- Only 1 signal present → returns `False` (false positive prevention)
- Low-intent queries ("may parking ba kayo?") → `False`

---

### `tests/test_models.py` (test, request-response)

**Source:** RESEARCH.md Validation Architecture — AGENT-04

Tests required:
- `BusinessProfile` renders correct Jinja2 output per industry (dental / aesthetics / real_estate)
- `pricing=None` raises `ValidationError` at instantiation (not at render time)
- `StageDetectionOutput` rejects confidence outside [0.0, 1.0]

---

### `litellm_config.yaml` (config)

**Source:** AI-SPEC Section 3 + PROJECT.md (referenced in CONTEXT.md canonical refs)

Must include all 3 providers with `rpm` and `tpm` set for Groq, `routing_strategy: usage-based-routing-v2`.

---

### `pyproject.toml` (config)

**Source:** RESEARCH.md Standard Stack — pinned versions

```toml
[project]
requires-python = ">=3.12"   # langgraph requires 3.12; system Python 3.9.6 is insufficient

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

Key pins (use actual PyPI versions, not AI-SPEC versions):
- `langgraph==0.6.11`
- `langgraph-checkpoint-postgres==2.0.25`
- `litellm==1.83.9`
- `fastapi[standard]==0.128.8`
- `psycopg[binary,pool]>=3.2.0,<4`
- `pydantic>=2.9.0,<3`
- `jinja2>=3.1.0`

---

## Shared Patterns

### AsyncPostgresSaver Lifespan Pattern
**Source:** AI-SPEC Section 4b.2, lines 542-562
**Apply to:** `api/main.py`

Always use `async with AsyncPostgresSaver.from_conn_string(...) as checkpointer` inside `@asynccontextmanager` lifespan. Always call `await checkpointer.setup()` after context entry. Set `compiled_graph` as a module-level variable inside lifespan.

### Jinja2 StrictUndefined
**Source:** AI-SPEC Section 4b.1 + Section 4b.3
**Apply to:** `agent/graph.py` (Environment creation), `agent/models.py` (render_system_prompt)

```python
from jinja2 import Environment, FileSystemLoader, StrictUndefined
env = Environment(loader=FileSystemLoader("agent/prompts"), undefined=StrictUndefined)
```

Never use default `Undefined` — missing fields silently render as empty string, causing mid-conversation persona corruption.

### Taglish Code-Switching Prompt Instruction
**Source:** AI-SPEC Section 4b.3 + Decision D-11
**Apply to:** `agent/prompts/base.j2`

No language detection library. Instruction only: "Respond in the same mix of Tagalog and English the lead uses."

### NPC 2024-04 AI Disclosure
**Source:** AI-SPEC Section 6 (Online Guardrails) + RESEARCH.md Code Examples
**Apply to:** `agent/prompts/base.j2`, `api/ws_handler.py` (online guardrail check)

The intro message must contain an explicit AI disclosure phrase before any data-collection prompt. Guardrail: block send if `stage == "intro" and turn_index == 0` and disclosure phrase is absent.

### Async-First Rule
**Source:** AI-SPEC Section 4b.2
**Apply to:** `api/ws_handler.py`, `api/main.py`, all `async def` test functions

Never use `asyncio.run()` inside FastAPI. Every LangGraph call must be `await`-ed directly.

---

## No Analog Found

All 26 files have no analog — this is a brand new codebase. All patterns are sourced exclusively from `01-AI-SPEC.md`.

---

## Critical Implementation Notes for Planner

1. **Python 3.12 required** — system Python is 3.9.6 (RESEARCH.md Environment Availability). Wave 0 must include pyenv/brew Python 3.12 setup before any `pip install`.

2. **Version pin override** — AI-SPEC installation block lists `langgraph==1.2.4` (does not exist on PyPI). Use `langgraph==0.6.11` and `langgraph-checkpoint-postgres==2.0.25` everywhere.

3. **Wave 0 verification task** — before implementing anything else, scaffold the minimal entry point from AI-SPEC Section 3 against installed `langgraph==0.6.11` and verify `AsyncPostgresSaver` import path: `from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver`.

4. **instructor.patch() compatibility** — verify at install time whether `instructor.patch(router)` supports LiteLLM `Router` instances. If not, fall back to `response_format={"type": "json_object"}` + `StageDetectionOutput.model_validate_json(...)`.

---

## Metadata

**Analog search scope:** N/A — no existing source files in project root
**Files scanned:** 0 source files; 3 planning files read
**Pattern sources:** 01-AI-SPEC.md (primary), 01-RESEARCH.md (version corrections + pitfalls), 01-CONTEXT.md (decisions D-01 through D-12)
**Pattern extraction date:** 2026-06-11
