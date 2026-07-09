"""InteractionGraph — DIG 因果交互图 (arXiv 2603.00309).
交互拓扑→错误类型映射，使失败可预测可解释。"""
from __future__ import annotations
import logging
from collections import defaultdict
logger = logging.getLogger(__name__)

class InteractionGraph:
    def __init__(self):
        self._edges: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._failures = []
    def record_interaction(self, agent_a: str, agent_b: str, success: bool = True):
        self._edges[agent_a][agent_b] += 1
        if not success:
            self._failures.append({"from": agent_a, "to": agent_b, "ts": __import__('time').time()})
    def build_graph(self, logs: list[dict]) -> dict:
        for log in logs:
            self.record_interaction(log.get("from", ""), log.get("to", ""), log.get("success", True))
        return dict(self._edges)
    def diagnose_failures(self, graph: dict = None) -> list[dict]:
        g = graph or dict(self._edges)
        diagnoses = []
        for agent, targets in g.items():
            for target, count in targets.items():
                fail_count = sum(1 for f in self._failures if f["from"] == agent and f["to"] == target)
                if fail_count > 2:
                    diagnoses.append({"agents": [agent, target], "error_type": "repeated_failure", "count": fail_count, "confidence": min(1.0, fail_count / 5)})
        return diagnoses
    def get_stats(self) -> dict:
        return {"edges": sum(len(t) for t in self._edges.values()), "failures": len(self._failures)}
