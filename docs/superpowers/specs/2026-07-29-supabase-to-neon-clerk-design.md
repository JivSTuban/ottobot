# Migration Design — Supabase → Neon (DB) + Clerk (Auth)

**Date:** 2026-07-29
**Status:** Approved (brainstorming) — pending implementation plan
**Scope:** Replace Supabase with Neon (serverless Postgres) + Clerk (auth). Backend stays Python/FastAPI/LangGraph. No data-layer rewrite.

## Motivation

Supabase in OttoBot does exactly three things, all Postgres/JWT — no Realtime, RLS, Storage, or Edge Functions:

1. **LangGraph checkpointer** — `AsyncPostgresSaver.from_conn_string(db_uri)` (`api/main.py:323`)
2. **Auth** — verify Supabase-issued JWTs with `pyjwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])` (`api/main.py:60`); mobile + onboarding sign in via Supabase Auth
3. **Direct SQL** — psycopg to Supabase Postgres for `businesses`, `leads`, `messages`, `escalations`, `business_availability`, `appointments`, `business_push_tokens`

Because it is effectively *hosted Postgres + a JWT issuer*, the lowest-risk pivot keeps Postgres (→ Neon) and swaps only the auth provider (→ Clerk). Convex was considered and rejected: TS-native, non-Postgres, would kill the LangGraph checkpointer and force a full data-layer rewrite with a two-runtime Python↔Convex bridge.

**Key scope win:** there are **no schema/migration files to port**. All app tables are created in-app via `CREATE TABLE IF NOT EXISTS` at startup (`api/main.py`), and LangGraph's `checkpointer.setup()` creates its own. Point the app at an empty Neon DB → it builds everything on first boot.

## Architecture

```
Expo mobile ─┐                         ┌─ Neon Postgres (DATABASE_URL)
             ├─ Clerk (auth/JWT) ──►   │    • businesses, leads, messages, escalations,
React/Vite ──┘                         │      business_availability, appointments,
onboarding                             │      business_push_tokens
                                       │    • langgraph checkpointer tables
   │  Authorization: Bearer <Clerk JWT>│
   ▼                                   │
FastAPI / LangGraph (Python) ──────────┘
   • verify_business_from_jwt: RS256 + Clerk JWKS → email claim → businesses.owner_email → business_id
   • AsyncPostgresSaver(DATABASE_URL)
   • psycopg request-path queries
```

Data flow is unchanged except one call: `settings.tsx` currently reads the `businesses` table **directly from the client** via the Supabase SDK. Neon has no client SDK, so that read moves to a new backend endpoint.

## Components / Changes

### 1. DB connection (backend)
- Introduce one helper `_db_uri()` returning `os.environ["DATABASE_URL"]`; replace all `SUPABASE_DIRECT_URL`/`SUPABASE_DB_URI` reads (~8 sites in `api/main.py`, `api/ws_handler.py`, `api/escalation_service.py`).
- `AsyncPostgresSaver.from_conn_string(DATABASE_URL)` unchanged.
- **Neon connection strategy:** use the **direct (unpooled)** endpoint for the checkpointer + DDL (`setup()` runs schema); use the **pooled** endpoint for request-path psycopg. Both require `sslmode=require`. Represent as `DATABASE_URL` (pooled) + `DATABASE_DIRECT_URL` (direct); checkpointer uses the direct one.

### 2. Auth verification (backend) — `verify_business_from_jwt`
- Swap HS256 + shared secret → **RS256 + Clerk JWKS**: fetch Clerk's JWKS from `CLERK_JWKS_URL`, cache keys (with kid lookup), verify signature + issuer (`CLERK_ISSUER`).
- Keep: `email` claim → `SELECT id FROM businesses WHERE owner_email = %s` → `business_id`. `business_id` still never trusted from request body.
- New env: `CLERK_JWKS_URL`, `CLERK_ISSUER`. Remove `SUPABASE_JWT_SECRET`.
- **Requires** a Clerk JWT template that emits the `email` claim (dashboard config step, documented in cutover).

### 3. New endpoint — `GET /me/business`
- Returns `{ "business_id": <uuid> }` for the caller, derived from the verified JWT (reuses `verify_business_from_jwt` dependency).
- Replaces the client-side Supabase read at `mobile/app/(tabs)/settings.tsx:49`.

### 4. Mobile (Expo)
- `lib/supabase.ts` → `lib/clerk.ts`: `ClerkProvider` config + `expo-secure-store` token cache.
- `hooks/useAuth.tsx` → wrap Clerk `useAuth()` (`isSignedIn`, `getToken`, `signOut`); preserve the same hook surface consumers already use.
- `app/login.tsx` → Clerk `useSignIn()` email/password; **keep the existing Tagalog UI/copy and error strings**.
- `app/_layout.tsx` → guard on Clerk `isSignedIn` instead of Supabase `session`; push-token registration flow unchanged.
- All `fetch(... , { headers: { Authorization: 'Bearer ' + token }})` → `Bearer ${await getToken({ template })}`.
- `app/(tabs)/settings.tsx` → call `GET /me/business` for `business_id` instead of `supabase.from('businesses')`.
- Deps: remove `@supabase/supabase-js`; add `@clerk/clerk-expo`, `expo-secure-store`.

### 5. Onboarding frontend (React/Vite)
- `OnboardingWizard.tsx` step 1 (account creation) → Clerk `useSignUp()` / `<SignUp>`.
- Business-row creation continues via the existing backend endpoint (unchanged).
- Deps: swap Supabase JS → `@clerk/clerk-react`.

### 6. Env / config / docs
- Root `.env.example`: add `DATABASE_URL`, `DATABASE_DIRECT_URL`, `CLERK_JWKS_URL`, `CLERK_ISSUER`; remove `SUPABASE_*`.
- `mobile/.env.example`: `EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY` (remove `EXPO_PUBLIC_SUPABASE_*`); keep `EXPO_PUBLIC_API_URL`.
- `frontend/.env.example`: `VITE_CLERK_PUBLISHABLE_KEY`.
- Update README / `scripts/dev.sh` run notes.

### 7. Tests
- Update `verify_business_from_jwt` tests to mock a JWKS endpoint + RS256-signed token (replace `SUPABASE_JWT_SECRET` HS256 fixtures).
- DB fixtures → `DATABASE_URL`.
- Add a test for `GET /me/business`.
- Keep the suite green (currently 135).

## UI craft (uses installed skills)

The Clerk login (mobile) and signup (onboarding) screens are net-new UI. Build them with the `prototype` skill — a small set of genuinely divergent variants behind the picker — held to the `emil-design-eng` craft bar (ease-out entrances, sub-300ms motion, transform/opacity only, reduced-motion). Use `pick-ui-library` before adding any auth-UI dependency. Keep OttoBot's existing dark tokens (`#0f1117` bg, `#6366f1` accent) and Tagalog copy.

## Cutover

1. Provision Neon → capture pooled + direct URLs.
2. Set `DATABASE_URL` / `DATABASE_DIRECT_URL` → boot backend → tables auto-create.
3. Provision Clerk app → publishable key, JWKS URL, issuer; configure JWT template emitting `email`.
4. Recreate the test user in Clerk. (Supabase project is dead per KB → no data migration. If live data exists later: `pg_dump` Supabase → `pg_restore` Neon.)
5. Verify E2E: mobile login → `GET /leads` → `GET /me/business` → settings save (`POST /availability`) → escalation → push.

## Non-goals (YAGNI)

- No Postgres RLS — `business_id` is already enforced server-side from the JWT; Phase 07 multi-account tenancy is a separate design.
- No Clerk Organizations yet.
- No data-migration tooling for a fresh start.

## Risks

- **Neon pooling** — DDL/checkpointer must use the direct endpoint, not the pooled one.
- **Clerk JWT template** — must emit `email` or business resolution 401s. Explicit dashboard step.
- **Expo SDK 56 compat** — verify `@clerk/clerk-expo` supports RN 0.85 / Expo 56 before the mobile swap; pin or fall back if not.
