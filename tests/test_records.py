"""Stored history becomes facts. The model does not write them."""

import sqlite3
from pathlib import Path

from underwriting.records import (
    ensure_database,
    insert_new_applicant,
    lookup_records,
    next_applicant_id,
    save_applicant,
    stored_name,
)


def _names(applicant_id: str) -> list[str]:
    return [fact.fact for fact in lookup_records(applicant_id)]


def test_lab_cases_keep_one_deciding_fact() -> None:
    assert _names("APP-1001") == ["hazardous_occupation"]
    assert _names("APP-1002") == ["prior_claim"]
    assert _names("APP-1003") == ["recent_lapse"]
    assert lookup_records("APP-1002")[0].source == "underwriting.db"


def test_roofer_with_a_claim_has_both_facts() -> None:
    assert _names("APP-1005") == ["prior_claim", "hazardous_occupation"]


def test_claim_and_lapse_both_stay_on_the_message() -> None:
    assert _names("APP-1006") == ["prior_claim", "recent_lapse"]


def test_clean_histories_have_no_facts() -> None:
    assert _names("APP-1004") == []
    assert _names("APP-1007") == []
    assert _names("APP-9999") == []


def test_next_id_follows_the_seed(tmp_path: Path) -> None:
    database = tmp_path / "underwriting.db"
    ensure_database(database)
    assert next_applicant_id(database) == "APP-1008"


def test_a_clean_new_person_has_no_policy(tmp_path: Path) -> None:
    database = tmp_path / "underwriting.db"
    ensure_database(database)
    insert_new_applicant("APP-1008", "dhyey", "teacher", False, False, database)
    insert_new_applicant("APP-1008", "dhyey", "teacher", False, False, database)
    save_applicant("APP-1008", "dhyey", 30, 50000, "approve", 0.95, database)
    save_applicant("APP-1008", "dhyey", 31, 60000, "deny", 0.55, database)
    assert stored_name("APP-1008", database) == "dhyey"
    assert lookup_records("APP-1008", database) == []
    connection = sqlite3.connect(database)
    try:
        people = connection.execute(
            "SELECT COUNT(*) FROM applicants WHERE applicant_id = 'APP-1008'"
        ).fetchone()
        policies = connection.execute(
            "SELECT COUNT(*) FROM policies WHERE applicant_id = 'APP-1008'"
        ).fetchone()
        applications = connection.execute(
            "SELECT decision FROM applications WHERE applicant_id = 'APP-1008'"
        ).fetchall()
    finally:
        connection.close()
    assert people is not None and people[0] == 1
    assert policies is not None and policies[0] == 0
    assert [row[0] for row in applications] == ["approve", "deny"]


def test_a_pilot_with_a_claim_and_a_lapse_stores_both(tmp_path: Path) -> None:
    database = tmp_path / "underwriting.db"
    ensure_database(database)
    insert_new_applicant("APP-1008", "dhyey", "pilot", True, True, database)
    assert lookup_records("APP-1008", database)[0].fact == "prior_claim"
    names = [fact.fact for fact in lookup_records("APP-1008", database)]
    assert names == ["prior_claim", "hazardous_occupation", "recent_lapse"]
    connection = sqlite3.connect(database)
    try:
        statuses = connection.execute(
            "SELECT status FROM policies WHERE applicant_id = 'APP-1008'"
        ).fetchall()
    finally:
        connection.close()
    assert [row[0] for row in statuses] == ["lapsed"]


def test_missing_database_file_returns_nothing(tmp_path: Path) -> None:
    missing = tmp_path / "missing.db"
    assert lookup_records("APP-1001", path=missing) == []
    assert not missing.exists()
