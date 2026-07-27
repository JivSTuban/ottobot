---
phase: 06-mobile-app
fixed_at: 2026-06-19T00:00:00Z
review_path: .planning/phases/06-mobile-app/06-REVIEW.md
iteration: 1
findings_in_scope: 9
fixed: 9
skipped: 0
status: all_fixed
---

# Phase 06: Code Review Fix Report

**Fixed at:** 2026-06-19T00:00:00Z
**Source review:** .planning/phases/06-mobile-app/06-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 9 (4 Critical + 5 Warning)
- Fixed: 9
- Skipped: 0

## Fixed Issues

### CR-01: Supabase JWT `sub` claim is user UUID, not email

**Files modified:** `api/main.py`
**Commit:** 57c186c
**Applied fix:** Changed `payload.get("sub", "")` to `payload.get("email", "") or payload.get("sub", "")`. Supabase JWTs carry the user email in the `email` claim; `sub` is the auth UUID. The fallback to `sub` is retained for custom tokens where `email` may be absent.

---

### CR-02: Settings screen sends auth UUID as `business_id`

**Files modified:** `mobile/app/(tabs)/settings.tsx`
**Commit:** 0713cb6
**Applied fix:** Added `businessId` state resolved via a Supabase direct query (`businesses WHERE owner_email = session.user.email`). Both `fetchAvailability` and `saveAvailability` now use `businessId` instead of `session.user.id`. The fetch `useEffect` depends on `fetchAvailability` (which itself depends on `businessId`), so availability auto-loads once the business row is resolved.

---

### CR-03: Expo push token format validation is incomplete

**Files modified:** `api/main.py`
**Commit:** 44712a0
**Applied fix:** Validation now checks both prefix `ExponentPushToken[` AND suffix `]` AND minimum length (`> len("ExponentPushToken[]")`). Tokens like `"ExponentPushToken[abc"` are now rejected with 422.

---

### CR-04: `_escalated_threads` set is unbounded

**Files modified:** `api/ws_handler.py`
**Commit:** a08a48d
**Applied fix:** Added eviction logic before every `add()`: when set size reaches 10,000, the oldest 5,000 entries (first half of the list snapshot) are discarded. Mirrors the expiry-based pruning pattern used by `_429_backoff`.

---

### WR-01: `useAuth` initial session fetch has no error handler

**Files modified:** `mobile/hooks/useAuth.tsx`
**Commit:** bdfe1c3
**Applied fix:** Added `.catch(() => { setSession(null); setLoading(false); })` so AsyncStorage failures (corrupted storage on fresh install) never leave `loading` permanently `true`, preventing blank-screen lockout.

---

### WR-02: `useEffect` missing fetch function in dependency arrays (3 files)

**Files modified:** `mobile/app/(tabs)/pipeline.tsx`, `mobile/app/(tabs)/conversation/[id].tsx`, `mobile/app/(tabs)/settings.tsx`
**Commit:** c51de63
**Applied fix:** Wrapped `fetchLeads`, `fetchData`, and `fetchAvailability` in `useCallback` with their real dependencies (`session`, `id`, `businessId`). Each `useEffect` now lists the stable callback reference instead of the raw `session`/`id` values, eliminating stale closure risk.

---

### WR-03: `pushToken.ts` — missing `projectId` guard

**Files modified:** `mobile/lib/pushToken.ts`
**Commit:** 5c86340
**Applied fix:** Added early return `null` with `console.warn` when `Constants.expoConfig?.extra?.eas?.projectId` is undefined. `getExpoPushTokenAsync` is no longer called with `undefined`, preventing throws in Expo SDK 49+.

---

### WR-04: `business_id` for push lookup taken from WebSocket message body

**Files modified:** `api/ws_handler.py`
**Commit:** 5a0b4e7
**Applied fix:** Changed `business_id = ws_message.get("business_id", ...)` to `business_id = values.get("business_id", ...)` where `values` is the server-side graph state. Push notification lookup now uses the server-authoritative value, not the client-supplied frame field.

---

### WR-05: API `role` field not mapped to `sender` — all bubbles render as lead

**Files modified:** `mobile/app/(tabs)/conversation/[id].tsx`
**Commit:** c51de63 (bundled with WR-02)
**Applied fix:** Added `.map((m: any) => ({ ...m, sender: m.role === 'assistant' ? 'agent' : 'lead' }))` in the message sort pipeline. API `role: 'assistant'` maps to `sender: 'agent'`; all other roles map to `sender: 'lead'`. `MessageBubble` now receives the correct `sender` value.

---

## Skipped Issues

None — all 9 in-scope findings were fixed.

---

_Fixed: 2026-06-19T00:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
