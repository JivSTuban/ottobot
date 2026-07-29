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
