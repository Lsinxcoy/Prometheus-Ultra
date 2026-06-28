"""SkillRegistry + Curator + SkillClaw — Skill system."""
from __future__ import annotations
import time


class SkillRegistry:
    def __init__(self):
        self._skills: list[dict] = []
        self._skill_map: dict[str, dict] = {}

    def register(self, skill) -> dict:
        name = getattr(skill, 'name', f'skill_{len(self._skills)}')
        version = self._skill_map.get(name, {}).get("version", 0) + 1
        entry = {"name": name, "version": version, "registered_at": time.time(),
                 "tags": getattr(skill, 'tags', []), "status": "active"}
        self._skills.append(entry)
        self._skill_map[name] = entry
        return entry

    def get_skill(self, name: str) -> dict | None:
        return self._skill_map.get(name)

    def get_active_skills(self) -> list[dict]:
        return [s for s in self._skills if s["status"] == "active"]

    def get_stats(self) -> dict:
        return {"total_skills": len(self._skills), "active": len(self.get_active_skills())}


class Curator:
    def __init__(self, registry=None):
        self._registry = registry
        self._evaluations: list[dict] = []

    def evaluate(self, skill) -> dict:
        name = getattr(skill, 'name', 'unknown')
        content = getattr(skill, 'content', '')
        existing_names = set()
        if self._registry and hasattr(self._registry, '_skills'):
            existing_names = {s.get("name", "") for s in self._registry._skills}
        criteria = {"novelty": 0.8 if name not in existing_names else 0.3,
                    "utility": min(1.0, len(content.split()) / 20) if content else 0.2,
                    "correctness": 0.7, "composability": 0.6 if len(content.split()) > 5 else 0.3}
        weights = {"novelty": 0.3, "utility": 0.3, "correctness": 0.25, "composability": 0.15}
        quality = sum(criteria[k] * weights[k] for k in weights)
        result = {"name": name, "quality": quality, "criteria": criteria}
        self._evaluations.append(result)
        return result

    def get_stats(self) -> dict:
        return {"evaluations": len(self._evaluations)}


class SkillClaw:
    def __init__(self):
        self._routes: list[dict] = []
        self._skill_registry: dict[str, dict] = {}
        self._route_stats: dict[str, int] = {}

    def register_skill(self, name: str, keywords: list[str] | None = None, category: str = "general"):
        self._skill_registry[name] = {"keywords": keywords or [], "category": category, "usage_count": 0}

    def route(self, query: str) -> dict:
        query_lower = query.lower()
        query_words = set(query_lower.split())
        best_skill, best_score = None, 0.0
        for name, skill in self._skill_registry.items():
            score = len(query_words & set(skill["keywords"])) / max(len(skill["keywords"]), 1) * 0.6
            if skill["category"].lower() in query_lower:
                score += 0.3
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
        return {"routes": len(self._routes), "skills_registered": len(self._skill_registry)}
