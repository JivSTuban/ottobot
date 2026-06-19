# Phase 6: Mobile App - Pattern Map

**Mapped:** 2026-06-19
**Files analyzed:** 14
**Analogs found:** 10 / 14

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `api/main.py` (add GET /leads, GET /leads/{id}/messages, POST /push/send) | controller | request-response | `api/main.py` GET /availability/{business_id} + POST /availability | exact |
| `api/escalation_service.py` (add send_push_notification) | service | request-response | `api/escalation_service.py` send_escalation_email | exact |
| `tests/test_push_service.py` | test | request-response | `tests/test_escalation_service.py` | exact |
| `tests/test_push_endpoint.py` | test | request-response | `tests/test_appointment_api.py` | exact |
| `tests/test_leads_endpoints.py` | test | request-response | `tests/test_appointment_api.py` | exact |
| `mobile/lib/supabase.ts` | utility | request-response | `frontend/src/App.tsx` (Supabase init pattern) | partial |
| `mobile/lib/pushToken.ts` | utility | event-driven | no analog — Expo-specific | none |
| `mobile/hooks/useAuth.tsx` | hook | event-driven | no analog — React Native/Expo | none |
| `mobile/app/_layout.tsx` | component | request-response | no analog — Expo Router specific | none |
| `mobile/app/login.tsx` | component | request-response | no analog — RN specific | none |
| `mobile/app/(tabs)/pipeline.tsx` | component | request-response | `frontend/src/OwnerPanel.tsx` (list + fetch pattern) | partial |
| `mobile/app/(tabs)/settings.tsx` | component | request-response | `frontend/src/OwnerPanel.tsx` (availability section) | partial |
| `mobile/app/conversation/[leadId].tsx` | component | request-response | `frontend/src/LeadChat.tsx` | role-match |
| `mobile/components/LeadRow.tsx` + `MessageBubble.tsx` | component | transform | `frontend/src/LeadChat.tsx` | partial |

---

## Pattern Assignments

### `api/main.py` — new GET /leads, GET /leads/{lead_id}/messages, POST /push/send

**Analog:** `api/main.py` — `GET /availability/{business_id}` (lines 330–369)

**Imports pattern** (lines 1–19 of main.py):
```python
import logging
import os
import uuid

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
```

**Validation pattern** (lines 331–339):
```python
@app.get("/availability/{business_id}")
async def get_availability(business_id: str):
    if not validate_business_id(business_id):
        raise HTTPException(status_code=400, detail="business_id must be a valid UUID v4")
```

**Core GET-with-DB pattern** (lines 340–369):
```python
    db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
    if not db_uri:
        return {"slots": [], "fallback": FALLBACK_PHRASE}

    async with await psycopg.AsyncConnection.connect(db_uri) as conn:
        cursor = await conn.execute(
            "SELECT day_of_week, start_time, end_time FROM business_availability WHERE business_id = %s",
            (business_id,),
        )
        raw_rows = await cursor.fetchall()

    rows = [{"day_of_week": r[0], ...} for r in raw_rows]
    return {"slots": rows}
```

**Auth guard for new Phase 6 endpoints — NEW pattern (no analog in codebase):**
Phase 6 requires JWT cross-check: extract `sub` (owner_email) from Bearer token, join to `businesses.owner_email` to get `business_id`, then query. This differs from all existing endpoints which trust client-supplied `business_id`. Use FastAPI `Depends` with `HTTPBearer`:
```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()

async def get_business_id_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    # Decode JWT sub (owner_email), look up business_id in businesses table
    # Raise HTTPException(401) if invalid
    ...
```

**Pydantic model pattern** (lines 190–199):
```python
class AvailabilityRequest(BaseModel):
    business_id: str
    slots: list[AvailabilitySlotIn]
```
Apply same pattern for `PushTokenRequest(BaseModel)` with `expo_token: str`, `business_id: str`.

---

### `api/escalation_service.py` — add `send_push_notification()`

**Analog:** `api/escalation_service.py` — `send_escalation_email()` (lines 22–65) — EXACT match

**Core pattern** (lines 33–65):
```python
async def send_escalation_email(to_email, lead_phone, conversation_summary) -> None:
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        logger.debug("RESEND_API_KEY not set — skipping escalation email")
        return

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                RESEND_API_URL,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={...},
            )
            if resp.status_code >= 400:
                logger.warning("Resend API returned %s ...", resp.status_code)
        except httpx.RequestError as exc:
            logger.warning("Resend API request failed: %s", type(exc).__name__)
```

Copy this exactly for `send_push_notification()`, replacing:
- `RESEND_API_URL` → `"https://exp.host/--/api/v2/push/send"`
- `api_key` guard → `if not expo_token: return`
- No `Authorization` header needed for Expo Push API
- JSON payload: `{"to": expo_token, "title": ..., "body": ..., "data": {}, "sound": "default", "channelId": "default"}`

---

### `tests/test_push_service.py`

**Analog:** `tests/test_escalation_service.py` (lines 1–136) — EXACT match

**Test structure pattern** (lines 1–12):
```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_send_push_no_token(monkeypatch):
    """No-op when expo_token is empty."""
    from api.escalation_service import send_push_notification
    with patch("httpx.AsyncClient") as mock_client:
        await send_push_notification("", "title", "body")
        mock_client.assert_not_called()
```

**httpx mock pattern** (lines 34–52):
```python
mock_response = MagicMock()
mock_response.status_code = 200
mock_post = AsyncMock(return_value=mock_response)
mock_client_instance = AsyncMock()
mock_client_instance.post = mock_post
mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
mock_client_instance.__aexit__ = AsyncMock(return_value=False)

with patch("api.escalation_service.httpx.AsyncClient", return_value=mock_client_instance):
    await send_push_notification("ExponentPushToken[xxx]", "Hot lead", "Call now")

call_kwargs = mock_post.call_args
sent_json = call_kwargs.kwargs["json"]
assert sent_json["to"] == "ExponentPushToken[xxx]"
```

---

### `tests/test_push_endpoint.py` + `tests/test_leads_endpoints.py`

**Analog:** `tests/test_appointment_api.py` (lines 1–60) — EXACT match

**TestClient + fixture pattern** (lines 1–59):
```python
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

VALID_BID = str(uuid.uuid4())

def _make_mock_conn():
    mock_cursor = MagicMock()
    mock_cursor.fetchall = AsyncMock(return_value=[(...)]) 
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=mock_cursor)
    mock_conn_ctx = AsyncMock()
    mock_conn_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn_ctx.__aexit__ = AsyncMock(return_value=False)
    return mock_conn_ctx

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SUPABASE_DIRECT_URL", "")
    with patch("psycopg.AsyncConnection.connect", return_value=_make_mock_conn()):
        from api.main import app
        with TestClient(app) as c:
            yield c
```

---

### `mobile/app/(tabs)/pipeline.tsx`

**Analog:** `frontend/src/OwnerPanel.tsx` — list rendering + fetch pattern

**Fetch + state pattern** (copy structure, adapt to React Native):
```typescript
// Analog pattern: fetch on mount, store in state, render list
const [leads, setLeads] = useState<Lead[]>([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
  fetchLeads();
}, []);

async function fetchLeads() {
  const res = await fetch(`${API_URL}/leads?business_id=${businessId}`, {
    headers: { Authorization: `Bearer ${session?.access_token}` },
  });
  const json = await res.json();
  setLeads(json.leads ?? []);
  setLoading(false);
}
```

Replace `<div>` → `<SectionList>`, `className` → `StyleSheet`, browser `fetch` stays the same.

---

### `mobile/app/conversation/[leadId].tsx`

**Analog:** `frontend/src/LeadChat.tsx` — chat log render pattern

Key difference: use `FlatList inverted` with `data` sorted newest-first (descending `created_at`). The web analog uses a `<div>` scroll container — the mobile version must flip to FlatList.

---

## Shared Patterns

### DB Access — No-op when DB missing
**Source:** `api/main.py` (all endpoints), `api/escalation_service.py` (lines 33–36)
**Apply to:** All 3 new FastAPI endpoints
```python
db_uri = os.environ.get("SUPABASE_DIRECT_URL") or os.environ.get("SUPABASE_DB_URI", "")
if not db_uri:
    return {"status": "ok", ...}  # graceful no-op for test environments
```

### Parameterized Queries (no SQL injection surface)
**Source:** `api/main.py` lines 317–325
**Apply to:** All new DB queries in Phase 6 endpoints
```python
await conn.execute(
    "SELECT ... FROM leads WHERE business_id = %s",
    (business_id,),   # always tuple, never f-string
)
```

### UUID Validation
**Source:** `api/main.py` lines 31–57 (`validate_business_id`, `validate_thread_id`)
**Apply to:** `GET /leads?business_id=`, `GET /leads/{lead_id}/messages`, `POST /push/send`
```python
if not validate_business_id(business_id):
    raise HTTPException(status_code=400, detail="business_id must be a valid UUID v4")
```

### httpx AsyncClient pattern (external HTTP)
**Source:** `api/escalation_service.py` lines 44–65
**Apply to:** `send_push_notification()` in `escalation_service.py`
```python
async with httpx.AsyncClient(timeout=10.0) as client:
    try:
        resp = await client.post(url, headers={...}, json={...})
        if resp.status_code >= 400:
            logger.warning(...)
    except httpx.RequestError as exc:
        logger.warning("... %s", type(exc).__name__)
```

### Test: mock httpx AsyncClient
**Source:** `tests/test_escalation_service.py` lines 34–52
**Apply to:** `tests/test_push_service.py`
Use the `mock_client_instance.__aenter__` + `__aexit__` pattern with `patch("api.escalation_service.httpx.AsyncClient", ...)`.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `mobile/lib/pushToken.ts` | utility | event-driven | No Expo/RN code in codebase; use RESEARCH.md Pattern 1 verbatim |
| `mobile/hooks/useAuth.tsx` | hook | event-driven | No RN hooks in codebase; use Supabase `onAuthStateChange` pattern from RESEARCH.md |
| `mobile/app/_layout.tsx` | component | request-response | No Expo Router layouts in codebase; use RESEARCH.md structure |
| `mobile/app/login.tsx` | component | request-response | No RN auth screens in codebase |
| `mobile/lib/supabase.ts` | utility | request-response | Frontend uses Supabase via onboarding form fetch, not supabase-js client; use RESEARCH.md Pattern 2 (`detectSessionInUrl: false` is critical) |

---

## Metadata

**Analog search scope:** `api/`, `frontend/src/`, `tests/`
**Files scanned:** 7 source files, 2 test files
**Pattern extraction date:** 2026-06-19
