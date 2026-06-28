"""AgentForest — Agent forest with specialization and performance tracking."""
from __future__ import annotations
import time


class AgentForest:
    def __init__(self):
        self._agents: dict[str, dict] = {}
        self._performance: dict[str, list[float]] = {}

    def add_agent(self, name: str, config: dict | None = None):
        cfg = config or {}
        self._agents[name] = {"capabilities": cfg.get("capabilities", []), "score": cfg.get("score", 0.5),
                              "tasks": 0, "created_at": time.time()}

    def record_performance(self, agent_name: str, score: float):
        if agent_name not in self._performance:
            self._performance[agent_name] = []
        self._performance[agent_name].append(score)
        if len(self._performance[agent_name]) > 100:
            self._performance[agent_name] = self._performance[agent_name][-50:]
        if agent_name in self._agents:
            self._agents[agent_name]["score"] = score
            self._agents[agent_name]["tasks"] += 1

    def get_best_agent(self, capability: str | None = None) -> str | None:
        candidates = {}
        for name, agent in self._agents.items():
            if capability and capability not in agent.get("capabilities", []):
                continue
            scores = self._performance.get(name, [agent["score"]])
            candidates[name] = sum(scores) / len(scores)
        return max(candidates, key=candidates.get) if candidates else None

    def get_stats(self) -> dict:
        return {"agents": len(self._agents), "ranked_agents": len(self._performance)}
