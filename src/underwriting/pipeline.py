"""Hand each finished message to the next queue. No shared case file."""

from datetime import datetime
from typing import Any, Callable

from pydantic import BaseModel

from underwriting.agents.enrichment import enrichment_agent
from underwriting.agents.intake import intake_agent
from underwriting.agents.recommendation import recommendation_agent
from underwriting.agents.risk import risk_scoring_agent
from underwriting.llm import LlmClient
from underwriting.queues import MessageQueue
from underwriting.retry import call_with_retry
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
        agent_name: str = "",
    ) -> Any:
        response = self.inner.complete(
            system=system,
            user=user,
            applicant_id=applicant_id,
            agent_name=agent_name,
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
    attempt: int,
    error: str | None,
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
        attempt=attempt,
        error=error,
        queue_depth=queue_depth,
    )


def _depths(
    received: MessageQueue,
    enriched_q: MessageQueue,
    assessed: MessageQueue,
) -> dict[str, int]:
    return {
        received.name: received.depth(),
        enriched_q.name: enriched_q.depth(),
        assessed.name: assessed.depth(),
    }


def _run_step(
    usage: _Usage,
    traces: list[TraceStep],
    step: str,
    agent: str,
    source: str,
    received: dict[str, Any],
    action: Callable[[], Any],
    queue_depth: int,
) -> Any:
    before_in = usage.input_tokens
    before_out = usage.output_tokens
    rows = call_with_retry(action)
    result = None
    for row in rows:
        produced = {}
        if row.result is not None and hasattr(row.result, "model_dump"):
            produced = row.result.model_dump()
            result = row.result
        traces.append(_record(
            step,
            agent,
            source,
            received,
            produced,
            row.started,
            row.elapsed_s,
            usage.input_tokens - before_in,
            usage.output_tokens - before_out,
            queue_depth,
            row.attempt,
            row.error,
        ))
        before_in = usage.input_tokens
        before_out = usage.output_tokens
    if rows[-1].error is not None:
        return None
    return result


def run_case(raw: RawApplication, llm: LlmClient) -> CaseResult:
    usage = _Usage(llm)
    received_q = MessageQueue("application_received")
    enriched_q = MessageQueue("enrichment_complete")
    assessed = MessageQueue("risk_assessed")
    traces: list[TraceStep] = []

    intake = _run_step(
        usage,
        traces,
        "intake",
        "intake_agent",
        "user",
        raw.model_dump(),
        lambda: intake_agent(raw, usage),
        0,
    )
    if intake is None:
        return _refer(raw, traces, received_q, enriched_q, assessed, "intake_agent")
    received_q.put(intake.model_dump())
    traces[-1].queue_depth = received_q.depth()

    intake_message = IntakeResult.model_validate(received_q.get())
    enriched = _run_step(
        usage,
        traces,
        "enrichment",
        "enrichment_agent",
        "application_received",
        intake_message.model_dump(),
        lambda: enrichment_agent(intake_message, usage),
        0,
    )
    if enriched is None:
        return _refer(
            raw, traces, received_q, enriched_q, assessed, "enrichment_agent"
        )
    enriched_q.put(enriched.model_dump())
    traces[-1].queue_depth = enriched_q.depth()

    enrichment_message = EnrichmentResult.model_validate(enriched_q.get())
    scored = _run_step(
        usage,
        traces,
        "risk_assessment",
        "risk_scoring_agent",
        "enrichment_complete",
        enrichment_message.model_dump(),
        lambda: risk_scoring_agent(enrichment_message, usage),
        0,
    )
    if scored is None:
        return _refer(
            raw, traces, received_q, enriched_q, assessed, "risk_scoring_agent"
        )
    assessed.put(scored.model_dump())
    traces[-1].queue_depth = assessed.depth()

    risk_message = RiskResult.model_validate(assessed.get())
    recommendation = _run_step(
        usage,
        traces,
        "recommendation",
        "recommendation_agent",
        "risk_assessed",
        risk_message.model_dump(),
        lambda: recommendation_agent(risk_message, usage),
        assessed.depth(),
    )
    if recommendation is None:
        return _refer(
            raw, traces, received_q, enriched_q, assessed, "recommendation_agent"
        )
    return CaseResult(
        applicant_id=raw.applicant_id,
        decision=recommendation.decision,
        reason=recommendation.reason,
        traces=traces,
        queue_depths=_depths(received_q, enriched_q, assessed),
    )


def _refer(
    raw: RawApplication,
    traces: list[TraceStep],
    received_q: MessageQueue,
    enriched_q: MessageQueue,
    assessed: MessageQueue,
    agent: str,
) -> CaseResult:
    return CaseResult(
        applicant_id=raw.applicant_id,
        decision="refer",
        reason=f"{agent} did not respond after retry",
        traces=traces,
        queue_depths=_depths(received_q, enriched_q, assessed),
    )
