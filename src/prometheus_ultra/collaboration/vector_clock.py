"""VectorClock — Causal ordering via vector clocks."""
from __future__ import annotations


class VectorClock:
    def __init__(self):
        self._clock: dict[str, int] = {}
        self._node_id = "local"

    def increment(self):
        self._clock[self._node_id] = self._clock.get(self._node_id, 0) + 1

    def merge(self, other: dict[str, int]):
        for k, v in other.items():
            self._clock[k] = max(self._clock.get(k, 0), v)

    def get_clock(self) -> dict[str, int]:
        return dict(self._clock)

    def get_stats(self) -> dict:
        return {"entries": len(self._clock)}
