"""tests/test_db_config.py — Unit tests for api.db connection-string helpers."""
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
