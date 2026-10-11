"""Run three mock applications through the local model and print traces."""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from underwriting.llm import OllamaClient  # noqa: E402
from underwriting.pipeline import run_case  # noqa: E402
from underwriting.samples import CASES  # noqa: E402


def main() -> None:
    base_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    client = OllamaClient(base_url=base_url)
    for raw in CASES:
        print(f"=== {raw.applicant_id} ===", flush=True)
        result = run_case(raw, client)
        print(json.dumps(
            [step.model_dump() for step in result.traces],
            indent=2,
        ))
        duration = sum(step.duration_ms for step in result.traces)
        tokens = sum(step.tokens_used for step in result.traces)
        cost = sum(step.cost_usd for step in result.traces)
        print(f"decision={result.decision}")
        print(f"total_duration_ms={duration}")
        print(f"total_tokens={tokens}")
        print(f"cost_usd={cost:.2f}")
        print(flush=True)


if __name__ == "__main__":
    main()
