"""Lookup of extra facts. The model does not invent these."""

import json
from pathlib import Path

from underwriting.schemas import Fact

RECORDS_PATH = Path(__file__).resolve().parents[2] / "data" / "applicant_records.json"
SOURCE = "applicant_records.json"


def lookup_records(
    applicant_id: str,
    path: Path = RECORDS_PATH,
) -> list[Fact]:
    if not path.is_file():
        return []
    rows = json.loads(path.read_text(encoding="utf-8")).get(applicant_id, [])
    return [Fact(fact=row["fact"], source=SOURCE) for row in rows]
