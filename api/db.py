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
