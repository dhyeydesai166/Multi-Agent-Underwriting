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


def _client(applicant_id: str, age: int, amount: int, score: float) -> ScriptedClient:
    intake = {
        "applicant_id": applicant_id,
        "full_name": "Ada Lovelace",
        "age": age,
        "coverage_amount": amount,
        "missing_fields": [],
    }
    return ScriptedClient([
        json.dumps(intake),
        json.dumps({"extra_facts": []}),
        json.dumps({"risk_score": score, "risk_factors": []}),
        json.dumps({"decision": "deny", "reason": "Reviewed the score."}),
    ])


def test_handoffs_and_approve() -> None:
    form = _form("APP-9001", 35, 25000)
    result = run_case(form, _client("APP-9001", 35, 25000, 0.82))
    assert [step.agent for step in result.traces] == [
        "intake_agent",
        "enrichment_agent",
        "risk_scoring_agent",
        "recommendation_agent",
    ]
    assert result.traces[1].input_source == "application_received"
    assert result.traces[1].input["applicant_id"] == "APP-9001"
    assert result.traces[2].input_source == "enrichment_complete"
    assert result.traces[3].input_source == "risk_assessed"
    assert result.decision == "approve"
    assert result.queue_depths == {
        "application_received": 0,
        "enrichment_complete": 0,
        "risk_assessed": 0,
    }


def test_prior_claim_is_refer() -> None:
    result = run_case(
        _form("APP-1002", 52, 500000),
        _client("APP-1002", 52, 500000, 0.90),
    )
    assert result.decision == "refer"


def test_hazardous_occupation_is_refer() -> None:
    result = run_case(
        _form("APP-1001", 35, 25000),
        _client("APP-1001", 35, 25000, 0.90),
    )
    assert result.decision == "refer"


def test_recent_lapse_is_deny() -> None:
    result = run_case(
        _form("APP-1003", 19, 400000),
        _client("APP-1003", 19, 400000, 0.90),
    )
    assert result.decision == "deny"


def test_low_score_is_deny() -> None:
    result = run_case(
        _form("APP-9002", 19, 400000),
        _client("APP-9002", 19, 400000, 0.40),
    )
    assert result.decision == "deny"
