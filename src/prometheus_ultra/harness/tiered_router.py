"""TieredRouter — AgentFloor 层级路由 (arXiv 2605.00334).

小模型匹配 GPT-5 在 30 个任务上，差距只在长期规划时明显。
日常用小模型，长期规划用大模型。
"""

from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)

_TIER_KEYWORDS = {
    "simple": ["greet", "echo", "convert", "format", "simple math", "today"],
    "routine": ["search", "lookup", "calculate", "translate", "summarize"],
    "complex": ["analyze", "compare", "optimize", "design", "strategy"],
    "planning": ["plan", "roadmap", "architecture", "multi-step", "long-term"],
}


class TieredRouter:
    """层级路由：根据任务复杂度路由到不同模型层级。"""

    TIERS = ["simple", "routine", "complex", "planning"]

    def __init__(self):
        self._routing_log: list[dict] = []
        self._total = 0

    def route(self, task: str) -> dict:
        self._total += 1
        low = task.lower()
        scores = {tier: 0 for tier in self.TIERS}
        for tier, keywords in _TIER_KEYWORDS.items():
            for kw in keywords:
                if kw in low:
                    scores[tier] += 1

        # 偏好高 tier（有重叠时选最高）
        selected = "simple"
        for tier in reversed(self.TIERS):
            if scores[tier] > 0:
                selected = tier
                break

        result = {"tier": selected, "reason": f"matched {scores[selected]} keywords"}
        self._routing_log.append(result)
        return result

    def get_stats(self) -> dict:
        distribution = {t: 0 for t in self.TIERS}
        for r in self._routing_log:
            distribution[r["tier"]] = distribution.get(r["tier"], 0) + 1
        return {
            "total": self._total,
            "distribution": distribution,
        }
