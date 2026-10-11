"""Enrichment, alone. Invented facts are dropped."""

import json

import pytest

from tests.fakes import FakeClient
from underwriting.agents.enrichment import enrichment_agent
from underwriting.schemas import IntakeResult


def _intake(applicant_id: str) -> IntakeResult:
    return IntakeResult(
        applicant_id=applicant_id,
        full_name="Grace Hopper",
        age=52,
        coverage_amount=500000,
        missing_fields=[],
    )


def test_drops_invented_fact() -> None:
    fake = FakeClient(json.dumps({
        "extra_facts": [
            {"fact": "prior_claim", "source": "applicant_records.json"},
            {"fact": "bankruptcy", "source": "model"},
        ],
    }))
    result = enrichment_agent(_intake("APP-1002"), fake)
    assert result.applicant_id == "APP-1002"
    assert len(result.extra_facts) == 1
    assert result.extra_facts[0].fact == "prior_claim"
    assert result.extra_facts[0].source == "applicant_records.json"


def test_hazardous_occupation_comes_from_the_file() -> None:
    fake = FakeClient(json.dumps({
        "extra_facts": [
            {"fact": "hazardous_occupation", "source": "applicant_records.json"},
            {"fact": "bankruptcy", "source": "model"},
        ],
    }))
    result = enrichment_agent(_intake("APP-1001"), fake)
    assert len(result.extra_facts) == 1
    assert result.extra_facts[0].fact == "hazardous_occupation"
    assert result.extra_facts[0].source == "applicant_records.json"


def test_recent_lapse_comes_from_the_file() -> None:
    fake = FakeClient(json.dumps({
        "extra_facts": [
            {"fact": "recent_lapse", "source": "applicant_records.json"},
            {"fact": "bankruptcy", "source": "model"},
        ],
    }))
    result = enrichment_agent(_intake("APP-1003"), fake)
    assert len(result.extra_facts) == 1
    assert result.extra_facts[0].fact == "recent_lapse"
    assert result.extra_facts[0].source == "applicant_records.json"


def test_enrichment_rejects_a_reply_that_is_not_json() -> None:
    fake = FakeClient("not json")
    with pytest.raises(ValueError, match="enrichment output failed validation"):
        enrichment_agent(_intake("APP-1002"), fake)
    assert fake.calls == 1


def test_unknown_id_has_no_facts() -> None:
    fake = FakeClient(json.dumps({
        "extra_facts": [{"fact": "bankruptcy", "source": "model"}],
    }))
    result = enrichment_agent(_intake("APP-9999"), fake)
    assert result.extra_facts == []
