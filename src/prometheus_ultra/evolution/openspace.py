"""OpenSpace — Open-space exploration for agent evolution.

Based on: EvoAgentBench leaderboard (OpenSpace method)

Implements exploration of high-dimensional fitness landscapes using
population-based search with adaptive exploration strategies.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import math
import random


@dataclass
class ExplorationPoint:
    genes: list[float] = field(default_factory=list)
    fitness: float = 0.0
    generation: int = 0
    lineage: list[int] = field(default_factory=list)


@dataclass
class OpenSpaceResult:
    method: str = "openspace"
    improvement: float = 0.0
    cost_delta: float = 0.0
    details: str = ""


class OpenSpace:
    """Open-space exploration for agent evolution.

    Uses population-based search with:
    - Adaptive exploration rate based on fitness diversity
    - Tournament selection for parent choosing
    - Gaussian mutation with adaptive step size
    - Elitism to preserve best solutions

    Usage:
        os_explore = OpenSpace(space_dim=5, population_size=20)
        result = os_explore.evolve(task="optimize", current_fitness=0.5)
    """

    def __init__(self, space_dim: int = 5, exploration_rate: float = 0.3,
                 population_size: int = 10):
        self._dim = space_dim
        self._rate = exploration_rate
        self._pop_size = population_size
        self._population: list[ExplorationPoint] = []
        self._history: list[dict] = []
        self._generation = 0
        self._mutation_rate = exploration_rate
        self._best_ever: ExplorationPoint | None = None

    def evolve(self, task: str, current_fitness: float = 0.5,
                eval_fn=None) -> OpenSpaceResult:
        if not self._population:
            self._population = self._initialize_population(current_fitness)

        fitnesses = []
        for p in self._population:
            if eval_fn:
                p.fitness = eval_fn(p.genes)
            else:
                p.fitness = self._default_eval(p.genes, current_fitness)
            fitnesses.append(p.fitness)

        self._population.sort(key=lambda p: p.fitness, reverse=True)

        if self._best_ever is None or self._population[0].fitness > self._best_ever.fitness:
            self._best_ever = ExplorationPoint(
                genes=list(self._population[0].genes),
                fitness=self._population[0].fitness,
                generation=self._generation,
            )

        fitness_std = self._compute_std(fitnesses)
        self._adapt_mutation_rate(fitness_std)

        parents = self._tournament_select(k=3)
        offspring = self._crossover(parents)
        mutated = self._mutate(offspring)
        self._population = self._select_next_generation(mutated)

        self._generation += 1
        improvement = self._population[0].fitness - current_fitness

        self._history.append({
            "task": task,
            "generation": self._generation,
            "best_fitness": self._population[0].fitness,
            "avg_fitness": sum(fitnesses) / len(fitnesses),
            "fitness_std": fitness_std,
            "mutation_rate": self._mutation_rate,
        })

        return OpenSpaceResult(
            method="openspace",
            improvement=max(0, improvement),
            cost_delta=self._pop_size * 0.01,
            details="gen=%d, best=%.3f, avg=%.3f, std=%.3f" % (
                self._generation, self._population[0].fitness,
                sum(fitnesses) / len(fitnesses), fitness_std),
        )

    def _initialize_population(self, base_fitness: float) -> list[ExplorationPoint]:
        pop = []
        for i in range(self._pop_size):
            genes = [random.gauss(base_fitness, 0.2) for _ in range(self._dim)]
            genes = [max(0.0, min(1.0, g)) for g in genes]
            pop.append(ExplorationPoint(genes=genes, fitness=base_fitness, generation=0))
        return pop

    def _default_eval(self, genes: list[float], base_fitness: float) -> float:
        if not genes:
            return base_fitness
        gene_sum = sum(genes)
        gene_count = len(genes)
        avg = gene_sum / gene_count
        variance = sum((g - avg) ** 2 for g in genes) / gene_count
        balance_bonus = max(0, 0.1 - variance)
        return max(0.0, min(1.0, avg + balance_bonus + random.gauss(0, 0.02)))

    def _tournament_select(self, k: int = 3) -> list[ExplorationPoint]:
        parents = []
        for _ in range(2):
            candidates = random.sample(self._population, min(k, len(self._population)))
            winner = max(candidates, key=lambda p: p.fitness)
            parents.append(winner)
        return parents

    def _crossover(self, parents: list[ExplorationPoint]) -> ExplorationPoint:
        if len(parents) < 2:
            return ExplorationPoint(genes=list(parents[0].genes) if parents else [])
        p1, p2 = parents[0], parents[1]
        child_genes = []
        for i in range(self._dim):
            if random.random() < 0.5:
                child_genes.append(p1.genes[i] if i < len(p1.genes) else 0.5)
            else:
                child_genes.append(p2.genes[i] if i < len(p2.genes) else 0.5)
        return ExplorationPoint(
            genes=child_genes,
            generation=self._generation + 1,
            lineage=[id(p1), id(p2)],
        )

    def _mutate(self, point: ExplorationPoint) -> ExplorationPoint:
        mutated_genes = []
        for g in point.genes:
            if random.random() < self._mutation_rate:
                new_g = g + random.gauss(0, self._mutation_rate)
                mutated_genes.append(max(0.0, min(1.0, new_g)))
            else:
                mutated_genes.append(g)
        point.genes = mutated_genes
        return point

    def _select_next_generation(self, offspring: ExplorationPoint) -> list[ExplorationPoint]:
        self._population.append(offspring)
        self._population.sort(key=lambda p: p.fitness, reverse=True)
        return self._population[:self._pop_size]

    def _adapt_mutation_rate(self, fitness_std: float):
        if fitness_std < 0.05:
            self._mutation_rate = min(0.5, self._mutation_rate * 1.2)
        elif fitness_std > 0.3:
            self._mutation_rate = max(0.05, self._mutation_rate * 0.8)

    def _compute_std(self, values: list[float]) -> float:
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return math.sqrt(variance)

    def get_best(self) -> ExplorationPoint | None:
        return self._best_ever

    def get_stats(self) -> dict:
        return {
            "population": len(self._population),
            "evolutions": len(self._history),
            "generation": self._generation,
            "mutation_rate": self._mutation_rate,
            "best_ever": self._best_ever.fitness if self._best_ever else None,
        }
