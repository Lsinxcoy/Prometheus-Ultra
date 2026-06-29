"""OpenSpace — Open-space exploration for agent evolution.

Based on: EvoAgentBench leaderboard (OpenSpace method)
Performance: mixed results across domains
"""
from __future__ import annotations
from dataclasses import dataclass, field
import random


@dataclass
class ExplorationPoint:
    x: float = 0.0
    y: float = 0.0
    fitness: float = 0.0
    visited: bool = False


@dataclass
class EvolutionResult:
    method: str = "openspace"
    improvement: float = 0.0
    cost_delta: float = 0.0
    details: str = ""


class OpenSpace:
    """Open-space exploration for agent evolution.

    Usage:
        os_explore = OpenSpace(space_dim=5, exploration_rate=0.3)
        result = os_explore.evolve(task="optimize", current_fitness=0.5)
    """

    def __init__(self, space_dim: int = 5, exploration_rate: float = 0.3,
                 population_size: int = 10):
        self._dim = space_dim
        self._rate = exploration_rate
        self._pop_size = population_size
        self._population: list[ExplorationPoint] = []
        self._history: list[dict] = []

    def evolve(self, task: str, current_fitness: float = 0.5,
               eval_fn=None) -> EvolutionResult:
        if not self._population:
            self._population = [
                ExplorationPoint(x=random.random(), y=random.random(), fitness=current_fitness)
                for _ in range(self._pop_size)
            ]

        if eval_fn:
            for p in self._population:
                p.fitness = eval_fn([p.x, p.y])
        else:
            for p in self._population:
                p.fitness = (p.x + p.y) / 2 + random.gauss(0, 0.05)

        self._population.sort(key=lambda p: p.fitness, reverse=True)

        # Exploration: random perturbation
        for p in self._population[:3]:
            p.x = max(0, min(1, p.x + random.gauss(0, self._rate)))
            p.y = max(0, min(1, p.y + random.gauss(0, self._rate)))

        best = self._population[0]
        improvement = best.fitness - current_fitness

        self._history.append({"task": task, "best_fitness": best.fitness})

        return EvolutionResult(
            method="openspace",
            improvement=max(0, improvement),
            cost_delta=self._pop_size * 0.01,
            details="best_fitness=%.3f, dim=%d" % (best.fitness, self._dim),
        )

    def get_stats(self) -> dict:
        return {"population": len(self._population), "evolutions": len(self._history)}
