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

import jwt as pyjwt
import psycopg
from fastapi import Depends, FastAPI, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from agent.graph import builder
from api.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

# Set during lifespan startup; None at import time (tests must patch this).
compiled_graph = None

manager = ConnectionManager()

# ---------------------------------------------------------------------------
# JWT authentication (Phase 6 — mobile app endpoints)
# ---------------------------------------------------------------------------

security = HTTPBearer()


async def get_business_id_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Decode Supabase JWT Bearer token and resolve business_id from owner_email.

    T-06-01, T-06-02, T-06-03 mitigations:
    - business_id is NEVER trusted from request body — always derived from JWT sub
    - JWT decoded server-side using SUPABASE_JWT_SECRET
    - owner_email → businesses table join verifies the token owner has a business

    Raises HTTPException(401) for:
    - Missing or invalid JWT
    - SUPABASE_JWT_SECRET not configured
    - No business found for the token's owner_email
    """
    jwt_secret = os.environ.get("SUPABASE_JWT_SECRET", "")
    if not jwt_secret:
        raise HTTPException(status_code=401, detail="Auth not configured")

    try:
        payload = pyjwt.decode(
            credentials.credentials,
            jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    owner_email = payload.get("sub", "")
    if not owner_email:
        raise HTTPException(status_code=401, detail="Invalid token")

    db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
    if not db_uri:
        raise HTTPException(status_code=401, detail="Business not found for this token")

    async with await psycopg.AsyncConnection.connect(db_uri) as conn:
        cursor = await conn.execute(
            "SELECT id FROM businesses WHERE owner_email = %s LIMIT 1",
            (owner_email,),
        )
        row = await cursor.fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Business not found for this token")

    return str(row[0])


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


async def setup_escalation_tables() -> None:
    """
    Idempotently create the escalations table.

    Called from lifespan after setup_appointment_tables().
    No-ops when DB URI is absent (test environments).
    """
    db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
    if not db_uri:
        return
    async with await psycopg.AsyncConnection.connect(db_uri) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS escalations (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                thread_id TEXT NOT NULL,
                business_id TEXT NOT NULL,
                lead_phone TEXT NOT NULL DEFAULT '',
                conversation_summary TEXT NOT NULL DEFAULT '',
                triggered_at TIMESTAMPTZ DEFAULT NOW(),
                outcome TEXT NOT NULL DEFAULT 'not_called'
                    CHECK (outcome IN ('called', 'not_called', 'ignored')),
                UNIQUE (thread_id)
            )
        """)


async def setup_onboarding_tables() -> None:
    """
    Idempotently create the businesses table for onboarding.

    Called from lifespan after setup_channel_tables().
    No-ops when DB URI is absent (test environments).
    """
    db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
    if not db_uri:
        return
    async with await psycopg.AsyncConnection.connect(db_uri) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS businesses (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                owner_email TEXT NOT NULL,
                name TEXT NOT NULL,
                industry TEXT NOT NULL CHECK (industry IN ('dental', 'aesthetics', 'real_estate')),
                phone TEXT NOT NULL DEFAULT '',
                city TEXT NOT NULL DEFAULT '',
                services TEXT NOT NULL DEFAULT '',
                pricing TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE (owner_email)
            )
        """)


async def setup_channel_tables() -> None:
    """
    Idempotently create leads and messages tables for real channel ingestion.

    Called from lifespan after setup_escalation_tables().
    No-ops when DB URI is absent (test environments).
    """
    db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
    if not db_uri:
        return
    async with await psycopg.AsyncConnection.connect(db_uri) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                phone TEXT NOT NULL,
                name TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'unknown'
                    CHECK (source IN ('csv_upload', 'lead_form', 'sms_inbound', 'fb_messenger', 'unknown')),
                business_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new'
                    CHECK (status IN ('new', 'in_progress', 'booked', 'escalated', 'closed')),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE (phone, business_id)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                thread_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)


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


class PushTokenRequest(BaseModel):
    expo_token: str
    business_id: str = ""  # ignored — business_id always extracted from JWT


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
            await setup_escalation_tables()
            await setup_channel_tables()
            await setup_onboarding_tables()
            await setup_push_token_table()
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


# ---------------------------------------------------------------------------
# Channel processing helper (shared by SMS + Facebook webhooks)
# ---------------------------------------------------------------------------


async def process_channel_message(
    thread_id: str,
    user_text: str,
    industry: str,
    business_id: str,
) -> str:
    """
    Run the LangGraph agent for a single channel message and return the reply text.

    Used by SMS and Facebook webhooks — shares the same compiled_graph as the
    WebSocket handler. Returns empty string if graph is not yet compiled.

    Thread ID should be deterministic_thread_id(phone, business_id) for real channels.
    """
    if compiled_graph is None:
        return ""

    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "messages": [{"role": "user", "content": user_text}],
        "industry": industry,
        "message_timestamps": [],
    }

    import time as _time
    initial_state["message_timestamps"] = [_time.time()]

    reply_parts: list[str] = []
    async for update in compiled_graph.astream(initial_state, config=config, stream_mode="updates"):
        for _node, node_update in update.items():
            for msg in node_update.get("messages", []):
                role = (
                    msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)
                    or ({"ai": "assistant"}.get(getattr(msg, "type", ""), "user"))
                )
                content = (
                    msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")
                )
                if role in ("assistant", "ai") and content:
                    reply_parts.append(content)

    return " ".join(reply_parts)


# ---------------------------------------------------------------------------
# SMS webhook (Semaphore PH)
# ---------------------------------------------------------------------------


class SmsWebhookRequest(BaseModel):
    message: str
    senderNumber: str
    receiverNumber: str = ""
    network: str = ""


@app.post("/webhook/sms")
async def sms_webhook(req: SmsWebhookRequest):
    """
    Receive inbound SMS from Semaphore PH webhook.

    Semaphore posts fields: message, senderNumber, receiverNumber, network.
    The sender's phone number is used to derive a deterministic thread_id.
    Business is identified by BUSINESS_ID env var (Phase 5 will auth-gate this).
    """
    from api.channels import deterministic_thread_id, send_sms

    business_id = os.environ.get("BUSINESS_ID", "")
    industry = os.environ.get("DEFAULT_INDUSTRY", "dental")
    thread_id = deterministic_thread_id(req.senderNumber, business_id)

    reply = await process_channel_message(thread_id, req.message, industry, business_id)
    if reply:
        await send_sms(req.senderNumber, reply)

    return {"status": "ok", "thread_id": thread_id}


# ---------------------------------------------------------------------------
# Facebook Messenger webhook
# ---------------------------------------------------------------------------


@app.get("/webhook/facebook")
async def facebook_webhook_verify(
    hub_mode: str = "",
    hub_challenge: str = "",
    hub_verify_token: str = "",
):
    """
    Meta webhook verification (GET). Returns hub.challenge when verify token matches.

    Query param names contain dots — FastAPI maps them to underscore params.
    """
    verify_token = os.environ.get("FACEBOOK_VERIFY_TOKEN", "")
    if hub_mode == "subscribe" and hub_challenge and hub_verify_token == verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook/facebook")
async def facebook_webhook(payload: dict):
    """
    Receive Facebook Messenger messages from Meta webhook.

    Iterates entries and messaging objects, routes each to the agent, replies via Graph API.
    """
    from api.channels import deterministic_thread_id, send_facebook_message

    business_id = os.environ.get("BUSINESS_ID", "")
    industry = os.environ.get("DEFAULT_INDUSTRY", "dental")

    for entry in payload.get("entry", []):
        for event in entry.get("messaging", []):
            sender_id: str = event.get("sender", {}).get("id", "")
            message_obj = event.get("message", {})
            text: str = message_obj.get("text", "")
            if not sender_id or not text:
                continue

            thread_id = deterministic_thread_id(f"fb:{sender_id}", business_id)
            reply = await process_channel_message(thread_id, text, industry, business_id)
            if reply:
                await send_facebook_message(sender_id, reply)

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Lead ingestion — CSV upload + Meta Lead Ads webhook
# ---------------------------------------------------------------------------


@app.post("/leads/upload")
async def upload_leads(
    business_id: str,
    file: UploadFile,
):
    """
    Accept a CSV file with columns: phone (required), name (optional).

    Upserts each row into the leads table and fires an outbound SMS to kick off
    the conversation. business_id passed as query param.

    T-02-04: validate_business_id() guard applied.
    """
    import csv
    import io

    from api.channels import deterministic_thread_id, send_sms

    if not validate_business_id(business_id):
        raise HTTPException(status_code=400, detail="business_id must be a valid UUID v4")

    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))

    db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
    industry = os.environ.get("DEFAULT_INDUSTRY", "dental")

    upserted: int = 0
    for row in reader:
        phone = (row.get("phone") or "").strip()
        if not phone:
            continue
        name = (row.get("name") or "").strip()

        if db_uri:
            async with await psycopg.AsyncConnection.connect(db_uri) as conn:
                await conn.execute(
                    """
                    INSERT INTO leads (phone, name, source, business_id, status)
                    VALUES (%s, %s, 'csv_upload', %s, 'new')
                    ON CONFLICT (phone, business_id) DO NOTHING
                    """,
                    (phone, name, business_id),
                )

        thread_id = deterministic_thread_id(phone, business_id)
        greeting = os.environ.get(
            "OUTBOUND_GREETING",
            "Magandang araw po! Ako si OttoBot, tumutulong po ako para sa inyong appointment.",
        )
        await send_sms(phone, greeting)
        upserted += 1

    return {"status": "ok", "upserted": upserted}


class LeadFormWebhookRequest(BaseModel):
    """Meta Lead Ads webhook payload (simplified)."""
    object: str = "page"
    entry: list = []


@app.post("/webhook/lead-form")
async def lead_form_webhook(payload: LeadFormWebhookRequest):
    """
    Ingest leads from Meta Lead Ads webhook.

    Expects Meta Lead Ads format: entry[].changes[].value.leads[].field_data[].
    Upserts each lead and fires the first outbound SMS.
    """
    from api.channels import deterministic_thread_id, send_sms

    business_id = os.environ.get("BUSINESS_ID", "")
    industry = os.environ.get("DEFAULT_INDUSTRY", "dental")
    db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")

    ingested: int = 0
    for entry in payload.entry:
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for lead in value.get("leads", []):
                # Extract phone and name from field_data
                field_data: list = lead.get("field_data", [])
                fields = {f["name"]: f.get("values", [""])[0] for f in field_data}
                phone = fields.get("phone_number", fields.get("phone", "")).strip()
                name = fields.get("full_name", fields.get("name", "")).strip()
                if not phone:
                    continue

                if db_uri:
                    async with await psycopg.AsyncConnection.connect(db_uri) as conn:
                        await conn.execute(
                            """
                            INSERT INTO leads (phone, name, source, business_id, status)
                            VALUES (%s, %s, 'lead_form', %s, 'new')
                            ON CONFLICT (phone, business_id) DO NOTHING
                            """,
                            (phone, name, business_id),
                        )

                thread_id = deterministic_thread_id(phone, business_id)
                greeting = os.environ.get(
                    "OUTBOUND_GREETING",
                    "Magandang araw po! Ako si OttoBot, tumutulong po ako para sa inyong appointment.",
                )
                await send_sms(phone, greeting)
                ingested += 1

    return {"status": "ok", "ingested": ingested}


# ---------------------------------------------------------------------------
# Onboarding endpoints (Phase 5)
# ---------------------------------------------------------------------------


class OnboardingData(BaseModel):
    owner_email: str
    name: str
    industry: str
    phone: str = ""
    city: str = ""
    services: str = ""
    pricing: str = ""
    agent_name: str = ""


@app.post("/onboarding/preview")
async def onboarding_preview(data: OnboardingData):
    """
    Return a rendered persona preview using the submitted onboarding data.

    Uses the same Jinja2 env as the agent (singleton jinja_env from graph.py).
    Returns {"preview": "<rendered system prompt>"}.

    Industry must be one of dental | aesthetics | real_estate.
    """
    from agent.graph import jinja_env
    from agent.models import BusinessProfile, Industry

    valid_industries = {i.value for i in Industry}
    if data.industry not in valid_industries:
        raise HTTPException(
            status_code=400,
            detail=f"industry must be one of: {', '.join(valid_industries)}",
        )

    services_list = [s.strip() for s in data.services.split(",") if s.strip()] or ["service"]
    agent_name = data.agent_name or f"Ate {data.name.split()[0]}" if data.name else "Ate Ana"

    profile = BusinessProfile(
        agent_name=agent_name,
        business_name=data.name or "My Business",
        industry=Industry(data.industry),
        services=services_list,
        pricing=data.pricing or "varies",
        phone=data.phone or "+63917XXXXXXX",
    )
    preview_text = profile.render_system_prompt(jinja_env)
    return {"preview": preview_text}


@app.post("/onboarding/submit")
async def onboarding_submit(data: OnboardingData):
    """
    Store or update a business record in Supabase.

    Uses UPSERT on owner_email so re-submitting the form updates the record.
    Returns {"status": "ok", "business_id": "<uuid>"}.
    """
    valid_industries = {"dental", "aesthetics", "real_estate"}
    if data.industry not in valid_industries:
        raise HTTPException(status_code=400, detail="Invalid industry")
    if not data.owner_email or "@" not in data.owner_email:
        raise HTTPException(status_code=400, detail="Invalid owner_email")

    db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
    if not db_uri:
        return {"status": "ok", "business_id": str(uuid.uuid4())}

    async with await psycopg.AsyncConnection.connect(db_uri) as conn:
        cursor = await conn.execute(
            """
            INSERT INTO businesses (owner_email, name, industry, phone, city, services, pricing)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (owner_email)
            DO UPDATE SET
                name = EXCLUDED.name,
                industry = EXCLUDED.industry,
                phone = EXCLUDED.phone,
                city = EXCLUDED.city,
                services = EXCLUDED.services,
                pricing = EXCLUDED.pricing
            RETURNING id
            """,
            (
                data.owner_email,
                data.name,
                data.industry,
                data.phone,
                data.city,
                data.services,
                data.pricing,
            ),
        )
        row = await cursor.fetchone()
        business_id = str(row[0]) if row else str(uuid.uuid4())

    return {"status": "ok", "business_id": business_id}


# ---------------------------------------------------------------------------
# Mobile app endpoints (Phase 6) — all require JWT auth
# ---------------------------------------------------------------------------


async def setup_push_token_table() -> None:
    """
    Idempotently create the business_push_tokens table for mobile push notifications.

    Called from lifespan after setup_onboarding_tables().
    No-ops when DB URI is absent (test environments).
    """
    db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
    if not db_uri:
        return
    async with await psycopg.AsyncConnection.connect(db_uri) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS business_push_tokens (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                business_id TEXT NOT NULL UNIQUE,
                expo_token TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)


@app.get("/leads")
async def get_leads(business_id: str = Depends(get_business_id_from_token)):
    """
    Return all leads for the authenticated business owner.

    T-06-01 mitigation: business_id from JWT sub → businesses join only.
    T-06-04 mitigation: parameterized query.
    Returns {"leads": [...]} with status field per lead for mobile SectionList grouping.
    """
    if not validate_business_id(business_id):
        raise HTTPException(status_code=400, detail="business_id must be a valid UUID v4")

    db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
    if not db_uri:
        return {"leads": [], "grouped": {}}

    async with await psycopg.AsyncConnection.connect(db_uri) as conn:
        cursor = await conn.execute(
            "SELECT id, phone, status, created_at FROM leads WHERE business_id = %s ORDER BY created_at DESC",
            (business_id,),
        )
        rows = await cursor.fetchall()

    leads_list = [
        {"id": str(r[0]), "phone": r[1], "status": r[2], "created_at": str(r[3])}
        for r in rows
    ]
    return {"leads": leads_list}


@app.get("/leads/{lead_id}/messages")
async def get_lead_messages(
    lead_id: str,
    business_id: str = Depends(get_business_id_from_token),
):
    """
    Return messages for a lead, newest-first (for FlatList inverted on mobile).

    T-06-02 mitigation: lead ownership verified via leads table before fetching messages.
    T-06-04 mitigation: parameterized queries only.
    Returns {"messages": [...]} ordered by created_at DESC.

    Note: messages table links to leads via thread_id = deterministic_thread_id(phone, business_id).
    We resolve: lead_id → phone → thread_id → messages.
    """
    if not validate_thread_id(lead_id):
        raise HTTPException(status_code=400, detail="lead_id must be a valid UUID v4")

    db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
    if not db_uri:
        return {"messages": []}

    from api.channels import deterministic_thread_id

    async with await psycopg.AsyncConnection.connect(db_uri) as conn:
        # Ownership check: verify lead belongs to authenticated business
        lead_cursor = await conn.execute(
            "SELECT phone FROM leads WHERE id = %s AND business_id = %s LIMIT 1",
            (lead_id, business_id),
        )
        lead_row = await lead_cursor.fetchone()
        if not lead_row:
            raise HTTPException(status_code=404, detail="Lead not found")

        phone = lead_row[0]
        thread_id = deterministic_thread_id(phone, business_id)

        cursor = await conn.execute(
            """
            SELECT id, content, role, created_at
            FROM messages
            WHERE thread_id = %s
            ORDER BY created_at DESC
            """,
            (thread_id,),
        )
        rows = await cursor.fetchall()

    messages = [
        {"id": str(r[0]), "content": r[1], "role": r[2], "created_at": str(r[3])}
        for r in rows
    ]
    return {"messages": messages}


@app.post("/push/send")
async def register_push_token(
    req: PushTokenRequest,
    business_id: str = Depends(get_business_id_from_token),
):
    """
    Register or update an Expo push token for the authenticated business.

    T-06-03 mitigation: business_id from JWT only — body business_id ignored.
    T-06-05 mitigation: expo_token format validated before storage.
    One token per business (UPSERT on business_id).
    """
    if not req.expo_token.startswith("ExponentPushToken["):
        raise HTTPException(status_code=422, detail="Invalid Expo push token format")

    db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
    if not db_uri:
        return {"status": "ok", "stored": False}

    async with await psycopg.AsyncConnection.connect(db_uri) as conn:
        await conn.execute(
            """
            INSERT INTO business_push_tokens (id, business_id, expo_token, created_at)
            VALUES (gen_random_uuid(), %s, %s, NOW())
            ON CONFLICT (business_id) DO UPDATE SET expo_token = EXCLUDED.expo_token, created_at = NOW()
            """,
            (business_id, req.expo_token),
        )

    return {"status": "ok", "stored": True}
