"""UCB1Bandit — Upper Confidence Bound strategy selection.

Algorithm:
    UCB1: aᵢ = x̄ᵢ + √(2·ln(n)/nᵢ)
    Where:
    - x̄ᵢ = average reward for arm i
    - n = total pulls
    - nᵢ = pulls for arm i

    Select arm with highest UCB1 value.

    Cold start: unvisited arms are selected first.

Complexity:
    Select: O(K) where K = number of arms
    Update: O(1)
"""
from __future__ import annotations
import math
import random


class UCB1Bandit:
    """UCB1 bandit for strategy selection.

    Usage:
        bandit = UCB1Bandit(arm_names=["strategy_a", "strategy_b", "strategy_c"])
        for _ in range(100):
            arm = bandit.select()
            reward = evaluate(arm)
            bandit.update(arm, reward)
        print(f"Best arm: {bandit.get_best_arm()}")
    """

    def __init__(self, arm_names: list[str] | None = None):
        self._arms = arm_names or ["default"]
        self._counts: dict[str, int] = {a: 0 for a in self._arms}
        self._values: dict[str, float] = {a: 0.0 for a in self._arms}
        self._total = 0
        self._history: list[dict] = []

    def select(self) -> str:
        for arm in self._arms:
            if self._counts[arm] == 0:
                return arm
        ucb_values = {}
        for arm in self._arms:
            avg = self._values[arm] / self._counts[arm]
            exploration = math.sqrt(2 * math.log(max(self._total, 1)) / self._counts[arm])
            ucb_values[arm] = avg + exploration
        return max(ucb_values, key=ucb_values.get)

    def update(self, arm: str, reward: float):
        if arm in self._counts:
            self._counts[arm] += 1
            self._values[arm] += reward
            self._total += 1
            self._history.append({"arm": arm, "reward": reward, "total": self._total})

    def get_best_arm(self) -> str:
        best = max(self._arms, key=lambda a: self._values[a] / max(self._counts[a], 1))
        return best

    def get_arm_stats(self) -> dict[str, dict]:
        stats = {}
        for arm in self._arms:
            stats[arm] = {
                "count": self._counts[arm],
                "total_reward": self._values[arm],
                "avg_reward": self._values[arm] / max(self._counts[arm], 1),
            }
        return stats

    def get_stats(self) -> dict:
        return {"arms": len(self._arms), "total": self._total,
                "best_arm": self.get_best_arm()}
