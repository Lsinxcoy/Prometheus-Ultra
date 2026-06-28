"""MechanismRegistry — Mechanism registration and lifecycle management."""
from __future__ import annotations


class MechanismRegistry:
    def __init__(self):
        self._mechanisms: dict[str, dict] = {}
        self._enabled: set[str] = set()
        self._history: list[dict] = []

    def register(self, name: str, data: dict | None = None, dependencies: list[str] | None = None):
        entry = {"name": name, "data": data or {}, "dependencies": dependencies or [],
                 "status": "registered", "invoke_count": 0}
        self._mechanisms[name] = entry
        self._enabled.add(name)
        self._history.append({"action": "register", "name": name})

    def enable(self, name: str):
        if name in self._mechanisms:
            self._mechanisms[name]["status"] = "enabled"
            self._enabled.add(name)

    def disable(self, name: str):
        if name in self._mechanisms:
            self._mechanisms[name]["status"] = "disabled"
            self._enabled.discard(name)

    def invoke(self, name: str) -> bool:
        if name not in self._enabled:
            return False
        self._mechanisms[name]["invoke_count"] += 1
        return True

    def get_stats(self) -> dict:
        return {"registered": len(self._mechanisms), "enabled": len(self._enabled)}
