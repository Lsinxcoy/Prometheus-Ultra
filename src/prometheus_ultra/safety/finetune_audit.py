"""FineTuneAudit — 微调后行为漂移检测 (arXiv 2602.00298).

窄域微调导致广泛涌现偏差（incorrect-math 0%, gore-movie-trivia 87.67%）。
对比微调前后的行为分布检测漂移。
"""

from __future__ import annotations
import logging
import time
logger = logging.getLogger(__name__)

class FineTuneAudit:
    def __init__(self): self._audits = []
    def detect_drift(self, before: list[dict], after: list[dict]) -> dict:
        if not before or not after: return {"drifted": False, "drifted_tasks": [], "effect_size": 0.0}
        drifted_tasks = []
        b_map = {t.get("task", ""): t.get("accuracy", 0) for t in before}
        a_map = {t.get("task", ""): t.get("accuracy", 0) for t in after}
        for task, b_acc in b_map.items():
            if task in a_map:
                diff = abs(a_map[task] - b_acc)
                if diff > 0.2:
                    drifted_tasks.append({"task": task, "before": b_acc, "after": a_map[task], "delta": diff})
        result = {"drifted": len(drifted_tasks) > 0, "drifted_tasks": drifted_tasks, "effect_size": len(drifted_tasks) / max(len(before), 1)}
        self._audits.append(result)
        return result
    def get_stats(self) -> dict: return {"audits": len(self._audits), "drifts_detected": sum(1 for a in self._audits if a["drifted"])}
