"""Intake, alone. A bad form never reaches the model."""

import json

import pytest

from tests.fakes import FakeClient
from underwriting.agents.intake import intake_agent
from underwriting.schemas import RawApplication


def _form(**overrides: object) -> RawApplication:
    data: dict[str, object] = {
        "applicant_id": "APP-1001",
        "full_name": "Ada Lovelace",
        "age": 35,
        "coverage_amount": 25000,
    }
    data.update(overrides)
    return RawApplication.model_validate(data)


def _good_response() -> str:
    return json.dumps({
        "applicant_id": "APP-1001",
        "full_name": "Ada Lovelace",
        "age": 35,
        "coverage_amount": 25000,
        "missing_fields": [],
    })


def test_intake_keeps_known_fields() -> None:
    fake = FakeClient(_good_response())
    result = intake_agent(_form(), fake)
    assert result.applicant_id == "APP-1001"
    assert result.full_name == "Ada Lovelace"
    assert result.age == 35
    assert result.coverage_amount == 25000
    assert isinstance(result.missing_fields, list)
    assert fake.calls == 1


@pytest.mark.parametrize(
    "overrides",
    [
        {"full_name": ""},
        {"full_name": "   "},
        {"applicant_id": ""},
        {"age": 17},
        {"age": 121},
        {"coverage_amount": 0},
    ],
)
def test_intake_rejects_before_model(overrides: dict[str, object]) -> None:
    fake = FakeClient("{}")
    with pytest.raises(ValueError):
        intake_agent(_form(**overrides), fake)
    assert fake.calls == 0


def test_intake_rejects_a_reply_that_is_not_json() -> None:
    fake = FakeClient("not json")
    with pytest.raises(ValueError, match="intake output failed validation"):
        intake_agent(_form(), fake)
    assert fake.calls == 1
