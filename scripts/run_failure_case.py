"""Show a risk-scoring timeout: retry once, then refer. Exit 0."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from underwriting.llm import FailureDemoClient  # noqa: E402
from underwriting.pipeline import run_case  # noqa: E402
from underwriting.schemas import RawApplication  # noqa: E402


def main() -> None:
    raw = RawApplication(
        applicant_id="APP-TIMEOUT",
        full_name="Timeout Case",
        age=40,
        coverage_amount=10000,
    )
    result = run_case(raw, FailureDemoClient())
    print(json.dumps([step.model_dump() for step in result.traces], indent=2))
    print(f"decision={result.decision}")
    print(f"reason={result.reason}")


if __name__ == "__main__":
    main()
