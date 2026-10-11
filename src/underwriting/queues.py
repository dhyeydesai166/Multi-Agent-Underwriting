"""In-memory queues. A step starts only after it pulls a finished message."""

from collections import deque
from typing import Any

from underwriting.config import QUEUE_DEPTH_WARNING


class MessageQueue:
    def __init__(self, name: str) -> None:
        self.name = name
        self._items: deque[dict[str, Any]] = deque()

    def put(self, message: dict[str, Any]) -> str | None:
        self._items.append(message)
        if self.depth() > QUEUE_DEPTH_WARNING:
            return f"{self.name} depth is {self.depth()}"
        return None

    def get(self) -> dict[str, Any]:
        return self._items.popleft()

    def depth(self) -> int:
        return len(self._items)
