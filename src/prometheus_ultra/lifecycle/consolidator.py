"""ConsolidationEngine — Memory consolidation with importance-based processing.

基于:
- "Sleep-Dependent Memory Consolidation" (Diekelmann & Born, 2010) + Omega记忆整合
  - 强度计算: importance × 0.1 + min(access × 0.01, 0.2)
  - 强化: strength > 0 → 加强记忆
  - 整合: importance >= strength_threshold → 整合
  - 修剪: importance < prune_threshold → 标记修剪

算法:
    run(memories):
        1. 对每个记忆计算strength
        2. strength > 0 → strengthen计数+1
        3. importance >= 0.3 → consolidate计数+1
        4. importance < 0.1 → prune计数+1

来源: Omega系统 consolidation 记忆整合引擎 + lifecycle/consolidation_engine.py
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)



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
        self._pending_memories: list[dict] = []

    def add_memory(self, memory: dict):
        self._pending_memories.append(memory)

    def run(self, memories: list | None = None) -> dict:
        self._runs += 1

        mems = memories or self._pending_memories
        if not mems:
            return {"processed": 0, "consolidated": 0, "pruned": 0, "strengthened": 0}

        for mem in mems:
            importance = mem.get("importance", 0.5)
            access = mem.get("access_count", 0)
            strength = importance * 0.1 + min(access * 0.01, 0.2)
            if strength > 0:
                self._strengthened += 1
            if importance >= self._strength_threshold:
                self._consolidated += 1
        for mem in mems:
            if mem.get("importance", 0.5) < self._prune_threshold:
                self._pruned += 1

        processed = len(mems)
        if not memories:
            self._pending_memories = [
                m for m in self._pending_memories
                if m.get("importance", 0.5) >= self._prune_threshold
            ]

        return {
            "processed": processed,
            "consolidated": sum(1 for m in mems if m.get("importance", 0.5) >= self._strength_threshold),
            "pruned": sum(1 for m in mems if m.get("importance", 0.5) < self._prune_threshold),
            "strengthened": sum(1 for m in mems if m.get("importance", 0.5) * 0.1 + min(m.get("access_count", 0) * 0.01, 0.2) > 0),
        }

    def consolidate(self, memories: list | None = None) -> dict:
        return self.run(memories)

    def get_stats(self) -> dict:
        return {
            "runs": self._runs,
            "consolidated": self._consolidated,
            "strengthened": self._strengthened,
            "pruned": self._pruned,
            "pending": len(self._pending_memories),
        }
