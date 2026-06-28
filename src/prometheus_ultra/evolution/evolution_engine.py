"""EvolutionEngine — actual evolutionary algorithm with mutation and selection.

Implements: population-based evolution, mutation, crossover, selection, elitism.
"""
from __future__ import annotations
from dataclasses import dataclass
import random
import time


@dataclass
class EvolutionEvalResult:
    iteration: int = 0
    fitness: float = 0.0
    improved: bool = False
    population_size: int = 0
    best_fitness: float = 0.0


class EvolutionEngine:
    def __init__(self, eval_fn=None, population_size: int = 20,
                 mutation_rate: float = 0.1, crossover_rate: float = 0.7,
                 elitism: int = 2):
        self._eval_fn = eval_fn
        self._pop_size = population_size
        self._mutation_rate = mutation_rate
        self._crossover_rate = crossover_rate
        self._elitism = elitism
        self._population: list[dict] = []
        self._fitnesses: list[float] = []
        self._generation = 0
        self._history: list[EvolutionEvalResult] = []

    def _init_population(self):
        self._population = [{"genes": [random.random() for _ in range(5)],
                              "fitness": 0.0} for _ in range(self._pop_size)]

    def _evaluate_population(self):
        for ind in self._population:
            genes = ind["genes"]
            ind["fitness"] = self._eval_fn(genes) if self._eval_fn else sum(genes) / len(genes)
        self._fitnesses = [ind["fitness"] for ind in self._population]

    def _select(self) -> dict:
        # Tournament selection (size 3)
        tournament = random.sample(self._population, min(3, len(self._population)))
        return max(tournament, key=lambda x: x["fitness"])

    def _crossover(self, p1: dict, p2: dict) -> dict:
        if random.random() > self._crossover_rate:
            return {"genes": list(p1["genes"]), "fitness": 0.0}
        point = random.randint(1, len(p1["genes"]) - 1)
        child_genes = p1["genes"][:point] + p2["genes"][point:]
        return {"genes": child_genes, "fitness": 0.0}

    def _mutate(self, individual: dict):
        for i in range(len(individual["genes"])):
            if random.random() < self._mutation_rate:
                individual["genes"][i] += random.gauss(0, 0.1)
                individual["genes"][i] = max(0.0, min(1.0, individual["genes"][i]))

    def evolve(self, context: str = "", fitness_fn=None) -> EvolutionEvalResult:
        fn = fitness_fn or self._eval_fn
        self._eval_fn = fn

        if not self._population:
            self._init_population()

        self._evaluate_population()
        self._generation += 1

        # Sort by fitness
        self._population.sort(key=lambda x: x["fitness"], reverse=True)
        best_fitness = self._population[0]["fitness"]

        # Elitism: keep top individuals
        new_pop = [{"genes": list(ind["genes"]), "fitness": ind["fitness"]}
                    for ind in self._population[:self._elitism]]

        # Generate rest of new population
        while len(new_pop) < self._pop_size:
            p1 = self._select()
            p2 = self._select()
            child = self._crossover(p1, p2)
            self._mutate(child)
            new_pop.append(child)

        self._population = new_pop
        self._evaluate_population()
        new_best = max(self._fitnesses)

        result = EvolutionEvalResult(
            iteration=self._generation,
            fitness=new_best,
            improved=new_best > best_fitness,
            population_size=self._pop_size,
            best_fitness=new_best,
        )
        self._history.append(result)
        return result

    def evaluate(self, data: dict | None = None) -> dict:
        if self._population:
            self._evaluate_population()
        return {"evaluated": True, "generation": self._generation,
                "best_fitness": max(self._fitnesses) if self._fitnesses else 0}

    def get_stats(self) -> dict:
        return {
            "generations": self._generation,
            "population_size": self._pop_size,
            "history": len(self._history),
            "best_ever": max((h.best_fitness for h in self._history), default=0),
        }
