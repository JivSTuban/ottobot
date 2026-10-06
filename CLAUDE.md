# OttoBot — Claude Code Project Instructions

## Workflow

This project runs on the `/dev` system. Load context before acting; log learnings after.

- Project KB (Obsidian): `~/Second Brain/Projects/ottobot/` — `NOW`, `DECISIONS`, `WORKS`, `FAILURES`, `TASKS`, `PLAN`, `JOURNAL`
- Start a task: `/dev <source>` · debug: `/dev-debug` · review diff: `/dev-review` · ship: `/dev-ship`
- Read `NOW.md` + `TASKS.md` for current state; `DECISIONS.md`/`WORKS.md`/`FAILURES.md` for constraints and traps before writing code.
- The old GSD autonomous-build artifacts are archived read-only at `.planning-archive/` (POLICY.md there still holds the pre-answered per-phase design decisions for phases 7–8).

## Project

OttoBot — Filipino AI outbound sales agent (Tagalog/Taglish) that books SMB appointments.

**Stack:** Python 3.12 + FastAPI + LangGraph + Supabase + React/Vite + Expo + Llama 4 Maverick via LiteLLM/Groq

**Current state:** Phases 1–6 shipped (144 tests passing on `feat/neon-clerk-migration`). Migrating Supabase → Neon + Clerk (plan Tasks 7–10 open). Active goal: Filipinohomes pilot MVP, see `docs/PRD-filipinohomes-mvp.md` (supersedes the archived v1 requirements; Phase 07/08 are out of scope for it). Research record: `docs/research/2026-10-06-filipinohomes-deep-research.md`.

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

## To Continue Work

```
/dev            # start a session — gather → context → plan → confirm → execute → verify → log
```

Reads the Obsidian KB for state and constraints. See `PLAN.md` for the current slice.
