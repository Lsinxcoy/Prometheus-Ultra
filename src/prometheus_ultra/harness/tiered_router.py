"""TieredRouter — 基于关键词的简易任务复杂度路由。

注意: 本文件名曾引用 AgentFloor (arXiv 2605.00334) 作为参考，
但当前实现仅为基于关键词匹配的轻量级任务路由，不实现
AgentFloor 的 30 任务/6 层级/16 模型的评估范式。

当前实现:
- 4 个路由层级: simple/routine/complex/planning
- 基于关键词匹配（简单字符串包含）
- 非 AgentFloor 的小模型能力阶梯评估

如需真正的 AgentFloor 基准评估，需要:
- 30 个标准化任务覆盖 6 个能力层级
- 16 个开源模型的评估框架
- 指令遵循/工具使用/多步协调/长期规划的层次化测试
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
    """层级路由：根据任务关键词匹配路由到不同复杂度层级。"""

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
