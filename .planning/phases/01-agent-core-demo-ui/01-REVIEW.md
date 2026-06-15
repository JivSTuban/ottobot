---
phase: 01-agent-core-demo-ui
reviewed: 2026-06-15T00:00:00Z
depth: standard
files_reviewed: 39
files_reviewed_list:
  - agent/escalation.py
  - agent/graph.py
  - agent/llm.py
  - agent/models.py
  - agent/prompts/aesthetics.j2
  - agent/prompts/base.j2
  - agent/prompts/dental.j2
  - agent/prompts/real_estate.j2
  - agent/stage_detection.py
  - agent/state.py
  - api/connection_manager.py
  - api/guardrails.py
  - api/main.py
  - api/ws_handler.py
  - evals/check_thresholds.py
  - evals/judge_config.py
  - evals/promptfoo.yaml
  - frontend/src/App.tsx
  - frontend/src/IndustrySelector.tsx
  - frontend/src/LeadChat.tsx
  - frontend/src/OwnerPanel.tsx
  - frontend/src/__tests__/App.test.tsx
  - frontend/src/__tests__/IndustrySelector.test.tsx
  - frontend/src/__tests__/OwnerPanel.test.tsx
  - frontend/src/__tests__/useWebSocket.test.ts
  - frontend/src/assets/personas.ts
  - frontend/src/index.css
  - frontend/src/types.ts
  - frontend/src/useWebSocket.ts
  - frontend/vite.config.ts
  - scripts/dev.sh
  - tests/conftest.py
  - tests/test_escalation.py
  - tests/test_graph_module.py
  - tests/test_llm_router.py
  - tests/test_models.py
  - tests/test_persistence.py
  - tests/test_stage_detection.py
  - tests/test_stage_routing.py
  - tests/test_versions.py
  - tests/test_websocket.py
findings:
  critical: 4
  warning: 6
  info: 3
  total: 13
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-06-15
**Depth:** standard
**Files Reviewed:** 39
**Status:** issues_found

## Summary

Reviewed the full agent core, API layer, frontend, and eval harness for OttoBot Wave 0. The implementation is well-structured and shows awareness of key pitfalls (asyncio.run inside event loop, Pydantic v2, StrictUndefined, uuid4 thread validation). However, four correctness/security issues require fixes before this ships. Six additional warnings degrade robustness.

---

## Critical Issues

### CR-01: WebSocket send called on non-OPEN socket — silently drops messages

**File:** `frontend/src/useWebSocket.ts:117-122`

**Issue:** The `send` callback checks `readyState === WebSocket.OPEN` on the true branch, but the `else if` branch (socket exists but is NOT open) calls `ws.send()` unconditionally. Calling `send()` on a `CONNECTING`, `CLOSING`, or `CLOSED` socket throws a `DOMException: Still in CONNECTING state` (or similar) which is uncaught, and the message is lost with no feedback to the user.

```typescript
// Current (buggy):
if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
  wsRef.current.send(JSON.stringify({ text, industry }));
} else if (wsRef.current) {
  // Queue the send for when the socket opens (handles early sends)
  wsRef.current.send(JSON.stringify({ text, industry })); // THROWS if not OPEN
}
```

The comment says "queue the send for when the socket opens" but no queuing mechanism exists — it just calls `send()` again and will throw.

**Fix:** Either drop the non-OPEN branch, or implement actual queuing:
```typescript
const pendingRef = useRef<Array<{text: string; industry: IndustryKey}>>([]);

// In onopen handler:
ws.onopen = () => {
  setWsError(false);
  // Flush queued messages
  for (const msg of pendingRef.current) {
    ws.send(JSON.stringify(msg));
  }
  pendingRef.current = [];
};

// In send callback:
const send = useCallback((text: string, industry: IndustryKey) => {
  setMessages((prev) => [...prev, { role: "user", content: text }]);
  if (wsRef.current?.readyState === WebSocket.OPEN) {
    wsRef.current.send(JSON.stringify({ text, industry }));
  } else {
    pendingRef.current.push({ text, industry });
  }
}, []);
```

---

### CR-02: `compiled_graph` is None after lifespan exits — request handler crashes with AttributeError

**File:** `api/main.py:89`, `api/ws_handler.py:78`

**Issue:** `compiled_graph` is set inside the `AsyncPostgresSaver` context manager (`async with`) and becomes invalid (but NOT set back to `None`) after the lifespan exits. More critically, `compiled_graph` is `None` at import time. If the WebSocket endpoint receives a request before the lifespan completes (race on slow startup), `app_state.compiled_graph.astream(...)` at `ws_handler.py:78` will raise `AttributeError: 'NoneType' object has no attribute 'astream'`. This error is unhandled and will surface as a 500 / WS close to the client with no diagnostic.

**Fix:** Guard in `handle_ws` before streaming:
```python
if app_state.compiled_graph is None:
    await websocket.send_json({
        "type": "system_alert",
        "content": "Server is still starting up. Please try again in a moment.",
    })
    return
```

---

### CR-03: `message_timestamps` only ever has one entry per turn — cadence signal (signal_3) is permanently broken

**File:** `api/ws_handler.py:71-73`

**Issue:** Each turn, `initial_state` is built with `"message_timestamps": [time.time()]` — a single-element list. LangGraph merges this via the `add_messages` reducer only for the `messages` field; `message_timestamps` is a plain `list[float]` in `ConversationState` (no Annotated reducer), so every turn it is **replaced** with the single-element list `[time.time()]`. The `escalation_scorer` requires `len(timestamps) >= 2` to compute cadence (signal_3), which is never satisfied. Signal_3 always returns `False`.

This silently degrades the 2-of-3 escalation scorer — the cadence signal is the only one that doesn't require explicit phrase-matching, so genuine fast-cadence leads are systematically under-escalated.

**Fix:** Either (a) accumulate timestamps in `agent_node` return value the same way `visit_count` is accumulated, or (b) apply an `Annotated` reducer to `message_timestamps` in `ConversationState`:
```python
# agent/state.py
from langgraph.graph.message import add_messages
from typing import Annotated, Literal, TypedDict, Sequence

def _append_timestamps(existing: list, new: list) -> list:
    return (existing or []) + (new or [])

class ConversationState(TypedDict):
    messages: Annotated[list, add_messages]
    stage: STAGES
    thread_id: str
    escalated: bool
    visit_count: dict[str, int]
    message_timestamps: Annotated[list[float], _append_timestamps]
```

---

### CR-04: Jinja2 template `base.j2` uses `{% block %}` — the base template itself will silently render the block placeholder as empty string

**File:** `agent/prompts/base.j2:13`

**Issue:** `base.j2` ends with `{% block persona %}{% endblock %}`. When `base.j2` is rendered **directly** (not via a child template that extends it), the block produces an empty string — the persona section is missing. `agent_node` in `graph.py:110-112` calls `profile.render_system_prompt(env)`, which calls `env.get_template(f"{self.industry.value}.j2")` — this correctly loads `dental.j2` etc., which extend `base.j2`, so normal operation is fine.

However, `api/ws_handler.py:103-107` also calls `profile.render_system_prompt(env)` in the AI disclosure guardrail check (Guardrail 3). Because those calls correctly go through `dental.j2`/`aesthetics.j2`/`real_estate.j2`, this is safe at runtime. But `check_ai_disclosure` in `api/guardrails.py` compares against `AI_DISCLOSURE_PHRASE = "AI assistant"` (case-sensitive), while `base.j2:3` renders: `"Para sa transparency po, ako ay AI assistant ni {{ agent_name }}."` — the phrase is present verbatim, so the check passes.

The real risk: nothing prevents a future developer from calling `env.get_template("base.j2").render(...)` directly — StrictUndefined will raise on `{{ agent_name }}` before the block issue even surfaces, but this is a latent structural defect. The Jinja2 `Environment` has `StrictUndefined` which would raise `UndefinedError` on missing variables, so a direct render of `base.j2` fails loudly on `agent_name` — this is recoverable. **Downgrading from BLOCKER to CRITICAL only because the runtime path is safe; documented here because the guardrail's make_env() call inside ws_handler is wasteful and creates an env per-request.**

**Actual blocker sub-issue:** `api/ws_handler.py:103-106` calls `make_env()` on every intro-stage message. `make_env()` creates a new `FileSystemLoader` + `Environment` instance per call. For a high-throughput demo this means repeated filesystem stat/template-load calls. More importantly: the `jinja_env` singleton already exists in `agent/graph.py:37` — the guardrail should reuse it instead of creating a fresh env:

```python
# ws_handler.py line 103-107 — replace:
from agent.models import make_env
env = make_env()
rendered_system = profile.render_system_prompt(env)

# With:
from agent.graph import jinja_env
rendered_system = profile.render_system_prompt(jinja_env)
```

This is a WARNING-level quality issue. Reclassifying CR-04 as the actual blocker it contains:

**Actual CR-04 blocker:** `_extract_content` in `agent/graph.py:77-78` has a redundant/misleading double `.get()`:
```python
if hasattr(msg, "get"):
    content = msg.get("content") or msg.get("content", "")
```
`msg.get("content") or msg.get("content", "")` — the `or` means: if `msg.get("content")` is falsy (e.g. empty string `""`), it falls through to `msg.get("content", "")` which also returns `""`. This is harmless for normal strings but **silently drops any message whose content is the integer `0` or boolean `False`** — unlikely in practice but the pattern is broken: the second `.get("content", "")` is identical to the first and provides no additional safety. The real concern: the intent was likely `msg.get("content", "")` (single call with default), and the `or` branch creates a subtle footgun that would silently coerce numeric/falsy content to empty string.

```python
# Fix:
if hasattr(msg, "get"):
    content = msg.get("content", "") or ""
```

---

## Warnings

### WR-01: `_429_backoff` is module-level shared state — not thread-safe and never expires old entries

**File:** `api/ws_handler.py:27`

**Issue:** `_429_backoff: dict[str, float] = {}` accumulates thread_id → expiry epoch entries and is never pruned. In a long-running process, every unique thread_id that hits a 429 adds a permanent entry. Over time this is a memory leak. Additionally, under concurrent async execution with multiple WebSocket connections hitting the handler simultaneously, mutation of the dict from different coroutines is not explicitly protected. While the GIL makes individual dict operations atomic in CPython, multi-step read-check-write sequences are not.

**Fix:** Prune expired entries on each write, or use a TTLCache from `cachetools`:
```python
# Simple prune-on-write approach:
_429_backoff[thread_id] = time.time() + 30
# Prune expired entries (keep dict bounded)
now = time.time()
expired = [k for k, v in _429_backoff.items() if v < now]
for k in expired:
    del _429_backoff[k]
```

---

### WR-02: `route_next_stage` returns `END` (the LangGraph sentinel object) as a string for unknown stages

**File:** `agent/graph.py:188`

**Issue:** `_STAGE_PROGRESSION.get(current, END)` returns the LangGraph `END` sentinel object when `current` is not in the mapping (e.g. an unexpected stage value or if `stage` is missing). `END` is not a string — it's a special object. LangGraph's conditional edge routing expects a string matching a node name or `END`. Returning `END` from `.get()` default is intentional for the `escalate` → END transition, but `_STAGE_PROGRESSION["escalate"] = END` is already in the dict, so the `.get(current, END)` default only fires for a `current` value not in the dict at all. This will silently terminate the graph for any corrupt state rather than raising an error. No validation is performed on the incoming `stage` field.

**Fix:** Return `END` only for known terminal cases; raise for unexpected:
```python
next_stage = _STAGE_PROGRESSION.get(current)
if next_stage is None:
    import logging
    logging.getLogger(__name__).error("Unknown stage '%s' — terminating graph", current)
    return END
return next_stage
```

---

### WR-03: `escalation_scorer` signal_2 fires on any single positive sentiment phrase in the last two messages — threshold is too loose

**File:** `agent/escalation.py:73`

**Issue:** `signal_2 = sum(1 for m in last_two if any(p in m for p in POSITIVE_SENTIMENT_PHRASES)) >= 1` requires only ONE of the last two messages to contain a positive sentiment phrase. Because phrases like `"ok"`, `"sige"`, `"pwede"`, `"oo"` appear in casual Taglish conversation as filler words (e.g. "ok lang, anong oras kayo?"), signal_2 fires far too easily. Combined with the fast-cadence signal (which fires if any two adjacent messages arrive within 30 seconds — normal chat speed), 2-of-3 fires even for benign low-intent conversations.

This is a correctness issue: the scorer over-escalates, surfacing false positives to the owner panel.

**Fix:** Raise the signal_2 threshold to require both of the last two messages to contain a positive phrase, or narrow the phrase list to exclude single-syllable filler words (`"ok"`, `"oo"`, `"pwede"`):
```python
signal_2 = sum(1 for m in last_two if any(p in m for p in POSITIVE_SENTIMENT_PHRASES)) >= 2
```

---

### WR-04: `agent_node` checks `existing_roles` but never uses it

**File:** `agent/graph.py:104-105`

**Issue:** Line 104 computes `existing_roles = [_extract_content(m) for m in messages]` — building a list of content strings named `existing_roles`. This variable is never referenced again. The actual system-message check on line 105-108 correctly computes `has_system` by looking at `.role`, not at content. `existing_roles` is dead code and represents a logic gap: the variable name implies it was meant to hold roles (not content), and the content extraction was wrong before the variable was abandoned.

**Fix:** Delete line 104 entirely:
```python
# Remove this line:
existing_roles = [_extract_content(m) for m in messages]
```

---

### WR-05: `detect_stage_structured` instructor-patched path does not return the fallback on exhaustion

**File:** `agent/stage_detection.py:76-93`

**Issue:** The `patched_router is not None` branch retries up to `_MAX_ATTEMPTS` times but after exhausting all attempts, falls through to the `else` branch's fallback return at line 117. Wait — actually there is no `return` after the `for` loop on the instructor path. The code structure is:

```python
if patched_router is not None:
    for attempt in range(_MAX_ATTEMPTS):
        try:
            result = await patched_router.chat.completions.create(...)
            return result
        except Exception as exc:
            logger.warning(...)
    # <--- NO RETURN HERE — falls through to else branch
else:
    for attempt in range(_MAX_ATTEMPTS):
        ...

# Exhausted all attempts (only reached after json-mode path)
logger.error(...)
return StageDetectionOutput(next_stage=current_stage, ...)
```

After exhausting the instructor path's 3 attempts, execution falls through to the `else` block — but `else` on an `if/else` is mutually exclusive, so after the `if` block's loop exhausts, Python skips the `else` block entirely and reaches the final fallback `return`. **This is actually correct behavior** for the fallback. However it is confusing and fragile: the `else` block's fallback is unreachable after the `if` block runs. If a developer adds a `return` inside the `else` block without understanding that the `if` block falls through to the shared fallback, the instructor path will return `None` (implicit) on exhaustion.

**Fix:** Refactor to make both paths explicitly reach the same fallback:
```python
for attempt in range(_MAX_ATTEMPTS):
    try:
        if patched_router is not None:
            result = await patched_router.chat.completions.create(
                model="chat", messages=full_messages,
                response_model=StageDetectionOutput, max_tokens=100, temperature=0.0,
            )
        else:
            response = await router.acompletion(
                model="chat", messages=full_messages,
                response_format={"type": "json_object"}, max_tokens=100, temperature=0.0,
            )
            result = StageDetectionOutput.model_validate_json(
                response.choices[0].message.content
            )
        return result
    except Exception as exc:
        logger.warning("detect_stage_structured attempt %d/%d failed: %s", attempt + 1, _MAX_ATTEMPTS, exc)

logger.error("stage detection failed after %d attempts", _MAX_ATTEMPTS)
return StageDetectionOutput(next_stage=current_stage, confidence=0.0, reasoning="fallback")
```

---

### WR-06: `check_thresholds.py` silently returns 1.0 (pass) when no tests match a dimension

**File:** `evals/check_thresholds.py:38`

**Issue:** `compute_pass_rate` returns `1.0` when `dimension_tests` is empty (`if not dimension_tests: return 1.0`). The comment says "no tests for this dimension — skip". But a 1.0 pass rate causes the CI check to print `PASS` for that dimension, giving a false green signal. If the promptfoo results file has a different structure (e.g. different description format), all 5 dimensions can silently pass with 100% when no tests were actually evaluated.

**Fix:** Return `None` and skip the dimension explicitly rather than reporting it as 100% passing:
```python
def compute_pass_rate(results: dict, dimension: str) -> float | None:
    tests = results.get("results", [])
    dimension_tests = [t for t in tests if dimension in t.get("description", "").lower().replace(" ", "_")]
    if not dimension_tests:
        return None  # No tests found — do not report as passing
    passed = sum(1 for t in dimension_tests if t.get("success", False))
    return passed / len(dimension_tests)

# In main(), handle None:
rate = compute_pass_rate(results, dim)
if rate is None:
    print(f"  {dim:<30} N/A   [SKIP — no matching tests]")
    continue
```

---

## Info

### IN-01: `stageToLeadStatus` mapping collapses `pitch`, `objection_handling`, `propose_appointment` all to `"qualifying"` — the `default` branch is unreachable

**File:** `frontend/src/types.ts:40-56`

**Issue:** The `default` case returns `"new"`, but all 7 backend `Stage` values are explicitly handled in the switch. The TypeScript type `Stage` is a closed union, so `default` is dead code. Additionally, the docstring in the JSX comment above `stageToLeadStatus` says `pitch / objection_handling / propose_appointment -> qualifying`, which is correct, but also says `default -> new` — implying there could be unknown stage values. This is misleading.

**Fix:** Remove the unreachable `default` branch (TypeScript exhaustiveness check will catch missing cases at compile time if new stages are added):
```typescript
export function stageToLeadStatus(stage: Stage): LeadStatus {
  switch (stage) {
    case "intro":
    case "qualify":
    case "pitch":
    case "objection_handling":
    case "propose_appointment":
      return "qualifying";
    case "confirm":
      return "booked";
    case "escalate":
      return "hot";
  }
}
```

---

### IN-02: `wsUrl` hardcodes `ws://localhost:8000` — will fail in any non-local deployment

**File:** `frontend/src/App.tsx:29`

**Issue:** `const wsUrl = useMemo(() => \`ws://localhost:8000/ws/${threadId}\`, [threadId])`. The Vite proxy in `vite.config.ts` forwards `/ws` to `ws://localhost:8000`, but the frontend is constructing an absolute URL directly to `localhost:8000` rather than going through the proxy. In a staging or production environment, or when accessed from any device other than the dev machine, this will fail immediately. The correct approach is to use a relative WebSocket URL so the browser resolves it against the current host.

**Fix:**
```typescript
const wsUrl = useMemo(
  () => `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws/${threadId}`,
  [threadId]
);
```

---

### IN-03: `scripts/dev.sh` uses a bare `sleep 1` before printing the banner — services may not be ready

**File:** `scripts/dev.sh:59`

**Issue:** `sleep 1` is used to wait for background services before printing the "servers running" banner. One second is not a reliable readiness check — Phoenix, uvicorn, and Vite may take longer on first run (npm install, cold venv, etc.). The banner prints even if all three processes have already exited with an error. No health-check polling is performed.

**Fix:** Replace `sleep 1` with a readiness poll, or at minimum increase the sleep and add a note that the banner is informational:
```bash
# Wait for uvicorn health endpoint
echo "Waiting for API to become ready..."
for i in $(seq 1 15); do
  if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
```

---

_Reviewed: 2026-06-15_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
