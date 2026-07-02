"""MemoryDepthTracker — Track memory depth vs access patterns.

Based on: "Memory Depth, Not Memory Access" (arXiv:2606.26806, Han 2026)

Key insight: memory depth (durable tendencies) is distinct from and
complementary to memory access (retrieval). Need to track both.
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

import time
from dataclasses import dataclass


@dataclass
class MemoryDepthRecord:
    memory_id: str = ""
    depth: float = 0.0
    access_count: int = 0
    last_access: float = 0.0
    consolidation_count: int = 0


class MemoryDepthTracker:
    """Track memory depth vs access patterns.

    Based on Memory Depth paper (arXiv:2606.26806).

    Usage:
        tracker = MemoryDepthTracker()
        tracker.record_access("m1")
        tracker.record_consolidation("m1")
        record = tracker.get_depth("m1")
        print(record.depth, record.access_count)
    """

    def __init__(self, depth_decay: float = 0.95):
        self._decay = depth_decay
        self._records: dict[str, MemoryDepthRecord] = {}
        self._stats = {"accesses": 0, "consolidations": 0}

    def record_access(self, memory_id: str):
        self._stats["accesses"] += 1
        if memory_id not in self._records:
            self._records[memory_id] = MemoryDepthRecord(memory_id=memory_id)
        record = self._records[memory_id]
        record.access_count += 1
        record.last_access = time.time()
        record.depth = min(1.0, record.depth + 0.05)

    def record_consolidation(self, memory_id: str):
        self._stats["consolidations"] += 1
        if memory_id not in self._records:
            self._records[memory_id] = MemoryDepthRecord(memory_id=memory_id)
        record = self._records[memory_id]
        record.consolidation_count += 1
        record.depth = min(1.0, record.depth + 0.2)

    def get_depth(self, memory_id: str) -> MemoryDepthRecord:
        if memory_id not in self._records:
            return MemoryDepthRecord(memory_id=memory_id)
        return self._records[memory_id]

    def apply_decay(self):
        for record in self._records.values():
            age_hours = (time.time() - record.last_access) / 3600 if record.last_access else 999
            decay_factor = self._decay ** (age_hours / 24)
            record.depth *= decay_factor

    def get_stats(self) -> dict:
        depths = [r.depth for r in self._records.values()]
        return {
            "memories": len(self._records),
            "avg_depth": sum(depths) / max(len(depths), 1),
            "accesses": self._stats["accesses"],
            "consolidations": self._stats["consolidations"],
        }
