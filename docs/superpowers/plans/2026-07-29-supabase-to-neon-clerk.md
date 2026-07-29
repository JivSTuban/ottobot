# Supabase → Neon + Clerk Migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Supabase (Postgres + Auth) with Neon (serverless Postgres) + Clerk (auth) without rewriting the Python/LangGraph data layer.

**Architecture:** Backend stays FastAPI/LangGraph. DB host swaps to Neon via connection-string change (schema auto-creates from existing `CREATE TABLE IF NOT EXISTS`). Auth verify swaps from HS256+shared-secret to RS256+Clerk JWKS. Mobile (Expo) and onboarding (React/Vite) swap the Supabase Auth SDK for Clerk. One client-side Supabase DB read moves behind a new backend endpoint.

**Tech Stack:** Python 3.12, FastAPI, LangGraph (`AsyncPostgresSaver`), pyjwt 2.13 (`PyJWKClient`) + cryptography, psycopg (async), Neon, Clerk, Expo SDK 56 / RN 0.85 / React 19.2, Vite.

## Global Constraints

- Backend test suite MUST stay green — currently **135 passing** (`pytest`).
- `business_id` is NEVER trusted from a request body — always derived from the verified JWT.
- Preserve the mobile login's **Tagalog** copy and error strings, and the dark tokens **bg `#0f1117`**, **accent `#6366f1`**.
- New auth-screen UI is built via the `prototype` skill and held to the `emil-design-eng` craft bar: `ease-out` on entrances (never `ease-in`), sub-300ms UI motion, `transform`/`opacity` only, `transform-origin` correct, `prefers-reduced-motion` handled.
- Run `pick-ui-library` before adding any new auth-UI dependency; do not hand-roll or install abandoned packages.
- Expo SDK 56 / RN 0.85: verify `@clerk/clerk-expo` supports this before the mobile swap (Task 5, Step 1). Mobile has no unit-test harness — mobile tasks gate on `npx tsc --noEmit` (run in `mobile/`) plus the Task 9 E2E.
- Neon: **direct/unpooled** endpoint for DDL + the checkpointer; **pooled** endpoint for request-path psycopg; both `sslmode=require`.

---

### Task 1: Backend DB config → Neon

**Files:**
- Create: `api/db.py`
- Modify: `api/main.py` (all `SUPABASE_DIRECT_URL`/`SUPABASE_DB_URI` reads incl. checkpointer lifespan ~`main.py:323`), `api/ws_handler.py:41,269`, `api/escalation_service.py:120`
- Test: `tests/test_db_config.py`

**Interfaces:**
- Produces: `api.db.db_uri() -> str` (pooled, reads `DATABASE_URL`); `api.db.direct_db_uri() -> str` (reads `DATABASE_DIRECT_URL`, falls back to `DATABASE_URL`). New env vars `DATABASE_URL`, `DATABASE_DIRECT_URL`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_db_config.py
import importlib

def test_db_uri_reads_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://pool/db")
    monkeypatch.delenv("DATABASE_DIRECT_URL", raising=False)
    from api import db
    importlib.reload(db)
    assert db.db_uri() == "postgresql://pool/db"
    # direct falls back to pooled when DATABASE_DIRECT_URL unset
    assert db.direct_db_uri() == "postgresql://pool/db"

def test_direct_db_uri_prefers_direct(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://pool/db")
    monkeypatch.setenv("DATABASE_DIRECT_URL", "postgresql://direct/db")
    from api import db
    importlib.reload(db)
    assert db.direct_db_uri() == "postgresql://direct/db"
    assert db.db_uri() == "postgresql://pool/db"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_db_config.py -v`
Expected: FAIL — `ModuleNotFoundError: api.db`.

- [ ] **Step 3: Create the helper module**

```python
# api/db.py
"""Central Neon connection-string helpers.

Pooled URL for request-path queries; direct URL for DDL + the LangGraph
checkpointer (which runs schema on setup()). See docs/superpowers/specs.
"""
import os


def db_uri() -> str:
    """Pooled Neon connection for request-path psycopg queries."""
    return os.environ.get("DATABASE_URL", "")


def direct_db_uri() -> str:
    """Direct (unpooled) Neon connection for DDL + the checkpointer.

    Falls back to the pooled URL when DATABASE_DIRECT_URL is not set.
    """
    return os.environ.get("DATABASE_DIRECT_URL") or os.environ.get("DATABASE_URL", "")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_db_config.py -v`
Expected: PASS (both tests).

- [ ] **Step 5: Replace all Supabase DB-URI reads**

In `api/main.py`, `api/ws_handler.py`, `api/escalation_service.py`, replace every occurrence of:
```python
db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
```
with (add `from api.db import db_uri, direct_db_uri` at the top of each file; note the local variable was also named `db_uri` — rename the local to `uri` to avoid shadowing the import):
```python
uri = db_uri()
```
and use `uri` in the following `psycopg.AsyncConnection.connect(uri)` / guard lines.

In `api/main.py` lifespan, the `AsyncPostgresSaver.from_conn_string(...)` call (~line 323) and the startup DDL (`CREATE TABLE IF NOT EXISTS ...` blocks) MUST use the **direct** URL:
```python
async with AsyncPostgresSaver.from_conn_string(direct_db_uri()) as checkpointer:
    await checkpointer.setup()
```

- [ ] **Step 6: Run the full suite**

Run: `pytest -q`
Expected: 135+ pass (2 new from Step 1). If any test set `SUPABASE_DIRECT_URL`/`SUPABASE_DB_URI`, update it to set `DATABASE_URL`.

- [ ] **Step 7: Commit**

```bash
git add api/db.py api/main.py api/ws_handler.py api/escalation_service.py tests/test_db_config.py
git commit -m "refactor(db): centralize Neon connection helpers, drop SUPABASE_* db vars"
```

---

### Task 2: Backend auth → Clerk JWKS (RS256)

**Files:**
- Modify: `api/main.py` (`get_business_id_from_token`, ~line 39-95; imports ~line 16)
- Test: `tests/test_auth_jwt.py`

**Interfaces:**
- Consumes: `api.db.db_uri` (Task 1).
- Produces: `get_business_id_from_token(credentials) -> str` unchanged signature (async FastAPI dependency returning `business_id`); new `api.main._jwks_client() -> jwt.PyJWKClient`. New env `CLERK_JWKS_URL`, `CLERK_ISSUER`. Removes `SUPABASE_JWT_SECRET`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_auth_jwt.py
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

BID = str(uuid.uuid4())
ISSUER = "https://clerk.test"


def _keypair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    pub = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return priv, pub


def _token(priv, **claims):
    payload = {"iss": ISSUER, "email": "owner@shop.ph", **claims}
    return pyjwt.encode(payload, priv, algorithm="RS256")


def _creds(tok):
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=tok)


def _mock_business_conn(row):
    conn = AsyncMock()
    cursor = AsyncMock()
    cursor.fetchone = AsyncMock(return_value=row)
    conn.execute = AsyncMock(return_value=cursor)
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=conn)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


async def test_valid_clerk_token_resolves_business_id(monkeypatch):
    priv, pub = _keypair()
    monkeypatch.setenv("CLERK_JWKS_URL", "https://clerk.test/.well-known/jwks.json")
    monkeypatch.setenv("CLERK_ISSUER", ISSUER)
    monkeypatch.setenv("DATABASE_URL", "postgresql://x/y")
    from api import main
    signing_key = MagicMock()
    signing_key.key = pub
    fake_client = MagicMock()
    fake_client.get_signing_key_from_jwt.return_value = signing_key
    with (
        patch.object(main, "_jwks_client", return_value=fake_client),
        patch("api.main.psycopg.AsyncConnection.connect", return_value=_mock_business_conn((BID,))),
    ):
        bid = await main.get_business_id_from_token(_creds(_token(priv)))
    assert bid == BID


async def test_bad_signature_rejected(monkeypatch):
    priv, pub = _keypair()
    other_priv, _ = _keypair()  # token signed by a different key
    monkeypatch.setenv("CLERK_JWKS_URL", "https://clerk.test/jwks")
    monkeypatch.setenv("CLERK_ISSUER", ISSUER)
    from api import main
    signing_key = MagicMock(); signing_key.key = pub
    fake_client = MagicMock(); fake_client.get_signing_key_from_jwt.return_value = signing_key
    with patch.object(main, "_jwks_client", return_value=fake_client):
        with pytest.raises(HTTPException) as exc:
            await main.get_business_id_from_token(_creds(_token(other_priv)))
    assert exc.value.status_code == 401


async def test_missing_email_claim_rejected(monkeypatch):
    priv, pub = _keypair()
    monkeypatch.setenv("CLERK_JWKS_URL", "https://clerk.test/jwks")
    monkeypatch.setenv("CLERK_ISSUER", ISSUER)
    from api import main
    signing_key = MagicMock(); signing_key.key = pub
    fake_client = MagicMock(); fake_client.get_signing_key_from_jwt.return_value = signing_key
    tok = pyjwt.encode({"iss": ISSUER}, priv, algorithm="RS256")  # no email, no sub
    with patch.object(main, "_jwks_client", return_value=fake_client):
        with pytest.raises(HTTPException) as exc:
            await main.get_business_id_from_token(_creds(tok))
    assert exc.value.status_code == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_auth_jwt.py -v`
Expected: FAIL — `_jwks_client` attribute missing / still HS256.

- [ ] **Step 3: Rewrite the auth dependency**

In `api/main.py` imports (~line 16), add:
```python
from functools import lru_cache
```
Replace the body of `get_business_id_from_token` (keep the `async def get_business_id_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:` signature) and add the JWKS client helper directly above it:
```python
@lru_cache(maxsize=1)
def _jwks_client() -> "pyjwt.PyJWKClient":
    jwks_url = os.environ.get("CLERK_JWKS_URL", "")
    if not jwks_url:
        raise HTTPException(status_code=401, detail="Auth not configured")
    return pyjwt.PyJWKClient(jwks_url)


async def get_business_id_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Verify a Clerk RS256 JWT via JWKS and resolve business_id from owner_email.

    - business_id is NEVER trusted from the request body — derived from the JWT.
    - Signature verified against Clerk's JWKS; issuer checked when CLERK_ISSUER set.
    """
    issuer = os.environ.get("CLERK_ISSUER", "")
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(credentials.credentials)
        payload = pyjwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["RS256"],
            issuer=issuer or None,
            options={"verify_aud": False, "verify_iss": bool(issuer)},
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    owner_email = payload.get("email", "") or payload.get("sub", "")
    if not owner_email:
        raise HTTPException(status_code=401, detail="Invalid token")

    uri = db_uri()
    if not uri:
        raise HTTPException(status_code=401, detail="Business not found for this token")
    async with await psycopg.AsyncConnection.connect(uri) as conn:
        cursor = await conn.execute(
            "SELECT id FROM businesses WHERE owner_email = %s LIMIT 1",
            (owner_email,),
        )
        row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Business not found for this token")
    return str(row[0])
```
Ensure `from api.db import db_uri, direct_db_uri` (added in Task 1) is present. Delete any remaining `SUPABASE_JWT_SECRET` reference.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_auth_jwt.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Run the full suite**

Run: `pytest -q`
Expected: all pass (endpoint tests already override `get_business_id_from_token` via `dependency_overrides`, so they are unaffected).

- [ ] **Step 6: Commit**

```bash
git add api/main.py tests/test_auth_jwt.py
git commit -m "feat(auth): verify Clerk RS256 JWTs via JWKS, drop Supabase HS256"
```

---

### Task 3: Backend `GET /me/business`

**Files:**
- Modify: `api/main.py` (add route near the other `/leads` routes)
- Test: `tests/test_me_endpoint.py`

**Interfaces:**
- Consumes: `get_business_id_from_token` (Task 2).
- Produces: `GET /me/business` → `{"business_id": "<uuid>"}`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_me_endpoint.py
import uuid
from fastapi.testclient import TestClient
from api.main import app, get_business_id_from_token

VALID_BID = str(uuid.uuid4())


def test_me_business_returns_business_id():
    app.dependency_overrides[get_business_id_from_token] = lambda: VALID_BID
    try:
        client = TestClient(app)
        r = client.get("/me/business", headers={"Authorization": "Bearer x"})
        assert r.status_code == 200
        assert r.json() == {"business_id": VALID_BID}
    finally:
        app.dependency_overrides.pop(get_business_id_from_token, None)


def test_me_business_requires_auth():
    client = TestClient(app)
    r = client.get("/me/business")
    assert r.status_code in (401, 403)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_me_endpoint.py -v`
Expected: FAIL — 404 (route missing).

- [ ] **Step 3: Add the route**

In `api/main.py`, near the other authenticated routes:
```python
@app.get("/me/business")
async def get_my_business(business_id: str = Depends(get_business_id_from_token)):
    """Return the caller's business_id, derived from the verified JWT."""
    return {"business_id": business_id}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_me_endpoint.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add api/main.py tests/test_me_endpoint.py
git commit -m "feat(api): add GET /me/business (replaces client-side businesses read)"
```

---

### Task 4: Backend env + docs cleanup

**Files:**
- Modify: `.env.example`, `README.md` (run section), `scripts/dev.sh` (if it references SUPABASE_*)
- Test: repo-wide grep gate (no code test)

**Interfaces:** none produced.

- [ ] **Step 1: Update `.env.example`**

Remove `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`, `SUPABASE_DIRECT_URL`, `SUPABASE_DB_URI`. Add:
```dotenv
# Neon Postgres
DATABASE_URL=postgresql://user:pass@ep-xxx-pooler.neon.tech/ottobot?sslmode=require
DATABASE_DIRECT_URL=postgresql://user:pass@ep-xxx.neon.tech/ottobot?sslmode=require
# Clerk auth
CLERK_JWKS_URL=https://<your-clerk-subdomain>.clerk.accounts.dev/.well-known/jwks.json
CLERK_ISSUER=https://<your-clerk-subdomain>.clerk.accounts.dev
```

- [ ] **Step 2: Grep for stragglers**

Run: `grep -rniE "SUPABASE" api agent scripts README.md | grep -v test`
Expected: no matches. Fix any that remain (comments/docstrings referencing "Supabase table" may be reworded to "Postgres table").

- [ ] **Step 3: Run full suite**

Run: `pytest -q`
Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add .env.example README.md scripts/dev.sh
git commit -m "docs(env): swap Supabase env for Neon + Clerk"
```

---

### Task 5: Mobile — Clerk provider, token cache, useAuth

**Files:**
- Create: `mobile/lib/clerk.ts`
- Delete: `mobile/lib/supabase.ts`
- Modify: `mobile/app/_layout.tsx`, `mobile/hooks/useAuth.tsx`, `mobile/package.json`, `mobile/.env.example`
- Gate: `npx tsc --noEmit` (in `mobile/`)

**Interfaces:**
- Produces: `useAuth() -> { isSignedIn: boolean; loading: boolean; getToken: () => Promise<string | null>; signOut: () => void }` (same surface consumers already call).

- [ ] **Step 1: Verify Clerk supports Expo SDK 56, then install**

Run `pick-ui-library` mentally for auth SDK → Clerk is the chosen provider. Confirm compat:
```bash
cd mobile && npm info @clerk/clerk-expo peerDependencies
```
Expected: React/React Native ranges include RN 0.85 / React 19. If incompatible, STOP and report — do not force. Then:
```bash
npm uninstall @supabase/supabase-js
npm install @clerk/clerk-expo expo-secure-store
```

- [ ] **Step 2: Create the Clerk token cache module**

```typescript
// mobile/lib/clerk.ts
import * as SecureStore from 'expo-secure-store';
import type { TokenCache } from '@clerk/clerk-expo/dist/cache';

export const tokenCache: TokenCache = {
  async getToken(key) {
    try { return await SecureStore.getItemAsync(key); } catch { return null; }
  },
  async saveToken(key, value) {
    try { await SecureStore.setItemAsync(key, value); } catch {}
  },
};

export const CLERK_PUBLISHABLE_KEY = process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY!;
```

- [ ] **Step 3: Wrap the app in ClerkProvider + guard on isSignedIn**

In `mobile/app/_layout.tsx`: replace the Supabase `session` import/guard. Wrap the tree in `<ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY} tokenCache={tokenCache}>`, use `<ClerkLoaded>` for the loading gate, and redirect with Clerk's `useAuth().isSignedIn`:
```tsx
import { ClerkProvider, ClerkLoaded, useAuth } from '@clerk/clerk-expo';
import { CLERK_PUBLISHABLE_KEY, tokenCache } from '../lib/clerk';
// ...
function Gate() {
  const { isSignedIn, isLoaded } = useAuth();
  if (!isLoaded) return null;
  if (!isSignedIn) return <Redirect href="/login" />;
  return (/* existing SafeAreaProvider + Stack */);
}
export default function RootLayout() {
  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY} tokenCache={tokenCache}>
      <ClerkLoaded><Gate /></ClerkLoaded>
    </ClerkProvider>
  );
}
```
Keep the existing push-token registration `useEffect`, but trigger it on `isSignedIn` and get the bearer via `getToken()` (Step 4) instead of `session.access_token`.

- [ ] **Step 4: Rewrite the useAuth hook to wrap Clerk**

```tsx
// mobile/hooks/useAuth.tsx
import { useAuth as useClerkAuth } from '@clerk/clerk-expo';

export function useAuth() {
  const { isSignedIn, isLoaded, getToken, signOut } = useClerkAuth();
  return {
    isSignedIn: !!isSignedIn,
    loading: !isLoaded,
    getToken: () => getToken(),
    signOut: () => signOut(),
  };
}
```

- [ ] **Step 5: Update mobile/.env.example**

Remove `EXPO_PUBLIC_SUPABASE_*`; add `EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...`. Keep `EXPO_PUBLIC_API_URL`.

- [ ] **Step 6: Typecheck**

Run: `cd mobile && npx tsc --noEmit`
Expected: clean (0 errors). Consumers of `useAuth` that read `session.access_token` will error here — they are fixed in Tasks 6 and 7.

- [ ] **Step 7: Commit**

```bash
git add mobile/lib/clerk.ts mobile/app/_layout.tsx mobile/hooks/useAuth.tsx mobile/package.json mobile/package-lock.json mobile/.env.example
git rm mobile/lib/supabase.ts
git commit -m "feat(mobile): ClerkProvider + secure-store token cache + useAuth wrapper"
```

---

### Task 6: Mobile — Clerk login screen (prototype skill)

**Files:**
- Modify: `mobile/app/login.tsx`
- Gate: `npx tsc --noEmit` + Task 9 E2E

**Interfaces:**
- Consumes: `@clerk/clerk-expo` `useSignIn`.

- [ ] **Step 1: Prototype the login UI**

Invoke the `prototype` skill with the brief: *"OttoBot mobile login — email + password + 'Mag-login' CTA, dark theme (bg #0f1117, accent #6366f1), Tagalog copy, sits on the auth gate."* Build 3 divergent variants behind the picker, held to the `emil-design-eng` craft bar. Present the picker; the user picks a winner.

- [ ] **Step 2: Promote the winner + wire Clerk auth**

Integrate the picked variant into `mobile/app/login.tsx`. The auth handler MUST use Clerk (keeping the existing Tagalog error strings `'Mali ang email o password. Subukan ulit.'` / `'Hindi makakonekta. Tingnan ang internet mo.'`):
```tsx
import { useSignIn } from '@clerk/clerk-expo';
// inside component:
const { signIn, setActive, isLoaded } = useSignIn();
async function handleLogin() {
  if (!isLoaded) return;
  setLoading(true); setError(null);
  try {
    const res = await signIn.create({ identifier: email, password });
    if (res.status === 'complete') {
      await setActive({ session: res.createdSessionId });
      // root layout auth gate redirects to /(tabs)/pipeline
    } else {
      setError('Mali ang email o password. Subukan ulit.');
    }
  } catch (e: any) {
    const msg = String(e?.errors?.[0]?.message ?? e?.message ?? '').toLowerCase();
    setError(msg.includes('network') || msg.includes('fetch')
      ? 'Hindi makakonekta. Tingnan ang internet mo.'
      : 'Mali ang email o password. Subukan ulit.');
  } finally { setLoading(false); }
}
```
Delete the prototype surface per the skill's Hard Rule 5.

- [ ] **Step 3: Typecheck**

Run: `cd mobile && npx tsc --noEmit`
Expected: clean.

- [ ] **Step 4: Commit**

```bash
git add mobile/app/login.tsx
git commit -m "feat(mobile): Clerk email/password login (prototype-picked UI)"
```

---

### Task 7: Mobile — settings via /me/business + Clerk bearer on all fetches

**Files:**
- Create: `mobile/lib/api.ts`
- Modify: `mobile/app/(tabs)/settings.tsx`, `mobile/app/(tabs)/pipeline.tsx`, `mobile/app/(tabs)/conversation/[id].tsx`
- Gate: `npx tsc --noEmit`

**Interfaces:**
- Consumes: `useAuth().getToken` (Task 5), `GET /me/business` (Task 3).
- Produces: `api.ts` helper `authedFetch(path: string, getToken: () => Promise<string|null>, init?: RequestInit) => Promise<Response>`.

- [ ] **Step 1: Create the authed-fetch helper**

```typescript
// mobile/lib/api.ts
const BASE = process.env.EXPO_PUBLIC_API_URL;

export async function authedFetch(
  path: string,
  getToken: () => Promise<string | null>,
  init: RequestInit = {},
): Promise<Response> {
  const token = await getToken();
  return fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      ...(init.headers ?? {}),
      Authorization: `Bearer ${token ?? ''}`,
    },
  });
}
```

- [ ] **Step 2: Replace the client-side Supabase businesses read in settings.tsx**

Remove `import { supabase }` and the `supabase.from('businesses').select('id')...` effect. Resolve `businessId` via the new endpoint:
```tsx
import { authedFetch } from '../../lib/api';
// inside component, using const { getToken } = useAuth();
useEffect(() => {
  authedFetch('/me/business', getToken)
    .then((r) => (r.ok ? r.json() : null))
    .then((j) => { if (j?.business_id) setBusinessId(j.business_id); })
    .catch(() => {});
}, [getToken]);
```
Update the `fetchAvailability` + `saveAvailability` `fetch(...)` calls in the same file to use `authedFetch('/availability/...', getToken, ...)` and `authedFetch('/availability', getToken, { method: 'POST', headers: {'Content-Type':'application/json'}, body })`.

- [ ] **Step 3: Update pipeline.tsx and conversation/[id].tsx fetches**

Replace their `fetch(${API_URL}/leads ...)` and `fetch(${API_URL}/leads/${id}/messages ...)` calls (which read `session.access_token`) with `authedFetch('/leads', getToken)` / `authedFetch(\`/leads/${id}/messages\`, getToken)`, pulling `getToken` from `useAuth()`.

- [ ] **Step 4: Typecheck**

Run: `cd mobile && npx tsc --noEmit`
Expected: clean, and no remaining `@supabase/supabase-js` imports anywhere:
```bash
grep -rn "supabase" mobile/app mobile/hooks mobile/lib
```
Expected: no matches.

- [ ] **Step 5: Commit**

```bash
git add mobile/lib/api.ts "mobile/app/(tabs)/settings.tsx" "mobile/app/(tabs)/pipeline.tsx" "mobile/app/(tabs)/conversation/[id].tsx"
git commit -m "feat(mobile): route data through backend with Clerk bearer; drop client DB read"
```

---

### Task 8: Onboarding frontend — Clerk signup

**Files:**
- Modify: `frontend/src/OnboardingWizard.tsx`, `frontend/package.json`, `frontend/.env.example`, `frontend/src/main.tsx` (ClerkProvider)
- Gate: `cd frontend && npm run build` (and `npm test` if it exists)

**Interfaces:**
- Consumes: `@clerk/clerk-react` `useSignUp`, business-creation backend endpoint (unchanged).

- [ ] **Step 1: Swap the dependency**

```bash
cd frontend && npm uninstall @supabase/supabase-js && npm install @clerk/clerk-react
```

- [ ] **Step 2: Wrap the app in ClerkProvider**

In `frontend/src/main.tsx`, wrap `<App/>` in `<ClerkProvider publishableKey={import.meta.env.VITE_CLERK_PUBLISHABLE_KEY}>`.

- [ ] **Step 3: Replace step-1 account creation with Clerk**

In `OnboardingWizard.tsx`, replace the Supabase Auth signup call with Clerk `useSignUp()` (`signUp.create({ emailAddress, password })` → email code verify → `setActive`). Keep the existing wizard step flow and the subsequent business-row creation call to the backend unchanged. The business is still linked by `owner_email` server-side.

- [ ] **Step 4: Update frontend/.env.example**

Remove `VITE_SUPABASE_*`; add `VITE_CLERK_PUBLISHABLE_KEY=pk_test_...`.

- [ ] **Step 5: Build gate**

Run: `cd frontend && npm run build`
Expected: build succeeds; then `grep -rn "supabase" frontend/src` → no matches.

- [ ] **Step 6: Commit**

```bash
git add frontend/src frontend/package.json frontend/package-lock.json frontend/.env.example
git commit -m "feat(onboarding): Clerk signup, drop Supabase Auth"
```

---

### Task 9: Cutover, E2E verification, docs

**Files:**
- Modify: `.gitignore` (add `.agents/`), `docs/superpowers/specs/2026-07-29-supabase-to-neon-clerk-design.md` (status → shipped), Obsidian KB (`NOW.md`, `DECISIONS.md`) via MCP
- No code test — live E2E.

- [ ] **Step 1: Provision + configure**

Provision Neon (capture pooled + direct URLs) and a Clerk app (publishable key, JWKS URL, issuer). In the Clerk dashboard, add a **JWT template that emits the `email` claim** (business resolution 401s without it). Fill root `.env`, `mobile/.env`, `frontend/.env`. Create a test user in Clerk + a matching `businesses` row (`owner_email` = that user's email).

- [ ] **Step 2: Boot + auto-create schema**

Run: `./scripts/dev.sh` (backend on :8000). Confirm startup logs show `checkpointer.setup()` + the `CREATE TABLE IF NOT EXISTS` blocks run against Neon with no error.

- [ ] **Step 3: E2E walk (mobile)**

`cd mobile && npx expo start` on a physical device. Verify: login (Clerk) → Pipeline (`GET /leads`) → open a lead (`GET /leads/{id}/messages`, bubble alignment outbound-right) → Settings (`GET /me/business` + toggle + `POST /availability` toast) → trigger an escalation → push `"Hot lead — tumawag na!"` arrives. This closes Phase 06 UAT tests 6–11.

- [ ] **Step 4: Gitignore vendored skills + finalize docs**

Add `.agents/` to `.gitignore`. Flip the spec's status to `Shipped`.

- [ ] **Step 5: Commit + push**

```bash
git add .gitignore docs/superpowers/specs/2026-07-29-supabase-to-neon-clerk-design.md
git commit -m "chore: gitignore vendored skills; mark Neon+Clerk migration shipped"
git push origin main   # or the feature branch
```

- [ ] **Step 6: Update the KB**

Via Obsidian MCP, update `Projects/ottobot/NOW.md` (stack line → Neon + Clerk; Supabase tasks done) and add a `DECISIONS.md` entry: "Left Supabase → Neon (Postgres) + Clerk (auth); Convex rejected (TS-native, kills LangGraph PG checkpointer). 2026-07-29."

---

## Self-Review

**Spec coverage:** DB swap → Task 1; auth verify → Task 2; `/me/business` → Task 3; env/docs → Task 4/9; mobile Clerk (provider, useAuth, login, settings, fetches) → Tasks 5–7; onboarding → Task 8; cutover + E2E (closes UAT 6–11) → Task 9; UI craft via prototype/emil-design-eng → Tasks 6 (+8). All spec sections mapped.

**Placeholder scan:** No TBD/TODO; every code step has concrete code; test bodies are complete. Mobile/onboarding tasks gate on `tsc`/`build` (no RN/unit harness exists — stated in Global Constraints), not fabricated unit tests.

**Type consistency:** `db_uri()`/`direct_db_uri()` (Task 1) consumed in Tasks 2. `get_business_id_from_token` signature preserved (Tasks 2, 3). `useAuth()` surface `{ isSignedIn, loading, getToken, signOut }` defined in Task 5, consumed in Tasks 6–7. `authedFetch(path, getToken, init)` defined Task 7 Step 1, used Steps 2–3. Consistent.
