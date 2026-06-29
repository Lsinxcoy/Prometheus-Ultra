"""EVAF — Surprise-valence gated parametric consolidation.

Based on: "Memory Depth, Not Memory Access" (arXiv:2606.26806, Han 2026)

Key insight: memory depth (durable tendencies) vs memory access (retrieval).
EVAF selects which memories to consolidate based on surprise and valence.
Only 2-3 parametric writes per 200 events needed.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ConsolidationCandidate:
    memory_id: str = ""
    surprise: float = 0.0
    valence: float = 0.0
    score: float = 0.0
    should_consolidate: bool = False


class EVAFConsolidation:
    """Surprise-valence gated consolidation.

    Based on Memory Depth paper (arXiv:2606.26806).

    Usage:
        evaf = EVAFConsolidation(surprise_threshold=0.6, valence_threshold=0.3)
        candidate = evaf.evaluate(memory_id="m1", surprise=0.8, valence=0.5)
        if candidate.should_consolidate:
            consolidate_to_parametric(candidate)
    """

    def __init__(self, surprise_threshold: float = 0.6, valence_threshold: float = 0.3,
                 max_consolidations_per_window: int = 3, window_size: int = 200):
        self._surprise_threshold = surprise_threshold
        self._valence_threshold = valence_threshold
        self._max_per_window = max_consolidations_per_window
        self._window_size = window_size
        self._window_count = 0
        self._consolidation_count = 0
        self._stats = {"evaluated": 0, "consolidated": 0}

    def evaluate(self, memory_id: str, surprise: float, valence: float) -> ConsolidationCandidate:
        self._stats["evaluated"] += 1
        self._window_count += 1

        if self._window_count >= self._window_size:
            self._window_count = 0
            self._consolidation_count = 0

        score = surprise * 0.6 + abs(valence) * 0.4
        should_consolidate = (
            surprise >= self._surprise_threshold
            and abs(valence) >= self._valence_threshold
            and self._consolidation_count < self._max_per_window
        )

        if should_consolidate:
            self._consolidation_count += 1
            self._stats["consolidated"] += 1

        self._stats["evaluated"] += 1

        return ConsolidationCandidate(
            memory_id=memory_id,
            surprise=surprise,
            valence=valence,
            score=score,
            should_consolidate=should_consolidate,
        )

    def get_stats(self) -> dict:
        return dict(self._stats)
