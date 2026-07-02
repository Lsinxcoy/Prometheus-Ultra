"""EDREReplicator — Equilibrium Distribution Replicator Dynamics.

Based on EDRE equilibrium theory from SkillSmith (arXiv:2606.01314):
    dx_i/dt = x_i * (f_i - f̄) + ε * ∇H(x)

Where:
    x_i = population share of strategy i
    f_i = fitness of strategy i
    f̄ = weighted average fitness
    ε = selection intensity
    H(x) = Shannon entropy (diversity pressure)

Uses RK4 integration for ODE stability.
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

import math


class EDREReplicator:
    """Equilibrium-based replicator dynamics with diversity pressure.

    Usage:
        edre = EDREReplicator()
        edre.replicate({"context": "coding"}, fitness=0.8)
        edre.replicate({"context": "research"}, fitness=0.6)
        stats = edre.get_stats()
    """

    def __init__(self, selection_intensity: float = 0.1, diversity_pressure: float = 0.01):
        self._epsilon = selection_intensity
        self._diversity_coeff = diversity_pressure
        self._populations: dict[str, float] = {}
        self._fitnesses: dict[str, float] = {}
        self._replications: list[dict] = []
        self._generation = 0
        self._diversity_history: list[float] = []
        self._population_history: list[list[float]] = []

    def replicate(self, data: dict | None = None, fitness: float = 0.5):
        """Add/update a population with given fitness."""
        data = data or {}
        context = data.get("context", "default")

        if context not in self._populations:
            self._populations[context] = 1.0

        self._fitnesses[context] = fitness
        self._generation += 1

        self._step_ode(dt=0.1)

        self._replications.append({"data": data, "fitness": fitness, "gen": self._generation})

        if self._populations:
            total = sum(self._populations.values())
            if total > 0:
                shares = [v / total for v in self._populations.values()]
                entropy = -sum(p * math.log(p + 1e-10) for p in shares if p > 0)
                self._diversity_history.append(entropy)

            self._population_history.append(list(self._populations.values()))

    def _replicator_derivatives(self, pops: dict[str, float]) -> dict[str, float]:
        """Compute replicator equation: dx_i/dt = x_i * (f_i - f̄) + ε * dH/dx_i."""
        total = sum(pops.values())
        if total <= 0:
            return {k: 0.0 for k in pops}

        shares = {k: v / total for k, v in pops.items()}
        avg_fitness = sum(shares.get(k, 0) * self._fitnesses.get(k, 0.5) for k in pops)

        derivs = {}
        for name in pops:
            x_i = shares.get(name, 0.0)
            f_i = self._fitnesses.get(name, 0.5)
            dH = -math.log(x_i + 1e-10) - 1.0
            derivs[name] = x_i * (f_i - avg_fitness) + self._diversity_coeff * dH
        return derivs

    def _step_ode(self, dt: float = 0.1):
        """Single RK4 step for replicator dynamics."""
        names = list(self._populations.keys())
        pops = dict(self._populations)

        k1 = self._replicator_derivatives(pops)

        pops_k2 = {n: max(1e-6, pops[n] + 0.5 * dt * k1.get(n, 0)) for n in names}
        k2 = self._replicator_derivatives(pops_k2)

        pops_k3 = {n: max(1e-6, pops[n] + 0.5 * dt * k2.get(n, 0)) for n in names}
        k3 = self._replicator_derivatives(pops_k3)

        pops_k4 = {n: max(1e-6, pops[n] + dt * k3.get(n, 0)) for n in names}
        k4 = self._replicator_derivatives(pops_k4)

        for n in names:
            new_pop = pops[n] + (dt / 6.0) * (k1.get(n, 0) + 2 * k2.get(n, 0) + 2 * k3.get(n, 0) + k4.get(n, 0))
            self._populations[n] = max(1e-6, new_pop)

    def get_shares(self) -> dict[str, float]:
        total = sum(self._populations.values())
        if total <= 0:
            return {}
        return {k: v / total for k, v in self._populations.items()}

    def get_dominant(self) -> str | None:
        if not self._populations:
            return None
        return max(self._populations, key=self._populations.get)

    def get_stats(self) -> dict:
        total = sum(self._populations.values())
        shares = self.get_shares()
        return {
            "replications": len(self._replications),
            "generation": self._generation,
            "species": len(self._populations),
            "diversity": self._diversity_history[-1] if self._diversity_history else 0,
            "dominant": self.get_dominant(),
            "shares": shares,
        }
