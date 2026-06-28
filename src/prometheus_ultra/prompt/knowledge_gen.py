"""KnowledgeGenerator — Knowledge synthesis from context."""
from __future__ import annotations


class KnowledgeGenerator:
    def __init__(self):
        self._facts: list[dict] = []
        self._relations: list[dict] = []

    def generate(self, context: dict | None = None) -> dict:
        ctx = context or {}
        new_facts = []
        if "query" in ctx:
            words = ctx["query"].split()
            for i in range(len(words) - 2):
                if words[i + 1].lower() in ("is", "are", "has", "have", "does"):
                    fact = {"subject": words[i], "predicate": words[i + 1], "object": " ".join(words[i + 2:])}
                    new_facts.append(fact)
                    self._facts.append(fact)
        if "results" in ctx and isinstance(ctx["results"], int):
            for i in range(min(ctx["results"], 5)):
                rel = {"source": ctx.get("source", ""), "target": ctx.get("query", ""), "type": "learned_from"}
                self._relations.append(rel)
        return {"generated": True, "new_facts": len(new_facts), "total_facts": len(self._facts)}

    def get_stats(self) -> dict:
        return {"facts": len(self._facts), "relations": len(self._relations)}
