"""ConfidenceGate + EvolutionGrill — Governance gates."""
from __future__ import annotations
import time

from prometheus_ultra.foundation.schema import AutonomyLevel, TrustLevel


class ConfidenceGate:
    def __init__(self, base_threshold: float = 0.5, adaptive: bool = True):
        self._base_threshold = base_threshold
        self._adaptive = adaptive
        self._current_threshold = base_threshold
        self._checks = 0
        self._passed = 0
        self._history: list[float] = []

    def check(self, context: dict | None = None) -> dict:
        ctx = context or {}
        self._checks += 1
        fitness = ctx.get("fitness", 0.5)
        context_quality = min(1.0, len(str(ctx)) / 100)
        confidence = fitness * 0.7 + context_quality * 0.3
        self._history.append(confidence)
        if len(self._history) > 100:
            self._history = self._history[-50:]
        if self._adaptive and len(self._history) >= 10:
            avg = sum(self._history[-10:]) / 10
            self._current_threshold = self._base_threshold * 0.8 + avg * 0.2
        passed = confidence >= self._current_threshold
        if passed:
            self._passed += 1
        return {"passed": passed, "confidence": confidence, "threshold": self._current_threshold}

    def get_stats(self) -> dict:
        return {"checks": self._checks, "passed": self._passed,
                "pass_rate": self._passed / max(self._checks, 1)}


class EvolutionGrill:
    def __init__(self):
        self._reviews: list[dict] = []
        self._approved = 0
        self._rejected = 0

    def review(self, data: dict | None = None) -> dict:
        data = data or {}
        self._reviews.append(data)
        delta = abs(data.get("delta", 0))
        safety_ok = delta < 0.5
        context_ok = bool(data.get("context"))
        approved = safety_ok and context_ok
        if approved:
            self._approved += 1
        else:
            self._rejected += 1
        return {"reviewed": True, "approved": approved}

    def get_stats(self) -> dict:
        return {"reviews": len(self._reviews), "approved": self._approved, "rejected": self._rejected}
