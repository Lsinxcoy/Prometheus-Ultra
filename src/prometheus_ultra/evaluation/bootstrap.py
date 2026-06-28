"""BootstrapCI — Bootstrap confidence interval."""
from __future__ import annotations
import random


class BootstrapCI:
    def __init__(self, n_bootstrap: int = 1000, confidence: float = 0.95):
        self._n = n_bootstrap
        self._confidence = confidence
        self._results: list[dict] = []

    def compute(self, samples: list[float]) -> dict:
        if len(samples) < 2:
            return {"mean": 0, "ci_lower": 0, "ci_upper": 0}
        means = []
        for _ in range(self._n):
            bootstrap = [random.choice(samples) for _ in range(len(samples))]
            means.append(sum(bootstrap) / len(bootstrap))
        means.sort()
        alpha = (1 - self._confidence) / 2
        ci_lower = means[int(alpha * len(means))]
        ci_upper = means[int((1 - alpha) * len(means))]
        result = {"mean": sum(samples) / len(samples), "ci_lower": ci_lower, "ci_upper": ci_upper}
        self._results.append(result)
        return result

    def get_stats(self) -> dict:
        return {"computations": len(self._results)}
