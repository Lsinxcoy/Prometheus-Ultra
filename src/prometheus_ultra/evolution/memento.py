"""Memento — Memory-driven method evolution.

Based on: EvoAgentBench leaderboard (Memento method)
Best on: GDPVal (+66-100%), LiveCode (+27%)
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field


@dataclass
class MethodMemory:
    method_name: str = ""
    context: str = ""
    success_count: int = 0
    failure_count: int = 0
    last_used: float = 0.0
    confidence: float = 0.5


@dataclass
class EvolutionResult:
    method: str = "memento"
    improvement: float = 0.0
    cost_delta: float = 0.0
    details: str = ""


class Memento:
    """Memory-driven method evolution.

    Usage:
        memento = Memento(memory_size=100)
        result = memento.evolve(task="data validation", current_method="regex")
    """

    def __init__(self, memory_size: int = 100):
        self._memory_size = memory_size
        self._memory: list[MethodMemory] = []
        self._history: list[dict] = []

    def evolve(self, task: str, current_method: str = "",
               success: bool = True) -> EvolutionResult:
        # Update memory for current method
        existing = [m for m in self._memory if m.method_name == current_method]
        if existing:
            m = existing[0]
            if success:
                m.success_count += 1
            else:
                m.failure_count += 1
            m.confidence = m.success_count / max(m.success_count + m.failure_count, 1)
            m.last_used = time.time()
        else:
            self._memory.append(MethodMemory(
                method_name=current_method, context=task,
                success_count=1 if success else 0,
                failure_count=0 if success else 1,
                confidence=1.0 if success else 0.0,
                last_used=time.time(),
            ))

        # Select best method for this task type
        best_method = self._select_method(task)
        improvement = 0.0
        if best_method != current_method:
            improvement = 0.1

        self._history.append({"task": task, "method": current_method, "success": success})

        return EvolutionResult(
            method="memento",
            improvement=improvement,
            cost_delta=0.02,
            details="best=%s, confidence=%.2f" % (best_method, self._get_confidence(best_method)),
        )

    def _select_method(self, task: str) -> str:
        candidates = [(m.method_name, m.confidence) for m in self._memory]
        if not candidates:
            return "default"
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def _get_confidence(self, method: str) -> float:
        for m in self._memory:
            if m.method_name == method:
                return m.confidence
        return 0.0

    def get_stats(self) -> dict:
        return {"memory_size": len(self._memory), "evolutions": len(self._history)}
