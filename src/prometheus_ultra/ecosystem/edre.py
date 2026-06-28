"""EDREReplicator — Equilibrium-based replicator dynamics."""
from __future__ import annotations
import math


class EDREReplicator:
    def __init__(self):
        self._replications: list[dict] = []
        self._populations: dict[str, float] = {}
        self._generation = 0
        self._diversity_history: list[float] = []

    def replicate(self, data: dict | None = None, fitness: float = 0.5):
        data = data or {}
        context = data.get("context", "default")
        if context not in self._populations:
            self._populations[context] = 1.0
        avg_fitness = sum(self._populations.values()) / max(len(self._populations), 1)
        growth = self._populations[context] * (fitness - avg_fitness) * 0.1
        self._populations[context] = max(0.01, self._populations[context] + growth)
        self._generation += 1
        self._replications.append({"data": data, "fitness": fitness, "gen": self._generation})
        if self._populations:
            total = sum(self._populations.values())
            probs = [v / total for v in self._populations.values()]
            entropy = -sum(p * math.log(p) for p in probs if p > 0)
            self._diversity_history.append(entropy)

    def get_stats(self) -> dict:
        return {"replications": len(self._replications), "generation": self._generation,
                "diversity": self._diversity_history[-1] if self._diversity_history else 0}
