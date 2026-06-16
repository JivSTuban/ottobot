"""
api/main.py — FastAPI application with AsyncPostgresSaver lifespan, ConnectionManager,
              WebSocket endpoint, Phoenix OTLP instrumentation, and health check.

Exports: app, compiled_graph, manager, lifespan, validate_thread_id

Anti-pattern: NEVER call asyncio.run() inside a FastAPI route or WebSocket handler
(see AI-SPEC Section 4b.2 — raises RuntimeError: This event loop is already running).
"""

import logging
import os
import uuid
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from agent.graph import builder
from api.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

# Set during lifespan startup; None at import time (tests must patch this).
compiled_graph = None

manager = ConnectionManager()


def validate_business_id(business_id: str) -> bool:
    """
    Return True iff business_id is a valid UUID version 4.

    T-02-04 mitigation: rejects non-UUID business_id at every endpoint that
    accepts one, preventing spoofing or accidental cross-business data access.
    Never log the business_id value.
    """
    try:
        val = uuid.UUID(business_id)    # parse WITHOUT version coercion
        return val.version == 4         # explicit version check
    except (ValueError, AttributeError):
        return False


def validate_thread_id(thread_id: str) -> bool:
    """
    Return True iff thread_id is a valid UUID version 4.

    Used by the WebSocket route to reject non-uuid4 thread_ids (V3 ASVS
    Session Management, T-05-01 mitigation).
    """
    try:
        val = uuid.UUID(thread_id)    # parse WITHOUT version coercion
        return val.version == 4       # explicit version check
    except (ValueError, AttributeError):
        return False


async def setup_appointment_tables() -> None:
    """
    Idempotently create business_availability and appointments tables.

    Uses CREATE TABLE IF NOT EXISTS — safe to call on every startup.
    No-ops when SUPABASE_DIRECT_URL and SUPABASE_DB_URI are both unset
    (e.g. test environments). Never logs the db_uri value (T-02-06).

    Call from lifespan after checkpointer.setup().
    """
    db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
    if not db_uri:
        return  # graceful: no-op in test environments without DB
    async with await psycopg.AsyncConnection.connect(db_uri) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS business_availability (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                business_id TEXT NOT NULL,
                day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                UNIQUE (business_id, day_of_week, start_time)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                thread_id TEXT NOT NULL,
                business_id TEXT NOT NULL,
                proposed_time TIMESTAMPTZ NOT NULL,
                status TEXT NOT NULL DEFAULT 'proposed'
                    CHECK (status IN ('proposed', 'confirmed', 'cancelled')),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------

class AvailabilitySlotIn(BaseModel):
    day_of_week: int  # 0-6
    start_time: str   # "HH:MM"
    end_time: str     # "HH:MM"


class AvailabilityRequest(BaseModel):
    business_id: str
    slots: list[AvailabilitySlotIn]


class ConfirmAppointmentRequest(BaseModel):
    thread_id: str
    business_id: str
    proposed_time: str  # ISO 8601 datetime string


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    1. Sets up Phoenix OTLP tracing (wrapped in try/except — does NOT crash if
       Phoenix is unreachable).
    2. Opens AsyncPostgresSaver connection to Supabase Postgres.
    3. Awaits checkpointer.setup() — idempotent migration runner (Pitfall 2).
    4. Compiles the LangGraph builder with the checkpointer and stores the result
       in the module-level `compiled_graph`.
    5. Yields — app is ready.
    6. AsyncPostgresSaver connection closes on exit.
    """
    global compiled_graph

    # --- Phoenix OTLP instrumentation (try/except — must NOT crash the app) ---
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from openinference.instrumentation.langchain import LangChainInstrumentor

        phoenix_endpoint = (
            os.environ.get("PHOENIX_HOST", "http://localhost:6006") + "/v1/traces"
        )
        exporter = OTLPSpanExporter(endpoint=phoenix_endpoint)
        provider = TracerProvider()
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        LangChainInstrumentor().instrument()
        logger.info("Phoenix OTLP tracing enabled: %s", phoenix_endpoint)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Phoenix instrumentation unavailable — continuing without tracing: %s", exc)

    # --- AsyncPostgresSaver + graph compilation ---
    from contextlib import asynccontextmanager as _acm

    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    db_uri = (
        os.environ.get("SUPABASE_DIRECT_URL")  # direct connection (port 5432) — bypasses pgbouncer DNS lag
        or os.environ.get("SUPABASE_DB_URI", "")  # pooler (port 6543) — fallback
    )
    logger.info(
        "Connecting to Postgres via: %s",
        (db_uri[:40] + "…") if len(db_uri) > 40 else db_uri,
    )
    try:
        async with AsyncPostgresSaver.from_conn_string(db_uri) as checkpointer:
            await checkpointer.setup()
            await setup_appointment_tables()
            compiled_graph = builder.compile(checkpointer=checkpointer)
            logger.info("LangGraph compiled with AsyncPostgresSaver")
            yield
    except Exception as db_exc:
        # Postgres unreachable (e.g. IPv6-only host on IPv4-only network, pooler
        # propagation lag on a brand-new project). Fall back to InMemorySaver so
        # the API can start; persistence tests will be blocked, not broken.
        logger.warning(
            "Postgres connection failed — falling back to InMemorySaver (no persistence): %s",
            db_exc,
        )
        from langgraph.checkpoint.memory import MemorySaver

        compiled_graph = builder.compile(checkpointer=MemorySaver())
        logger.info("LangGraph compiled with InMemorySaver (fallback)")
        yield
    # Connection closes here; compiled_graph becomes invalid after this point.


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    """Health check endpoint — returns whether the graph is compiled and ready."""
    return {"ok": True, "compiled": compiled_graph is not None}


# ---------------------------------------------------------------------------
# Availability endpoints
# ---------------------------------------------------------------------------

@app.post("/availability")
async def set_availability(req: AvailabilityRequest):
    """
    Upsert weekly availability schedule for a business.

    T-02-04: validate_business_id() rejects non-UUID-v4 business_id.
    T-02-05: parameterized %s placeholders — no SQL injection surface.
    T-02-06: never log db_uri or business_id values.
    """
    if not validate_business_id(req.business_id):
        raise HTTPException(status_code=400, detail="business_id must be a valid UUID v4")

    for slot in req.slots:
        if slot.day_of_week not in range(7):
            raise HTTPException(status_code=400, detail="day_of_week must be between 0 and 6")

    db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
    if not db_uri:
        return {"status": "ok", "upserted": len(req.slots)}

    async with await psycopg.AsyncConnection.connect(db_uri) as conn:
        for slot in req.slots:
            await conn.execute(
                """
                INSERT INTO business_availability (business_id, day_of_week, start_time, end_time)
                VALUES (%s, %s, %s::time, %s::time)
                ON CONFLICT (business_id, day_of_week, start_time)
                DO UPDATE SET end_time = EXCLUDED.end_time
                """,
                (req.business_id, slot.day_of_week, slot.start_time, slot.end_time),
            )

    return {"status": "ok", "upserted": len(req.slots)}


@app.get("/availability/{business_id}")
async def get_availability(business_id: str):
    """
    Return computed available slots for the next 7 days for a given business.

    T-02-04: validate_business_id() check applied.
    T-02-05: parameterized query.
    """
    if not validate_business_id(business_id):
        raise HTTPException(status_code=400, detail="business_id must be a valid UUID v4")

    from agent.slots import FALLBACK_PHRASE, compute_next_slots, format_slot_tagalog

    db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
    if not db_uri:
        return {"slots": [], "fallback": FALLBACK_PHRASE}

    async with await psycopg.AsyncConnection.connect(db_uri) as conn:
        cursor = await conn.execute(
            "SELECT day_of_week, start_time, end_time FROM business_availability WHERE business_id = %s",
            (business_id,),
        )
        raw_rows = await cursor.fetchall()

    # Convert tuple rows to dicts for compute_next_slots
    rows = [
        {"day_of_week": r[0], "start_time": r[1], "end_time": r[2]}
        for r in raw_rows
    ]

    slots = compute_next_slots(rows)
    if not slots:
        return {"slots": [], "fallback": FALLBACK_PHRASE}

    return {
        "slots": [
            {"iso": dt.isoformat(), "display": format_slot_tagalog(dt)}
            for dt in slots
        ]
    }


# ---------------------------------------------------------------------------
# Appointment confirmation endpoint
# ---------------------------------------------------------------------------

@app.post("/appointments/confirm")
async def confirm_appointment(req: ConfirmAppointmentRequest):
    """
    Store a confirmed appointment in Supabase.

    T-02-03: validate_thread_id() UUID v4 check.
    T-02-04: validate_business_id() UUID v4 check.
    T-02-05: parameterized INSERT — no SQL injection surface.
    T-02-06: never log db_uri or business_id values.
    """
    if not validate_thread_id(req.thread_id):
        raise HTTPException(status_code=400, detail="thread_id must be a valid UUID v4")

    if not validate_business_id(req.business_id):
        raise HTTPException(status_code=400, detail="business_id must be a valid UUID v4")

    db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
    if not db_uri:
        return {"status": "confirmed", "thread_id": req.thread_id}

    async with await psycopg.AsyncConnection.connect(db_uri) as conn:
        await conn.execute(
            """
            INSERT INTO appointments (thread_id, business_id, proposed_time, status)
            VALUES (%s, %s, %s::timestamptz, 'confirmed')
            """,
            (req.thread_id, req.business_id, req.proposed_time),
        )

    return {"status": "confirmed", "thread_id": req.thread_id}


@app.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    """
    WebSocket endpoint for a single lead conversation.

    Validates thread_id is a uuid4 (V3 ASVS, T-05-01) before accepting the
    connection. On invalid thread_id, closes with code 1008 (policy violation).
    """
    if not validate_thread_id(thread_id):
        await websocket.close(code=1008, reason="thread_id must be uuid4")
        return

    await manager.connect(websocket)
    try:
        from api.ws_handler import handle_ws

        await handle_ws(websocket, thread_id)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
