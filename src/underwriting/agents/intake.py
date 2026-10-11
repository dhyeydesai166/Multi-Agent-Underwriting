"""Turn a raw form into a clean application."""

import json

from pydantic import ValidationError

from underwriting.llm import LlmClient
from underwriting.prompt_loader import load_prompt, wrap_untrusted
from underwriting.schemas import IntakeResult, RawApplication

PROMPT = load_prompt("intake_v1.md")


def _reject_invalid(raw: RawApplication) -> None:
    if not raw.applicant_id.strip() or not raw.full_name.strip():
        raise ValueError("applicant_id and full_name are required")
    if raw.age < 18 or raw.age > 120:
        raise ValueError("age must be from 18 to 120")
    if raw.coverage_amount <= 0:
        raise ValueError("coverage_amount must be greater than 0")


def intake_agent(raw: RawApplication, llm: LlmClient) -> IntakeResult:
    _reject_invalid(raw)
    response = llm.complete(
        system=PROMPT,
        user=wrap_untrusted("application", raw.model_dump_json()),
        applicant_id=raw.applicant_id,
    )
    try:
        return IntakeResult.model_validate(json.loads(response.text))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError("intake output failed validation") from exc
