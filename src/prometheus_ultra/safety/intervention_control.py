"""InterventionController — 干预导向风险控制 (arXiv 2606.21399).

论文核心方法：
标量风险预测不是正确的控制目标。
监督应从"agent 多可能失败"转向"干预是否改善结果"。
基于反事实推理：如果干预 X，结果会改善多少？
"""

from __future__ import annotations
import logging
import math
from typing import Any

logger = logging.getLogger(__name__)


class InterventionController:
    """干预控制器——基于预期改善选择动作。"""

    def __init__(self):
        self._interventions: list[dict] = []
        self._total = 0
        self._improvement_history: list[float] = []

    def intervene(self, state: dict, actions: list[dict]) -> dict:
        """选择能最大化预期改善的动作。

        Args:
            state: 当前状态，含 {"risk_score": float, "error_count": int, "success_rate": float, ...}
            actions: 候选动作列表，每个含 {"action": str, "expected_value": float, "cost": float, ...}

        Returns:
            {"recommended_action": str, "expected_improvement": float, "reasoning": str}
        """
        self._total += 1
        if not actions:
            return {"recommended_action": "", "expected_improvement": 0.0, "reasoning": "no actions"}

        # 基线：什么都不做的预期结果
        baseline_risk = state.get("risk_score", 0.5)

        best_action = None
        best_improvement = -float("inf")

        for action in actions:
            action_name = action.get("action", "")
            expected_value = action.get("expected_value", 0.0)
            cost = action.get("cost", 0.0)
            confidence = action.get("confidence", 0.5)

            # 预期改善 = (基线风险降低 + 期望价值) × 置信度 - 成本
            risk_reduction = baseline_risk * 0.3  # 假设干预可降低 30% 风险
            improvement = (risk_reduction + expected_value) * confidence - cost

            if improvement > best_improvement:
                best_improvement = improvement
                best_action = action_name

        if best_action is None:
            return {"recommended_action": "", "expected_improvement": 0.0, "reasoning": "no viable action"}

        result = {
            "recommended_action": best_action,
            "expected_improvement": round(max(0.0, best_improvement), 4),
            "reasoning": f"baseline_risk={baseline_risk:.2f}, expected_improvement={best_improvement:.4f}",
        }
        self._interventions.append(result)
        self._improvement_history.append(best_improvement)

        return result

    def get_stats(self) -> dict:
        if not self._interventions:
            return {"total": 0, "avg_improvement": 0.0, "best_action": ""}
        avg_imp = sum(self._improvement_history) / len(self._improvement_history)
        best_action = max(self._interventions, key=lambda r: r["expected_improvement"])["recommended_action"]
        return {
            "total": self._total,
            "avg_improvement": round(avg_imp, 4),
            "best_action": best_action,
        }
