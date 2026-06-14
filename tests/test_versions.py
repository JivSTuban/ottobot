"""
Wave 0 sanity tests: Python version and key import paths.
These MUST pass before any implementation begins.
"""

import sys


def test_python_312_or_higher():
    """Assert Python >= 3.12 is the active interpreter (langgraph requires >=3.12)."""
    assert sys.version_info >= (3, 12), (
        f"Python 3.12+ required; got {sys.version_info}. "
        "Run: brew install python@3.12 and recreate venv."
    )


def test_async_postgres_saver_import_path():
    """Assert AsyncPostgresSaver resolves at the expected import path (RESEARCH.md Critical action)."""
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    assert AsyncPostgresSaver.__module__ == "langgraph.checkpoint.postgres.aio", (
        f"Unexpected module: {AsyncPostgresSaver.__module__}. "
        "Import path changed in installed version — update all references."
    )


def test_langgraph_importable():
    import langgraph
    assert langgraph is not None


def test_litellm_importable():
    import litellm
    assert litellm is not None


def test_fastapi_importable():
    import fastapi
    assert fastapi is not None


def test_pydantic_v2():
    import pydantic
    major = int(pydantic.__version__.split(".")[0])
    assert major >= 2, f"Pydantic v2 required; got {pydantic.__version__}"


def test_jinja2_importable():
    import jinja2
    from jinja2 import StrictUndefined  # must be available for pitfall prevention
    assert StrictUndefined is not None
