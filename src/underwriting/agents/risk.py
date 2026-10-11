"""Score the enriched case. Code sets the number. The model lists factors."""

import json

from underwriting.llm import LlmClient
from underwriting.prompt_loader import load_prompt, wrap_untrusted
from underwriting.schemas import EnrichmentResult, RiskResult

PROMPT = load_prompt("risk_v1.md")


def approval_score(enriched: EnrichmentResult) -> float:
    score = 0.50
    age = enriched.age
    if age <= 25:
        score += 0.05
    elif age <= 45:
        score += 0.20
    elif age <= 60:
        score += 0.10
    amount = enriched.coverage_amount
    if amount <= 50_000:
        score += 0.25
    elif amount <= 200_000:
        score += 0.15
    elif amount <= 400_000:
        score += 0.05
    names = {fact.fact for fact in enriched.extra_facts}
    if "prior_claim" in names:
        score -= 0.25
    if "hazardous_occupation" in names:
        score -= 0.15
    if "recent_lapse" in names:
        score -= 0.30
    return round(min(1.0, max(0.0, score)), 2)


def risk_scoring_agent(enriched: EnrichmentResult, llm: LlmClient) -> RiskResult:
    response = llm.complete(
        system=PROMPT,
        user=wrap_untrusted("case", enriched.model_dump_json()),
        applicant_id=enriched.applicant_id,
        agent_name="risk_scoring_agent",
    )
    try:
        data = json.loads(response.text)
        model_score = float(data["risk_score"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError("risk output failed validation") from exc
    if model_score < 0 or model_score > 1:
        raise ValueError("risk_score must be from 0 to 1")
    factors = data.get("risk_factors", [])
    if not isinstance(factors, list):
        raise ValueError("risk_factors must be a list")
    return RiskResult(
        applicant_id=enriched.applicant_id,
        risk_score=approval_score(enriched),
        risk_factors=[str(factor) for factor in factors],
        extra_facts=enriched.extra_facts,
    )
