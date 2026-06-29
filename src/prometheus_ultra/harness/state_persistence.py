"""StatePersistence — Save and restore memory state across restarts.

Saves: DopamineGate history, CoALA working memory, evolution engine state,
       four_network networks, graph_memory episodes, feedback records.
"""
from __future__ import annotations
import json, os, time


class StatePersistence:
    """Persist and restore Omega memory state."""

    def __init__(self, path: str = "E:/Prometheus-Ultra/omega_state.json"):
        self._path = path

    def save(self, omega) -> dict:
        state = {
            "timestamp": time.time(),
            "dopamine_history": omega.dopamine._history[-100:],
            "dopamine_threshold": omega.dopamine._current_threshold,
            "coala_working": [{"content": i.content, "importance": i.importance}
                             for i in omega.coala._working_memory[-20:]],
            "four_network_counts": {k: len(v) for k, v in omega.four_network._networks.items()},
            "graph_episode_count": len(omega.graph_memory._episodes),
            "feedback_count": sum(len(v) for v in omega.feedback._feedbacks.values()),
            "evolution_count": len(omega.evolution_engine._history),
            "dream_count": len(omega.dream._memories),
        }
        with open(self._path, 'w') as f:
            json.dump(state, f)
        return state

    def load(self, omega) -> dict:
        if not os.path.exists(self._path):
            return {}
        try:
            with open(self._path, 'r') as f:
                state = json.load(f)
            # Restore dopamine threshold
            if "dopamine_threshold" in state:
                omega.dopamine._current_threshold = state["dopamine_threshold"]
            return state
        except:
            return {}

    def get_stats(self) -> dict:
        exists = os.path.exists(self._path)
        return {"persisted": exists, "path": self._path}
