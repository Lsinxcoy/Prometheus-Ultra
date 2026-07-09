"""NonAdversarialLeakageDetector — 非对抗性数据泄露风险分类器。

参考: arXiv 2606.17114 中提出的 5 类非对抗性数据泄露：
data_awareness, audience_awareness, policy_compliance,
data_minimization, access_boundary。

当前实现仅提供了 5 类风险分类的计数和简单风险比率计算，
不实现论文的实际评估方法论（真实企业场景中的邮件/数据库/
文档代理工具使用评估）。

如需完整实现，需要:
- 企业场景模拟（邮件、数据库、文档系统）
- 真实代理工具使用模式
- 5 类风险的细粒度评估框架
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
