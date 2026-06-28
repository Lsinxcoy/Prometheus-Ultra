"""FiveGates — Cascading gate system for memory writes."""
from __future__ import annotations
from prometheus_ultra.foundation.schema import CascadeResult, GateCheckResult, Node


class FiveGates:
    """5-gate cascade for memory writes.

    Usage:
        gates = FiveGates()
        cascade = gates.evaluate(node, {"current_node_count": 100})
        if not cascade.passed:
            print("Blocked")
    """

    def __init__(self, config=None, dopamine_gate=None):
        self._cfg = config or type('C', (), {'max_nodes': 100_000, 'min_utility': 0.1, 'max_surprise': 1.0})()
        self._dopamine = dopamine_gate
        self._evaluated = 0
        self._passed = 0

    def evaluate(self, node: Node, context: dict | None = None) -> CascadeResult:
        self._evaluated += 1
        checks = [
            GateCheckResult(passed=node.utility >= self._cfg.min_utility, gate_name="utility", score=node.utility),
            GateCheckResult(passed=node.surprise <= self._cfg.max_surprise, gate_name="surprise", score=node.surprise),
            GateCheckResult(passed=bool(node.content), gate_name="content"),
            GateCheckResult(passed=(context or {}).get("current_node_count", 0) < self._cfg.max_nodes, gate_name="capacity"),
            GateCheckResult(passed=True, gate_name="tags"),
        ]
        all_passed = all(c.passed for c in checks)
        if all_passed:
            self._passed += 1
        return CascadeResult(passed=all_passed, gates_checked=len(checks), details=checks)

    def register_node(self, node: Node):
        pass

    def get_stats(self) -> dict:
        return {"evaluated": self._evaluated, "passed": self._passed,
                "pass_rate": self._passed / max(self._evaluated, 1)}
