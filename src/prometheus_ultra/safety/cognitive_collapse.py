"""CognitiveCollapse — Detect over-reliance on external reasoning.

From MiMo Knowledge #39: "认知坍缩=相变，超过临界阈值后能力突然崩溃"
"""
from __future__ import annotations
from collections import Counter


class CognitiveCollapse:
    """Detect cognitive collapse from over-reliance on AI assistance."""
    def __init__(self, threshold: float = 0.7):
        self._threshold = threshold
        self._delegation_history: list[float] = []
        self._alerts: list[dict] = []

    def record_delegation(self, task_complexity: float, ai_assistance_level: float):
        self._delegation_history.append(ai_assistance_level)

    def detect(self) -> dict:
        if len(self._delegation_history) < 10:
            return {"collapsed": False, "reason": "insufficient_data"}

        recent = self._delegation_history[-10:]
        avg_delegation = sum(recent) / len(recent)

        older = self._delegation_history[:-10] if len(self._delegation_history) > 10 else recent
        older_avg = sum(older) / max(len(older), 1)

        if avg_delegation > self._threshold and avg_delegation > older_avg * 1.5:
            self._alerts.append({"severity": "critical", "delegation": avg_delegation})
            return {"collapsed": True, "reason": "threshold_exceeded (%.2f > %.2f)" % (avg_delegation, self._threshold)}

        return {"collapsed": False, "delegation_avg": avg_delegation}

    def get_stats(self) -> dict:
        return {"history": len(self._delegation_history), "alerts": len(self._alerts)}
