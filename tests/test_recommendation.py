"""Recommendation, alone. Code replaces the model's decision word."""

import json

import pytest

from tests.fakes import FakeClient
from underwriting.agents.recommendation import PROMPT, recommendation_agent
from underwriting.schemas import Fact, RiskResult


def _risk(score: float, facts: list[Fact]) -> RiskResult:
    return RiskResult(
        applicant_id="APP-1001",
        risk_score=score,
        risk_factors=[],
        extra_facts=facts,
    )


def _fake(decision: str) -> FakeClient:
    return FakeClient(json.dumps({
        "decision": decision,
        "reason": "Reviewed the score and the records.",
    }))


def test_high_score_without_claim_is_approve() -> None:
    result = recommendation_agent(_risk(0.82, []), _fake("deny"))
    assert result.decision == "approve"


def test_low_score_without_claim_is_deny() -> None:
    result = recommendation_agent(_risk(0.40, []), _fake("approve"))
    assert result.decision == "deny"


def test_prior_claim_is_refer_even_with_high_score() -> None:
    facts = [Fact(fact="prior_claim", source="underwriting.db")]
    result = recommendation_agent(_risk(0.90, facts), _fake("approve"))
    assert result.decision == "refer"


def test_hazardous_occupation_is_refer_even_with_high_score() -> None:
    facts = [Fact(fact="hazardous_occupation", source="underwriting.db")]
    result = recommendation_agent(_risk(0.90, facts), _fake("approve"))
    assert result.decision == "refer"


def test_recent_lapse_is_deny_even_with_high_score() -> None:
    facts = [Fact(fact="recent_lapse", source="underwriting.db")]
    result = recommendation_agent(_risk(0.90, facts), _fake("approve"))
    assert result.decision == "deny"


def test_score_at_cutoff_is_approve() -> None:
    result = recommendation_agent(_risk(0.7, []), _fake("deny"))
    assert result.decision == "approve"


def test_recommendation_rejects_a_reply_that_is_not_json() -> None:
    with pytest.raises(ValueError, match="output failed validation"):
        recommendation_agent(_risk(0.82, []), FakeClient("not json"))


def test_recommendation_rejects_a_missing_reason() -> None:
    fake = FakeClient(json.dumps({"decision": "approve"}))
    with pytest.raises(ValueError, match="output failed validation"):
        recommendation_agent(_risk(0.82, []), fake)


def test_the_prompt_says_a_higher_score_is_safer() -> None:
    assert "A higher `risk_score` is safer." in PROMPT


def test_recommendation_rejects_a_blank_reason() -> None:
    fake = FakeClient(json.dumps({"decision": "approve", "reason": "   "}))
    with pytest.raises(ValueError, match="reason is required"):
        recommendation_agent(_risk(0.82, []), fake)
