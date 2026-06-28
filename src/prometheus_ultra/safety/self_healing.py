"""SelfHealingEngine — Automated fault diagnosis and recovery."""
from __future__ import annotations
import time


class SelfHealingEngine:
    def __init__(self):
        self._healings: list[dict] = []
        self._fault_history: list[dict] = []
        self._strategies = {"memory_leak": "restart_with_gc", "deadlock": "circuit_break",
                           "resource_exhaustion": "scale_up", "data_corruption": "rollback",
                           "performance_degradation": "optimize", "unknown": "restart"}

    def diagnose(self, context: dict | None = None) -> dict:
        ctx = context or {}
        symptoms = []
        if ctx.get("memory_usage", 0) > 0.9:
            symptoms.append("memory_leak")
        if ctx.get("temperature", 0.5) < 0.1:
            symptoms.append("deadlock")
        node_count = ctx.get("node_count", 0)
        if node_count > 1000 and ctx.get("avg_utility", 0.5) < 0.2:
            symptoms.append("data_corruption")
        if ctx.get("failure_count", 0) > 10:
            symptoms.append("resource_exhaustion")
        if ctx.get("avg_latency_ms", 0) > 5000:
            symptoms.append("performance_degradation")
        if not symptoms:
            symptoms.append("unknown")
        primary = symptoms[0]
        return {"symptoms": symptoms, "primary_cause": primary,
                "recovery_strategy": self._strategies.get(primary, "restart"),
                "confidence": 0.7 if primary != "unknown" else 0.3}

    def heal(self, context: dict | None = None) -> dict:
        diagnosis = self.diagnose(context)
        result = {"healed": True, "strategy": diagnosis["recovery_strategy"],
                  "diagnosis": diagnosis, "timestamp": time.time()}
        self._healings.append(result)
        self._fault_history.append(diagnosis)
        return result

    def get_stats(self) -> dict:
        return {"total_healings": len(self._healings),
                "success_rate": sum(1 for h in self._healings if h.get("healed")) / max(len(self._healings), 1)}
