"""Lookup of extra facts. The model does not invent these."""

import sqlite3
from datetime import datetime
from pathlib import Path

from underwriting.schemas import Fact

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "underwriting.db"
SCHEMA_PATH = DATA_DIR / "schema.sql"
SEED_PATH = DATA_DIR / "seed.sql"
SOURCE = "underwriting.db"
HAZARDOUS = {"pilot", "logger", "roofer", "commercial fisher"}


def ensure_database(path: Path = DB_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        count = connection.execute("SELECT COUNT(*) FROM applicants").fetchone()
        if count is not None and count[0] == 0:
            connection.executescript(SEED_PATH.read_text(encoding="utf-8"))
        connection.commit()
    finally:
        connection.close()


def _open(path: Path) -> sqlite3.Connection | None:
    if path == DB_PATH or path.is_file():
        ensure_database(path)
    if not path.is_file():
        return None
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def stored_name(applicant_id: str, path: Path = DB_PATH) -> str | None:
    connection = _open(path)
    if connection is None:
        return None
    try:
        person = connection.execute(
            "SELECT full_name FROM applicants WHERE applicant_id = ?",
            (applicant_id,),
        ).fetchone()
    finally:
        connection.close()
    if person is None:
        return None
    return str(person["full_name"])


def next_applicant_id(path: Path = DB_PATH) -> str:
    connection = _open(path)
    if connection is None:
        return "APP-1001"
    try:
        rows = connection.execute("SELECT applicant_id FROM applicants").fetchall()
    finally:
        connection.close()
    highest = 1000
    for row in rows:
        text = str(row["applicant_id"])
        if text.startswith("APP-") and text[4:].isdigit():
            highest = max(highest, int(text[4:]))
    return f"APP-{highest + 1}"


def insert_new_applicant(
    applicant_id: str,
    full_name: str,
    occupation: str,
    prior_claim: bool,
    recent_lapse: bool,
    path: Path = DB_PATH,
) -> None:
    connection = _open(path)
    if connection is None:
        return
    year = datetime.now().year
    try:
        existing = connection.execute(
            "SELECT 1 FROM applicants WHERE applicant_id = ?",
            (applicant_id,),
        ).fetchone()
        if existing is not None:
            return
        connection.execute(
            """
            INSERT INTO applicants (applicant_id, full_name, occupation)
            VALUES (?, ?, ?)
            """,
            (applicant_id, full_name, occupation),
        )
        if prior_claim:
            connection.execute(
                """
                INSERT INTO claims (applicant_id, year, amount_usd)
                VALUES (?, ?, ?)
                """,
                (applicant_id, year, 0),
            )
        if recent_lapse:
            connection.execute(
                """
                INSERT INTO policies (applicant_id, status, year)
                VALUES (?, 'lapsed', ?)
                """,
                (applicant_id, year),
            )
        connection.commit()
    finally:
        connection.close()


def save_applicant(
    applicant_id: str,
    full_name: str,
    age: int,
    coverage_amount: int,
    decision: str,
    risk_score: float | None = None,
    path: Path = DB_PATH,
) -> None:
    connection = _open(path)
    if connection is None:
        return
    year = datetime.now().year
    try:
        existing = connection.execute(
            "SELECT 1 FROM applicants WHERE applicant_id = ?",
            (applicant_id,),
        ).fetchone()
        if existing is None:
            return
        connection.execute(
            """
            INSERT INTO applications (
                applicant_id, age, coverage_amount, risk_score, decision, year
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (applicant_id, age, coverage_amount, risk_score, decision, year),
        )
        connection.commit()
    finally:
        connection.close()


def lookup_records(
    applicant_id: str,
    path: Path = DB_PATH,
) -> list[Fact]:
    connection = _open(path)
    if connection is None:
        return []
    try:
        person = connection.execute(
            "SELECT occupation FROM applicants WHERE applicant_id = ?",
            (applicant_id,),
        ).fetchone()
        if person is None:
            return []
        claim = connection.execute(
            "SELECT 1 FROM claims WHERE applicant_id = ? LIMIT 1",
            (applicant_id,),
        ).fetchone()
        lapsed = connection.execute(
            """
            SELECT 1 FROM policies
            WHERE applicant_id = ? AND status = 'lapsed'
            LIMIT 1
            """,
            (applicant_id,),
        ).fetchone()
    finally:
        connection.close()
    occupation = str(person["occupation"]).strip().lower()
    facts: list[Fact] = []
    if claim is not None:
        facts.append(Fact(fact="prior_claim", source=SOURCE))
    if occupation in HAZARDOUS:
        facts.append(Fact(fact="hazardous_occupation", source=SOURCE))
    if lapsed is not None:
        facts.append(Fact(fact="recent_lapse", source=SOURCE))
    return facts
