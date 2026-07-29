"""
tests/test_me_endpoint.py — Unit tests for GET /me/business endpoint.

Covers:
- GET /me/business returns {"business_id": "<uuid>"} with authenticated business_id from JWT
- GET /me/business without Authorization header → 401 or 403

Uses FastAPI TestClient (synchronous). JWT auth dependency is overridden via
FastAPI dependency_overrides for unit-test isolation.

asyncio_mode = "auto" in pyproject.toml — no @pytest.mark.asyncio decorator needed.
"""

import uuid
from fastapi.testclient import TestClient
from api.main import app, get_business_id_from_token

VALID_BID = str(uuid.uuid4())


def test_me_business_returns_business_id():
    """GET /me/business with mock JWT → 200, {"business_id": "<uuid>"}."""
    app.dependency_overrides[get_business_id_from_token] = lambda: VALID_BID
    try:
        client = TestClient(app)
        r = client.get("/me/business", headers={"Authorization": "Bearer x"})
        assert r.status_code == 200
        assert r.json() == {"business_id": VALID_BID}
    finally:
        app.dependency_overrides.pop(get_business_id_from_token, None)


def test_me_business_requires_auth():
    """GET /me/business without Authorization header → 401 or 403."""
    client = TestClient(app)
    r = client.get("/me/business")
    assert r.status_code in (401, 403)
