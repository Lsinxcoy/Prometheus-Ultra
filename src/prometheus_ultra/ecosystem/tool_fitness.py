"""ToolFitnessPredictor — Tool effectiveness modeling."""
from __future__ import annotations
from collections import defaultdict


class ToolFitnessPredictor:
    def __init__(self):
        self._tool_stats: dict[str, dict] = {}

    def record_usage(self, tool: str, action: str, success: bool, latency_ms: float = 0):
        if tool not in self._tool_stats:
            self._tool_stats[tool] = {"uses": 0, "successes": 0, "total_latency": 0, "actions": defaultdict(int)}
        stats = self._tool_stats[tool]
        stats["uses"] += 1
        if success:
            stats["successes"] += 1
        stats["total_latency"] += latency_ms
        stats["actions"][action] += 1

    def predict(self, tool: str, action: str = "") -> dict:
        stats = self._tool_stats.get(tool)
        if not stats or stats["uses"] == 0:
            fitness = 0.5
        else:
            success_rate = stats["successes"] / stats["uses"]
            avg_latency = stats["total_latency"] / stats["uses"]
            latency_score = max(0, 1 - avg_latency / 5000)
            fitness = success_rate * 0.5 + latency_score * 0.3 + 0.2
        return {"tool": tool, "fitness": fitness, "action": action}

    def get_stats(self) -> dict:
        return {"tools_tracked": len(self._tool_stats)}
