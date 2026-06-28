"""EvalDrivenEngine — Iterative evaluation-driven evolution.

Algorithm:
    Iteratively improve fitness via:
    fitness = min(1.0, current + learning_rate × (1 - current))

    Converges when fitness >= threshold or max_iterations reached.

    Learning rate controls convergence speed:
    - High rate (0.1): fast convergence, may overshoot
    - Low rate (0.01): slow convergence, more stable
    - Adaptive rate: adjusts based on recent improvements

Edge Cases:
    - max_iterations = 0: returns initial fitness
    - threshold > 1: never converges, runs all iterations
    - All iterations same fitness: returns final fitness

Complexity: O(max_iterations)
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class EvolutionContext:
    """Context for evolution."""
    metadata: dict = field(default_factory=dict)


@dataclass
class EvolutionEvalResult:
    """Result of an evolution evaluation."""
    iteration: int = 0
    fitness: float = 0.0
    improved: bool = False
    population_size: int = 0
    best_fitness: float = 0.0
    duration_ms: float = 0.0


class EvalDrivenEngine:
    """Evaluation-driven evolution engine.

    Usage:
        engine = EvalDrivenEngine(max_iterations=10, convergence_threshold=0.95)
        result = engine.evolve(EvolutionContext())
        print(f"Final fitness: {result.fitness:.4f} after {result.iteration} iterations")
    """

    def __init__(self, max_iterations: int = 10, convergence_threshold: float = 0.95,
                 learning_rate: float = 0.05, adaptive_lr: bool = False):
        self._max_iter = max_iterations
        self._threshold = convergence_threshold
        self._lr = learning_rate
        self._adaptive_lr = adaptive_lr
        self._history: list[EvolutionEvalResult] = []
        self._best_ever = 0.0
        self._fitness_history: list[float] = []

    def evolve(self, context: EvolutionContext | None = None) -> EvolutionEvalResult:
        start_time = time.time()
        fitness = 0.5
        for i in range(self._max_iter):
            lr = self._compute_lr(i)
            fitness = min(1.0, fitness + lr * (1 - fitness))
            self._fitness_history.append(fitness)

            if fitness >= self._threshold:
                elapsed = (time.time() - start_time) * 1000
                result = EvolutionEvalResult(iteration=i + 1, fitness=fitness, improved=True,
                                             best_fitness=fitness, duration_ms=elapsed)
                self._history.append(result)
                self._best_ever = max(self._best_ever, fitness)
                return result

        elapsed = (time.time() - start_time) * 1000
        result = EvolutionEvalResult(iteration=self._max_iter, fitness=fitness,
                                     improved=fitness > 0.5, best_fitness=fitness,
                                     duration_ms=elapsed)
        self._history.append(result)
        self._best_ever = max(self._best_ever, fitness)
        return result

    def _compute_lr(self, iteration: int) -> float:
        if not self._adaptive_lr:
            return self._lr
        # Adaptive: decrease lr as we approach convergence
        progress = iteration / max(self._max_iter, 1)
        return self._lr * (1.0 - progress * 0.5)

    def evaluate(self, data: dict | None = None) -> dict:
        return {"evaluated": True, "history_len": len(self._history), "best_ever": self._best_ever}

    def get_fitness_history(self) -> list[float]:
        return list(self._fitness_history)

    def get_convergence_curve(self) -> list[dict]:
        return [{"iteration": h.iteration, "fitness": h.fitness} for h in self._history]

    def get_stats(self) -> dict:
        return {"evaluations": len(self._history), "best_ever": self._best_ever,
                "avg_fitness": sum(self._fitness_history) / max(len(self._fitness_history), 1)}


import time
