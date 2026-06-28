"""SpeculativeEvolution — Speculative branch-and-bound evolution."""
from __future__ import annotations
import random
import time


class SpeculativeEvolution:
    """Speculative evolution with fork/rollback.

    Usage:
        se = SpeculativeEvolution(max_forks=10)
        fork = se.fork("context", fitness=0.5)
        result = se.evaluate_and_select()
    """

    def __init__(self, max_forks: int = 10):
        self._max_forks = max_forks
        self._forks: list[dict] = []
        self._active_forks: list[dict] = []
        self._rollbacks = 0
        self._promotions = 0

    def fork(self, context: str = "", fitness: float = 0.5) -> dict:
        fork = {
            "context": context, "parent_fitness": fitness,
            "variant_genes": [random.random() for _ in range(5)],
            "speculative_fitness": fitness * (0.8 + random.random() * 0.4),
            "created_at": time.time(), "status": "active",
        }
        if len(self._active_forks) < self._max_forks:
            self._active_forks.append(fork)
        else:
            weakest = min(self._active_forks, key=lambda f: f["speculative_fitness"])
            if fork["speculative_fitness"] > weakest["speculative_fitness"]:
                self._active_forks.remove(weakest)
                weakest["status"] = "rolled_back"
                self._rollbacks += 1
                self._active_forks.append(fork)
        self._forks.append(fork)
        return fork

    def evaluate_and_select(self) -> dict | None:
        if not self._active_forks:
            return None
        for fork in self._active_forks:
            fork["actual_fitness"] = fork["speculative_fitness"] * (0.9 + random.random() * 0.2)
        best = max(self._active_forks, key=lambda f: f.get("actual_fitness", 0))
        if best.get("actual_fitness", 0) > best["parent_fitness"]:
            best["status"] = "promoted"
            self._promotions += 1
            return best
        else:
            best["status"] = "rolled_back"
            self._rollbacks += 1
            return None

    def get_stats(self) -> dict:
        return {
            "total_forks": len(self._forks), "active": len(self._active_forks),
            "promotions": self._promotions, "rollbacks": self._rollbacks,
            "success_rate": self._promotions / max(self._promotions + self._rollbacks, 1),
        }
