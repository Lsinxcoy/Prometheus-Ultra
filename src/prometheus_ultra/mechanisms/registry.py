"""MechanismRegistry + XMemoryAdapter + YBankAdapter — Mechanism system."""
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


class XMemoryAdapter:
    def __init__(self):
        self._adaptations: list[dict] = []
        self._schema_map = {"id": "node_id", "content": "text", "importance": "utility", "tags": "labels"}

    def adapt(self, data: dict | None = None) -> dict:
        data = data or {}
        adapted = {self._schema_map.get(k, k): v for k, v in data.items()}
        adapted["_adapter"] = "XMemoryAdapter"
        result = {"adapted": True, "source": "X", "mapped_fields": len(adapted)}
        self._adaptations.append(result)
        return result

    def get_stats(self) -> dict:
        return {"adaptations": len(self._adaptations)}


class YBankAdapter:
    def __init__(self):
        self._adaptations: list[dict] = []
        self._tier_map = {"working": 0, "short_term": 1, "long_term": 2, "episodic": 3, "semantic": 4, "archive": 6}

    def adapt(self, data: dict | None = None) -> dict:
        data = data or {}
        adapted = dict(data)
        utility = data.get("utility", 0.5)
        adapted["tier"] = self._tier_map["long_term"] if utility > 0.8 else self._tier_map["short_term"] if utility > 0.5 else self._tier_map["working"]
        adapted["_adapter"] = "YBankAdapter"
        result = {"adapted": True, "source": "Y", "assigned_tier": adapted["tier"]}
        self._adaptations.append(result)
        return result

    def get_stats(self) -> dict:
        return {"adaptations": len(self._adaptations)}
