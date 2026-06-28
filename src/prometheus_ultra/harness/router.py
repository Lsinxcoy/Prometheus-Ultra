"""ModelRouter — Model selection based on query complexity."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ModelConfig:
    name: str = "default"
    cost_per_1k_tokens: float = 0.01
    max_tokens: int = 4096
    avg_latency_ms: float = 100.0
    capabilities: list[str] | None = None


class ModelRouter:
    def __init__(self, models: dict | None = None):
        self._models = models or {"default": ModelConfig()}
        self._routes: list[dict] = []
        self._model_usage: dict[str, int] = {}

    def route(self, query: str, constraints: dict | None = None) -> str:
        constraints = constraints or {}
        max_cost = constraints.get("max_cost", float("inf"))
        max_latency = constraints.get("max_latency_ms", float("inf"))
        required_caps = set(constraints.get("capabilities", []))
        complexity = self._estimate_complexity(query)
        best_model, best_score = None, -1
        for name, model in self._models.items():
            model_caps = set(model.capabilities or [])
            if required_caps and not required_caps.issubset(model_caps):
                continue
            estimated_tokens = len(query.split()) * 2
            estimated_cost = model.cost_per_1k_tokens * estimated_tokens / 1000
            if estimated_cost > max_cost or model.avg_latency_ms > max_latency:
                continue
            score = model.max_tokens / max(model.cost_per_1k_tokens, 0.001) * (0.5 + complexity * 0.5)
            if score > best_score:
                best_score = score
                best_model = name
        selected = best_model or "default"
        self._routes.append({"query": query[:50], "model": selected, "complexity": complexity})
        self._model_usage[selected] = self._model_usage.get(selected, 0) + 1
        return selected

    def _estimate_complexity(self, query: str) -> float:
        words = query.split()
        length_score = min(1.0, len(words) / 50)
        tech_words = {"algorithm", "implementation", "architecture", "distributed", "optimization"}
        tech_score = min(1.0, sum(1 for w in words if w.lower() in tech_words) * 0.3)
        return min(1.0, length_score * 0.4 + tech_score * 0.4 + (0.3 if "?" in query else 0) * 0.2)

    def get_stats(self) -> dict:
        return {"routes": len(self._routes), "models": len(self._models)}
