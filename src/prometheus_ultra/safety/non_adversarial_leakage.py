"""NonAdversarialLeakage — 非对抗性数据泄露检测 (arXiv 2606.17114).

日常操作也会泄露数据。五类风险：数据感知/受众感知/策略合规/数据最小化/访问边界。
"""

from __future__ import annotations
import logging
logger = logging.getLogger(__name__)

class NonAdversarialLeakageDetector:
    CATEGORIES = ["data_awareness", "audience_awareness", "policy_compliance", "data_minimization", "access_boundary"]
    def __init__(self):
        self._detections = []; self._total = 0
    def detect_leakage(self, operations: list[dict]) -> dict:
        self._total += 1
        categories = {}
        for op in operations:
            cat = op.get("category", "")
            if cat in self.CATEGORIES:
                categories[cat] = categories.get(cat, 0) + 1
        risk = min(1.0, sum(categories.values()) / max(len(operations), 1))
        result = {"risk": round(risk, 4), "categories": categories, "recommendations": [f"Review {c} controls" for c in categories if categories[c] > 2]}
        self._detections.append(result)
        return result
    def get_stats(self) -> dict:
        avg_risk = sum(d["risk"] for d in self._detections) / max(len(self._detections), 1)
        return {"total_scans": self._total, "avg_risk": round(avg_risk, 4), "detections": len(self._detections)}
