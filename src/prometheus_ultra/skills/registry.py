"""SkillRegistry — Skill registration and lifecycle management."""
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
