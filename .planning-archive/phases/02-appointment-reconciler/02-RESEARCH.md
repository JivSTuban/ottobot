# Phase 2: Appointment Reconciler — Research

**Researched:** 2026-06-16
**Domain:** Supabase availability storage, LangGraph tool node, FastAPI REST + WebSocket, React appointment UI
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Data Layer**
- Availability storage: Supabase table `business_availability` (id, business_id, day_of_week int 0-6, start_time time, end_time time)
- Appointments table: `appointments` (id, thread_id, business_id, proposed_time timestamptz, status: proposed/confirmed/cancelled, created_at)
- No external calendar (Google Calendar, Calendly) — Supabase only for v1
- Business ID source: derive from industry + a placeholder UUID stored in env; real multi-business comes in Phase 5

**Agent Integration**
- New LangGraph tool node `get_available_slots(business_id, days_ahead=7)` — queries Supabase, returns 2 slots max
- Add `proposed_appointment` field to `ConversationState` (str or None) — stores proposed ISO datetime
- Agent proposes slots only when stage reaches `propose_appointment`
- Slot format in Tagalog: "Mayroon kaming bakante sa [Day] ng [Date] sa [Time]"
- If no slots available: "Tatawagan ka namin para mag-ayos ng oras" (fallback phrase)

**API**
- `POST /availability` — upsert weekly schedule for a business
- `GET /availability/{business_id}` — return available slots for next 7 days
- `POST /appointments/confirm` — business owner confirms a proposed slot
- All new endpoints use same `validate_thread_id` / `validate_business_id` guard patterns
- Keep behind existing FastAPI app (no separate service)

**UI (OwnerPanel extension)**
- New "Appointments" section below existing escalation panel
- Shows proposed appointment time (if any) with Confirm / Counter-propose buttons
- Counter-propose: text input for owner to type alternate time (simple, no calendar picker)
- Confirmation triggers WebSocket message `confirm_appointment` → backend stores to Supabase

**WebSocket Protocol**
- New message type from owner to server: `{ type: "confirm_appointment", thread_id, proposed_time, action: "confirm" | "counter", counter_time? }`
- New message type server to lead client: `{ type: "appointment_confirmed", confirmed_time }` — agent appends confirmation message to conversation

**Testing**
- Unit tests: `test_appointment_slots.py` — test slot generation, time math, Tagalog formatting
- Unit tests: `test_appointment_api.py` — test availability API endpoints (mock Supabase)
- Frontend: `OwnerPanel.test.tsx` extended with appointment UI tests

### Claude's Discretion

- Internal implementation of `get_available_slots` (SQL query shape, Python datetime helpers)
- Time zone handling approach (assume PH local time UTC+8)
- Exact Supabase Python client usage pattern (direct psycopg vs supabase-py SDK)
- Structure of `agent/slots.py` helper module
- Exact CSS for the Appointments UI section in OwnerPanel

### Deferred Ideas (OUT OF SCOPE)

- Appointment reminders (Phase 4 when SMS channel exists)
- Calendar integrations (Google/Apple Calendar)
- Lead-side rescheduling flow
- Appointment analytics dashboard
- Multi-business availability (Phase 5+)
- Recurring appointment patterns
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| APPT-01 | Business owner sets weekly availability schedule (days + hours) saved to Supabase | POST /availability endpoint + `business_availability` table schema |
| APPT-02 | Agent proposes time windows from available slots; lead states preference | `get_available_slots` tool node in LangGraph + `propose_appointment` stage |
| APPT-03 | Business owner confirms or counter-proposes via app — no calendar integration | WebSocket `confirm_appointment` message + OwnerPanel UI section |
| APPT-04 | Confirmed appointments stored in Supabase with lead, business, time, and status | `appointments` table + `POST /appointments/confirm` endpoint |
</phase_requirements>

---

## Summary

Phase 2 extends OttoBot's conversation flow with a lightweight appointment scheduling loop. The design deliberately avoids external calendar services — availability is stored as a weekly recurring schedule in Supabase (`business_availability`), and appointment records are simple rows in an `appointments` table. The key insight is that Filipino SMBs work on phone confirmation patterns, not calendar invites, so the reconciler only needs to propose 2 candidate times and hand off to a human confirm step.

The existing codebase is a clean integration surface. `ConversationState` in `agent/state.py` receives a new scalar field `proposed_appointment: str | None`. The LangGraph graph in `agent/graph.py` gets a new **async tool node** `get_available_slots_node` wired before `agent_node` when stage is `propose_appointment`. FastAPI in `api/main.py` gets three new REST endpoints (upsert schedule, read slots, confirm appointment). `api/ws_handler.py` gets a new message type handler branch for `confirm_appointment`. `frontend/src/OwnerPanel.tsx` gets a new Appointments section with two action buttons.

The supabase Python client SDK is **not installed** in this project — all Supabase access happens via `langgraph-checkpoint-postgres` + raw psycopg3 connections. Phase 2 must follow this same pattern: use `psycopg` (already a dependency) for direct SQL queries to Supabase Postgres, not the `supabase` PyPI client. [VERIFIED: pyproject.toml inspection]

**Primary recommendation:** Add a single `agent/slots.py` helper module that owns slot math and Tagalog formatting; keep graph, API, and WebSocket handler thin wiring layers.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Availability schedule storage | Database (Supabase) | API (FastAPI) | Data lives in `business_availability` table; API is write path only |
| Slot computation (next 7 days) | API / Backend (Python) | — | Date arithmetic, filtering past slots; pure function in `agent/slots.py` |
| Slot proposal to lead | Agent (LangGraph) | — | Agent node reads slots at `propose_appointment` stage, generates Tagalog text |
| Appointment record creation | API / Backend (FastAPI) | Database | `POST /appointments/confirm` writes to `appointments` table |
| Business owner confirmation UI | Frontend (React) | WebSocket | OwnerPanel sends `confirm_appointment` WS message; backend persists |
| WebSocket message routing | Backend (ws_handler) | — | Existing `handle_ws` loop; new branch for `type == "confirm_appointment"` |

---

## Standard Stack

### Core (all already installed — no new packages needed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| psycopg | >=3.2.0,<4 | Direct Postgres queries for availability + appointments | Already used for AsyncPostgresSaver; no new dependency |
| langgraph | 0.6.11 | Tool node for slot retrieval | Phase 1 graph; new node added here |
| fastapi | 0.128.8 | REST endpoints for availability + confirmation | Phase 1 API; routes added |
| pydantic | 2.12.5 | Request/response validation for new endpoints | Already used |

[VERIFIED: pyproject.toml + venv site-packages inspection]

### No New Packages Required

Phase 2 introduces no new dependencies. All needed capabilities (async Postgres, HTTP routing, data validation, JSON serialization) are already present.

**Installation:** No `pip install` needed — all packages already in venv. [VERIFIED: pyproject.toml]

---

## Package Legitimacy Audit

No new packages introduced in this phase. Audit is N/A.

| Package | Registry | Verdict | Disposition |
|---------|----------|---------|-------------|
| (none new) | — | — | N/A |

---

## Architecture Patterns

### System Architecture Diagram

```
Lead WebSocket ─────────────────────────────────────────────────────────────────┐
                                                                                │
  [ws_handler.handle_ws]                                                        │
       │                                                                        │
       ├─ type == "text" (normal turn) ──► [LangGraph astream]                 │
       │                                        │                               │
       │                               stage == "propose_appointment"?          │
       │                                  YES ▼                                 │
       │                          [get_available_slots_node]                    │
       │                            psycopg → Supabase Postgres                 │
       │                            returns 2 slots or empty                    │
       │                                  │                                     │
       │                          [agent_node]                                  │
       │                            slot data injected into state               │
       │                            LLM generates Tagalog proposal              │
       │                                  │                                     │
       │                          {type:"token"} ──────────────────────────────►
       │                          {type:"state", proposed_appointment:…} ───────►
       │                                                                        │
       └─ type == "confirm_appointment" ──► validate → psycopg INSERT           │
                                            → {type:"appointment_confirmed"} ───►
                                                                                │
Owner WebSocket ─────────────────────────────────────────────────────────────────┘
  [OwnerPanel.tsx]
       │
       ├─ sees stage == "propose_appointment" → renders Appointments section
       ├─ Confirm button → send {type:"confirm_appointment", action:"confirm"}
       └─ Counter-propose → text input + send {type:"confirm_appointment", action:"counter", counter_time}

REST API (for availability setup)
  POST /availability  ──► psycopg UPSERT → business_availability
  GET  /availability/{business_id} ──► compute next-7-days slots ──► JSON
  POST /appointments/confirm ──► psycopg INSERT → appointments
```

### Recommended Project Structure

```
agent/
├── slots.py         # NEW: get_available_slots(), format_slot_tagalog(), compute_next_slots()
├── state.py         # EDIT: add proposed_appointment: str | None field
├── graph.py         # EDIT: add get_available_slots_node, wire into builder
api/
├── main.py          # EDIT: add /availability + /appointments routes
├── ws_handler.py    # EDIT: add confirm_appointment branch in handle_ws
tests/
├── test_appointment_slots.py   # NEW: slot generation, time math, Tagalog formatting
├── test_appointment_api.py     # NEW: availability API endpoints (mock Supabase)
frontend/src/
├── OwnerPanel.tsx   # EDIT: add Appointments section
├── types.ts         # EDIT: add AppointmentMessage, AvailabilitySlot types
```

### Pattern 1: Async Psycopg Query (consistent with existing lifespan pattern)

The project uses `psycopg[binary,pool]` already. For Phase 2 Supabase queries, open a connection from the same URI:

```python
# Source: existing api/main.py lifespan pattern
import psycopg

async def get_available_slots(business_id: str, days_ahead: int = 7) -> list[dict]:
    db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
    async with await psycopg.AsyncConnection.connect(db_uri) as conn:
        rows = await conn.execute(
            """
            SELECT day_of_week, start_time, end_time
            FROM business_availability
            WHERE business_id = %s
            ORDER BY day_of_week, start_time
            """,
            (business_id,)
        )
        return [dict(r) for r in await rows.fetchall()]
```

[ASSUMED] — psycopg3 `AsyncConnection.connect` API is consistent with this shape; exact method signatures should be verified against psycopg docs.

### Pattern 2: LangGraph Tool Node (async, wired conditionally)

```python
# Source: agent/graph.py pattern — new node added to builder
async def get_available_slots_node(state: ConversationState) -> dict:
    """Fetch available slots from Supabase and inject into state."""
    business_id = os.environ.get("BUSINESS_ID", "")
    slots = await get_available_slots(business_id, days_ahead=7)
    # Convert to 2-slot max, format as ISO datetimes
    proposed = compute_next_slots(slots, max_count=2)
    proposed_str = proposed[0] if proposed else None
    return {"proposed_appointment": proposed_str}
```

Wire in `builder`: add conditional pre-edge from entry — when `stage == "propose_appointment"`, go through `get_available_slots_node` then `agent_node`. Otherwise, skip directly to `agent_node`.

[ASSUMED] — LangGraph 0.6.x supports routing to intermediate nodes before the main agent; verify graph topology during planning to avoid "unknown channel" pitfall.

### Pattern 3: FastAPI REST Endpoint (pydantic validation + validate guard)

```python
# Source: api/main.py — follows existing validate_thread_id guard pattern
from pydantic import BaseModel

class AvailabilitySlot(BaseModel):
    day_of_week: int  # 0 = Monday, 6 = Sunday
    start_time: str   # "HH:MM"
    end_time: str     # "HH:MM"

class AvailabilityRequest(BaseModel):
    business_id: str
    slots: list[AvailabilitySlot]

@app.post("/availability")
async def set_availability(req: AvailabilityRequest):
    validate_business_id(req.business_id)   # guard — raise 400 on invalid
    # psycopg UPSERT into business_availability
    ...
```

### Pattern 4: WebSocket Branch in ws_handler (new message type)

```python
# In handle_ws, before existing text-routing logic:
async for ws_message in websocket.iter_json():
    msg_type = ws_message.get("type", "text")

    if msg_type == "confirm_appointment":
        # Owner panel confirm/counter flow
        thread_id_from_msg = ws_message.get("thread_id", "")
        if not validate_thread_id(thread_id_from_msg):
            await websocket.send_json({"type": "error", "content": "Invalid thread_id"})
            continue
        action = ws_message.get("action", "confirm")
        proposed_time = ws_message.get("proposed_time")
        counter_time = ws_message.get("counter_time")
        confirmed_time = counter_time if action == "counter" else proposed_time
        # INSERT into appointments table via psycopg
        await store_appointment(thread_id_from_msg, confirmed_time)
        await websocket.send_json({"type": "appointment_confirmed", "confirmed_time": confirmed_time})
        continue

    user_text = ws_message.get("text", "").strip()
    ...  # existing handling
```

### Pattern 5: Tagalog Slot Formatting

```python
# Source: CONTEXT.md specifics — agent/slots.py
DAYS_PH = ["Lunes", "Martes", "Miyerkules", "Huwebes", "Biyernes", "Sabado", "Linggo"]

def format_slot_tagalog(dt: datetime) -> str:
    """Format a datetime as Filipino natural language time."""
    day_name = DAYS_PH[dt.weekday()]
    date_str = dt.strftime("%B %d")  # "June 20"
    hour = dt.hour
    if hour < 12:
        time_str = f"ika-{hour} ng umaga"
    elif hour == 12:
        time_str = "tanghaling tapat"
    else:
        time_str = f"ika-{hour - 12} ng hapon"
    return f"Mayroon kaming bakante sa {day_name} ng {date_str} sa {time_str}"
```

[ASSUMED] — Filipino time phrasing — verify with native speaker or adjust based on product feedback.

### Anti-Patterns to Avoid

- **Do not use the `supabase` PyPI client** — it is not installed; use `psycopg` directly (consistent with existing codebase pattern). [VERIFIED: pyproject.toml]
- **Do not call `asyncio.run()` inside FastAPI routes or WebSocket handlers** — raises `RuntimeError: This event loop is already running`. This is the existing documented pitfall in `api/main.py` and `api/ws_handler.py`. [VERIFIED: code inspection]
- **Do not reuse `make_env()` per request** — singleton `jinja_env` is already exported from `graph.py`; import and reuse it. [VERIFIED: code inspection, WR-06 pattern]
- **Do not propose > 2 slots** — locked decision; choice friction is real for Filipino leads. [VERIFIED: CONTEXT.md]
- **Do not propose slots < 2 hours from now** — CONTEXT.md specifies this buffer; implement in `compute_next_slots()`. [VERIFIED: CONTEXT.md]
- **Do not add a new LangGraph conditional edge that returns an unregistered node name** — the existing pitfall pattern (logged in STATE.md Plan 01-GAP) causes silent routing to END. Always use explicit `path_map`. [VERIFIED: code inspection]

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Async Postgres queries | Custom connection pool | `psycopg.AsyncConnection.connect()` | Already in pyproject.toml; psycopg3 handles pooling |
| Request body validation | Manual JSON parsing | Pydantic BaseModel on FastAPI route | Already used throughout; automatic 422 error generation |
| UUID generation for appointment IDs | Custom ID scheme | `import uuid; str(uuid.uuid4())` | PostgreSQL can also generate via `gen_random_uuid()` |
| Time zone conversion | Custom UTC offset math | Python `datetime` + `timezone(timedelta(hours=8))` | Standard library; no extra package |

---

## Runtime State Inventory

> Phase 2 is a greenfield extension — no rename or migration involved. However: two new Supabase tables must be created before runtime. This is setup-only, not a rename.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | No existing `business_availability` or `appointments` tables | CREATE TABLE migration via psycopg in lifespan setup or separate migration script |
| Live service config | LangGraph `AsyncPostgresSaver` already running — new tables are additive | None — checkpointer setup is idempotent |
| OS-registered state | None | None |
| Secrets/env vars | `BUSINESS_ID` env var needed (placeholder UUID for Phase 2 single-business mode) | Add to `.env.example` |
| Build artifacts | None | None |

---

## Common Pitfalls

### Pitfall 1: LangGraph node wiring — "unknown channel" silent routing
**What goes wrong:** Adding a new node (`get_available_slots_node`) but not including it in `add_conditional_edges` path_map causes LangGraph to silently route to END instead of the intended next node.
**Why it happens:** LangGraph 0.6.x requires every node referenced in a path_map to be registered first via `add_node`.
**How to avoid:** Register node first (`builder.add_node("get_slots", get_available_slots_node)`), then wire with explicit path_map. See Plan 01-GAP fix pattern in STATE.md.
**Warning signs:** Conversation ends prematurely at `propose_appointment` stage.

### Pitfall 2: asyncio.run() inside running loop
**What goes wrong:** If `get_available_slots` uses `asyncio.run()` to call async psycopg, raises `RuntimeError: This event loop is already running`.
**Why it happens:** FastAPI + uvicorn already run an event loop; nested `asyncio.run()` is forbidden.
**How to avoid:** All psycopg calls inside nodes and routes must use `await` directly. Make all slot functions `async def`.
**Warning signs:** RuntimeError in logs at `propose_appointment` stage.

### Pitfall 3: Slot time logic — proposing past slots or < 2h from now
**What goes wrong:** `compute_next_slots()` returns slots that have already passed today (e.g., 9 AM slot when it's 3 PM).
**Why it happens:** Weekly availability is stored as day_of_week + time, not absolute datetimes; naive iteration can produce past datetimes.
**How to avoid:** When computing candidate datetimes, always check `candidate_dt > now + timedelta(hours=2)` before including a slot. Use timezone-aware datetimes with UTC+8.
**Warning signs:** Agent proposes "Lunes ng June 16 sa ika-9 ng umaga" when it's already June 16 afternoon.

### Pitfall 4: WebSocket message type routing — owner vs lead on same connection
**What goes wrong:** `confirm_appointment` message from the owner panel arrives on a WebSocket that also handles lead chat text. If the type check is placed after `user_text = ws_message.get("text", "")`, it falls through to LangGraph.
**Why it happens:** `handle_ws` currently assumes all messages have `type == "text"` (implicit); new message types need to be branched before user_text extraction.
**How to avoid:** Check `msg_type = ws_message.get("type", "text")` at the top of the loop, branch on `"confirm_appointment"` before touching `user_text`.
**Warning signs:** Appointment confirm triggers an empty LLM call.

### Pitfall 5: Supabase table creation — running CREATE TABLE in lifespan vs migration
**What goes wrong:** If tables are created inline in `lifespan()`, errors on repeated startup (table already exists) if not using `IF NOT EXISTS`.
**Why it happens:** `AsyncPostgresSaver.setup()` already runs migrations for checkpoint tables; new tables need explicit `CREATE TABLE IF NOT EXISTS`.
**How to avoid:** Create `business_availability` and `appointments` tables in a dedicated `setup_appointment_tables()` async function called during lifespan after `checkpointer.setup()`.
**Warning signs:** `psycopg.errors.DuplicateTable` on second startup.

---

## Code Examples

### SQL: Create Tables (run in lifespan setup)
```sql
-- Source: CONTEXT.md schema decisions
CREATE TABLE IF NOT EXISTS business_availability (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    business_id TEXT NOT NULL,
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    UNIQUE (business_id, day_of_week, start_time)
);

CREATE TABLE IF NOT EXISTS appointments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    thread_id TEXT NOT NULL,
    business_id TEXT NOT NULL,
    proposed_time TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed', 'confirmed', 'cancelled')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### ConversationState Extension (agent/state.py)
```python
# Add to ConversationState TypedDict:
proposed_appointment: str | None  # ISO 8601 datetime string, or None
```
No reducer needed — scalar field; last-write-wins across graph turns.

### Validate Business ID Helper (api/main.py pattern)
```python
def validate_business_id(business_id: str) -> bool:
    """Return True iff business_id is a valid UUID v4."""
    try:
        val = uuid.UUID(business_id)
        return val.version == 4
    except (ValueError, AttributeError):
        return False
```
Mirrors `validate_thread_id` — same guard pattern. [VERIFIED: code inspection]

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| External calendar (Calendly, Google Calendar) | Supabase-native availability table | Project design decision | No OAuth, no webhook, simpler flow |
| supabase-py SDK | psycopg direct connection | Phase 1 baseline | Fewer dependencies, same Postgres |

**Deprecated/outdated:**
- `supabase` PyPI client: not used in this project; do not add it.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `psycopg.AsyncConnection.connect(uri)` is the correct async connection call | Code Examples | API may differ slightly; verify against psycopg3 docs before implementing |
| A2 | Filipino time phrasing "ika-N ng hapon" is natural for SMB leads | Pattern 5 | Minor UX issue; easy to fix post-ship |
| A3 | LangGraph 0.6.11 supports wiring a pre-agent tool node conditionally on stage | Pattern 2 | If not, slot fetching must move into agent_node directly |
| A4 | `gen_random_uuid()` is available in Supabase Postgres | SQL schema | Supabase uses PostgreSQL 15 which has `gen_random_uuid()` built-in; highly likely |

---

## Open Questions

1. **LangGraph tool node topology**
   - What we know: LangGraph 0.6.11 is installed; Phase 1 uses a single "agent" node with a conditional edge
   - What's unclear: Whether adding a second node (`get_slots`) before `agent_node` conditionally requires a new entry-point rewrite or just an extra conditional edge from "agent"
   - Recommendation: Simplest approach — fetch slots directly inside `agent_node` when `stage == "propose_appointment"`, avoiding graph topology changes entirely. The slot fetch is fast (single SQL query) and doesn't warrant a separate node unless parallelism is needed.

2. **Connection pooling for slot queries**
   - What we know: `langgraph-checkpoint-postgres` opens its own connection via `AsyncPostgresSaver.from_conn_string`; new psycopg calls in `agent/slots.py` would open additional connections
   - What's unclear: Whether per-request `psycopg.AsyncConnection.connect()` is acceptable under demo load
   - Recommendation: For Phase 2 demo scale, per-request connections are fine. Phase 5+ should introduce a shared pool.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| psycopg | Direct SQL queries for slots/appointments | ✓ | >=3.2.0 (in venv) | — |
| langgraph | Tool node wiring | ✓ | 0.6.11 | — |
| fastapi | New REST endpoints | ✓ | 0.128.8 | — |
| pydantic | Request validation | ✓ | 2.12.5 | — |
| Supabase Postgres | Table storage | ✓ (configured in .env) | PostgreSQL 15 | InMemory mock for tests |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio 0.23 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_appointment_slots.py tests/test_appointment_api.py -x` |
| Full suite command | `pytest` |
| Frontend framework | Vitest (vite-based) |
| Frontend quick run | `cd frontend && npm test -- --run OwnerPanel` |
| Frontend full suite | `cd frontend && npm test -- --run` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| APPT-01 | POST /availability saves to business_availability | unit (mock psycopg) | `pytest tests/test_appointment_api.py::test_set_availability -x` | ❌ Wave 0 |
| APPT-01 | GET /availability/{business_id} returns computed slots | unit (mock psycopg) | `pytest tests/test_appointment_api.py::test_get_availability -x` | ❌ Wave 0 |
| APPT-02 | compute_next_slots returns max 2 slots | unit | `pytest tests/test_appointment_slots.py::test_slot_count -x` | ❌ Wave 0 |
| APPT-02 | compute_next_slots skips slots < 2h from now | unit | `pytest tests/test_appointment_slots.py::test_slot_buffer -x` | ❌ Wave 0 |
| APPT-02 | format_slot_tagalog returns correct Tagalog string | unit | `pytest tests/test_appointment_slots.py::test_tagalog_format -x` | ❌ Wave 0 |
| APPT-02 | Empty availability returns fallback phrase | unit | `pytest tests/test_appointment_slots.py::test_empty_availability -x` | ❌ Wave 0 |
| APPT-03 | OwnerPanel shows Appointments section at propose_appointment stage | frontend unit | `cd frontend && npm test -- --run OwnerPanel` | ❌ Wave 0 |
| APPT-03 | confirm_appointment WS message persists appointment | unit (mock psycopg) | `pytest tests/test_appointment_api.py::test_confirm_appointment -x` | ❌ Wave 0 |
| APPT-04 | appointments table receives correct status on confirm | unit (mock psycopg) | `pytest tests/test_appointment_api.py::test_appointment_status -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_appointment_slots.py tests/test_appointment_api.py -x`
- **Per wave merge:** `pytest` (full suite, including Phase 1 regression)
- **Phase gate:** Full suite green + `cd frontend && npm test -- --run` green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_appointment_slots.py` — covers APPT-01, APPT-02 (slot math + Tagalog format)
- [ ] `tests/test_appointment_api.py` — covers APPT-03, APPT-04 (API endpoints, mock psycopg)
- [ ] OwnerPanel.test.tsx extended — covers APPT-03 frontend

*(All existing 68 tests must still pass — no regression allowed)*

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Phase 5 adds auth |
| V3 Session Management | yes | `validate_thread_id` UUID v4 check — applied to all new endpoints |
| V4 Access Control | no | Single-business demo; multi-tenant RLS in Phase 7 |
| V5 Input Validation | yes | Pydantic BaseModel on all POST bodies; day_of_week 0-6 range check; status enum constraint |
| V6 Cryptography | no | No crypto in this phase |

### Known Threat Patterns for Phase 2 Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Invalid business_id in availability endpoints | Tampering | `validate_business_id()` UUID v4 check (mirrors validate_thread_id) |
| Negative day_of_week or out-of-range values | Tampering | Pydantic `int` with CHECK constraint in SQL |
| Appointment confirm with spoofed thread_id | Spoofing | `validate_thread_id()` on `thread_id` in confirm_appointment WS message |
| SQL injection via business_id parameter | Tampering | Parameterized psycopg queries (`%s` placeholders) — never string interpolation |
| No secrets in logs | Info Disclosure | `os.environ.get()` pattern — never log env var values |

---

## Project Constraints (from CLAUDE.md)

| Directive | Category | Enforced By |
|-----------|----------|-------------|
| API keys via `os.environ.get("KEY_NAME")` — never hardcoded | Security | Code review |
| Thread IDs: UUID v4, validated via `validate_thread_id()` | Session management | Existing guard; apply to business_id too |
| State mergers: use `Annotated[list, _append_list]` for list fields | LangGraph | Not needed here — `proposed_appointment` is scalar |
| Jinja2 templates: use singleton `jinja_env` from `agent/graph.py` | Performance | Import existing singleton |
| WebSocket send: always check `readyState === WebSocket.OPEN` | Frontend | Existing `useWebSocket.ts` pattern |
| Do not modify `.planning/` artifacts (ROADMAP.md, REQUIREMENTS.md) | Policy | Manual |
| Do not modify `litellm_config.yaml` routing weights | Config | Manual |
| Do not drop or rename existing Supabase columns | Data integrity | Migration review |

---

## Sources

### Primary (HIGH confidence — codebase verified)
- `/Users/jivtuban/Desktop/ottobot/agent/state.py` — ConversationState TypedDict; extension point for `proposed_appointment`
- `/Users/jivtuban/Desktop/ottobot/agent/graph.py` — LangGraph builder, node patterns, pitfall documentation
- `/Users/jivtuban/Desktop/ottobot/api/main.py` — FastAPI lifespan, validate_thread_id guard, psycopg connection
- `/Users/jivtuban/Desktop/ottobot/api/ws_handler.py` — WebSocket message handling loop; extension point
- `/Users/jivtuban/Desktop/ottobot/frontend/src/OwnerPanel.tsx` — current panel structure; extension point
- `/Users/jivtuban/Desktop/ottobot/pyproject.toml` — confirmed installed packages and versions
- `/Users/jivtuban/Desktop/ottobot/.planning/phases/02-appointment-reconciler/02-CONTEXT.md` — locked decisions

### Secondary (MEDIUM confidence)
- `.planning/POLICY.md` — pre-answered design decisions for Phase 2

### Tertiary (LOW confidence — assumptions)
- A1–A4 in Assumptions Log above

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified in pyproject.toml and venv
- Architecture: HIGH — patterns derived directly from Phase 1 codebase inspection
- Pitfalls: HIGH — pitfalls 1–4 are Phase 1 historical patterns from STATE.md + code inspection
- Tagalog phrasing: LOW — not verified with native speaker

**Research date:** 2026-06-16
**Valid until:** 2026-07-16 (stable stack)
