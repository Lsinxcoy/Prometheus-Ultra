"""MultiAgentSystem — Multi-agent coordination with task allocation."""
from __future__ import annotations
import time


class MultiAgentSystem:
    def __init__(self):
        self._agents: dict[str, dict] = {}
        self._tasks: list[dict] = []
        self._allocations: list[dict] = []
        self._consensus_history: list[dict] = []

    def register_agent(self, name: str, config: dict | None = None):
        cfg = config or {}
        self._agents[name] = {"capabilities": cfg.get("capabilities", []), "load": 0,
                              "tasks_completed": 0, "registered_at": time.time()}

    def allocate_task(self, task: dict, strategy: str = "least_loaded") -> str | None:
        if not self._agents:
            return None
        required_caps = set(task.get("required_capabilities", []))
        capable = {n: a for n, a in self._agents.items()
                   if not required_caps or required_caps.issubset(set(a["capabilities"]))}
        if not capable:
            capable = self._agents
        if strategy == "least_loaded":
            selected = min(capable, key=lambda n: capable[n]["load"])
        else:
            selected = list(capable.keys())[0]
        self._agents[selected]["load"] += 1
        self._allocations.append({"agent": selected, "task": task, "ts": time.time()})
        return selected

    def reach_consensus(self, proposals: list[dict]) -> dict:
        if not proposals:
            return {"consensus": None, "agreement": 0}
        from collections import Counter
        counts = Counter(str(p.get("value", "")) for p in proposals)
        total = len(proposals)
        winner = counts.most_common(1)[0][0]
        agreement = counts[winner] / total
        result = {"consensus": winner, "agreement": agreement}
        self._consensus_history.append(result)
        return result

    def get_stats(self) -> dict:
        return {"agents": len(self._agents), "tasks_allocated": len(self._allocations)}
