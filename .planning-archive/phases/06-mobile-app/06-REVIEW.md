---
phase: 06-mobile-app
reviewed: 2026-06-19T00:00:00Z
depth: standard
files_reviewed: 15
files_reviewed_list:
  - api/main.py
  - api/escalation_service.py
  - api/ws_handler.py
  - tests/test_push_service.py
  - mobile/lib/supabase.ts
  - mobile/lib/pushToken.ts
  - mobile/hooks/useAuth.tsx
  - mobile/app/_layout.tsx
  - mobile/app/login.tsx
  - mobile/app/(tabs)/_layout.tsx
  - mobile/app/(tabs)/pipeline.tsx
  - mobile/app/(tabs)/conversation/[id].tsx
  - mobile/app/(tabs)/settings.tsx
  - mobile/components/LeadRow.tsx
  - mobile/components/MessageBubble.tsx
findings:
  critical: 4
  warning: 5
  info: 3
  total: 12
status: fixed
---

# Phase 06: Code Review Report

**Reviewed:** 2026-06-19T00:00:00Z
**Depth:** standard
**Files Reviewed:** 15
**Status:** issues_found

## Summary

Reviewed all 15 Phase 6 source files covering the FastAPI mobile endpoints, push notification wiring, and the Expo React Native mobile app. The JWT auth dependency and SQL parameterization are correctly implemented. The main security finding is a TOCTOU (time-of-check / time-of-use) gap in the JWT dependency: the `sub` claim is assumed to be an email address but Supabase JWTs use the user's UUID as `sub`, not the email — this means the businesses table lookup will never match and the `owner_email` query will always 401. Three additional critical issues were found: the `/availability` settings screen sends `session.user.id` (the Supabase auth UUID) as `business_id` instead of the businesses-table UUID (breaking a core flow), the `expo_token` format validation is incomplete (it does not enforce a closing `]`), and the `_escalated_threads` and `_429_backoff` in-process sets are never purged after escalation resolution, growing indefinitely in long-running processes.

---

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Supabase JWT `sub` claim is user UUID, not email — auth dependency always 401s

**File:** `api/main.py:69`
**Issue:** `get_business_id_from_token` reads `payload.get("sub", "")` and then queries `SELECT id FROM businesses WHERE owner_email = %s` using that value. Supabase access tokens set `sub` to the user's UUID (e.g. `"7d3f..."`), not the user's email address. The email is in a separate `email` claim. The query will therefore never find a matching row, every mobile endpoint will return 401, and the mobile app is entirely non-functional in production.

**Fix:**
```python
# Replace line 69 with:
owner_email = payload.get("email", "") or payload.get("sub", "")
# Supabase JWTs carry the email in the "email" claim; "sub" is the auth UUID.
# Fallback to "sub" is intentional for custom tokens where "email" may be absent.
if not owner_email:
    raise HTTPException(status_code=401, detail="Invalid token")
```

---

### CR-02: Settings screen sends auth UUID as `business_id`, bypassing the businesses table

**File:** `mobile/app/(tabs)/settings.tsx:47,95`
**Issue:** Both `fetchAvailability()` and `saveAvailability()` use `session.user.id` as the `business_id`. `session.user.id` is the Supabase auth UUID — it is different from the `id` column in the `businesses` table (which is the UUID assigned on `onboarding/submit`). The GET `/availability/{business_id}` and POST `/availability` endpoints validate that `business_id` is a UUID-v4, so the format check passes, but the lookup returns no rows (the auth UUID is not in the `business_availability` table). This means availability can never be fetched or saved from the mobile app.

**Fix:** After login, resolve and store the real `businesses.id` using the `/onboarding/submit` or a new GET `/me` endpoint, then pass that value as `business_id`. For example:

```typescript
// In useAuth or a dedicated useBusiness hook:
const { data } = await supabase
  .from('businesses')
  .select('id')
  .eq('owner_email', session.user.email)
  .single();
const businessId = data?.id;
```

Then pass `businessId` (not `session.user.id`) to the availability calls.

---

### CR-03: Expo push token format validation is incomplete — accepts malformed tokens

**File:** `api/main.py:968`
**Issue:** The validation `req.expo_token.startswith("ExponentPushToken[")` checks the prefix but not the closing `]`. A token like `"ExponentPushToken[abc"` passes validation and is stored in the DB. The Expo Push API will reject it, but the backend silently stores a permanently broken token. Any subsequent push delivery attempt will fail every time with no indication the stored token is invalid.

**Fix:**
```python
token = req.expo_token
if not (token.startswith("ExponentPushToken[") and token.endswith("]") and len(token) > len("ExponentPushToken[]")):
    raise HTTPException(status_code=422, detail="Invalid Expo push token format")
```

---

### CR-04: `_escalated_threads` set is unbounded — memory leak in long-running processes

**File:** `api/ws_handler.py:35`
**Issue:** `_escalated_threads: set[str]` accumulates every thread_id that has escalated and is never pruged. In a long-running production process with high lead volume, this set grows indefinitely. Unlike `_429_backoff` (which has an expiry-based pruning loop on line 153–155), `_escalated_threads` has no eviction mechanism. The set is also in-process memory, so it resets on restart — but escalation de-dup is supposed to persist across restarts (preventing duplicate push notifications if a worker restarts).

**Fix:** Either (a) persist escalation de-dup in the `escalations` table (which already has a `UNIQUE (thread_id)` constraint — the `ON CONFLICT DO NOTHING` already handles re-insertion at DB level, so the push notification is the only action that needs de-dup), or (b) cap the in-memory set with a bounded LRU structure. At minimum, remove the in-process set and rely on the DB uniqueness constraint:

```python
# In ws_handler.py — check DB instead of in-memory set
# After store_escalation() which uses ON CONFLICT DO NOTHING,
# query whether the push was already sent by checking if row exists with a
# push_sent boolean column, or simply accept that the push fires once
# per process lifetime and document the limitation.
```

---

## Warnings

### WR-01: `useAuth` initial session fetch has no error handler — silent failure on startup

**File:** `mobile/hooks/useAuth.tsx:11`
**Issue:** `supabase.auth.getSession().then(...)` is called without a `.catch()`. If `AsyncStorage` is unavailable or throws (e.g. corrupted storage on a fresh install with bad data), `loading` is never set to `false`, and the app renders a permanent blank screen (returns `null` at line 38 of `_layout.tsx`).

**Fix:**
```typescript
supabase.auth.getSession()
  .then(({ data: { session } }) => {
    setSession(session);
    setLoading(false);
  })
  .catch(() => {
    setSession(null);
    setLoading(false);
  });
```

---

### WR-02: `pipeline.tsx` — `useEffect` `fetchLeads` ESLint exhaustive-deps violation causes stale closures

**File:** `mobile/app/(tabs)/pipeline.tsx:67-69`
**Issue:** `useEffect(() => { fetchLeads(); }, [session])` calls `fetchLeads` which is declared inside the component. `fetchLeads` is not stable (recreated each render) and is missing from the dependency array. This is a known React hooks trap: if `fetchLeads` captures a stale `session` ref due to closure timing, the fetch silently uses an expired token. Same pattern appears in `settings.tsx:113-115` and `conversation/[id].tsx:65-67`.

**Fix:** Either wrap `fetchLeads` in `useCallback` with its dependencies, or inline the fetch logic in `useEffect`:
```typescript
useEffect(() => {
  if (!session?.access_token) return;
  // inline fetch logic here
}, [session]);
```

---

### WR-03: `pushToken.ts` — missing `projectId` causes `getExpoPushTokenAsync` to throw in some Expo SDK versions

**File:** `mobile/lib/pushToken.ts:24`
**Issue:** `Constants.expoConfig?.extra?.eas?.projectId` can be `undefined` at runtime if the `app.json`/`app.config.js` does not define `extra.eas.projectId`. Passing `{ projectId: undefined }` to `getExpoPushTokenAsync` throws a descriptive error in Expo SDK 49+ but silently returns a development token in earlier versions. The calling code in `_layout.tsx` wraps this in try/catch so it won't crash, but the push token stored will be invalid.

**Fix:**
```typescript
const projectId = Constants.expoConfig?.extra?.eas?.projectId;
if (!projectId) {
  console.warn('EAS projectId not configured — push token registration skipped');
  return null;
}
const token = (await Notifications.getExpoPushTokenAsync({ projectId })).data;
```

---

### WR-04: `ws_handler.py` — `business_id` in escalation block is taken from WebSocket message body (client-controlled)

**File:** `api/ws_handler.py:207`
**Issue:** `business_id = ws_message.get("business_id", os.environ.get("BUSINESS_ID", ""))` trusts the client's WebSocket frame for the `business_id` used in escalation storage and push lookup. An attacker controlling the WebSocket frame could supply an arbitrary `business_id` to divert push notifications to a different business's registered device. The WebSocket endpoint does not require JWT auth (it's protected only by `thread_id` UUID validation), so this is a real escalation misdirection vector.

**Fix:** For the push notification lookup, derive `business_id` from the conversation state stored in the graph/DB rather than from the incoming message:
```python
# Pull business_id from the checkpointed state, not from ws_message
business_id = values.get("business_id", os.environ.get("BUSINESS_ID", ""))
```

---

### WR-05: `conversation/[id].tsx` — API `role` field mapped nowhere; `MessageBubble.sender` always defaults to `lead`

**File:** `mobile/app/(tabs)/conversation/[id].tsx:51-57`
**Issue:** The API returns messages with `role: 'user' | 'assistant' | 'system'` (from the messages table). The `Message` interface in `[id].tsx` defines `sender: 'agent' | 'lead'`. The API response is stored directly (`json.messages`) without mapping `role → sender`. `MessageBubble` checks `message.sender === 'agent'` — because `sender` is always `undefined` (it comes from the API as `role`), every bubble renders as a lead bubble. The UI shows all messages on the same side with the wrong colour.

**Fix:**
```typescript
const sorted: Message[] = (json.messages ?? []).map((m: any) => ({
  ...m,
  sender: m.role === 'assistant' ? 'agent' : 'lead',
})).sort(
  (a: Message, b: Message) =>
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
);
```

---

## Info

### IN-01: `supabase.ts` — Non-null assertions on env vars will throw at runtime, not at build time

**File:** `mobile/lib/supabase.ts:5-6`
**Issue:** `process.env.EXPO_PUBLIC_SUPABASE_URL!` and `process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY!` use TypeScript non-null assertions. At runtime in React Native/Expo these evaluate to `undefined` if the env vars are not set (Expo strips the `!` at compile time). The `createClient` call receives `undefined` arguments and throws an opaque Supabase error rather than a clear configuration error.

**Fix:** Add runtime guards:
```typescript
const url = process.env.EXPO_PUBLIC_SUPABASE_URL;
const key = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY;
if (!url || !key) throw new Error('Missing EXPO_PUBLIC_SUPABASE_URL or EXPO_PUBLIC_SUPABASE_ANON_KEY');
export const supabase = createClient(url, key, { ... });
```

---

### IN-02: `LeadRow.tsx` — `lead.name` and `lead.last_message` may be empty/undefined from API

**File:** `mobile/components/LeadRow.tsx:34,39`
**Issue:** The API `GET /leads` returns `{ id, phone, status, created_at }` — no `name` and no `last_message` fields. The `Lead` interface in `pipeline.tsx` and `LeadRow.tsx` declares both as required strings. At runtime `lead.name` and `lead.last_message` will be `undefined`, rendering blank text nodes. The `accessibilityLabel` will be `"Lead: undefined"`.

**Fix:** Either extend `GET /leads` to return `name` and last message, or make both fields optional in the interface and add fallbacks:
```typescript
<Text style={styles.name}>{lead.name || lead.phone || '—'}</Text>
<Text style={styles.lastMessage} numberOfLines={1}>
  {lead.last_message || 'Walang mensahe pa'}
</Text>
```

---

### IN-03: `_layout.tsx` — `console.error` used for push token registration failure

**File:** `mobile/app/_layout.tsx:29`
**Issue:** `console.error('Push token registration failed:', error)` logs to the console. In production Expo/React Native builds this may surface in Sentry/error tracking as an uncaught error event depending on the error reporting setup, creating noise. Prefer `console.warn` for non-fatal expected failures.

**Fix:** Change to `console.warn('Push token registration failed (non-fatal):', error);`

---

_Reviewed: 2026-06-19T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
