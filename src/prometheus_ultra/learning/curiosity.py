"""CuriosityQueue — priority queue for curious questions."""
from __future__ import annotations
import heapq


class CuriosityQueue:
    def __init__(self):
        self._queue: list[tuple[int, str]] = []
        self._seen: set[str] = set()

    def add(self, question: str, priority: int = 5):
        if question not in self._seen:
            heapq.heappush(self._queue, (priority, question))
            self._seen.add(question)

    def pop(self) -> str | None:
        if self._queue:
            _, q = heapq.heappop(self._queue)
            return q
        return None

    def get_stats(self) -> dict:
        return {"pending": len(self._queue), "total_seen": len(self._seen)}
