"""BehaviorMirror — Behavioral pattern analysis and deviation detection."""
from __future__ import annotations
from collections import Counter
import math


class BehaviorMirror:
    def __init__(self, window: int = 100):
        self._window = window
        self._mirrors: list[dict] = []
        self._action_history: dict[str, list[str]] = {}
        self._profiles: dict[str, dict] = {}

    def mirror(self, agent: str, action: str, data: dict | None = None):
        self._mirrors.append({"agent": agent, "action": action, "data": data or {}})
        if len(self._mirrors) > self._window * 2:
            self._mirrors = self._mirrors[-self._window:]
        if agent not in self._action_history:
            self._action_history[agent] = []
        self._action_history[agent].append(action)
        if len(self._action_history[agent]) > self._window:
            self._action_history[agent] = self._action_history[agent][-self._window:]

    def compute_profile(self, agent: str) -> dict:
        actions = self._action_history.get(agent, [])
        if not actions:
            return {"agent": agent, "entropy": 0, "unique_actions": 0}
        counts = Counter(actions)
        total = len(actions)
        probs = [c / total for c in counts.values()]
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)
        profile = {"agent": agent, "entropy": entropy, "unique_actions": len(counts), "total_actions": total}
        self._profiles[agent] = profile
        return profile

    def detect_deviation(self, agent: str, current_window: int = 10) -> float:
        history = self._action_history.get(agent, [])
        if len(history) < current_window + 10:
            return 0.0
        older = history[:-current_window]
        recent = history[-current_window:]
        old_counts, rec_counts = Counter(older), Counter(recent)
        all_actions = set(old_counts) | set(rec_counts)
        old_total, rec_total = max(len(older), 1), max(len(recent), 1)
        jsd = 0.0
        for action in all_actions:
            p = old_counts.get(action, 0) / old_total
            q = rec_counts.get(action, 0) / rec_total
            m = (p + q) / 2
            if p > 0 and m > 0:
                jsd += 0.5 * p * math.log(p / m)
            if q > 0 and m > 0:
                jsd += 0.5 * q * math.log(q / m)
        return jsd

    def get_stats(self) -> dict:
        return {"mirrors": len(self._mirrors), "agents_profiled": len(self._profiles)}
