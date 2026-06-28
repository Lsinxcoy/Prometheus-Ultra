"""ToolOverloadDetector — Detects when too many tools harm performance.

Based on: "Tool Overload: When More Tools Hurt LLM Agent Performance"
(arXiv:2411.15399)

Key Concepts:
    1. Performance degrades with too many tools (46 tools → failure)
    2. Optimal tool count is task-dependent
    3. Tool description tokens consume context budget
    4. Irrelevant tools cause confusion

Paper Finding:
    "46 tools led to failure, while 19 tools achieved success
     on the same task. Tool count must be dynamically managed."

Algorithm:
    - Track tool usage patterns
    - Measure performance vs tool count
    - Recommend optimal tool set
    - Detect when adding tools hurts performance
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ToolUsageRecord:
    """Record of tool usage."""
    tool_name: str = ""
    used: bool = False
    success: bool = False
    latency_ms: float = 0.0
    relevance: float = 0.5


class ToolOverloadDetector:
    """Detects tool overload and recommends optimal tool sets.

    Based on Tool Overload paper (arXiv:2411.15399).

    Usage:
        detector = ToolOverloadDetector()
        detector.record_usage("search_tool", used=True, success=True, relevance=0.9)
        detector.record_usage("math_tool", used=False, relevance=0.1)
        recommendation = detector.get_recommendation()
    """

    def __init__(self, optimal_range: tuple[int, int] = (5, 20)):
        """Initialize the detector.

        Args:
            optimal_range: Expected optimal tool count range.
        """
        self._optimal_min, self._optimal_max = optimal_range
        self._usage_records: list[ToolUsageRecord] = []
        self._tool_stats: dict[str, dict] = {}
        self._performance_history: list[dict] = []

    def record_usage(self, tool_name: str, used: bool = True, success: bool = True,
                     latency_ms: float = 0.0, relevance: float = 0.5) -> None:
        """Record tool usage."""
        record = ToolUsageRecord(
            tool_name=tool_name, used=used, success=success,
            latency_ms=latency_ms, relevance=relevance,
        )
        self._usage_records.append(record)

        if tool_name not in self._tool_stats:
            self._tool_stats[tool_name] = {"uses": 0, "successes": 0, "total_relevance": 0}
        stats = self._tool_stats[tool_name]
        stats["uses"] += 1
        if success:
            stats["successes"] += 1
        stats["total_relevance"] += relevance

    def get_tool_performance(self) -> dict[str, dict]:
        """Get performance metrics per tool."""
        result = {}
        for name, stats in self._tool_stats.items():
            uses = stats["uses"]
            success_rate = stats["successes"] / max(uses, 1)
            avg_relevance = stats["total_relevance"] / max(uses, 1)
            result[name] = {
                "uses": uses, "success_rate": success_rate,
                "avg_relevance": avg_relevance,
                "recommendation": "keep" if avg_relevance > 0.3 and success_rate > 0.5 else "remove",
            }
        return result

    def get_recommendation(self) -> dict:
        """Get recommendation for tool set optimization."""
        tool_perf = self.get_tool_performance()
        n_tools = len(tool_perf)

        # Check if in optimal range
        in_range = self._optimal_min <= n_tools <= self._optimal_max

        # Identify low-value tools
        low_value = [name for name, perf in tool_perf.items()
                     if perf["recommendation"] == "remove"]

        # Estimate performance impact
        if n_tools > self._optimal_max:
            overload_severity = (n_tools - self._optimal_max) / self._optimal_max
        elif n_tools < self._optimal_min:
            overload_severity = (self._optimal_min - n_tools) / self._optimal_min
        else:
            overload_severity = 0.0

        return {
            "tool_count": n_tools,
            "in_optimal_range": in_range,
            "overload_severity": overload_severity,
            "low_value_tools": low_value,
            "recommendation": "reduce" if n_tools > self._optimal_max else
                             "expand" if n_tools < self._optimal_min else "optimal",
        }

    def get_stats(self) -> dict:
        return {"total_records": len(self._usage_records),
                "unique_tools": len(self._tool_stats)}
