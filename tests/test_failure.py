"""A risk-scoring timeout retries once, then refers. The process does not crash."""

import subprocess
import sys

from underwriting.llm import FailureDemoClient
from underwriting.pipeline import run_case
from underwriting.schemas import RawApplication


def _raw() -> RawApplication:
    return RawApplication(
        applicant_id="APP-TIMEOUT",
        full_name="Timeout Case",
        age=40,
        coverage_amount=10000,
    )


def test_risk_timeout_retries_then_refers() -> None:
    result = run_case(_raw(), FailureDemoClient())
    risk_rows = [
        step for step in result.traces if step.agent == "risk_scoring_agent"
    ]
    assert [step.attempt for step in risk_rows] == [1, 2]
    assert risk_rows[0].error is not None
    assert risk_rows[1].error is not None
    assert result.decision == "refer"
    assert result.reason == "risk_scoring_agent did not respond after retry"
    assert all(step.agent != "recommendation_agent" for step in result.traces)
    assert result.queue_depths["risk_assessed"] == 0


def test_failure_script_exits_zero() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/run_failure_case.py"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "decision=refer" in completed.stdout
