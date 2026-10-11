"""The model writes the reason. Code sets approve, deny, or refer."""

import json
from typing import Literal

from underwriting.config import APPROVE_AT
from underwriting.llm import LlmClient
from underwriting.prompt_loader import load_prompt, wrap_untrusted
from underwriting.schemas import RecommendationResult, RiskResult

PROMPT = load_prompt("recommendation_v2.md")
Decision = Literal["approve", "deny", "refer"]


def decide(risk: RiskResult) -> Decision:
    names = {fact.fact for fact in risk.extra_facts}
    if "prior_claim" in names:
        return "refer"
    if "hazardous_occupation" in names:
        return "refer"
    if "recent_lapse" in names:
        return "deny"
    if risk.risk_score >= APPROVE_AT:
        return "approve"
    return "deny"


def recommendation_agent(risk: RiskResult, llm: LlmClient) -> RecommendationResult:
    response = llm.complete(
        system=PROMPT,
        user=wrap_untrusted("case", risk.model_dump_json()),
        applicant_id=risk.applicant_id,
        agent_name="recommendation_agent",
    )
    try:
        data = json.loads(response.text)
        reason = str(data["reason"]).strip()
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError("recommendation output failed validation") from exc
    if not reason:
        raise ValueError("recommendation reason is required")
    return RecommendationResult(
        applicant_id=risk.applicant_id,
        decision=decide(risk),
        reason=reason,
    )
