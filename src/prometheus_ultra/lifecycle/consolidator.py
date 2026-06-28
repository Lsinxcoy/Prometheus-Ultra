"""ConsolidationEngine — Memory consolidation with importance-based processing.

Algorithm:
    run(memories):
        1. For each memory, compute strength = importance × 0.1 + min(access × 0.01, 0.2)
        2. If strength > 0: strengthen
        3. If importance >= threshold: consolidate
        4. If importance < prune_threshold: mark for pruning

Complexity: O(N) where N = memories
"""
from __future__ import annotations


class ConsolidationEngine:
    """Memory consolidation engine.

    Usage:
        engine = ConsolidationEngine()
        engine.run(memories)
        stats = engine.get_stats()
    """

    def __init__(self, strength_threshold: float = 0.3, prune_threshold: float = 0.1):
        self._strength_threshold = strength_threshold
        self._prune_threshold = prune_threshold
        self._runs = 0
        self._consolidated = 0
        self._pruned = 0
        self._strengthened = 0

    def run(self, memories: list | None = None) -> None:
        """Run consolidation on memories."""
        self._runs += 1
        if not memories:
            return
        for mem in memories:
            importance = mem.get("importance", 0.5)
            access = mem.get("access_count", 0)
            strength = importance * 0.1 + min(access * 0.01, 0.2)
            if strength > 0:
                self._strengthened += 1
            if importance >= self._strength_threshold:
                self._consolidated += 1
        for mem in memories:
            if mem.get("importance", 0.5) < self._prune_threshold:
                self._pruned += 1

    def consolidate(self, memories: list | None = None) -> None:
        self.run(memories)

    def get_stats(self) -> dict:
        return {
            "runs": self._runs,
            "consolidated": self._consolidated,
            "strengthened": self._strengthened,
            "pruned": self._pruned,
        }
