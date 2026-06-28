"""Brain — Decision engine with utility-based action selection."""
from __future__ import annotations


class Brain:
    def __init__(self):
        self._decisions: list[dict] = []
        self._action_values: dict[str, float] = {}
        self._action_counts: dict[str, int] = {}

    def decide(self, context: dict | None = None) -> dict:
        ctx = context or {}
        action = ctx.get("action", "unknown")
        utility = self._estimate_utility(ctx)
        self._action_values[action] = self._action_values.get(action, 0.5) * 0.9 + utility * 0.1
        self._action_counts[action] = self._action_counts.get(action, 0) + 1
        candidates = ctx.get("candidates", [action])
        best = max(candidates, key=lambda a: self._action_values.get(a, 0.5))
        decision = {"selected": best, "utility": utility, "action": action,
                    "confidence": min(1.0, self._action_counts[action] / 10)}
        self._decisions.append(decision)
        return decision

    def _estimate_utility(self, ctx: dict) -> float:
        utility = ctx.get("utility", 0.5)
        if ctx.get("result_count", 0) > 0:
            utility += 0.1
        action = ctx.get("action", "")
        historical = self._action_values.get(action, 0.5)
        return max(0.0, min(1.0, utility * 0.7 + historical * 0.3))

    def get_stats(self) -> dict:
        return {"decisions": len(self._decisions), "unique_actions": len(self._action_values)}
