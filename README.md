# OttoBot — Phase 1 Demo

OttoBot gives Philippine SMBs (dental, aesthetics, real estate) a Tagalog-speaking AI sales agent that converts leads into booked appointments via web chat. A Filipino lead receives a natural Taglish conversation that ends in a confirmed appointment — without the business owner lifting a finger. Phase 1 delivers the core agent loop, real-time WebSocket streaming, and a split-screen demo UI for investor and customer demonstrations.

---

## Quickstart

### Prerequisites

- Python 3.12 (install via `brew install python@3.12` or pyenv)
- Node.js 20+ with npm

### Setup

```bash
# 1. Clone the repo
git clone <repo-url>
cd ottobot

# 2. Create and activate Python virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# 3. Install Python dependencies
pip install -e .[dev]

# 4. Install frontend dependencies
cd frontend && npm install && cd ..

# 5. Configure environment
cp .env.example .env
# Edit .env — fill in GROQ_API_KEY, GEMINI_API_KEY, MISTRAL_API_KEY, DATABASE_URL, CLERK_JWKS_URL

# 6. Start all services
scripts/dev.sh

# 7. Open the demo
open http://localhost:5173
```

---

## Architecture

| Subsystem | Technology | Responsibility |
|-----------|-----------|----------------|
| Agent core | LangGraph 0.6 + LiteLLM 1.83 | Stateful 7-stage conversation state machine with Groq/Gemini/Mistral routing |
| API server | FastAPI 0.128 + uvicorn | WebSocket `/ws/{thread_id}` streaming token/state/system_alert events |
| Persistence | LangGraph AsyncPostgresSaver → Neon Postgres | Conversation checkpoints survive server restart |
| Frontend | Vite 8 + React 19 + TypeScript 6 | Split-screen demo: lead chat (left) + owner panel with stage badge (right) |
| Tracing | Arize Phoenix + OpenTelemetry OTLP | Per-request LLM traces, latency, and token counts at http://localhost:6006 |
| Images | Gemini Flash (Plan 02) | Generated persona avatars and industry background images |

---

## Testing

```bash
# Backend (pytest)
pytest -x -q

# Frontend (vitest)
cd frontend && npm test -- --run
```

Expected: 0 failures in both suites.

---

## Demo Flow

See `.planning/phases/01-agent-core-demo-ui/01-DEMO-CHECKLIST.md` for the full manual verification checklist mapped to every AGENT-NN and DEMO-NN requirement.

Quick demo path:
1. Open http://localhost:5173
2. Select an industry (Dental / Aesthetics / Real Estate) and click **Simulan**
3. Type a Taglish lead message in the left panel (e.g., "Hi po, magkano ang whitening?")
4. Watch streamed tokens appear in real-time; stage badge updates in the right owner panel
5. Type "gusto ko mag-book bukas" — escalation alert appears within 5 seconds

---

## Environment Variables

Copy `.env.example` → `.env` and fill in the following:

| Variable | Description | Where to Get It |
|----------|-------------|-----------------|
| `GROQ_API_KEY` | Groq API key (primary LLM — Llama 4 Maverick) | https://console.groq.com/keys |
| `GEMINI_API_KEY` | Google Gemini API key (fallback LLM + image generation) | https://aistudio.google.com/app/apikey |
| `MISTRAL_API_KEY` | Mistral API key (secondary fallback) | https://console.mistral.ai/api-keys/ |
| `DATABASE_URL` | Neon pooled PostgreSQL connection string | Neon console → Project → Connection string |
| `DATABASE_DIRECT_URL` | Neon direct PostgreSQL connection (for migrations) | Neon console → Project → Direct connection |
| `CLERK_JWKS_URL` | Clerk JWKS public key URL for token verification | Clerk dashboard → API Keys → JWKS Public Key URL |
| `CLERK_ISSUER` | Clerk issuer URL for token claims validation | Clerk dashboard → API Keys section |
| `PHOENIX_HOST` | Phoenix tracing host (optional, defaults to localhost) | Leave blank for local dev |

---

## WebSocket Protocol

Connect to `/ws/{thread_id}` where `thread_id` is a UUID v4. The server rejects non-UUID strings with WebSocket close code 1008.

**Send (client → server):**
```json
{"industry": "dental", "text": "Hi po, magkano ang whitening?"}
```

**Receive (server → client):**
```json
{"type": "token", "content": "Kumusta"}
{"type": "state", "stage": "qualifying", "escalated": false}
{"type": "system_alert", "message": "AI assistant: Ito ay AI..."}
```

See `/ws/{thread_id}` for the full event schema.
