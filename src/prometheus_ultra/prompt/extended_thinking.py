"""ExtendedThinking — Recursive decomposition with depth-controlled reasoning."""
from __future__ import annotations


class ExtendedThinking:
    def __init__(self, max_depth: int = 5):
        self._max_depth = max_depth
        self._thoughts: list[dict] = []

    def think(self, context: dict | None = None, depth: int = 0) -> dict:
        ctx = context or {}
        thought = {"depth": depth, "context_keys": list(ctx.keys()), "sub_thoughts": []}
        if depth >= self._max_depth:
            thought["conclusion"] = "max_depth_reached"
            self._thoughts.append(thought)
            return thought
        if "context" in ctx:
            sub_contexts = self._decompose(ctx["context"])
            for sub_ctx in sub_contexts[:3]:
                sub_thought = self.think({"context": sub_ctx, **ctx}, depth + 1)
                thought["sub_thoughts"].append(sub_thought)
        thought["conclusion"] = f"depth_{depth}_complete"
        self._thoughts.append(thought)
        return thought

    def _decompose(self, text: str) -> list[str]:
        words = text.split()
        if len(words) <= 5:
            return [text]
        chunk_size = max(3, len(words) // 3)
        return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

    def get_stats(self) -> dict:
        return {"thoughts": len(self._thoughts), "max_depth": max((t.get("depth", 0) for t in self._thoughts), default=0)}
