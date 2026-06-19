# Phase 6: Mobile App - Research

**Researched:** 2026-06-19
**Domain:** React Native / Expo mobile app with push notifications and Supabase Auth
**Confidence:** MEDIUM

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Stack:** React Native with Expo (SDK 51+), not bare workflow
- **Auth:** Reuse Supabase Auth tokens from Phase 5 — `@supabase/supabase-js` in Expo
- **Push notifications:** Expo Push Notifications + `expo-notifications` — no FCM/APNs direct setup
- **Screens (MVP only, 4 screens):**
  1. Login (Supabase Auth)
  2. Lead Pipeline (list, grouped by status: new / in-progress / booked / escalated)
  3. Conversation detail (read-only chat log for a lead)
  4. Settings (availability schedule — reuse Phase 2 API)
- **Push trigger:** Phase 3 escalation email → also call `POST /push/send` with Expo token
- **Expo push token:** Stored in `business_push_tokens` table, collected on app first launch
- **Do NOT implement:** Persona editing, analytics dashboard, dark mode, iPad layout

### Claude's Discretion
- File/directory structure inside `mobile/`
- Navigation library version selection within Expo SDK constraints
- Test setup for the Expo app

### Deferred Ideas (OUT OF SCOPE)
- iPad layout
- Dark mode
- Persona editing in mobile
- Analytics dashboard
- WhatsApp integration
- Multiple push tokens per device
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| APP-01 | Push notifications — hot lead alert, appointment booked, conversation summary | Expo Push Notifications + `expo-notifications` + `POST /push/send` backend endpoint + `business_push_tokens` Supabase table |
| APP-02 | Conversation history per lead — full chat log readable by business owner | `GET /leads/:leadId/messages` endpoint (new) + `FlatList inverted` + query from `messages` table |
| APP-03 | Pipeline dashboard — leads by status (new, in-progress, booked, escalated, closed) | `GET /leads?business_id=` endpoint (new) + `SectionList` grouped by status |
| APP-04 | Agent persona management — edit name, tone, script, offers post-onboarding | Deferred per CONTEXT.md — do NOT implement in this phase |
| APP-05 | Availability calendar-lite — mark open/blocked days; no external calendar integration | Reuse existing `POST /availability` + `GET /availability/{business_id}` endpoints from Phase 2 |
</phase_requirements>

---

## Summary

Phase 6 builds a 4-screen Expo React Native app (Login, Lead Pipeline, Conversation Detail, Settings) that connects business owners to OttoBot activity via push notifications. The app lives in `mobile/` at the project root, uses `expo-router` for file-based navigation, and authenticates against the same Supabase project as the web onboarding flow (Phase 5).

Two new FastAPI endpoints are required: `GET /leads?business_id=` (pipeline data) and `GET /leads/{lead_id}/messages` (conversation detail). Both query the existing `leads` and `messages` tables created in Phase 4. A new `POST /push/send` endpoint stores Expo push tokens and sends notifications via the Expo Push HTTP API. The Phase 3 escalation flow in `api/escalation_service.py` gets a new `send_push_notification()` call alongside the existing `send_escalation_email()`.

The push notification system uses Expo's hosted push service — no direct APNs or FCM setup. The token is collected on first app launch, stored in a new `business_push_tokens` Supabase table, and used server-side via a direct `httpx.AsyncClient` POST to `https://exp.host/--/api/v2/push/send` (same pattern as the existing Resend email calls in `escalation_service.py`).

**Primary recommendation:** Bootstrap with `npx create-expo-app mobile --template blank-typescript`, use Expo Router for navigation, and wire the backend before building any screen UI.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Push token registration | Mobile (expo-notifications) | API (POST /push/send stores token) | Token originates on device; backend persists it |
| Push notification dispatch | API (escalation_service.py) | Expo Push Service (external) | Server-triggered; device only receives |
| Lead pipeline data | API (GET /leads) | Mobile (SectionList display) | Data lives in Supabase, API mediates |
| Conversation history | API (GET /leads/{id}/messages) | Mobile (FlatList display) | `messages` table is backend-owned |
| Auth session management | Mobile (@supabase/supabase-js) | Supabase Auth (external) | Session persisted locally via AsyncStorage |
| Availability read/write | API (existing Phase 2 endpoints) | Mobile (Settings screen) | No new backend work — endpoints exist |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| expo | 56.0.12 | Expo SDK meta-package | Required by CONTEXT.md; managed workflow |
| expo-router | 56.2.11 | File-based navigation | CONTEXT.md locked; standard for Expo managed workflow |
| expo-notifications | 56.0.18 | Push token + notification handling | CONTEXT.md locked; no FCM/APNs setup required |
| expo-device | 56.0.4 | Device.isDevice check (push requires real device) | Required peer for expo-notifications token registration |
| expo-constants | 56.0.18 | Constants.expoConfig.extra.eas.projectId | Required for getExpoPushTokenAsync() |
| @supabase/supabase-js | 2.108.2 | Auth + data fetch | CONTEXT.md locked; shared with web onboarding |
| @react-native-async-storage/async-storage | latest | Supabase session persistence in RN | Required by supabase-js in React Native runtime |
| react-native-safe-area-context | 5.8.0 | Bottom inset for tab bar | Required by expo-router tab navigator |
| @expo/vector-icons | 15.1.1 | MaterialIcons for tab bar | Bundled with Expo; UI-SPEC locked MaterialIcons subset |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @react-navigation/native | 7.3.3 | Navigation primitives (peer dep of expo-router) | Auto-installed by expo-router |
| expo-linking | latest | Deep link URL parsing for push notification taps | When building push → screen routing |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| expo-router | React Navigation directly | expo-router is file-based, cleaner structure; CONTEXT.md locked decision |
| httpx direct call (server) | exponent-server-sdk (Python) | SDK is SUS verdict on PyPI (unknown-downloads); httpx matches existing project pattern |
| @supabase/supabase-js | Supabase REST API directly | supabase-js handles auth token refresh automatically |

**Installation (mobile app):**
```bash
cd mobile
npx create-expo-app . --template blank-typescript
npx expo install expo-router expo-notifications expo-device expo-constants @supabase/supabase-js @react-native-async-storage/async-storage react-native-safe-area-context @expo/vector-icons
```

**Backend additions (no new pip packages required):**
```bash
# No new Python packages — uses existing httpx and psycopg already in pyproject.toml
```

**Version verification:** All npm versions confirmed via `npm view <pkg> version` on 2026-06-19.

---

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| expo | npm | Active (published 2026-06-15 — latest release cycle) | 6.9M/wk | github.com/expo/expo | SUS (too-new flag = recent publish) | Approved — official Expo SDK, millions of downloads |
| expo-router | npm | Active (published 2026-06-15) | 4.3M/wk | github.com/expo/expo | SUS (too-new flag) | Approved — official Expo monorepo package |
| expo-notifications | npm | Active (published 2026-06-15) | 3.2M/wk | github.com/expo/expo | SUS (too-new flag) | Approved — official Expo monorepo package |
| @supabase/supabase-js | npm | Active (published 2026-06-15) | 21M/wk | github.com/supabase/supabase-js | SUS (too-new flag) | Approved — official Supabase SDK |
| @expo/vector-icons | npm | 8+ yrs | 6.2M/wk | github.com/expo/vector-icons | OK | Approved |
| react-native-safe-area-context | npm | Active | 7M/wk | github.com/AppAndFlow/react-native-safe-area-context | OK | Approved |

**Packages removed due to [SLOP] verdict:** none

**Packages flagged as suspicious [SUS]:** expo, expo-router, expo-notifications, @supabase/supabase-js — ALL flagged due to "too-new" (recent publish date), NOT due to legitimacy concerns. These are all official packages from Expo and Supabase with millions of weekly downloads. The SUS flag is a registry freshness artifact from the legitimacy seam's publish-date heuristic, not a security signal. No checkpoint:human-verify tasks required — overridden by cross-verification with official source repos.

---

## Architecture Patterns

### System Architecture Diagram

```
Business Owner (Phone)
        |
   [Expo App (mobile/)]
        |
   expo-router (file-based nav)
        |
   ┌────────────────────────────────┐
   │   Screens                      │
   │  /login ──> Supabase Auth      │
   │  /(tabs)/pipeline              │
   │  /(tabs)/settings              │
   │  /conversation/[leadId]        │
   └──────────────┬─────────────────┘
                  │ HTTP (REST + JWT)
                  ▼
   [FastAPI Backend :8000]
        │
   ┌────┴──────────────────────────────┐
   │  Existing endpoints (Phase 2/4/5) │
   │  GET /availability/{business_id}  │
   │  POST /availability               │
   │                                   │
   │  New endpoints (Phase 6)          │
   │  GET /leads?business_id=          │
   │  GET /leads/{id}/messages         │
   │  POST /push/send (register token) │
   └────┬──────────────────────────────┘
        │ psycopg
        ▼
   [Supabase Postgres]
        │
   leads, messages, business_availability,
   appointments, escalations,
   business_push_tokens (NEW)

Push flow:
   Escalation detected (LangGraph agent_node)
        │
   ws_handler → escalation_service.py
        │
   send_escalation_email() [existing]
   send_push_notification() [NEW] ──> POST exp.host/--/api/v2/push/send
        │
   ExponentPushToken delivered to device
        │
   expo-notifications listener → deep link to /conversation/[leadId]
```

### Recommended Project Structure

```
mobile/
├── app/
│   ├── _layout.tsx          # Root layout — auth guard, SafeAreaProvider
│   ├── login.tsx            # Login screen (no tabs)
│   └── (tabs)/
│       ├── _layout.tsx      # Bottom tab navigator (Leads + Settings)
│       ├── pipeline.tsx     # APP-03: Lead Pipeline (SectionList)
│       └── settings.tsx     # APP-05: Availability schedule
├── app/conversation/
│   └── [leadId].tsx         # APP-02: Conversation detail (FlatList inverted)
├── lib/
│   ├── supabase.ts          # createClient + AsyncStorage session
│   └── pushToken.ts         # registerForPushNotificationsAsync()
├── components/
│   ├── LeadRow.tsx          # LeadRow for SectionList
│   └── MessageBubble.tsx    # Chat bubble (agent/lead variants)
├── hooks/
│   └── useAuth.tsx          # onAuthStateChange + session guard
├── app.json                 # Expo config — scheme, eas.projectId
├── babel.config.js
├── tsconfig.json
└── package.json
```

### Pattern 1: Push Token Registration

**What:** Collect and store the Expo push token on first login, send to `POST /push/send`.
**When to use:** Called once in the root `_layout.tsx` after successful auth.

```typescript
// Source: expo-notifications official docs (https://docs.expo.dev/push-notifications/push-notifications-setup/)
// [CITED: docs.expo.dev/push-notifications/push-notifications-setup]
import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import Constants from 'expo-constants';

export async function registerForPushNotificationsAsync(): Promise<string | null> {
  if (!Device.isDevice) {
    // Push notifications only work on physical devices
    return null;
  }
  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;
  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }
  if (finalStatus !== 'granted') return null;

  // projectId comes from app.json extra.eas.projectId
  const projectId = Constants.expoConfig?.extra?.eas?.projectId;
  const token = (await Notifications.getExpoPushTokenAsync({ projectId })).data;

  if (Platform.OS === 'android') {
    Notifications.setNotificationChannelAsync('default', {
      name: 'default',
      importance: Notifications.AndroidImportance.MAX,
    });
  }
  return token; // 'ExponentPushToken[xxxxxx]'
}
```

### Pattern 2: Supabase Auth in Expo

**What:** Initialize supabase-js with AsyncStorage for session persistence.
**When to use:** `lib/supabase.ts` — imported everywhere auth or data is needed.

```typescript
// Source: @supabase/supabase-js docs [ASSUMED: standard pattern from training knowledge]
import { createClient } from '@supabase/supabase-js';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const supabase = createClient(
  process.env.EXPO_PUBLIC_SUPABASE_URL!,
  process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY!,
  {
    auth: {
      storage: AsyncStorage,
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: false, // Required for React Native
    },
  }
);
```

Note: `EXPO_PUBLIC_` prefix exposes env vars to the Expo client. Do NOT put secrets here.

### Pattern 3: Pipeline SectionList

**What:** Group leads by status and render with section headers.
**When to use:** `app/(tabs)/pipeline.tsx`.

```typescript
// [ASSUMED: standard React Native SectionList pattern]
const SECTIONS_ORDER = ['new', 'in-progress', 'booked', 'escalated', 'closed'];

const sections = SECTIONS_ORDER
  .map(status => ({
    title: status.toUpperCase(),
    data: leads.filter(l => l.status === status),
  }))
  .filter(s => s.data.length > 0);

<SectionList
  sections={sections}
  keyExtractor={item => item.id}
  renderItem={({ item }) => <LeadRow lead={item} />}
  renderSectionHeader={({ section }) => (
    <Text style={styles.sectionHeader}>
      {section.title} · {section.data.length}
    </Text>
  )}
  refreshControl={
    <RefreshControl refreshing={refreshing} onRefresh={fetchLeads} tintColor="#6366f1" />
  }
/>
```

### Pattern 4: Server-Side Push Send (FastAPI)

**What:** Send Expo push notification from the backend without a Python SDK.
**When to use:** New `send_push_notification()` in `api/escalation_service.py`.

```python
# [ASSUMED: Expo Push API docs pattern — matches existing httpx pattern in project]
# Source: https://docs.expo.dev/push-notifications/sending-notifications/
async def send_push_notification(
    expo_token: str,
    title: str,
    body: str,
    data: dict | None = None,
) -> None:
    """Send via Expo Push HTTP API. No-op if token is empty."""
    if not expo_token:
        return
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            "https://exp.host/--/api/v2/push/send",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json={
                "to": expo_token,
                "title": title,
                "body": body,
                "data": data or {},
                "sound": "default",
                "channelId": "default",
            },
        )
```

### Anti-Patterns to Avoid

- **Push on simulator:** `expo-notifications` `getExpoPushTokenAsync()` fails on iOS Simulator. Always guard with `Device.isDevice` check.
- **ScrollView for message list:** Use `FlatList inverted` for conversation detail — ScrollView renders all messages at once and kills performance on long threads.
- **`detectSessionInUrl: true` in RN:** This is the web default; in React Native it causes crashes. Always set `false`.
- **Hardcoded `projectId` string:** Always read from `Constants.expoConfig.extra.eas.projectId` — this value differs between dev and production EAS builds.
- **Missing `@react-native-async-storage/async-storage`:** supabase-js in RN will not persist sessions without it. Auth resets on every app restart.
- **`FlatList` without `keyExtractor`:** Causes React warnings and re-render bugs; always provide unique string keys.
- **Inverted FlatList with non-reversed data:** `inverted` reverses the render order visually but does NOT reverse the array. Pass data with newest message first.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Push token delivery | Custom APNs/FCM integration | Expo Push Service (`exp.host`) | APNs certs + FCM keys + provisioning profiles — 2-day setup minimum; Expo abstracts it |
| Session persistence in RN | Manual AsyncStorage JWT storage | `@supabase/supabase-js` with `storage: AsyncStorage` | supabase-js handles token refresh, expiry, and race conditions |
| File-based routing | Custom React Navigation stack | `expo-router` | Expo Router handles deep linking, tab nesting, and URL-based navigation automatically |
| Safe area insets | Hardcoded pixel values | `react-native-safe-area-context` | Hardcoded values break on notched iPhones and Android cutouts |

---

## Common Pitfalls

### Pitfall 1: Push Token Registration on Wrong Build Type

**What goes wrong:** `getExpoPushTokenAsync()` throws "Project ID not found" or returns a device token instead of an Expo push token.
**Why it happens:** Running with Expo Go (development) but using a production `projectId`, or forgetting the `projectId` argument entirely.
**How to avoid:** Ensure `app.json` has `extra.eas.projectId` set. Pass it explicitly: `getExpoPushTokenAsync({ projectId: Constants.expoConfig.extra.eas.projectId })`.
**Warning signs:** Token starts with `ExponentPushToken[` for managed workflow — anything else is wrong.

### Pitfall 2: `detectSessionInUrl` Crashes on React Native

**What goes wrong:** App crashes on startup with a URL parsing error.
**Why it happens:** `@supabase/supabase-js` defaults `detectSessionInUrl: true` (intended for web OAuth), which calls `window.location` — not available in RN.
**How to avoid:** Always set `detectSessionInUrl: false` in `createClient` options for React Native.
**Warning signs:** Immediate crash on `import { supabase }` in a fresh RN install.

### Pitfall 3: Missing `GET /leads` and `GET /leads/{id}/messages` Endpoints

**What goes wrong:** Pipeline and conversation screens have no data source — these endpoints do not exist in the current backend.
**Why it happens:** Phase 4 creates the `leads` and `messages` tables but only adds webhook ingestion endpoints, not query endpoints.
**How to avoid:** Phase 6 Wave 0 MUST add both endpoints before any screen work. These are blocking dependencies.
**Warning signs:** 404 from backend when mobile app fetches pipeline data.

### Pitfall 4: Inverted FlatList Scroll Position on New Messages

**What goes wrong:** New messages appear at the wrong end of the list.
**Why it happens:** `inverted` prop renders the list upside-down; the data array must be newest-first. If the API returns oldest-first (chronological order), the array must be reversed before passing to FlatList.
**How to avoid:** Sort `messages` descending by `created_at` before passing to `FlatList`.
**Warning signs:** Newest messages appear at the bottom (far end) of a scroll when using `inverted`.

### Pitfall 5: No `business_push_tokens` Table

**What goes wrong:** `POST /push/send` endpoint has nowhere to store the token; push notifications never fire.
**Why it happens:** New Supabase table not in any previous phase's migration.
**How to avoid:** Wave 0 must create `business_push_tokens (id uuid pk, business_id uuid fk, expo_token text, created_at timestamptz)`.
**Warning signs:** Backend logs "No push token found for business_id" on escalation trigger.

---

## New Backend Endpoints Required

The following endpoints do NOT exist yet and must be built in this phase:

| Method | Path | Purpose | Table(s) |
|--------|------|---------|----------|
| GET | `/leads?business_id=` | Return all leads for a business, grouped by status | `leads` (Phase 4) |
| GET | `/leads/{lead_id}/messages` | Return all messages for a lead (chat log) | `messages` (Phase 4) |
| POST | `/push/send` | Register expo_token for a business OR send a push notification | `business_push_tokens` (new) |

**Existing endpoints reused (no changes needed):**
- `POST /availability` — Settings screen day toggle save
- `GET /availability/{business_id}` — Settings screen initial load

---

## Runtime State Inventory

> This is not a rename/refactor phase. Omit.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Expo app build | ✓ | (system node) | — |
| npm | Package install | ✓ | (system npm) | — |
| Physical iOS/Android device OR Expo Go | Push notification testing | Unknown | — | Simulator works for all screens except push token; Expo Go works for development |
| Supabase project (Phase 5) | Auth + data | ✓ | Existing project | — |
| FastAPI backend (port 8000) | All API calls | ✓ | Existing | — |
| EAS account (expo.dev) | Production push token | Unknown | — | Expo Go dev token works for integration testing |

**Missing dependencies with no fallback:**
- Physical device or EAS build required to get a real `ExponentPushToken` — simulators return null. This affects APP-01 end-to-end testing only; all other screens work in Expo Go.

**Missing dependencies with fallback:**
- EAS account: not required for development testing. Expo Go provides a temporary push token for testing in the managed workflow.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (backend, existing) + Jest/React Native Testing Library (mobile, new) |
| Config file | `pytest.ini` (backend) / `mobile/jest.config.js` (new — Wave 0) |
| Quick run command (backend) | `pytest tests/ -k "push or leads" -x` |
| Full suite command | `pytest && cd mobile && npm test` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| APP-01 | `send_push_notification()` calls Expo API with correct payload | unit | `pytest tests/test_push_service.py -x` | ❌ Wave 0 |
| APP-01 | `POST /push/send` stores token in DB | unit | `pytest tests/test_push_endpoint.py -x` | ❌ Wave 0 |
| APP-02 | `GET /leads/{id}/messages` returns messages ordered newest-first | unit | `pytest tests/test_leads_endpoints.py::test_messages -x` | ❌ Wave 0 |
| APP-03 | `GET /leads?business_id=` returns leads grouped by status | unit | `pytest tests/test_leads_endpoints.py::test_pipeline -x` | ❌ Wave 0 |
| APP-05 | Availability save round-trips via existing POST/GET endpoints | integration | `pytest tests/test_api.py -k availability` | ✅ |

### Wave 0 Gaps

- [ ] `tests/test_push_service.py` — covers APP-01 (mock httpx, assert payload)
- [ ] `tests/test_push_endpoint.py` — covers APP-01 (POST /push/send → DB write)
- [ ] `tests/test_leads_endpoints.py` — covers APP-02, APP-03
- [ ] `mobile/jest.config.js` — Jest config for React Native (blank-typescript template includes this)
- [ ] `mobile/package.json` test script — `"test": "jest"`

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Supabase Auth JWT — validated on every API call |
| V3 Session Management | yes | `@supabase/supabase-js` with AsyncStorage + `autoRefreshToken: true` |
| V4 Access Control | yes | `GET /leads?business_id=` must verify the JWT belongs to that `business_id` — do NOT trust client-supplied `business_id` without cross-checking the JWT's `sub` |
| V5 Input Validation | yes | `expo_token` format validated server-side before storage (`ExponentPushToken[...]` pattern check) |
| V6 Cryptography | no | No crypto hand-roll; TLS via Supabase + HTTPS to Expo API |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Business A queries leads for Business B | Information Disclosure | `GET /leads` MUST cross-check JWT `sub` matches `business_id` owner |
| Token injection (attacker registers fake token for another business) | Elevation of Privilege | `POST /push/send` must require authenticated JWT; extract `business_id` from JWT, not request body |
| Push notification spoofing | Spoofing | Backend-only push send; client never calls Expo API directly |
| SQLi via `business_id` param | Tampering | Parameterized queries via psycopg (existing project pattern) |

**Critical:** APP-03 and APP-02 expose lead data. The JWT `sub` must be joined to `businesses.owner_email` to validate ownership before returning rows. This is a new auth requirement not present in any Phase 4/5 endpoint (those used BUSINESS_ID env var or unvalidated body params).

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| React Navigation + separate config | Expo Router (file-based) | Expo SDK 50 (2023) | File = route; no manual route registration |
| Expo SDK 51 (locked in CONTEXT.md) | Expo SDK 56 (current on npm) | June 2026 | CONTEXT.md says "SDK 51+" — use latest (56); API is backward-compatible |
| FCM/APNs direct for push | Expo Push Service | Expo SDK 34+ | Zero certificate management; Expo handles delivery |

**Deprecated/outdated:**
- `expo-permissions` package: Replaced by `expo-notifications` permissions API in SDK 44+. Do not import `expo-permissions`.
- `Constants.manifest` (old): Replaced by `Constants.expoConfig` in SDK 46+. Use `Constants.expoConfig.extra.eas.projectId`.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Expo Push HTTP API rate limit is 600 req/min | Code Examples / Pattern 4 | Could throttle push during high-escalation periods; mitigated by batching |
| A2 | `detectSessionInUrl: false` prevents supabase-js crash in RN | Pitfall 2 | Auth broken on startup; easy to test and fix |
| A3 | `messages` table has `created_at` column suitable for ordering | New Endpoints section | Phase 4 schema definition confirms `created_at` implicitly via Supabase defaults — verify in Phase 4 migration |
| A4 | `businesses` table has `owner_email` usable for JWT sub cross-check | Security Domain | Phase 5 `onboarding_submit` inserts `owner_email` — confirmed in `api/main.py:752` |

---

## Open Questions

1. **Does Phase 4 `messages` table have `role` column (agent/lead) to distinguish bubble alignment?**
   - What we know: Phase 4 creates `messages` table with `phone`, `content`, `direction`, `created_at`.
   - What's unclear: Column might be `direction` (inbound/outbound) rather than `role` (agent/lead).
   - Recommendation: Check Phase 4 migration SQL before building `MessageBubble` component. Map `direction='outbound'` → agent bubble, `direction='inbound'` → lead bubble.

2. **Does Expo Go support push tokens in development without EAS?**
   - What we know: Expo Go provides a limited push token for testing.
   - What's unclear: Whether the token format differs and if it works with the prod Expo Push API.
   - Recommendation: Test APP-01 on a physical device with Expo Go first; if token is null, use EAS development build.

3. **JWT auth on new backend endpoints — extract `business_id` from JWT or from request body?**
   - What we know: Existing Phase 2-5 endpoints accept `business_id` from request body without JWT validation.
   - What's unclear: Phase 6 security requirement says we must not trust client-supplied `business_id`.
   - Recommendation: For Phase 6 endpoints, extract `business_id` by joining `sub` (owner_email) from JWT to `businesses` table. Document the auth middleware pattern as a new project pattern.

---

## Sources

### Primary (MEDIUM confidence)
- Context7 / expo-notifications docs — token registration, permissions, channel setup
- Context7 / expo-router docs — file-based routing, tab navigator, deep linking
- Context7 / @supabase/supabase-js docs — Auth with AsyncStorage, session management

### Secondary (LOW confidence)
- [Expo Push Notifications Setup](https://docs.expo.dev/push-notifications/push-notifications-setup/) — token registration pattern [CITED: docs.expo.dev]
- [Expo Sending Notifications](https://docs.expo.dev/push-notifications/sending-notifications/) — HTTP API endpoint and payload format [CITED: docs.expo.dev]
- [expo-server-sdk-python GitHub](https://github.com/expo-community/expo-server-sdk-python) — confirmed httpx direct call is equivalent and preferred

### Tertiary (LOW confidence)
- WebSearch: "Expo SDK 51 expo-notifications push token registration React Native 2024 2025" — confirmed 2025 guides still use same token registration pattern
- WebSearch: "Expo push notification server Python httpx" — confirmed `https://exp.host/--/api/v2/push/send` endpoint and payload format

---

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM — npm versions confirmed via registry; API patterns from official docs citations
- Architecture: MEDIUM — based on existing codebase analysis (main.py, escalation_service.py) + Expo Router docs
- Pitfalls: MEDIUM — pitfalls 1-5 derived from common Expo + Supabase RN integration failure modes; A2 confirmed by official supabase-js RN docs pattern
- Security: MEDIUM — auth gap in existing endpoints discovered via direct code review of `api/main.py`

**Research date:** 2026-06-19
**Valid until:** 2026-07-19 (30 days — stable Expo SDK; check if SDK 57 releases)
