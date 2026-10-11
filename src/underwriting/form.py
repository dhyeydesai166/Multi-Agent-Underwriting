"""Ask for one application. A bad field is asked again before any model call."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from underwriting.records import DB_PATH, next_applicant_id, stored_name
from underwriting.schemas import RawApplication

Ask = Callable[[str], str]
Report = Callable[[str], None]


@dataclass
class ApplicationEntry:
    raw: RawApplication
    new_person: bool
    occupation: str | None = None
    prior_claim: bool = False
    recent_lapse: bool = False


def _text(
    ask: Ask,
    report: Report,
    prompt: str,
    error: str,
) -> str:
    while True:
        value = ask(prompt).strip()
        if value:
            return value
        report(error)


def _number(
    ask: Ask,
    report: Report,
    prompt: str,
    error: str,
    allowed: Callable[[int], bool],
) -> int:
    while True:
        raw = ask(prompt).strip()
        try:
            number = int(raw)
        except ValueError:
            report(error)
            continue
        if allowed(number):
            return number
        report(error)


def _occupation(ask: Ask, report: Report) -> str:
    while True:
        value = ask("Occupation: ").strip()
        if value and value.casefold() != "unknown":
            return value
        report("occupation is required")


def _yes_no(ask: Ask, report: Report, prompt: str) -> bool:
    while True:
        value = ask(prompt).strip().casefold()
        if value == "yes":
            return True
        if value == "no":
            return False
        report("answer yes or no")


def _matches(typed: str, stored: str) -> bool:
    return typed.casefold() == stored.strip().casefold()


def _name_for(
    ask: Ask,
    report: Report,
    applicant_id: str,
    path: Path,
) -> str:
    while True:
        full_name = _text(
            ask,
            report,
            "Full name: ",
            "applicant_id and full_name are required",
        )
        known = stored_name(applicant_id, path)
        if known is None or _matches(full_name, known):
            return full_name
        report("full_name does not match this applicant id")


def read_application(
    ask: Ask,
    report: Report = print,
    path: Path = DB_PATH,
) -> ApplicationEntry:
    typed = ask("Applicant id: ").strip()
    known = stored_name(typed, path) if typed else None
    occupation = None
    prior_claim = False
    recent_lapse = False
    if known is None:
        if typed:
            report("applicant id is not on file")
        applicant_id = next_applicant_id(path)
        report(f"Your applicant id is {applicant_id}")
        full_name = _text(
            ask,
            report,
            "Full name: ",
            "applicant_id and full_name are required",
        )
        occupation = _occupation(ask, report)
        prior_claim = _yes_no(ask, report, "Prior claim (yes or no): ")
        recent_lapse = _yes_no(
            ask, report, "Previous policy lapsed (yes or no): "
        )
        new_person = True
    else:
        applicant_id = typed
        full_name = _name_for(ask, report, applicant_id, path)
        new_person = False
    age = _number(
        ask,
        report,
        "Age: ",
        "age must be from 18 to 120",
        lambda number: 18 <= number <= 120,
    )
    coverage_amount = _number(
        ask,
        report,
        "Coverage amount: ",
        "coverage_amount must be greater than 0",
        lambda number: number > 0,
    )
    return ApplicationEntry(
        raw=RawApplication(
            applicant_id=applicant_id,
            full_name=full_name,
            age=age,
            coverage_amount=coverage_amount,
        ),
        new_person=new_person,
        occupation=occupation,
        prior_claim=prior_claim,
        recent_lapse=recent_lapse,
    )
