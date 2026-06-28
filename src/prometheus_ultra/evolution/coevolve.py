"""CoEvolution — Multi-population co-evolution with Red Queen dynamics."""
from __future__ import annotations
import random


class CoEvolution:
    """Co-evolution with Red Queen dynamics.

    Usage:
        coevo = CoEvolution()
        coevo.evolve(["predator", "prey"], generations=10)
        stats = coevo.get_stats()
    """

    def __init__(self, niche_radius: float = 0.3):
        self._niche_radius = niche_radius
        self._populations: dict[str, list[dict]] = {}
        self._generation = 0
        self._history: list[dict] = []

    def evolve(self, contexts: list[str] | None = None, generations: int = 1):
        for ctx in (contexts or ["default"]):
            if ctx not in self._populations:
                self._populations[ctx] = [
                    {"genes": [random.random() for _ in range(5)], "fitness": 0.5}
                    for _ in range(10)
                ]
        for _ in range(generations):
            self._generation += 1
            # Evaluate
            for name, pop in self._populations.items():
                for ind in pop:
                    ind["fitness"] = max(0.01, min(1.0,
                        sum(ind["genes"]) / len(ind["genes"]) + random.gauss(0, 0.05)))
            # Red Queen coupling
            other_names = list(self._populations.keys())
            for name, pop in self._populations.items():
                opponents = [self._populations[n] for n in other_names if n != name]
                if opponents:
                    avg_opp = sum(sum(i["fitness"] for i in o) / max(len(o), 1)
                                  for o in opponents) / len(opponents)
                    for ind in pop:
                        coupling = 0.5 + 0.5 * (1 - avg_opp)
                        ind["effective_fitness"] = ind["fitness"] * coupling
            # Selection + reproduction
            for name, pop in self._populations.items():
                pop.sort(key=lambda x: x.get("effective_fitness", x["fitness"]), reverse=True)
                elites = pop[:max(2, len(pop) // 5)]
                new_pop = [dict(e) for e in elites]
                while len(new_pop) < len(pop):
                    p1, p2 = random.sample(elites, 2) if len(elites) >= 2 else (elites[0], elites[0])
                    child_genes = p1["genes"][:3] + p2["genes"][3:]
                    for i in range(len(child_genes)):
                        if random.random() < 0.1:
                            child_genes[i] = max(0, min(1, child_genes[i] + random.gauss(0, 0.1)))
                    new_pop.append({"genes": child_genes, "fitness": 0.0})
                self._populations[name] = new_pop
        stats = {n: sum(i["fitness"] for i in p) / max(len(p), 1)
                 for n, p in self._populations.items()}
        self._history.append(stats)

    def get_stats(self) -> dict:
        return {"populations": len(self._populations), "generation": self._generation}
