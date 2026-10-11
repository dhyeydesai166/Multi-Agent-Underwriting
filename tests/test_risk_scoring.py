"""Risk scoring, alone. Code sets the score. The model lists factors."""

import json

import pytest

from tests.fakes import FakeClient
from underwriting.agents.risk import approval_score, risk_scoring_agent
from underwriting.schemas import EnrichmentResult, Fact


def test_score_and_factors_are_kept() -> None:
    enriched = EnrichmentResult(
        applicant_id="APP-1002",
        full_name="Grace Hopper",
        age=52,
        coverage_amount=500000,
        extra_facts=[Fact(fact="prior_claim", source="underwriting.db")],
    )
    fake = FakeClient(json.dumps({
        "risk_score": 0.72,
        "risk_factors": ["prior_claim"],
    }))
    result = risk_scoring_agent(enriched, fake)
    assert result.risk_score == 0.35
    assert result.risk_factors == ["prior_claim"]
    assert result.extra_facts[0].fact == "prior_claim"
    assert fake.calls == 1


def _grace() -> EnrichmentResult:
    return EnrichmentResult(
        applicant_id="APP-1002",
        full_name="Grace Hopper",
        age=52,
        coverage_amount=500000,
        extra_facts=[Fact(fact="prior_claim", source="underwriting.db")],
    )


def test_risk_rejects_a_reply_that_is_not_json() -> None:
    with pytest.raises(ValueError, match="risk output failed validation"):
        risk_scoring_agent(_grace(), FakeClient("not json"))


def test_risk_rejects_a_score_outside_0_to_1() -> None:
    fake = FakeClient(json.dumps({"risk_score": 1.5, "risk_factors": []}))
    with pytest.raises(ValueError, match="risk_score must be from 0 to 1"):
        risk_scoring_agent(_grace(), fake)


def test_coverage_of_200000_adds_015() -> None:
    enriched = EnrichmentResult(
        applicant_id="APP-9001",
        full_name="Katherine Johnson",
        age=30,
        coverage_amount=200000,
        extra_facts=[],
    )
    assert approval_score(enriched) == 0.85


def test_risk_rejects_factors_that_are_not_a_list() -> None:
    fake = FakeClient(json.dumps({
        "risk_score": 0.72,
        "risk_factors": "prior_claim",
    }))
    with pytest.raises(ValueError, match="risk_factors must be a list"):
        risk_scoring_agent(_grace(), fake)
