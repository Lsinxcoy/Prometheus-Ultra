"""RareValidDetector — Rare-but-valid pattern detection.

Algorithm:
    observe(value):
        1. Discretize value into histogram bins
        2. Update bin counts

    detect(items):
        For each item:
            freq = bin_count / total_observations
            if freq < rarity_threshold:
                append to rare list
                mark as valid if utility > 0.05

Complexity:
    observe(): O(1)
    detect(): O(N) where N = items
"""
from __future__ import annotations
from collections import Counter


class RareValidDetector:
    """Detect rare but valid patterns.

    Usage:
        rvd = RareValidDetector(rarity_threshold=0.1)
        for item in items:
            rvd.observe(item.utility)
        rare = rvd.detect(items)
    """

    def __init__(self, rarity_threshold: float = 0.1):
        self._rarity_threshold = rarity_threshold
        self._detections: list[dict] = []
        self._histogram: Counter = Counter()
        self._total = 0

    def observe(self, value: float) -> None:
        bin_idx = int(value * 10)
        self._histogram[bin_idx] += 1
        self._total += 1

    def detect(self, items: list | None = None) -> list[dict]:
        rare = []
        if items:
            for item in items:
                if hasattr(item, 'utility') and item.utility is not None:
                    freq = self._histogram.get(int(item.utility * 10), 0) / max(self._total, 1)
                    if freq < self._rarity_threshold:
                        rare.append({
                            "id": getattr(item, 'id', ''),
                            "utility": item.utility,
                            "frequency": freq,
                            "valid": item.utility > 0.05,
                        })
        self._detections.extend(rare)
        return rare

    def get_rare_values(self) -> list[int]:
        total = max(self._total, 1)
        return [bin_idx for bin_idx, count in self._histogram.items()
                if count / total < self._rarity_threshold]

    def get_stats(self) -> dict:
        return {
            "observations": self._total,
            "detections": len(self._detections),
            "valid_detections": sum(1 for d in self._detections if d.get("valid")),
            "rarity_threshold": self._rarity_threshold,
        }
