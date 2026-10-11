"""Hand each finished message to the next queue. No shared case file."""

import time
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from underwriting.agents.enrichment import enrichment_agent
from underwriting.agents.intake import intake_agent
from underwriting.agents.recommendation import recommendation_agent
from underwriting.agents.risk import risk_scoring_agent
from underwriting.llm import LlmClient
from underwriting.queues import MessageQueue
from underwriting.schemas import (
    EnrichmentResult,
    IntakeResult,
    RawApplication,
    RiskResult,
)
from underwriting.tracing import TraceStep, step_cost


class CaseResult(BaseModel):
    applicant_id: str
    decision: str
    reason: str
    traces: list[TraceStep]
    queue_depths: dict[str, int]


class _Usage:
    def __init__(self, inner: LlmClient) -> None:
        self.inner = inner
        self.input_tokens = 0
        self.output_tokens = 0

    def complete(
        self,
        *,
        system: str,
        user: str,
        applicant_id: str,
    ) -> Any:
        response = self.inner.complete(
            system=system,
            user=user,
            applicant_id=applicant_id,
        )
        self.input_tokens += response.input_tokens
        self.output_tokens += response.output_tokens
        return response


def _record(
    step: str,
    agent: str,
    source: str,
    received: dict[str, Any],
    produced: dict[str, Any],
    started: datetime,
    elapsed_s: float,
    input_tokens: int,
    output_tokens: int,
    queue_depth: int,
) -> TraceStep:
    return TraceStep(
        step=step,
        agent=agent,
        input_source=source,
        input=received,
        output=produced,
        timestamp=started.isoformat().replace("+00:00", "Z"),
        duration_ms=int(elapsed_s * 1000),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        tokens_used=input_tokens + output_tokens,
        cost_usd=step_cost(input_tokens, output_tokens),
        attempt=1,
        error=None,
        queue_depth=queue_depth,
    )


def run_case(raw: RawApplication, llm: LlmClient) -> CaseResult:
    usage = _Usage(llm)
    received = MessageQueue("application_received")
    enriched_q = MessageQueue("enrichment_complete")
    assessed = MessageQueue("risk_assessed")
    traces: list[TraceStep] = []

    before_in, before_out = usage.input_tokens, usage.output_tokens
    started = datetime.now(timezone.utc)
    clock = time.perf_counter()
    intake = intake_agent(raw, usage)
    received.put(intake.model_dump())
    traces.append(_record(
        "intake",
        "intake_agent",
        "user",
        raw.model_dump(),
        intake.model_dump(),
        started,
        time.perf_counter() - clock,
        usage.input_tokens - before_in,
        usage.output_tokens - before_out,
        received.depth(),
    ))

    intake_message = IntakeResult.model_validate(received.get())
    before_in, before_out = usage.input_tokens, usage.output_tokens
    started = datetime.now(timezone.utc)
    clock = time.perf_counter()
    enriched = enrichment_agent(intake_message, usage)
    enriched_q.put(enriched.model_dump())
    traces.append(_record(
        "enrichment",
        "enrichment_agent",
        "application_received",
        intake_message.model_dump(),
        enriched.model_dump(),
        started,
        time.perf_counter() - clock,
        usage.input_tokens - before_in,
        usage.output_tokens - before_out,
        enriched_q.depth(),
    ))

    enrichment_message = EnrichmentResult.model_validate(enriched_q.get())
    before_in, before_out = usage.input_tokens, usage.output_tokens
    started = datetime.now(timezone.utc)
    clock = time.perf_counter()
    scored = risk_scoring_agent(enrichment_message, usage)
    assessed.put(scored.model_dump())
    traces.append(_record(
        "risk_assessment",
        "risk_scoring_agent",
        "enrichment_complete",
        enrichment_message.model_dump(),
        scored.model_dump(),
        started,
        time.perf_counter() - clock,
        usage.input_tokens - before_in,
        usage.output_tokens - before_out,
        assessed.depth(),
    ))

    risk_message = RiskResult.model_validate(assessed.get())
    before_in, before_out = usage.input_tokens, usage.output_tokens
    started = datetime.now(timezone.utc)
    clock = time.perf_counter()
    recommendation = recommendation_agent(risk_message, usage)
    traces.append(_record(
        "recommendation",
        "recommendation_agent",
        "risk_assessed",
        risk_message.model_dump(),
        recommendation.model_dump(),
        started,
        time.perf_counter() - clock,
        usage.input_tokens - before_in,
        usage.output_tokens - before_out,
        assessed.depth(),
    ))

    return CaseResult(
        applicant_id=raw.applicant_id,
        decision=recommendation.decision,
        reason=recommendation.reason,
        traces=traces,
        queue_depths={
            received.name: received.depth(),
            enriched_q.name: enriched_q.depth(),
            assessed.name: assessed.depth(),
        },
    )
