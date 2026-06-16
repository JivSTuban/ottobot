# OttoBot — Claude Code Project Instructions

## Autonomous Build Mode

This project uses autonomous build mode. Before starting any phase work, read:

```
.planning/POLICY.md
```

It pre-answers all design decisions for phases 2-7. Do not pause for confirmation on questions already answered there.

## Project

OttoBot — Filipino AI outbound sales agent (Tagalog/Taglish) that books SMB appointments.

**Stack:** Python 3.12 + FastAPI + LangGraph + Supabase + React/Vite + Llama 4 Maverick via LiteLLM/Groq

**Current state:** Phase 1 complete (agent core + demo UI, 68 tests passing).

## How to Run

```bash
./scripts/dev.sh          # starts backend (port 8000) + frontend (port 5173)
pytest                    # backend tests
cd frontend && npm test   # frontend tests
```

Env vars: copy `.env.example` → `.env`, fill in keys.

## Key Patterns

- API keys: `os.environ.get("KEY_NAME")` — never hardcoded
- Thread IDs: UUID v4, validated via `validate_thread_id()` in `api/main.py`
- State mergers: use `Annotated[list, _append_list]` for list fields in `ConversationState`
- Jinja2 templates: use singleton `jinja_env` from `agent/graph.py`, never `make_env()` per-request
- WebSocket send: always check `readyState === WebSocket.OPEN` before calling `.send()`

## To Start Autonomous Build

```
/gsd-autonomous --from 2
```

Reads `.planning/POLICY.md` for all design decisions. Jiv only needs to intervene on blockers.
