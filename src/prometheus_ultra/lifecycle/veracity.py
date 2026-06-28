"""VeracityBayesian — Bayesian truth confidence merging.

Algorithm:
    P(H|E) = P(E|H) × P(H) / [P(E|H) × P(H) + P(E|¬H) × P(¬H)]

    Where:
    - H: hypothesis (memory is true)
    - E: evidence (source confidence, consistency, corroboration)
    - P(H) = prior probability
    - P(E|H) = likelihood = source_confidence × consistency
    - P(E|¬H) = 1 - likelihood

    6-level confidence scale:
    0.0-0.2: UNVERIFIED
    0.2-0.4: LOW
    0.4-0.6: MODERATE
    0.6-0.8: HIGH
    0.8-0.95: VERY_HIGH
    0.95-1.0: CERTAIN

Complexity:
    compute_posterior(): O(1)
    compute_posterior_compat(): O(1)
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Evidence:
    """Evidence for Bayesian update."""
    source_confidence: float = 0.5
    consistency: float = 0.5
    corroboration: float = 0.5


class VeracityBayesian:
    """Bayesian truth confidence merging.

    Usage:
        vb = VeracityBayesian()

        # Single evidence update
        p = vb.compute_posterior(0.5, Evidence(0.8, 0.7, 0.6))

        # Multiple evidence updates
        p1 = vb.compute_posterior(0.5, Evidence(0.9, 0.8, 0.7))
        p2 = vb.compute_posterior(p1, Evidence(0.7, 0.6, 0.5))

        # Get confidence level
        level = vb.get_confidence_level(p2)

        # Get all posteriors
        stats = vb.get_stats()
    """

    # Confidence levels
    LEVELS = [
        (0.0, 0.2, "UNVERIFIED"),
        (0.2, 0.4, "LOW"),
        (0.4, 0.6, "MODERATE"),
        (0.6, 0.8, "HIGH"),
        (0.8, 0.95, "VERY_HIGH"),
        (0.95, 1.0, "CERTAIN"),
    ]

    def __init__(self):
        self._posteriors: list[float] = []

    def compute_posterior(self, prior: float, evidence: Evidence) -> float:
        """Compute Bayesian posterior probability.

        Args:
            prior: Prior probability P(H) [0, 1].
            evidence: Evidence with source_confidence, consistency, corroboration.

        Returns:
            Posterior probability P(H|E) [0, 1].
        """
        likelihood = evidence.source_confidence * evidence.consistency
        posterior = (likelihood * prior) / max(likelihood * prior + (1 - likelihood) * (1 - prior), 0.001)
        self._posteriors.append(posterior)
        return posterior

    def compute_posterior_compat(self, prior: float, evidence: Evidence) -> float:
        """Compute posterior (backward-compatible method)."""
        return self.compute_posterior(prior, evidence)

    def get_confidence_level(self, posterior: float) -> str:
        """Get confidence level string from posterior value."""
        for low, high, level in self.LEVELS:
            if low <= posterior < high:
                return level
        return "CERTAIN"

    def get_last_posterior(self) -> float:
        """Get the most recent posterior value."""
        return self._posteriors[-1] if self._posteriors else 0.5

    def get_posterior_history(self) -> list[float]:
        """Get history of posterior values."""
        return list(self._posteriors)

    def get_stats(self) -> dict:
        return {
            "posteriors": len(self._posteriors),
            "avg": sum(self._posteriors) / max(len(self._posteriors), 1),
            "last": self.get_last_posterior(),
            "last_level": self.get_confidence_level(self.get_last_posterior()),
        }
