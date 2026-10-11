"""The form re-asks a bad field. It does not call the model."""

from pathlib import Path

from underwriting.form import read_application
from underwriting.records import ensure_database


def _answers(*values: str):
    pending = list(values)

    def ask(prompt: str) -> str:
        assert prompt
        return pending.pop(0)

    return ask, pending


def test_a_complete_form_is_accepted() -> None:
    ask, pending = _answers("APP-1007", "Mary Jackson", "23", "30000")
    notes: list[str] = []
    result = read_application(ask, notes.append)
    assert result.new_person is False
    assert result.raw.applicant_id == "APP-1007"
    assert result.raw.full_name == "Mary Jackson"
    assert result.raw.age == 23
    assert result.raw.coverage_amount == 30000
    assert notes == []
    assert pending == []


def test_a_blank_name_is_asked_again() -> None:
    ask, _pending = _answers("APP-1004", "   ", "Katherine Johnson", "40", "100000")
    notes: list[str] = []
    result = read_application(ask, notes.append)
    assert result.raw.full_name == "Katherine Johnson"
    assert notes == ["applicant_id and full_name are required"]


def test_a_different_name_is_asked_again() -> None:
    ask, _pending = _answers(
        "APP-1007",
        "dhyey",
        "mary jackson",
        "23",
        "30000",
    )
    notes: list[str] = []
    result = read_application(ask, notes.append)
    assert result.raw.full_name == "mary jackson"
    assert notes == ["full_name does not match this applicant id"]


def test_an_unknown_id_is_replaced(tmp_path: Path) -> None:
    database = tmp_path / "underwriting.db"
    ensure_database(database)
    ask, _pending = _answers(
        "APP-9999", "dhyey", "teacher", "no", "no", "30", "50000"
    )
    notes: list[str] = []
    result = read_application(ask, notes.append, path=database)
    assert result.raw.applicant_id == "APP-1008"
    assert result.raw.full_name == "dhyey"
    assert result.new_person is True
    assert result.occupation == "teacher"
    assert result.prior_claim is False
    assert result.recent_lapse is False
    assert notes == [
        "applicant id is not on file",
        "Your applicant id is APP-1008",
    ]


def test_a_bad_age_and_amount_are_asked_again() -> None:
    ask, _pending = _answers(
        "APP-1007",
        "Mary Jackson",
        "abc",
        "17",
        "23",
        "0",
        "30000",
    )
    notes: list[str] = []
    result = read_application(ask, notes.append)
    assert result.raw.age == 23
    assert result.raw.coverage_amount == 30000
    assert notes == [
        "age must be from 18 to 120",
        "age must be from 18 to 120",
        "coverage_amount must be greater than 0",
    ]


def test_a_new_person_is_asked_for_history(tmp_path: Path) -> None:
    database = tmp_path / "underwriting.db"
    ensure_database(database)
    ask, pending = _answers(
        "",
        "dhyey",
        "   ",
        "unknown",
        "pilot",
        "maybe",
        "yes",
        "later",
        "yes",
        "30",
        "50000",
    )
    notes: list[str] = []
    result = read_application(ask, notes.append, path=database)
    assert result.raw.applicant_id == "APP-1008"
    assert result.occupation == "pilot"
    assert result.prior_claim is True
    assert result.recent_lapse is True
    assert pending == []
    assert notes == [
        "Your applicant id is APP-1008",
        "occupation is required",
        "occupation is required",
        "answer yes or no",
        "answer yes or no",
    ]
