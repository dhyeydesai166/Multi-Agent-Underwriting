"""The three live cases. The script imports this list."""

from underwriting.samples import CASES


def test_samples_are_ada_grace_and_alan() -> None:
    assert [(case.applicant_id, case.full_name) for case in CASES] == [
        ("APP-1001", "Ada Lovelace"),
        ("APP-1002", "Grace Hopper"),
        ("APP-1003", "Alan Turing"),
    ]
