"""Three mock applications. They differ by age, amount, and records."""

from underwriting.schemas import RawApplication

CASES = [
    RawApplication(
        applicant_id="APP-1001",
        full_name="Ada Lovelace",
        age=35,
        coverage_amount=25000,
    ),
    RawApplication(
        applicant_id="APP-1002",
        full_name="Grace Hopper",
        age=52,
        coverage_amount=500000,
    ),
    RawApplication(
        applicant_id="APP-1003",
        full_name="Alan Turing",
        age=19,
        coverage_amount=400000,
    ),
]
