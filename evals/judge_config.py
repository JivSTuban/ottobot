"""
Arize Phoenix LLM judge templates and configuration for OttoBot eval flywheel.
Source: AI-SPEC Section 5

This module defines constants and an example function — it does not execute at import time.
Use with: python evals/judge_config.py (example dry run) or import in eval scripts.
"""

# ---------------------------------------------------------------------------
# LLM Judge Templates
# ---------------------------------------------------------------------------

REGISTER_MATCH_TEMPLATE = """
You are a Filipino sales manager evaluating an AI sales agent.
Conversation turn:
Lead: {lead_message}
Agent: {agent_message}

Does the agent's reply match the lead's language register (Taglish/Tagalog/English ratio)?
Answer: PASS or FAIL. Then one sentence explaining why.
"""

AI_DISCLOSURE_TEMPLATE = """
You are reviewing an AI sales agent for regulatory compliance (NPC Advisory 2024-04).
The following is the agent's first message in a conversation:
Agent: {agent_message}

Does the agent clearly disclose that it is an AI assistant BEFORE asking for the lead's name or contact information?
Answer: PASS or FAIL. Then one sentence explaining why.
"""

PRICE_ACCURACY_TEMPLATE = """
You are evaluating an AI sales agent for price accuracy.
Business pricing: {pricing_range}
Agent's message: {agent_message}

Does the agent mention any prices that fall OUTSIDE the stated pricing range?
Answer: PASS (no hallucinated prices) or FAIL (prices outside range). Then one sentence explaining why.
"""

ESCALATION_TIMING_TEMPLATE = """
You are evaluating an AI sales agent's escalation behavior.
Lead's final message: {lead_message}
Agent's response: {agent_message}

The lead has expressed clear booking intent. Did the agent respond by moving toward appointment confirmation (not continuing to sell)?
Answer: PASS or FAIL. Then one sentence explaining why.
"""

OBJECTION_DEFLECTION_TEMPLATE = """
You are evaluating an AI sales agent's objection handling.
Lead's message: {lead_message}
Agent's response: {agent_message}

Did the agent handle the price objection with empathy and soft deflection WITHOUT agreeing to a discount?
Answer: PASS or FAIL. Then one sentence explaining why.
"""


# ---------------------------------------------------------------------------
# Example LLM classify call (requires arize-phoenix install)
# ---------------------------------------------------------------------------

def example_register_match_classify(eval_df):
    """
    Example: Run REGISTER_MATCH_TEMPLATE judge via Arize Phoenix llm_classify.

    Args:
        eval_df: pandas DataFrame with columns: lead_message, agent_message

    Returns:
        DataFrame with PASS/FAIL classifications
    """
    try:
        from phoenix.evals import OpenAIModel, llm_classify
    except ImportError:
        raise ImportError(
            "arize-phoenix not installed. Run: pip install arize-phoenix"
        )

    results = llm_classify(
        dataframe=eval_df,
        template=REGISTER_MATCH_TEMPLATE,
        model=OpenAIModel(model="gpt-4o-mini"),
        rails=["PASS", "FAIL"],
    )
    return results


# Dimension-to-template mapping for batch eval
JUDGE_TEMPLATES = {
    "taglish_register": REGISTER_MATCH_TEMPLATE,
    "ai_disclosure": AI_DISCLOSURE_TEMPLATE,
    "price_accuracy": PRICE_ACCURACY_TEMPLATE,
    "escalation_trigger": ESCALATION_TIMING_TEMPLATE,
    "objection_handling": OBJECTION_DEFLECTION_TEMPLATE,
}
