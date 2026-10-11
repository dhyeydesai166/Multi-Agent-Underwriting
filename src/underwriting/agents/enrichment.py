"""Add extra facts from the records file. Drop anything the model invents."""

import json

from underwriting.llm import LlmClient
from underwriting.prompt_loader import load_prompt, wrap_untrusted
from underwriting.records import lookup_records
from underwriting.schemas import EnrichmentResult, IntakeResult

PROMPT = load_prompt("enrichment_v1.md")


def enrichment_agent(intake: IntakeResult, llm: LlmClient) -> EnrichmentResult:
    facts = lookup_records(intake.applicant_id)
    payload = {
        "intake": intake.model_dump(),
        "records": [fact.model_dump() for fact in facts],
    }
    response = llm.complete(
        system=PROMPT,
        user=wrap_untrusted("case", json.dumps(payload)),
        applicant_id=intake.applicant_id,
        agent_name="enrichment_agent",
    )
    try:
        json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise ValueError("enrichment output failed validation") from exc
    return EnrichmentResult(
        applicant_id=intake.applicant_id,
        full_name=intake.full_name,
        age=intake.age,
        coverage_amount=intake.coverage_amount,
        extra_facts=facts,
    )
