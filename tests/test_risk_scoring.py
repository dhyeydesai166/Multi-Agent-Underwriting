"""Risk scoring, alone. The score stays on the enriched case."""

import json

from tests.fakes import FakeClient
from underwriting.agents.risk import risk_scoring_agent
from underwriting.schemas import EnrichmentResult, Fact


def test_score_and_factors_are_kept() -> None:
    enriched = EnrichmentResult(
        applicant_id="APP-1002",
        full_name="Grace Hopper",
        age=52,
        coverage_amount=500000,
        extra_facts=[Fact(fact="prior_claim", source="applicant_records.json")],
    )
    fake = FakeClient(json.dumps({
        "risk_score": 0.72,
        "risk_factors": ["prior_claim"],
    }))
    result = risk_scoring_agent(enriched, fake)
    assert result.risk_score == 0.72
    assert result.risk_factors == ["prior_claim"]
    assert result.extra_facts[0].fact == "prior_claim"
    assert fake.calls == 1
