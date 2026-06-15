---
phase: 01-agent-core-demo-ui
plan: "07"
subsystem: integration
tags: [bash, devops, documentation, demo, checklist]

requires:
  - 01-05: FastAPI WebSocket server (uvicorn api.main:app, /health, /ws/{thread_id})
  - 01-06: Vite frontend (npm run dev on port 5173)

provides:
  - scripts/dev.sh: single-command bootstrap launching Phoenix + uvicorn + Vite in parallel
  - README.md: quickstart, architecture, testing, demo flow, and env var documentation
  - .planning/phases/01-agent-core-demo-ui/01-DEMO-CHECKLIST.md: 8 AGENT/DEMO requirement sections + NPC 2024-04 AI disclosure item

affects:
  - All AGENT-01..05 and DEMO-01..03 requirements (checklist maps each to manual verification steps)

tech-stack:
  added:
    - bash (scripts/dev.sh — process orchestration with trap/wait)
  patterns:
    - SIGINT/SIGTERM trap kills child PIDs (T-07-03 mitigation)
    - .env and .venv guards at top of dev.sh (fail-fast)
    - Background process logging to /tmp/*.log (not echoed to terminal)

key-files:
  created:
    - scripts/dev.sh
    - README.md
    - .planning/phases/01-agent-core-demo-ui/01-DEMO-CHECKLIST.md
  modified: []

key-decisions:
  - "dev.sh sources .venv/bin/activate rather than echoing .env content — T-07-01 (secrets not leaked to log)"
  - "PIDs collected into PIDS array; cleanup() iterates and kills all on EXIT/SIGINT/SIGTERM — T-07-03 mitigation"
  - "Checklist uses explicit Result: __ pass / __ fail / __ blocked lines — T-07-02 (no silent skip)"

requirements-completed: []

duration: ~15m
completed: "2026-06-15"
---

# Phase 01 Plan 07: Integration Bootstrap + Demo Checklist Summary

**Single-command dev bootstrap (scripts/dev.sh), quickstart README, and a manual demo checklist covering all 8 Phase 1 requirement IDs — ready for human sign-off at Task 2 checkpoint**

## Performance

- **Duration:** ~15 minutes
- **Started:** 2026-06-15T10:31Z
- **Completed (Task 1):** 2026-06-15T10:46Z
- **Tasks:** 1 of 2 complete (Task 2 is a human-verify checkpoint)
- **Files created:** 3

## Accomplishments

- `scripts/dev.sh`: Bash bootstrap with `set -euo pipefail`, `.env` and `.venv` existence guards, background launch of Phoenix + uvicorn + Vite with PID tracking, `trap cleanup SIGINT SIGTERM EXIT`, URL banner, and `wait` for child processes. SIGINT/SIGTERM trap mitigates T-07-03 (orphan processes). `.env` is `source`d, not echoed, mitigating T-07-01 (secrets not leaked to log).
- `README.md`: Quickstart (7-step setup), architecture table (LangGraph/LiteLLM/FastAPI/Vite/Supabase/Phoenix), testing commands (`pytest -x -q` + `npm test -- --run`), demo flow pointer, environment variables table with source URLs, and WebSocket protocol reference for `/ws/{thread_id}`.
- `.planning/phases/01-agent-core-demo-ui/01-DEMO-CHECKLIST.md`: 9-item checklist (AGENT-01..05, DEMO-01..03, NPC 2024-04 AI disclosure). Each item has numbered Steps, Expected outcome, and `Result: __ pass / __ fail / __ blocked` line. Includes automated test path for AGENT-02 (pytest) and live saturation path as alternative.

## Task Commits

1. **Task 1: dev.sh + README.md + demo checklist** — `1bcf400`

## Verification Results

Task 1 automated checks passed:
- `test -x scripts/dev.sh` → executable ✓
- `grep -c 'uvicorn api.main:app' scripts/dev.sh` → 1 ✓
- `grep -c '/ws/{thread_id}' README.md` → 3 ✓
- `grep -cE 'AGENT-0[1-5]|DEMO-0[1-3]' 01-DEMO-CHECKLIST.md` → 24 (≥8) ✓

## Checkpoint Status

**Task 2 is a `checkpoint:human-verify` (gate=blocking).** The agent must run the full demo checklist after populating `.env` with real API keys and starting `scripts/dev.sh`. See checkpoint message for exact steps.

## Deviations from Plan

None — plan executed exactly as written for Task 1.

## Known Stubs

None in the files created by this plan. All checklist items have concrete verification steps; no placeholder text that prevents plan goal.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| T-07-01 mitigated | scripts/dev.sh | `.env` sourced with `source` — not `cat`-ed; secrets not printed to terminal or log |
| T-07-02 mitigated | 01-DEMO-CHECKLIST.md | Each checklist item ends with explicit `Result: __ pass / __ fail / __ blocked`; resume signal requires explicit failure list |
| T-07-03 mitigated | scripts/dev.sh | `trap cleanup SIGINT SIGTERM EXIT` kills child PIDs; no orphan processes on Ctrl+C |
| T-07-04 accepted | scripts/dev.sh | Phoenix failure is non-fatal; uvicorn and Vite continue even if Phoenix fails to start |

## Self-Check: PASSED

Files verified on disk:
- /Users/jivtuban/Desktop/ottobot/scripts/dev.sh — FOUND (executable, contains uvicorn api.main:app)
- /Users/jivtuban/Desktop/ottobot/README.md — FOUND (contains /ws/{thread_id})
- /Users/jivtuban/Desktop/ottobot/.planning/phases/01-agent-core-demo-ui/01-DEMO-CHECKLIST.md — FOUND (24 AGENT/DEMO ID matches)

Commits verified:
- 1bcf400 (Task 1: dev.sh + README.md + demo checklist)
