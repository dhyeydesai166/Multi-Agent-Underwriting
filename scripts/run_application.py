"""Ask for one application and run it through the local model."""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from underwriting.form import read_application  # noqa: E402
from underwriting.llm import OllamaClient  # noqa: E402
from underwriting.pipeline import run_case  # noqa: E402
from underwriting.records import insert_new_applicant, save_applicant  # noqa: E402


def main() -> None:
    entered = read_application(input)
    raw = entered.raw
    if entered.new_person and entered.occupation is not None:
        insert_new_applicant(
            raw.applicant_id,
            raw.full_name,
            entered.occupation,
            entered.prior_claim,
            entered.recent_lapse,
        )
    base_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    result = run_case(raw, OllamaClient(base_url=base_url))
    score = None
    for step in result.traces:
        if step.step == "risk_assessment" and "risk_score" in step.output:
            score = float(step.output["risk_score"])
    save_applicant(
        raw.applicant_id,
        raw.full_name,
        raw.age,
        raw.coverage_amount,
        result.decision,
        score,
    )
    print(json.dumps(
        [step.model_dump() for step in result.traces],
        indent=2,
    ))
    duration = sum(step.duration_ms for step in result.traces)
    tokens = sum(step.tokens_used for step in result.traces)
    cost = sum(step.cost_usd for step in result.traces)
    print(f"decision={result.decision}")
    print(f"reason={result.reason}")
    print(f"total_duration_ms={duration}")
    print(f"total_tokens={tokens}")
    print(f"cost_usd={cost:.2f}")


if __name__ == "__main__":
    main()
