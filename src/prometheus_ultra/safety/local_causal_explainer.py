"""LocalCausalExplainer — LOCA 局部因果解释 (arXiv 2605.00123).

平均 6 个干预修复 jailbreak。局部因果解释比全局规则更有效。
"""

from __future__ import annotations
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_JAILBREAK_MARKERS = [
    "ignore previous", "ignore all", "forget your", "you are now",
    "act as", "pretend to", "roleplay", "do not follow",
    "override", "new instruction", "system prompt",
]


class LocalCausalExplainer:
    """LOCA 局部因果解释器。"""

    def __init__(self):
        self._analyses: list[dict] = []
        self._total = 0

    def local_cause(self, failure_case: dict) -> dict:
        """分析 jailbreak 失败案例的根因。"""
        self._total += 1
        content = failure_case.get("content", "")
        low = content.lower()

        interventions = []
        target_tokens = []

        for marker in _JAILBREAK_MARKERS:
            if marker in low:
                target_tokens.append(marker)
                interventions.append(f"Block token sequence: '{marker}'")
                interventions.append(f"Strengthen instruction boundary at position {low.find(marker)}")

        severity = min(1.0, len(target_tokens) * 0.3 + 0.1)

        if not target_tokens:
            # 回退：检查异常 token 序列
            tokens = low.split()
            long_tokens = [t for t in tokens if len(t) > 20]
            if long_tokens:
                target_tokens = long_tokens[:3]
                interventions.append("Detected abnormally long tokens")
                severity = 0.4

        result = {
            "interventions": interventions,
            "target_tokens": target_tokens,
            "severity": round(severity, 4),
            "n_interventions": len(interventions),
        }
        self._analyses.append(result)
        return result

    def get_stats(self) -> dict:
        return {
            "total_analyses": self._total,
            "avg_severity": round(
                sum(a["severity"] for a in self._analyses) / max(len(self._analyses), 1), 4
            ),
        }
