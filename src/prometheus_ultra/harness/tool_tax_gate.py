"""ToolTaxGate — 工具使用成本门控决策器。

基于三层成本分解决定是否使用工具：
prompt_cost + protocol_cost + execution_cost vs estimated_gain

注意: 本文件曾引用 arXiv 2605.00136 (G-STEP)，该论文描述了
语义噪声条件下工具使用税可能超过收益的因子化干预框架。

当前实现:
- 3 组件成本结构
- 收益估计使用简单关键字分类
- 不包含论文的语义噪声分析
"""

from __future__ import annotations
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# 简单任务：原生 CoT 通常足够
_SIMPLE_COG_TASKS = {"calculate", "convert", "format", "today", "time", "weather", "math", "echo"}
# 中等任务：工具可能有用
_MODERATE_TASKS = {"search", "lookup", "translate", "summarize", "check", "find"}
# 复杂任务：工具通常必要
_COMPLEX_TASKS = {"analyze", "compare", "optimize", "code", "compile", "debug", "deploy"}

# 工具协议开销估计
_PROTOCOL_OVERHEAD = 0.15  # 格式化 + 参数序列化开销
_EXECUTION_GATE = 0.10     # 调用执行开销


class ToolTaxGate:
    """G-STEP 推理时门控。"""

    def __init__(self):
        self._decisions: list[dict] = []
        self._total = 0
        self._tools_used = 0

    def decide(self, task: str, tool_info: dict = None) -> dict:
        """决定是否使用工具。

        Args:
            task: 任务描述
            tool_info: 工具信息，含 {"cost": float, "gain": float, "protocol": str}

        Returns:
            {"use_tool": bool, "reason": str, "estimated_cost": float, "estimated_gain": float}
        """
        self._total += 1
        low = task.lower()

        # 计算工具使用总成本
        prompt_cost = len(task) / 100.0 * 0.01  # 每 100 字符 0.01
        protocol_cost = _PROTOCOL_OVERHEAD
        execution_cost = _EXECUTION_GATE
        if tool_info:
            execution_cost += tool_info.get("cost", 0.0)

        total_cost = prompt_cost + protocol_cost + execution_cost

        # 计算预期增益
        if any(t in low for t in _COMPLEX_TASKS):
            estimated_gain = 0.7  # 复杂任务工具增益大
            reason = "Complex task — tool likely beneficial"
            use_tool = True
        elif any(t in low for t in _MODERATE_TASKS):
            estimated_gain = 0.5
            reason = "Moderate task — tool may help"
            use_tool = True
        else:
            estimated_gain = 0.2
            reason = "Simple task — native CoT sufficient"
            use_tool = False

        # 工具信息中提供了特定增益时使用
        if tool_info and "gain" in tool_info:
            estimated_gain = tool_info["gain"]

        # 最终决策：增益 > 成本
        if estimated_gain <= total_cost:
            use_tool = False
            reason += " (tool tax > gain)"

        result = {
            "use_tool": use_tool,
            "reason": reason,
            "estimated_cost": round(total_cost, 4),
            "estimated_gain": round(estimated_gain, 4),
        }
        self._decisions.append(result)
        if use_tool:
            self._tools_used += 1
        return result

    def get_stats(self) -> dict:
        return {
            "total": self._total,
            "tool_use_rate": round(self._tools_used / max(self._total, 1), 4),
            "avg_cost": round(sum(d["estimated_cost"] for d in self._decisions) / max(len(self._decisions), 1), 4),
        }
