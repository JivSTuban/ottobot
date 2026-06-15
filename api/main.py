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

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from agent.graph import builder
from api.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

# Set during lifespan startup; None at import time (tests must patch this).
compiled_graph = None

manager = ConnectionManager()


def validate_thread_id(thread_id: str) -> bool:
    """
    Return True iff thread_id is a valid UUID version 4.

    Used by the WebSocket route to reject non-uuid4 thread_ids (V3 ASVS
    Session Management, T-05-01 mitigation).
    """
    try:
        uuid.UUID(thread_id, version=4)
        return True
    except (ValueError, AttributeError):
        return False


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
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    async with AsyncPostgresSaver.from_conn_string(
        os.environ["SUPABASE_DB_URI"]
    ) as checkpointer:
        await checkpointer.setup()  # idempotent migration runner (Pitfall 2)
        compiled_graph = builder.compile(checkpointer=checkpointer)
        logger.info("LangGraph compiled with AsyncPostgresSaver")
        yield
    # Connection closes here; compiled_graph becomes invalid after this point.


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    """Health check endpoint — returns whether the graph is compiled and ready."""
    return {"ok": True, "compiled": compiled_graph is not None}


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
