"""FiveViewEvaluator — 5-view comprehensive evaluation."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class FiveViewReport:
    composite_score: float = 0.5
    grade: str = "B"
    views: dict = field(default_factory=dict)


class FiveViewEvaluator:
    """5-view evaluation: memory, evolution, safety, efficiency, coherence.

    Usage:
        evaluator = FiveViewEvaluator()
        report = evaluator.evaluate(
            node_count=100, edge_count=50, bank_count=80,
            evolution_fitness=0.7, alert_level="GREEN",
            uptime_s=3600, failure_count=2,
        )
        print(report.composite_score, report.grade)
    """

    GRADES = [
        (0.9, "A+"), (0.85, "A"), (0.8, "A-"),
        (0.75, "B+"), (0.7, "B"), (0.65, "B-"),
        (0.6, "C+"), (0.5, "C"), (0.4, "C-"),
        (0.3, "D"), (0.0, "F"),
    ]

    def __init__(self):
        self._reports: list[FiveViewReport] = []

    def evaluate(self, node_count: int = 0, edge_count: int = 0,
                 bank_count: int = 0, evolution_fitness: float = 0.5,
                 alert_level: str = "GREEN", uptime_s: float = 0,
                 failure_count: int = 0, convergence: bool = False,
                 drift_alerts: int = 0) -> FiveViewReport:
        views = {}

        # Memory: node richness + edge connectivity + bank utilization
        node_score = min(1.0, node_count / 1000)
        edge_score = min(1.0, edge_count / max(node_count, 1))
        bank_score = min(1.0, bank_count / max(node_count, 1))
        views["memory"] = node_score * 0.4 + edge_score * 0.3 + bank_score * 0.3

        # Evolution: fitness + convergence bonus
        views["evolution"] = evolution_fitness * (1.1 if convergence else 1.0)
        views["evolution"] = min(1.0, views["evolution"])

        # Safety: alert level mapping + failure penalty
        safety_base = {"GREEN": 1.0, "YELLOW": 0.7, "ORANGE": 0.4, "RED": 0.1}.get(alert_level, 0.5)
        failure_penalty = min(0.3, failure_count * 0.05)
        views["safety"] = max(0.0, safety_base - failure_penalty)

        # Efficiency: uptime-based + low failure rate
        uptime_score = min(1.0, uptime_s / 86400)
        failure_rate = failure_count / max(uptime_s / 3600, 0.1)
        efficiency_base = 1.0 - min(1.0, failure_rate)
        views["efficiency"] = uptime_score * 0.3 + efficiency_base * 0.7

        # Coherence: low drift + edge-to-node ratio
        drift_penalty = min(0.5, drift_alerts * 0.1)
        coherence_base = min(1.0, edge_count / max(node_count, 1)) if node_count > 0 else 0.5
        views["coherence"] = max(0.0, coherence_base - drift_penalty)

        # Composite: weighted average
        weights = {"memory": 0.25, "evolution": 0.25, "safety": 0.2,
                   "efficiency": 0.15, "coherence": 0.15}
        composite = sum(views[k] * weights[k] for k in weights)
        composite = max(0.0, min(1.0, composite))

        # Grade
        grade = "F"
        for threshold, g in self.GRADES:
            if composite >= threshold:
                grade = g
                break

        report = FiveViewReport(composite_score=composite, grade=grade, views=views)
        self._reports.append(report)
        return report

    def get_stats(self) -> dict:
        scores = [r.composite_score for r in self._reports]
        return {"reports": len(self._reports),
                "avg_score": sum(scores) / max(len(scores), 1),
                "last_score": scores[-1] if scores else 0}
