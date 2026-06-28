"""SpeculativeFork — Fork management with divergence tracking."""
from __future__ import annotations
import time


class SpeculativeFork:
    def __init__(self):
        self._forks: list[dict] = []
        self._merges: list[dict] = []

    def fork(self, context: str = "", fitness: float = 0.5) -> dict:
        fork = {"id": len(self._forks), "context": context, "parent_fitness": fitness,
                "created_at": time.time(), "status": "active", "mutations": 0}
        self._forks.append(fork)
        return fork

    def merge(self, source_id: int, target_id: int, strategy: str = "best_fitness") -> dict:
        if source_id >= len(self._forks) or target_id >= len(self._forks):
            return {"merged": False}
        source, target = self._forks[source_id], self._forks[target_id]
        winner = source if source.get("parent_fitness", 0) > target.get("parent_fitness", 0) else target
        source["status"] = "merged"
        result = {"merged": True, "winner": winner["id"], "strategy": strategy}
        self._merges.append(result)
        return result

    def get_stats(self) -> dict:
        return {"forks": len(self._forks), "merges": len(self._merges)}
