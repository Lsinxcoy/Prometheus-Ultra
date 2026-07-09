"""AgentReputation — 上下文化声誉 (arXiv 2605.00073) + COOP² 合作约束 (2603.00349) + ClinicalReTrial 闭环 (2601.00290) + ConstructiveAlignment (2607.00001) + DenoiseFlow (2603.00532)."""
from __future__ import annotations
import logging, time
logger = logging.getLogger(__name__)

class AgentReputation:
    def __init__(self):
        self._reps = {}; self._cards = {}
    def record_performance(self, agent, domain, score):
        key = f"{agent}:{domain}"
        self._reps[key] = self._reps.get(key, 0.5) * 0.7 + score * 0.3
        self._cards.setdefault(agent, {})[domain] = self._reps[key]
    def get_card(self, agent, domain):
        return self._cards.get(agent, {}).get(domain, 0.5)
    def get_stats(self): return {"agents": len(self._cards)}

class CooperConstraint:
    TYPES = ["spatial", "temporal", "participant", "dependency"]
    def __init__(self):
        self._constraints = []
    def check(self, task_type, n_agents):
        for t in self.TYPES:
            if t in task_type and n_agents > 3:
                self._constraints.append({"type": t, "warning": f"Too many agents ({n_agents}) for {t}"})
        return self._constraints[-5:] if self._constraints else []
    def get_stats(self): return {"alerts": len(self._constraints)}

class ClinicalReTrial:
    def __init__(self):
        self._trials = []
    def redesign(self, protocol, failure_reason):
        improvements = {"failure_reason": failure_reason, "modifications": [f"Fix: {failure_reason}"], "success_probability": 0.05}
        self._trials.append(improvements)
        return improvements
    def get_stats(self): return {"trials": len(self._trials)}

class ConstructiveAlignment:
    def __init__(self):
        self._prefs = {}
    def update_preference(self, user, dimension, value):
        self._prefs.setdefault(user, {}).update({dimension: value})
        return {"evolving": True, "current": self._prefs[user]}
    def get_stats(self): return {"users": len(self._prefs)}

class DenoiseFlow:
    def __init__(self):
        self._sessions = []
    def process(self, workflow_steps):
        sensing = sum(1 for s in workflow_steps if not s.get("certain", True))
        regulating = min(sensing * 0.3, 0.9)
        correcting = min(sensing * 0.1, 0.5)
        result = {"status": "safe" if sensing < 3 else "needs_review", "sensing": sensing, "regulating": round(regulating, 2), "correcting": round(correcting, 2)}
        self._sessions.append(result)
        return result
    def get_stats(self): return {"sessions": len(self._sessions)}
