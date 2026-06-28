"""WeibullForgetting — Weibull distribution-based forgetting curve.

Architecture:
    Weibull CDF: R(t) = exp(-(t/λ)^k)
    Where:
    - t: age of memory
    - λ (scale): controls when forgetting accelerates
    - k (shape): controls curve shape (1=exponential, >1=sharper)

    LRU eviction when tracked nodes exceed max_tracked.

    Retention interpretation:
    - R = 1.0: perfect retention (just created)
    - R = 0.5: half-life point
    - R = 0.1: 90% forgotten
    - R → 0: completely forgotten

Algorithm:
    compute_retention(age):
        return exp(-(age / scale)^shape)

    compute_retention_compat(node_id, age):
        r = compute_retention(age)
        cache result
        evict if over max_tracked (LRU by retention)

Complexity:
    compute_retention(): O(1)
    compute_retention_compat(): O(1) amortized, O(N·log N) for eviction

Edge Cases:
    - age=0: R=1.0 (no forgetting)
    - age=∞: R→0 (complete forgetting)
    - shape=0: undefined (protected by init validation)
    - scale=0: undefined (protected by init validation)
"""
from __future__ import annotations

import math


class WeibullForgetting:
    """Weibull distribution-based forgetting curve.

    Usage:
        wf = WeibullForgetting(shape=1.5, scale=100.0)

        # Compute retention for different ages
        r_0 = wf.compute_retention(age=0.0)    # R=1.0
        r_50 = wf.compute_retention(age=50.0)   # R≈0.78
        r_100 = wf.compute_retention(age=100.0)  # R≈0.50
        r_200 = wf.compute_retention(age=200.0)  # R≈0.14

        # Cached version with LRU eviction
        wf.compute_retention_compat("node1", age=50.0)
        r = wf.get_retention("node1")

        # Find nodes that should be forgotten
        expired = wf.get_expired_nodes(threshold=0.1)
    """

    def __init__(self, shape: float = 1.5, scale: float = 100.0, max_tracked: int = 5000):
        """Initialize the forgetting curve.

        Args:
            shape: Weibull shape parameter (k). Higher = sharper forgetting.
            scale: Weibull scale parameter (λ). Higher = slower forgetting.
            max_tracked: Maximum nodes to track before LRU eviction.
        """
        if shape <= 0:
            raise ValueError(f"shape must be > 0, got {shape}")
        if scale <= 0:
            raise ValueError(f"scale must be > 0, got {scale}")
        self._shape = shape
        self._scale = scale
        self._max_tracked = max_tracked
        self._retentions: dict[str, float] = {}
        self._access_times: dict[str, float] = {}

    def compute_retention(self, age: float) -> float:
        """Compute retention probability for a given age.

        Args:
            age: Age of memory (in same units as scale).

        Returns:
            Retention probability [0, 1].
        """
        if age < 0:
            return 1.0
        return math.exp(-((age / self._scale) ** self._shape))

    def compute_retention_compat(self, node_id: str, age: float = 1.0) -> float:
        """Compute and cache retention for a node.

        Args:
            node_id: Node identifier.
            age: Age of the node.

        Returns:
            Retention probability [0, 1].
        """
        r = self.compute_retention(age)
        self._retentions[node_id] = r
        self._access_times[node_id] = time.time()

        # LRU eviction if over limit
        if len(self._retentions) > self._max_tracked:
            sorted_keys = sorted(self._retentions, key=lambda k: self._retentions[k])
            evict_count = len(self._retentions) // 4
            for k in sorted_keys[:evict_count]:
                del self._retentions[k]
                self._access_times.pop(k, None)

        return r

    def get_retention(self, node_id: str) -> float:
        """Get cached retention for a node."""
        return self._retentions.get(node_id, 1.0)

    def get_expired_nodes(self, threshold: float = 0.1) -> list[str]:
        """Get nodes with retention below threshold."""
        return [nid for nid, r in self._retentions.items() if r < threshold]

    def get_most_forgotten(self, top_k: int = 10) -> list[dict]:
        """Get nodes closest to being forgotten."""
        sorted_nodes = sorted(self._retentions.items(), key=lambda x: x[1])
        return [{"node_id": nid, "retention": r} for nid, r in sorted_nodes[:top_k]]

    def get_most_retained(self, top_k: int = 10) -> list[dict]:
        """Get nodes with highest retention."""
        sorted_nodes = sorted(self._retentions.items(), key=lambda x: x[1], reverse=True)
        return [{"node_id": nid, "retention": r} for nid, r in sorted_nodes[:top_k]]

    def get_retention_distribution(self, bins: int = 10) -> dict[int, int]:
        """Get retention distribution in bins."""
        distribution = {i: 0 for i in range(bins)}
        for r in self._retentions.values():
            bin_idx = min(int(r * bins), bins - 1)
            distribution[bin_idx] += 1
        return distribution

    def predict_forget_time(self, node_id: str, threshold: float = 0.1) -> float | None:
        """Predict when a node will be forgotten below threshold."""
        r = self._retentions.get(node_id, 1.0)
        if r <= threshold:
            return 0.0
        # Solve: threshold = exp(-(t/λ)^k) for t
        # t = λ * (-ln(threshold))^(1/k)
        t = self._scale * (-math.log(threshold)) ** (1 / self._shape)
        return t

    def get_stats(self) -> dict:
        vals = list(self._retentions.values())
        return {
            "tracked_nodes": len(self._retentions),
            "avg_retention": sum(vals) / max(len(vals), 1),
            "min_retention": min(vals) if vals else 0,
            "max_retention": max(vals) if vals else 1,
            "shape": self._shape,
            "scale": self._scale,
        }


import time
