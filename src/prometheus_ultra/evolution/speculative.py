"""SpeculativeEvolution — Speculative branch-and-bound evolution.

Based on SpecGen (arXiv:2606.17518) and Tree of Thoughts (arXiv:2305.10601).

Instead of random fitness, uses a pluggable evaluator function.
The structure follows ToT: fork → evaluate → select → promote/rollback.
"""
from __future__ import annotations
import random
import time
from typing import Callable


class SpeculativeEvolution:
    """Speculative evolution with fork/rollback and real evaluation.

    Based on SpecGen + Tree of Thoughts branching strategy.

    Usage:
        def my_evaluator(context: str, genes: list[float]) -> float:
            return sum(genes) / len(genes)

        se = SpeculativeEvolution(max_forks=10, evaluator=my_evaluator)
        fork = se.fork("context", fitness=0.5)
        result = se.evaluate_and_select()
    """

    def __init__(self, max_forks: int = 10,
                 evaluator: Callable[[str, list[float]], float] | None = None):
        self._max_forks = max_forks
        self._evaluator = evaluator or self._default_evaluator
        self._forks: list[dict] = []
        self._active_forks: list[dict] = []
        self._rollbacks = 0
        self._promotions = 0
        self._mutation_rate = 0.15
        self._gene_size = 8

    @staticmethod
    def _default_evaluator(context: str, genes: list[float]) -> float:
        """Default evaluator: weighted sum with context-dependent adjustments."""
        if not genes:
            return 0.5
        base = sum(genes) / len(genes)
        variance = sum((g - base) ** 2 for g in genes) / len(genes)
        diversity_bonus = min(0.1, variance * 0.5)
        return max(0.0, min(1.0, base + diversity_bonus))

    def fork(self, context: str = "", fitness: float = 0.5) -> dict:
        """Create a speculative fork with mutated genes.

        Uses Gaussian mutation on parent genes rather than pure random.
        """
        if self._active_forks:
            parent = max(self._active_forks, key=lambda f: f.get("actual_fitness", f["speculative_fitness"]))
            parent_genes = parent["variant_genes"]
            genes = [
                max(0.0, min(1.0, g + random.gauss(0, self._mutation_rate)))
                for g in parent_genes
            ]
        else:
            genes = [max(0.0, min(1.0, fitness + random.gauss(0, 0.2))) for _ in range(self._gene_size)]

        spec_fitness = self._evaluator(context, genes)

        fork = {
            "context": context,
            "parent_fitness": fitness,
            "variant_genes": genes,
            "speculative_fitness": spec_fitness,
            "actual_fitness": spec_fitness,
            "created_at": time.time(),
            "status": "active",
        }

        if len(self._active_forks) < self._max_forks:
            self._active_forks.append(fork)
        else:
            weakest = min(self._active_forks, key=lambda f: f.get("actual_fitness", 0))
            if spec_fitness > weakest.get("actual_fitness", 0):
                self._active_forks.remove(weakest)
                weakest["status"] = "rolled_back"
                self._rollbacks += 1
                self._active_forks.append(fork)

        self._forks.append(fork)
        return fork

    def evaluate_and_select(self) -> dict | None:
        """Evaluate all active forks and select the best.

        Uses real evaluation instead of random noise.
        """
        if not self._active_forks:
            return None

        for fork in self._active_forks:
            fork["actual_fitness"] = self._evaluator(fork["context"], fork["variant_genes"])

        best = max(self._active_forks, key=lambda f: f.get("actual_fitness", 0))

        if best.get("actual_fitness", 0) > best["parent_fitness"]:
            best["status"] = "promoted"
            self._promotions += 1
            return best
        else:
            best["status"] = "rolled_back"
            self._rollbacks += 1
            self._active_forks.remove(best)
            return None

    def get_best(self) -> dict | None:
        if not self._active_forks:
            return None
        return max(self._active_forks, key=lambda f: f.get("actual_fitness", 0))

    def get_stats(self) -> dict:
        return {
            "total_forks": len(self._forks),
            "active": len(self._active_forks),
            "promotions": self._promotions,
            "rollbacks": self._rollbacks,
            "success_rate": self._promotions / max(self._promotions + self._rollbacks, 1),
        }
