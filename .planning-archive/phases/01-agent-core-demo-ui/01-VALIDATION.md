---
phase: 1
slug: agent-core-demo-ui
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-11
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (Python agent) + vitest (Vite/React frontend) |
| **Config file** | `pytest.ini` / `vitest.config.ts` — Wave 0 installs |
| **Quick run command** | `pytest agent/tests/ -x -q` |
| **Full suite command** | `pytest agent/tests/ && cd frontend && npm test -- --run` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest agent/tests/ -x -q`
- **After every plan wave:** Run `pytest agent/tests/ && cd frontend && npm test -- --run`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 0 | AGENT-01 | — | N/A | unit | `pytest agent/tests/test_graph.py -x -q` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | AGENT-02 | — | N/A | unit | `pytest agent/tests/test_personas.py -x -q` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | AGENT-03 | — | N/A | unit | `pytest agent/tests/test_litellm_routing.py -x -q` | ❌ W0 | ⬜ pending |
| 1-01-04 | 01 | 2 | AGENT-04 | — | N/A | integration | `pytest agent/tests/test_websocket.py -x -q` | ❌ W0 | ⬜ pending |
| 1-01-05 | 01 | 2 | AGENT-05 | — | N/A | integration | `pytest agent/tests/test_persistence.py -x -q` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 2 | DEMO-01 | — | N/A | e2e | `cd frontend && npm test -- --run` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 2 | DEMO-02 | — | N/A | e2e | `cd frontend && npm test -- --run` | ❌ W0 | ⬜ pending |
| 1-02-03 | 02 | 2 | DEMO-03 | — | N/A | e2e | `cd frontend && npm test -- --run` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `agent/tests/test_graph.py` — stubs for AGENT-01 (LangGraph state machine)
- [ ] `agent/tests/test_personas.py` — stubs for AGENT-02 (Taglish persona injection)
- [ ] `agent/tests/test_litellm_routing.py` — stubs for AGENT-03 (fallback routing)
- [ ] `agent/tests/test_websocket.py` — stubs for AGENT-04 (WebSocket server)
- [ ] `agent/tests/test_persistence.py` — stubs for AGENT-05 (PostgresSaver)
- [ ] `agent/tests/conftest.py` — shared fixtures (BusinessProfile, mock LLM)
- [ ] `frontend/src/__tests__/` — vitest stubs for DEMO-01 through DEMO-03
- [ ] `pytest` + `vitest` install — Wave 0 infrastructure setup

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Taglish code-switching quality | AGENT-02 | LLM output quality cannot be asserted with a unit test | Run demo UI, type Taglish messages, verify agent mirrors language register |
| LiteLLM fallback in live environment | AGENT-03 | Requires real API rate-limit hit, not mockable reliably | Saturate Groq free tier, confirm Gemini takes over in logs |
| Business owner panel real-time sync | DEMO-02 | Requires visual inspection of split-screen UI | Open demo in two browser tabs, send messages, verify right panel updates |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
