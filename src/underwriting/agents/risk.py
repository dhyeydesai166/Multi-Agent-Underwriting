"""Score the enriched case. Copy extra facts forward for the decision rule."""

import json

from underwriting.llm import LlmClient
from underwriting.prompt_loader import load_prompt, wrap_untrusted
from underwriting.schemas import EnrichmentResult, RiskResult

PROMPT = load_prompt("risk_v1.md")


def risk_scoring_agent(enriched: EnrichmentResult, llm: LlmClient) -> RiskResult:
    response = llm.complete(
        system=PROMPT,
        user=wrap_untrusted("case", enriched.model_dump_json()),
        applicant_id=enriched.applicant_id,
        agent_name="risk_scoring_agent",
    )
    try:
        data = json.loads(response.text)
        score = float(data["risk_score"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError("risk output failed validation") from exc
    if score < 0 or score > 1:
        raise ValueError("risk_score must be from 0 to 1")
    factors = data.get("risk_factors", [])
    if not isinstance(factors, list):
        raise ValueError("risk_factors must be a list")
    return RiskResult(
        applicant_id=enriched.applicant_id,
        risk_score=score,
        risk_factors=[str(factor) for factor in factors],
        extra_facts=enriched.extra_facts,
    )
