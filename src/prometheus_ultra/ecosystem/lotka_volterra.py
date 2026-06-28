"""LotkaVolterra — Real predator-prey ODE system."""
from __future__ import annotations


class LotkaVolterra:
    def __init__(self):
        self._species: dict[str, dict] = {}
        self._simulations: list[dict] = []
        self._history: dict[str, list[float]] = {}

    def add_species(self, name: str, initial_pop: float = 100.0, growth_rate: float = 1.0,
                    prey: str | None = None, predation_rate: float = 0.1):
        self._species[name] = {"pop": initial_pop, "growth_rate": growth_rate, "prey": prey,
                               "predation_rate": predation_rate}
        self._history[name] = [initial_pop]

    def simulate(self, dt: float = 0.01, steps: int = 100) -> dict:
        for _ in range(steps):
            new_pops = {}
            for name, sp in self._species.items():
                pop = sp["pop"]
                if sp["prey"] and sp["prey"] in self._species:
                    prey_pop = self._species[sp["prey"]]["pop"]
                    dpredator = sp["predation_rate"] * prey_pop * pop - 0.5 * pop
                    new_pops[name] = max(0.1, pop + dpredator * dt)
                else:
                    total_predation = sum(o["predation_rate"] * o["pop"]
                                         for o in self._species.values() if o.get("prey") == name)
                    dprey = sp["growth_rate"] * pop - total_predation * pop
                    new_pops[name] = max(0.1, pop + dprey * dt)
            for name, new_pop in new_pops.items():
                self._species[name]["pop"] = new_pop
                self._history[name].append(new_pop)
        result = {name: sp["pop"] for name, sp in self._species.items()}
        self._simulations.append(result)
        return result

    def get_stats(self) -> dict:
        return {"species": len(self._species), "simulations": len(self._simulations)}
