---
phase: 01-agent-core-demo-ui
fixed_at: 2026-06-16T00:00:00Z
review_path: .planning/phases/01-agent-core-demo-ui/01-REVIEW.md
iteration: 1
findings_in_scope: 11
fixed: 11
skipped: 0
status: all_fixed
---

# Phase 01: Code Review Fix Report

**Fixed at:** 2026-06-16T00:00:00Z
**Source review:** .planning/phases/01-agent-core-demo-ui/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 11 (CR-01 through CR-05, WR-01 through WR-06)
- Fixed: 11
- Skipped: 0

---

## Fixed Issues

### CR-01: `message_timestamps` reducer missing — cadence signal permanently broken

**Files modified:** `agent/state.py`
**Commit:** c893a50
**Applied fix:** Added `_append_list` reducer function and wrapped `message_timestamps` with `Annotated[list[float], _append_list]` so LangGraph appends timestamps across turns rather than replacing the list on each merge.

---

### CR-02: `validate_thread_id` accepts non-uuid4 UUIDs — security bypass

**Files modified:** `api/main.py`
**Commit:** 689c4f6
**Applied fix:** Replaced `uuid.UUID(thread_id, version=4)` (which coerces version bits silently) with `val = uuid.UUID(thread_id)` followed by `return val.version == 4` — explicit version check without coercion.

---

### CR-03: `compiled_graph` is `None` before lifespan completes — AttributeError on startup race

**Files modified:** `api/ws_handler.py`
**Commit:** 9445ba2
**Applied fix:** Added null-guard at the top of `handle_ws` that sends a `system_alert` JSON message and returns early when `app_state.compiled_graph is None`.

---

### CR-04: WebSocket `send` calls on non-OPEN socket — silently drops or throws

**Files modified:** `frontend/src/useWebSocket.ts`
**Commit:** 7aadc36
**Applied fix:** Removed the else branch that called `wsRef.current.send()` on a non-OPEN socket. The else branch now calls `setWsError(true)` to surface the error to the user instead of silently throwing `InvalidStateError`.

---

### CR-05: AI disclosure guardrail checks post-turn stage — condition never true

**Files modified:** `api/ws_handler.py`
**Commit:** 9445ba2
**Applied fix:** Replaced `if stage == "intro"` check (which is never true after agent_node advances stage) with `is_first_turn = len(all_messages) <= 2` — keying the disclosure check on message count instead of post-turn stage.

---

### WR-01: `industry` field missing from `ConversationState` — persona resets to dental

**Files modified:** `agent/state.py`
**Commit:** c893a50
**Applied fix:** Added `industry: str` field to `ConversationState` TypedDict so the field is persisted in checkpointed state across turns. Combined with CR-01 in the same atomic commit since both changes are in the same file.

---

### WR-02: `_429_backoff` dict grows unbounded — memory leak

**Files modified:** `api/ws_handler.py`
**Commit:** 9445ba2
**Applied fix:** After recording a new backoff entry, pruning expired entries with a list comprehension: all entries where `v < now` are deleted from `_429_backoff` on each write.

---

### WR-03: `check_thresholds.py` silently reports 100% pass when no tests match

**Files modified:** `evals/check_thresholds.py`
**Commit:** a6b4776
**Applied fix:** Changed `compute_pass_rate` return type to `float | None`, returning `None` instead of `1.0` when no tests match. In `main()`, a `None` rate prints `NO TESTS  [FAIL]`, appends to `failed_dimensions`, and continues — so a missing dimension fails CI rather than passing silently.

---

### WR-04: `onclose` is a no-op — unexpected server disconnects invisible to user

**Files modified:** `frontend/src/useWebSocket.ts`
**Commit:** 7aadc36
**Applied fix:** Implemented `ws.onclose` handler: `if (event.code !== 1000) { setWsError(true); }` — surfaces abnormal close codes as a visible error state. Combined with CR-04 in the same atomic commit.

---

### WR-05: JSON-mode fallback prevented by `if/else` structure when instructor is installed but fails

**Files modified:** `agent/stage_detection.py`
**Commit:** 3ae16e6
**Applied fix:** Restructured `detect_stage_structured` to remove the `if/else` split. The instructor block is now a standalone `if` block that falls through on exhaustion. The JSON-mode loop follows unconditionally, serving as both the primary path (no instructor) and secondary fallback (instructor exhausted).

---

### WR-06: `make_env()` called per-request — unnecessary repeated filesystem I/O

**Files modified:** `api/ws_handler.py`
**Commit:** 9445ba2
**Applied fix:** Replaced `from agent.models import make_env; env = make_env()` with `from agent.graph import jinja_env` — reuses the module-level singleton instead of creating a new Jinja2 `Environment` with `FileSystemLoader` on each message.

---

## Skipped Issues

None — all 11 in-scope findings were successfully fixed.

---

_Fixed: 2026-06-16T00:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
