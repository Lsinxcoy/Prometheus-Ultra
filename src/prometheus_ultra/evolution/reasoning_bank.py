"""ReasoningBank — Reasoning strategy library with retrieval.

Based on: EvoAgentBench leaderboard (ReasoningBank method)
Best on: BrowseComp (+18-41%), SWE-Bench (+5-89%)
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ReasoningStrategy:
    name: str = ""
    description: str = ""
    task_types: list[str] = field(default_factory=list)
    success_rate: float = 0.5
    usage_count: int = 0


@dataclass
class EvolutionResult:
    method: str = "reasoning_bank"
    improvement: float = 0.0
    cost_delta: float = 0.0
    details: str = ""


class ReasoningBank:
    """Reasoning strategy library with retrieval.

    Usage:
        rb = ReasoningBank()
        rb.register_strategy("chain_of_thought", "Step-by-step reasoning", ["math", "logic"])
        rb.register_strategy("tree_search", "BFS/DFS exploration", ["puzzle", "optimization"])
        result = rb.evolve(task="solve equation", context={"type": "math"})
    """

    def __init__(self):
        self._strategies: list[ReasoningStrategy] = []
        self._history: list[dict] = []

    def register_strategy(self, name: str, description: str, task_types: list[str]):
        self._strategies.append(ReasoningStrategy(
            name=name, description=description, task_types=task_types,
        ))

    def evolve(self, task: str, context: dict = None) -> EvolutionResult:
        context = context or {}
        task_type = context.get("type", "general")

        best_strategy = self._retrieve_strategy(task_type)
        improvement = 0.1 if best_strategy else 0.0

        self._history.append({"task": task, "strategy": best_strategy})

        return EvolutionResult(
            method="reasoning_bank",
            improvement=improvement,
            cost_delta=0.03,
            details="strategy=%s" % best_strategy,
        )

    def _retrieve_strategy(self, task_type: str) -> str:
        candidates = []
        for s in self._strategies:
            if task_type in s.task_types:
                candidates.append((s.name, s.success_rate))
        if not candidates:
            return "default"
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def get_stats(self) -> dict:
        return {"strategies": len(self._strategies), "evolutions": len(self._history)}
