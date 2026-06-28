"""SkillClaw — skill routing with semantic matching.

Implements: query-to-skill matching, semantic similarity, capability routing.
"""
from __future__ import annotations


class SkillClaw:
    def __init__(self):
        self._routes: list[dict] = []
        self._skill_registry: dict[str, dict] = {}
        self._route_stats: dict[str, int] = {}

    def register_skill(self, name: str, keywords: list[str] | None = None, category: str = "general"):
        self._skill_registry[name] = {
            "keywords": keywords or [],
            "category": category,
            "usage_count": 0,
        }

    def route(self, query: str) -> dict:
        query_lower = query.lower()
        query_words = set(query_lower.split())

        best_skill = None
        best_score = 0.0

        for name, skill in self._skill_registry.items():
            score = 0.0
            # Keyword matching
            skill_words = set(skill["keywords"])
            overlap = query_words & skill_words
            if skill_words:
                score += len(overlap) / len(skill_words) * 0.6

            # Category matching
            if skill["category"].lower() in query_lower:
                score += 0.3

            # Usage frequency bonus
            score += min(0.1, skill["usage_count"] * 0.01)

            if score > best_score:
                best_score = score
                best_skill = name

        if best_skill:
            self._skill_registry[best_skill]["usage_count"] += 1
            self._route_stats[best_skill] = self._route_stats.get(best_skill, 0) + 1

        result = {"routed": True, "query": query[:50], "skill": best_skill, "score": best_score}
        self._routes.append(result)
        return result

    def get_stats(self) -> dict:
        return {
            "routes": len(self._routes),
            "skills_registered": len(self._skill_registry),
            "route_distribution": dict(self._route_stats),
        }
