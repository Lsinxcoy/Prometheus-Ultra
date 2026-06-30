"""EverOS — Search-oriented external memory evolution.

Based on: EvoAgentBench leaderboard (EverOS method)
Best on: SWE-Bench (+32-46%), BrowseComp (+76%)
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class SearchResult:
    query: str = ""
    results: list[str] = field(default_factory=list)
    relevance_scores: list[float] = field(default_factory=list)
    strategy: str = ""


@dataclass
class EverOSResult:
    method: str = "everos"
    improvement: float = 0.0
    cost_delta: float = 0.0
    details: str = ""


class EverOS:
    """Search-oriented external memory evolution.

    Usage:
        evos = EverOS(search_depth=3)
        result = evos.evolve(task="fix bug", current_approach="naive search")
    """

    def __init__(self, search_depth: int = 3, expansion_factor: int = 2):
        self._depth = search_depth
        self._expansion = expansion_factor
        self._history: list[dict] = []

    def evolve(self, task: str, current_approach: str = "",
                context: dict = None) -> EverOSResult:
        context = context or {}
        strategies = ["nearest_neighbor", "graph_walk", "keyword_expansion", "semantic_search"]

        best_strategy = strategies[0]
        best_score = 0.0

        for strategy in strategies:
            score = self._evaluate_strategy(task, strategy, context)
            if score > best_score:
                best_score = score
                best_strategy = strategy

        improvement = best_score * 0.15
        self._history.append({"task": task, "strategy": best_strategy, "score": best_score})

        return EverOSResult(
            method="everos",
            improvement=improvement,
            cost_delta=improvement * 0.1,
            details="strategy=%s, score=%.3f" % (best_strategy, best_score),
        )

    def _evaluate_strategy(self, task: str, strategy: str, context: dict) -> float:
        base_score = 0.5
        if strategy == "graph_walk":
            base_score += 0.2 if "relationship" in task.lower() else 0.0
        elif strategy == "keyword_expansion":
            base_score += 0.15
        elif strategy == "semantic_search":
            base_score += 0.1 if len(task.split()) > 3 else 0.0
        return min(1.0, base_score)

    def get_stats(self) -> dict:
        return {"evolutions": len(self._history)}
