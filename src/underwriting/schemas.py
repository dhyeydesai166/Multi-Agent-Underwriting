"""Shapes that cross a trust boundary. The model fills these. Code checks them."""

from typing import Literal

from pydantic import BaseModel, Field


class RawApplication(BaseModel):
    applicant_id: str
    full_name: str
    age: int
    coverage_amount: int


class IntakeResult(BaseModel):
    applicant_id: str
    full_name: str
    age: int
    coverage_amount: int
    missing_fields: list[str]


class Fact(BaseModel):
    fact: str
    source: str


class EnrichmentResult(BaseModel):
    applicant_id: str
    full_name: str
    age: int
    coverage_amount: int
    extra_facts: list[Fact]


class RiskResult(BaseModel):
    applicant_id: str
    risk_score: float = Field(ge=0, le=1)
    risk_factors: list[str]
    extra_facts: list[Fact]


class RecommendationResult(BaseModel):
    applicant_id: str
    decision: Literal["approve", "deny", "refer"]
    reason: str


class LlmResponse(BaseModel):
    text: str
    input_tokens: int
    output_tokens: int
