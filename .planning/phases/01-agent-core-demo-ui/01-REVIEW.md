---
phase: 01-agent-core-demo-ui
reviewed: 2026-06-16T00:00:00Z
depth: standard
files_reviewed: 31
files_reviewed_list:
  - agent/escalation.py
  - agent/graph.py
  - agent/llm.py
  - agent/models.py
  - agent/stage_detection.py
  - agent/state.py
  - api/connection_manager.py
  - api/guardrails.py
  - api/main.py
  - api/ws_handler.py
  - evals/check_thresholds.py
  - evals/judge_config.py
  - frontend/src/App.tsx
  - frontend/src/assets/personas.ts
  - frontend/src/index.css
  - frontend/src/IndustrySelector.tsx
  - frontend/src/LeadChat.tsx
  - frontend/src/OwnerPanel.tsx
  - frontend/src/types.ts
  - frontend/src/useWebSocket.ts
  - scripts/dev.sh
  - tests/conftest.py
  - tests/test_escalation.py
  - tests/test_graph_module.py
  - tests/test_graph_routing.py
  - tests/test_llm_router.py
  - tests/test_models.py
  - tests/test_persistence.py
  - tests/test_stage_detection.py
  - tests/test_stage_routing.py
  - tests/test_versions.py
  - tests/test_websocket.py
findings:
  critical: 5
  warning: 6
  info: 3
  total: 14
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-06-16T00:00:00Z
**Depth:** standard
**Files Reviewed:** 31
**Status:** issues_found

## Summary

Reviewed agent core, API layer, frontend, and eval harness. The implementation is well-structured with clear separation of concerns. Five blockers were found: a permanently broken escalation signal, a security bypass in UUID validation, a missing null-guard for graph startup races, silent message loss on WebSocket state changes, and a wrong condition in the AI disclosure guardrail. Six warnings and three info items cover additional correctness and quality gaps.

---

## Critical Issues

### CR-01: `message_timestamps` reducer missing — cadence signal (signal_3) permanently broken

**File:** `agent/state.py:27`, `api/ws_handler.py:74`

**Issue:** `ConversationState.message_timestamps` is declared as `list[float]` with no `Annotated` reducer. LangGraph replaces plain list fields on state merge rather than appending. `ws_handler.py:74` seeds `message_timestamps: [time.time()]` (one entry) every turn. The checkpointed state is overwritten with a single-element list each turn, so `len(timestamps) >= 2` in `escalation_scorer` is always `False`. Signal_3 (fast cadence) never fires. The 2-of-3 scorer silently degrades to 1-of-2 with no warning, and fast-cadence leads are systematically under-escalated.

**Fix:** Add an append reducer to `ConversationState`:
```python
# agent/state.py
def _append_list(existing: list, new: list) -> list:
    return (existing or []) + (new or [])

class ConversationState(TypedDict):
    messages: Annotated[list, add_messages]
    stage: STAGES
    thread_id: str
    escalated: bool
    visit_count: dict[str, int]
    message_timestamps: Annotated[list[float], _append_list]  # was plain list[float]
    system_alert: str
```

---

### CR-02: `validate_thread_id` accepts non-uuid4 UUIDs — security bypass of session isolation requirement

**File:** `api/main.py:37`

**Issue:** `uuid.UUID(thread_id, version=4)` does **not** reject UUID v1/v3/v5 strings. Python's `uuid.UUID` coerces the version bits to v4 and returns successfully without raising `ValueError`. A caller can pass a deterministic UUID v3/v5 (derived from a known namespace + name) and it passes the check, bypassing session isolation (T-05-01). An attacker who can predict another user's UUID v3/v5 thread_id can join their conversation.

**Fix:**
```python
def validate_thread_id(thread_id: str) -> bool:
    try:
        val = uuid.UUID(thread_id)    # parse WITHOUT version coercion
        return val.version == 4       # explicit version check
    except (ValueError, AttributeError):
        return False
```

---

### CR-03: `compiled_graph` is `None` before lifespan completes — `handle_ws` crashes with `AttributeError`

**File:** `api/main.py:24`, `api/ws_handler.py:80`

**Issue:** `compiled_graph = None` at module import time. If a WebSocket connection arrives before the lifespan startup completes (slow Postgres, startup race), `app_state.compiled_graph.astream(...)` at `ws_handler.py:80` raises `AttributeError: 'NoneType' object has no attribute 'astream'`. This exception is unhandled inside `handle_ws` and will propagate as an unclean WebSocket close with no user-visible diagnostic. The `aget_state` call at line 106 has the same issue.

**Fix:** Guard at the top of `handle_ws`:
```python
async def handle_ws(websocket: WebSocket, thread_id: str) -> None:
    if app_state.compiled_graph is None:
        await websocket.send_json({
            "type": "system_alert",
            "content": "Server is still initializing. Subukan ulit mamaya.",
        })
        return
    ...
```

---

### CR-04: WebSocket `send` calls `ws.send()` on a non-OPEN socket — silently drops or throws

**File:** `frontend/src/useWebSocket.ts:117-122`

**Issue:** The `else if` branch (lines 119-122) calls `wsRef.current.send(JSON.stringify({ text, industry }))` when `readyState !== WebSocket.OPEN`. Calling `send()` on a CONNECTING (0), CLOSING (2), or CLOSED (3) socket throws `InvalidStateError`. The exception is uncaught. The comment says "Queue the send for when the socket opens" but no queue exists — the message is silently lost after the throw.

**Fix:** Either drop the else branch and surface an error, or implement real queuing:
```ts
const send = useCallback((text: string, industry: IndustryKey) => {
  setMessages((prev) => [...prev, { role: "user", content: text }]);
  if (wsRef.current?.readyState === WebSocket.OPEN) {
    wsRef.current.send(JSON.stringify({ text, industry }));
  } else {
    // Socket not ready — surface error rather than silently drop
    setWsError(true);
  }
}, []);
```

---

### CR-05: AI disclosure guardrail checks post-turn stage — condition never true, guardrail never executes

**File:** `api/ws_handler.py:111`

**Issue:** The guardrail at line 111 checks `if stage == "intro"`, where `stage` is read from `final_state.values` — the **post-turn** state after `agent_node` has already advanced `stage` to `"qualify"`. On the first user turn, `_compute_next_stage` advances stage from `intro` to `qualify`, so `stage` from `aget_state` is `"qualify"`, never `"intro"`. The AI disclosure check (NPC 2024-04 compliance) therefore never executes at runtime.

**Fix:** Key the check on message count, not on post-turn stage:
```python
# After: final_state = await app_state.compiled_graph.aget_state(config)
values = final_state.values if final_state else {}
stage = values.get("stage", "intro")
all_messages = values.get("messages", [])
# First turn = exactly 2 messages (user + assistant) in state
is_first_turn = len(all_messages) <= 2

if is_first_turn and profile is not None:
    from agent.graph import jinja_env
    rendered_system = profile.render_system_prompt(jinja_env)
    if not check_ai_disclosure(rendered_system):
        ...
```

---

## Warnings

### WR-01: `industry` field missing from `ConversationState` — persona resets to dental after first turn

**File:** `agent/state.py`, `agent/graph.py:187`

**Issue:** `ConversationState` has no `industry` field. `ws_handler.py` passes `"industry"` in `initial_state` each turn, but LangGraph drops keys not declared in the TypedDict. After the first turn the checkpointed state has no `industry` key. `agent_node` calls `state.get("industry", "dental")`, which silently returns `"dental"` for aesthetics and real_estate sessions. The dental persona is used for all industries after turn 1.

**Fix:** Add `industry: str` to `ConversationState` and pass it through properly.

---

### WR-02: `_429_backoff` dict grows unbounded — memory leak in long-running process

**File:** `api/ws_handler.py:27`

**Issue:** `_429_backoff` is a module-level dict that accumulates entries forever. Every unique thread_id that triggers a 429 adds a permanent entry. The dict is never pruned. In production with many sessions this is an unbounded memory leak.

**Fix:** Prune expired entries on each write:
```python
_429_backoff[thread_id] = time.time() + 30
now = time.time()
for k in [k for k, v in _429_backoff.items() if v < now]:
    del _429_backoff[k]
```

---

### WR-03: `evals/check_thresholds.py` silently reports 100% pass when no tests match a dimension

**File:** `evals/check_thresholds.py:38`

**Issue:** `compute_pass_rate` returns `1.0` when `dimension_tests` is empty. If the promptfoo results file has a different structure (description field named differently, etc.), every critical dimension reports PASS with 100% coverage when zero tests were actually run. This defeats the CI gate entirely.

**Fix:** Return `None` and treat no-match as a SKIP/WARN rather than PASS:
```python
if not dimension_tests:
    return None  # signal: no tests found for this dimension

# In main():
rate = compute_pass_rate(results, dim)
if rate is None:
    print(f"  {dim:<30} NO TESTS  [FAIL]")
    failed_dimensions.append(dim)
    continue
```

---

### WR-04: `useWebSocket` `onclose` is a no-op — unexpected server disconnects invisible to user

**File:** `frontend/src/useWebSocket.ts:59-61`

**Issue:** `ws.onclose` has only a comment and no implementation. If the server closes the connection with a non-1000 code (e.g., 1008 on invalid thread_id after acceptance, or server crash), `wsError` stays `false`, no error banner is shown, and `send()` will subsequently throw (CR-04). `onerror` only fires for network-layer errors, not clean-close events with error codes.

**Fix:**
```ts
ws.onclose = (event) => {
  if (event.code !== 1000) {
    setWsError(true);
  }
};
```

---

### WR-05: `detect_stage_structured` instructor-path fallthrough to JSON-mode is prevented by `if/else` structure

**File:** `agent/stage_detection.py:74-113`

**Issue:** When `patched_router is not None` and all 3 instructor attempts fail, the `if` block exhausts and Python skips the `else` block (JSON-mode), jumping directly to the shared fallback at line 117. The JSON-mode fallback is never attempted when instructor is installed but fails. Correct behavior would try both backends before giving up.

**Fix:** Restructure so JSON-mode is a secondary fallback regardless of instructor availability:
```python
# Try instructor path first if available
if patched_router is not None:
    for attempt in range(_MAX_ATTEMPTS):
        try:
            result = await patched_router.chat.completions.create(...)
            return result
        except Exception as exc:
            logger.warning(...)
    # Instructor exhausted — fall through to json-mode

# JSON-mode (fallback or primary when instructor unavailable)
for attempt in range(_MAX_ATTEMPTS):
    try:
        response = await router.acompletion(...)
        return StageDetectionOutput.model_validate_json(response.choices[0].message.content)
    except Exception as exc:
        logger.warning(...)

logger.error("stage detection failed after all attempts")
return StageDetectionOutput(next_stage=current_stage, confidence=0.0, reasoning="fallback")
```

---

### WR-06: `make_env()` called inside `handle_ws` per request — creates a new Jinja2 Environment per message

**File:** `api/ws_handler.py:103-106`

**Issue:** Lines 103-106 call `make_env()` to create a new `Environment` with `FileSystemLoader` for every intro-stage message processed. A `jinja_env` singleton already exists in `agent/graph.py:45`. This is unnecessary repeated filesystem I/O.

**Fix:**
```python
# Replace:
from agent.models import make_env
env = make_env()
rendered_system = profile.render_system_prompt(env)

# With:
from agent.graph import jinja_env
rendered_system = profile.render_system_prompt(jinja_env)
```

---

## Info

### IN-01: `BOOKING_PHRASES_FAST` duplicates a subset of `escalation.BOOKING_PHRASES` — will drift

**File:** `agent/graph.py:47-60`

**Issue:** `BOOKING_PHRASES_FAST` (12 entries) is a hand-maintained subset of `BOOKING_PHRASES` in `escalation.py` (18 entries). These two lists are separate definitions that will drift. Phrases added to `BOOKING_PHRASES` but not `BOOKING_PHRASES_FAST` are caught by the 2-of-3 scorer but not the fast-rule path in `_compute_next_stage`.

**Fix:** Import from escalation.py as the single source:
```python
from agent.escalation import BOOKING_PHRASES as BOOKING_PHRASES_FAST
```

---

### IN-02: `tokens` state in `useWebSocket` accumulates unboundedly and is never consumed

**File:** `frontend/src/useWebSocket.ts:44, 73`

**Issue:** `setTokens((prev) => [...prev, tokenContent])` grows forever across the session lifetime. `tokens` is exported from the hook but never used in `App.tsx`, `LeadChat.tsx`, or `OwnerPanel.tsx`. It is dead exported state.

**Fix:** Remove `tokens` from state and the return object, or reset it on each `state` event if retained for future use.

---

### IN-03: `wsUrl` hardcodes `ws://localhost:8000` — breaks all non-local environments

**File:** `frontend/src/App.tsx:29`

**Issue:** `\`ws://localhost:8000/ws/${threadId}\`` bypasses the Vite proxy and hard-targets the local dev server. Any staging, production, or device-to-device access will fail immediately.

**Fix:**
```ts
const wsUrl = useMemo(
  () => `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws/${threadId}`,
  [threadId]
);
```

---

_Reviewed: 2026-06-16T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
