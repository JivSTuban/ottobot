"""
AGENT-03/04: BusinessProfile, Jinja2 render, DEMO_PROFILES, StageDetectionOutput,
and ConversationState tests.

Implements the 7 behaviors from Plan 01-03 Task 1.
"""

import pytest
import jinja2


def test_business_profile_valid_instantiation():
    """Test 1: BusinessProfile instantiates with all required fields."""
    from agent.models import BusinessProfile, Industry

    profile = BusinessProfile(
        agent_name="Ate Ana",
        business_name="Smile Dental Clinic",
        industry=Industry.dental,
        services=["dental cleaning"],
        pricing="P500-P2500",
        phone="+63917XXXXXXX",
    )
    assert profile.agent_name == "Ate Ana"
    assert profile.business_name == "Smile Dental Clinic"
    assert profile.industry == Industry.dental


def test_business_profile_pricing_none_raises():
    """Test 2: BusinessProfile raises ValidationError when pricing=None."""
    from agent.models import BusinessProfile, Industry
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        BusinessProfile(
            agent_name="Ate Ana",
            business_name="Smile Dental Clinic",
            industry=Industry.dental,
            services=["dental cleaning"],
            pricing=None,
            phone="+63917XXXXXXX",
        )


def test_demo_profiles_correct_names():
    """Test 3: DEMO_PROFILES contains Ate Ana/Ate Bea/Kuya Marco (D-12)."""
    from agent.models import DEMO_PROFILES

    assert DEMO_PROFILES["dental"].agent_name == "Ate Ana"
    assert DEMO_PROFILES["aesthetics"].agent_name == "Ate Bea"
    assert DEMO_PROFILES["real_estate"].agent_name == "Kuya Marco"


def test_demo_profile_dental_render_system_prompt():
    """Test 4: DEMO_PROFILES['dental'].render_system_prompt returns string with
    'Ate Ana', 'Smile Dental Clinic', and AI disclosure phrase 'AI assistant'."""
    from agent.models import DEMO_PROFILES, make_env

    env = make_env()
    rendered = DEMO_PROFILES["dental"].render_system_prompt(env)

    assert isinstance(rendered, str)
    assert len(rendered) > 0
    assert "Ate Ana" in rendered
    assert "Smile Dental Clinic" in rendered
    assert "AI assistant" in rendered


def test_jinja2_strict_undefined_raises_on_missing_field():
    """Test 5: Rendering with StrictUndefined raises UndefinedError when 'phone' is missing."""
    from agent.models import BusinessProfile, Industry, make_env
    from jinja2 import Environment, FileSystemLoader, StrictUndefined

    env = make_env()
    # Build a partial dict missing 'phone' and render manually
    template = env.get_template("dental.j2")
    with pytest.raises(jinja2.exceptions.UndefinedError):
        template.render(
            agent_name="Ate Ana",
            business_name="Smile Dental Clinic",
            industry="dental",
            services=["dental cleaning"],
            pricing="P500-P2500",
            # phone intentionally omitted
        )


def test_stage_detection_output_confidence_out_of_range_raises():
    """Test 6: StageDetectionOutput raises ValidationError when confidence > 1.0."""
    from agent.models import StageDetectionOutput
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        StageDetectionOutput(next_stage="pitch", confidence=1.5, reasoning="x")


def test_conversation_state_import():
    """Test 7: ConversationState is importable as TypedDict with all required fields."""
    from agent.state import ConversationState, STAGES

    # Verify it's a TypedDict by checking __annotations__
    assert "messages" in ConversationState.__annotations__
    assert "stage" in ConversationState.__annotations__
    assert "thread_id" in ConversationState.__annotations__
    assert "escalated" in ConversationState.__annotations__
    assert "visit_count" in ConversationState.__annotations__
    assert "message_timestamps" in ConversationState.__annotations__

    # STAGES is a Literal type — just verify it exists
    assert STAGES is not None
