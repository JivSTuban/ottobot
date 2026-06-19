"""
agent/models.py — BusinessProfile, Industry enum, StageDetectionOutput, DEMO_PROFILES.

Provides Pydantic models for business configuration and LLM structured output.
Provides Jinja2 environment factory and render_system_prompt method.

All templates live in agent/prompts/ and use StrictUndefined to catch missing fields.
"""

import os
from enum import Enum
from typing import List, Literal

import jinja2
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pydantic import BaseModel, Field, field_validator


class Industry(str, Enum):
    dental = "dental"
    aesthetics = "aesthetics"
    real_estate = "real_estate"


class BusinessProfile(BaseModel):
    agent_name: str = Field(..., description="Persona name, e.g. 'Ate Ana'")
    business_name: str
    industry: Industry
    services: List[str] = Field(..., min_length=1)
    pricing: str = Field(..., description="Price range string, e.g. 'P500-P1500'. Never leave None.")
    phone: str

    @field_validator("pricing")
    @classmethod
    def pricing_not_empty(cls, v: str) -> str:
        if v is None or v.strip() == "":
            raise ValueError("pricing must be a non-empty string")
        return v

    def render_system_prompt(self, env: jinja2.Environment, outbound_start: bool = False) -> str:
        template = env.get_template(f"{self.industry.value}.j2")
        return template.render(**self.model_dump(), outbound_start=outbound_start)


def make_env() -> Environment:
    """Return a Jinja2 Environment pointing at agent/prompts/ with StrictUndefined."""
    prompts_dir = os.path.join(os.path.dirname(__file__), "prompts")
    return Environment(
        loader=FileSystemLoader(prompts_dir),
        undefined=StrictUndefined,
    )


# DEMO personas — D-12 canonical names and data
DEMO_PROFILES: dict[str, "BusinessProfile"] = {
    "dental": BusinessProfile(
        agent_name="Ate Ana",
        business_name="Smile Dental Clinic",
        industry=Industry.dental,
        services=["dental cleaning", "whitening"],
        pricing="P500-P2500",
        phone="+63917XXXXXXX",
    ),
    "aesthetics": BusinessProfile(
        agent_name="Ate Bea",
        business_name="Bea Aesthetics Studio",
        industry=Industry.aesthetics,
        services=["facial", "whitening"],
        pricing="P800-P3000",
        phone="+63918XXXXXXX",
    ),
    "real_estate": BusinessProfile(
        agent_name="Kuya Marco",
        business_name="Marco Realty",
        industry=Industry.real_estate,
        services=["condo tours", "property listing"],
        pricing="varies",
        phone="+63919XXXXXXX",
    ),
}


class StageDetectionOutput(BaseModel):
    next_stage: Literal[
        "intro",
        "qualify",
        "pitch",
        "objection_handling",
        "propose_appointment",
        "confirm",
        "escalate",
    ]
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., max_length=200)
