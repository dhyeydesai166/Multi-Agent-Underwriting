"""The four desks talk only through queues."""

import json

from tests.fakes import ScriptedClient
from underwriting.pipeline import run_case
from underwriting.schemas import RawApplication


def _form(applicant_id: str, age: int, amount: int) -> RawApplication:
    return RawApplication(
        applicant_id=applicant_id,
        full_name="Ada Lovelace",
        age=age,
        coverage_amount=amount,
    )


def _client(score: float) -> ScriptedClient:
    intake = {
        "applicant_id": "APP-1001",
        "full_name": "Ada Lovelace",
        "age": 35,
        "coverage_amount": 25000,
        "missing_fields": [],
    }
    return ScriptedClient([
        json.dumps(intake),
        json.dumps({"extra_facts": []}),
        json.dumps({"risk_score": score, "risk_factors": []}),
        json.dumps({"decision": "deny", "reason": "Reviewed the score."}),
    ])


def test_handoffs_and_approve() -> None:
    form = _form("APP-1001", 35, 25000)
    result = run_case(form, _client(0.82))
    assert [step.agent for step in result.traces] == [
        "intake_agent",
        "enrichment_agent",
        "risk_scoring_agent",
        "recommendation_agent",
    ]
    assert result.traces[1].input_source == "application_received"
    assert result.traces[1].input["applicant_id"] == "APP-1001"
    assert result.traces[2].input_source == "enrichment_complete"
    assert result.traces[3].input_source == "risk_assessed"
    assert result.decision == "approve"
    assert result.queue_depths == {
        "application_received": 0,
        "enrichment_complete": 0,
        "risk_assessed": 0,
    }


def test_prior_claim_is_refer() -> None:
    form = _form("APP-1002", 52, 500000)
    client = _client(0.90)
    client.texts[0] = json.dumps({
        "applicant_id": "APP-1002",
        "full_name": "Ada Lovelace",
        "age": 52,
        "coverage_amount": 500000,
        "missing_fields": [],
    })
    result = run_case(form, client)
    assert result.decision == "refer"


def test_low_score_is_deny() -> None:
    form = _form("APP-1003", 19, 400000)
    client = _client(0.40)
    client.texts[0] = json.dumps({
        "applicant_id": "APP-1003",
        "full_name": "Ada Lovelace",
        "age": 19,
        "coverage_amount": 400000,
        "missing_fields": [],
    })
    result = run_case(form, client)
    assert result.decision == "deny"
