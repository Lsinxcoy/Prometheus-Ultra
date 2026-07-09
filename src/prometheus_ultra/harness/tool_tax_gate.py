"""ToolTaxGate — G-STEP 工具税门控 (arXiv 2605.00136).

工具使用税：格式化成本 + 协议开销可能超过工具增益。
很多场景原生 CoT 就够。
"""
from __future__ import annotations
import logging
import re
logger = logging.getLogger(__name__)

_SIMPLE_TASKS = {"calculate", "convert", "format", "today", "time", "weather", "math"}

class ToolTaxGate:
    def __init__(self):
        self._decisions = []
        self._total = 0
    def decide(self, task: str, tool_info: dict = None) -> dict:
        self._total += 1
        low = task.lower()
        is_simple = any(t in low for t in _SIMPLE_TASKS)
        use_tool = not is_simple
        reason = "Native CoT sufficient" if is_simple else f"Tool needed for complex task"
        result = {"use_tool": use_tool, "reason": reason, "estimated_cost": 0.1 if is_simple else 0.5, "estimated_gain": 0.2 if is_simple else 0.8}
        self._decisions.append(result)
        return result
    def get_stats(self) -> dict:
        return {"total": self._total, "tool_use_rate": round(sum(1 for d in self._decisions if d["use_tool"]) / max(self._total, 1), 4)}
