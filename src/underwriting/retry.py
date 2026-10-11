"""One retry, then stop. A missing answer is not a guessed score."""

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TypeVar

from underwriting.config import BACKOFF_SECONDS, MAX_ATTEMPTS

T = TypeVar("T")


@dataclass
class Attempt:
    attempt: int
    result: object
    error: str | None
    started: datetime
    elapsed_s: float


def call_with_retry(action: Callable[[], T]) -> list[Attempt]:
    rows: list[Attempt] = []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        started = datetime.now(timezone.utc)
        clock = time.perf_counter()
        try:
            result = action()
        except (TimeoutError, ValueError) as exc:
            rows.append(Attempt(
                attempt=attempt,
                result=None,
                error=str(exc),
                started=started,
                elapsed_s=time.perf_counter() - clock,
            ))
            if attempt == MAX_ATTEMPTS:
                return rows
            time.sleep(BACKOFF_SECONDS)
            continue
        rows.append(Attempt(
            attempt=attempt,
            result=result,
            error=None,
            started=started,
            elapsed_s=time.perf_counter() - clock,
        ))
        return rows
    return rows
