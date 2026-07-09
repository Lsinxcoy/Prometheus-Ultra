"""InterventionControl — Calibration ≠ Control (arXiv 2606.21399).

标量风险预测不是正确的控制目标。监督应从"agent 多可能失败"
转向"干预是否改善结果"。
"""

from __future__ import annotations
import logging
import time
logger = logging.getLogger(__name__)

class InterventionController:
    def __init__(self): self._interventions = []; self._total = 0
    def intervene(self, state: dict, actions: list[dict]) -> dict:
        self._total += 1
        if not actions: return {"recommended_action": "", "expected_improvement": 0.0}
        best = max(actions, key=lambda a: a.get("expected_value", 0))
        result = {"recommended_action": best.get("action", ""), "expected_improvement": best.get("expected_value", 0.0)}
        self._interventions.append(result)
        return result
    def get_stats(self) -> dict: return {"total": self._total, "recent": self._interventions[-5:]}
