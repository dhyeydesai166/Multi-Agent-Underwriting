"""One row per agent visit. This is the record of a case."""

from typing import Any

from pydantic import BaseModel

from underwriting.config import INPUT_USD_PER_MILLION, OUTPUT_USD_PER_MILLION


class TraceStep(BaseModel):
    step: str
    agent: str
    input_source: str
    input: dict[str, Any]
    output: dict[str, Any]
    timestamp: str
    duration_ms: int
    input_tokens: int
    output_tokens: int
    tokens_used: int
    cost_usd: float
    attempt: int
    error: str | None
    queue_depth: int


def step_cost(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens * INPUT_USD_PER_MILLION
        + output_tokens * OUTPUT_USD_PER_MILLION
    ) / 1_000_000
