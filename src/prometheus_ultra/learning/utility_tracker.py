"""UtilityTracker — node utility tracking over time."""
from __future__ import annotations


class UtilityTracker:
    def __init__(self):
        self._tracked: dict[str, list[float]] = {}

    def register(self, node_id: str, utility: float = 0.5):
        if node_id not in self._tracked:
            self._tracked[node_id] = []
        self._tracked[node_id].append(utility)

    def get_average(self, node_id: str) -> float:
        vals = self._tracked.get(node_id, [])
        return sum(vals) / len(vals) if vals else 0.0

    def get_stats(self) -> dict:
        return {"tracked_nodes": len(self._tracked)}
