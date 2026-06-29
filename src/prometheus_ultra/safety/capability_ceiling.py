"""CapabilityCeiling — 45% capability ceiling detection.

From MiMo Knowledge #7: "当单Agent基线超45%时加Agent负收益"
"""
from __future__ import annotations


class CapabilityCeiling:
    """Detect when adding agents becomes counter-productive."""
    CEILING_THRESHOLD = 0.45

    def __init__(self):
        self._baseline_scores: list[float] = []
        self._agent_counts: list[int] = []

    def record_baseline(self, score: float):
        self._baseline_scores.append(score)

    def record_agent_performance(self, agent_count: int, score: float):
        self._agent_counts.append(agent_count)

    def should_add_agents(self) -> tuple[bool, str]:
        if len(self._baseline_scores) < 3:
            return True, "insufficient_baseline_data"
        recent_baseline = sum(self._baseline_scores[-5:]) / min(len(self._baseline_scores), 5)
        if recent_baseline > self.CEILING_THRESHOLD:
            return False, "baseline_above_ceiling (%.2f > %.2f)" % (recent_baseline, self.CEILING_THRESHOLD)
        return True, "baseline_below_ceiling (%.2f)" % recent_baseline

    def estimate_optimal_agents(self) -> int:
        if not self._agent_counts:
            return 1
        if len(self._baseline_scores) < 3:
            return 2
        return max(1, int(len(self._agent_counts) * 0.8))

    def get_stats(self) -> dict:
        return {"baseline_samples": len(self._baseline_scores),
                "agent_samples": len(self._agent_counts)}
