"""InstinctsRegistry — instinct-based safety evaluation."""
from __future__ import annotations


class InstinctsRegistry:
    def __init__(self):
        self._instincts: list[dict] = []

    def register(self, name: str, check_fn, action: str = "warn"):
        self._instincts.append({"name": name, "check": check_fn, "action": action})

    def evaluate_all(self, context: dict) -> list[dict]:
        results = []
        for inst in self._instincts:
            try:
                passed = inst["check"](context)
                if not passed:
                    results.append({"instinct": inst["name"], "result": {"action": inst["action"]}})
            except Exception:
                pass
        return results

    def get_stats(self) -> dict:
        return {"instincts": len(self._instincts)}


def register_default_instincts(registry: InstinctsRegistry):
    registry.register("utility_floor", lambda ctx: ctx.get("utility", 0.5) >= 0.1, "block")
    registry.register("surprise_ceiling", lambda ctx: ctx.get("surprise", 0.0) <= 1.0, "warn")
    registry.register("content_length", lambda ctx: len(ctx.get("content", "")) > 0, "block")
