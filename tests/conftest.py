"""
Shared test fixtures for OttoBot Wave 0 test harness.

Fixtures:
- demo_profile_dental / aesthetics / real_estate  — BusinessProfile-shaped dicts
- mock_router — async fixture with deterministic acompletion response
- mock_checkpointer — in-memory shim with async setup/aget_state/aput
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


# ---------------------------------------------------------------------------
# BusinessProfile-shaped dicts (cannot import BusinessProfile yet — models
# land in Plan 03; using dicts that match the AI-SPEC Section 4b.1 schema)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def demo_profile_dental():
    return {
        "agent_name": "Ate Ana",
        "business_name": "Smile Dental Clinic",
        "industry": "dental",
        "services": ["dental cleaning", "whitening"],
        "pricing": "P500-P2500",
        "phone": "+63917XXXXXXX",
    }


@pytest.fixture(scope="session")
def demo_profile_aesthetics():
    return {
        "agent_name": "Ate Bea",
        "business_name": "Bea Aesthetics Studio",
        "industry": "aesthetics",
        "services": ["facial", "whitening"],
        "pricing": "P800-P3000",
        "phone": "+63918XXXXXXX",
    }


@pytest.fixture(scope="session")
def demo_profile_real_estate():
    return {
        "agent_name": "Kuya Marco",
        "business_name": "Marco Realty",
        "industry": "real_estate",
        "services": ["condo tours", "property listing"],
        "pricing": "varies",
        "phone": "+63919XXXXXXX",
    }


# ---------------------------------------------------------------------------
# Mock LiteLLM Router — returns deterministic acompletion response
# ---------------------------------------------------------------------------

@pytest.fixture
async def mock_router():
    """Async mock for litellm.Router with deterministic acompletion response."""
    router = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "MOCK_REPLY"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    router.acompletion = AsyncMock(return_value=mock_response)
    return router


# ---------------------------------------------------------------------------
# Mock checkpointer — in-memory shim that satisfies AsyncPostgresSaver interface
# ---------------------------------------------------------------------------

@pytest.fixture
async def mock_checkpointer():
    """In-memory mock checkpointer — avoids Supabase dependency in unit tests."""
    checkpointer = MagicMock()
    checkpointer.setup = AsyncMock(return_value=None)
    checkpointer.aget_tuple = AsyncMock(return_value=None)
    checkpointer.aput = AsyncMock(return_value=None)
    checkpointer.aget_state = AsyncMock(return_value=None)
    return checkpointer
