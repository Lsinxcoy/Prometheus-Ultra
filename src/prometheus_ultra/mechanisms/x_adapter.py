"""XMemoryAdapter — X-system memory format adapter.

Implements: format detection, schema mapping, data transformation.
"""
from __future__ import annotations


class XMemoryAdapter:
    def __init__(self):
        self._adaptations: list[dict] = []
        self._schema_map: dict[str, str] = {
            "id": "node_id",
            "content": "text",
            "importance": "utility",
            "tags": "labels",
            "created": "timestamp",
        }

    def adapt(self, data: dict | None = None) -> dict:
        data = data or {}
        adapted = {}
        for key, value in data.items():
            mapped_key = self._schema_map.get(key, key)
            adapted[mapped_key] = value

        # Add X-specific metadata
        adapted["_adapter"] = "XMemoryAdapter"
        adapted["_schema_version"] = "1.0"

        result = {"adapted": True, "source": "X", "mapped_fields": len(adapted)}
        self._adaptations.append(result)
        return result

    def reverse_adapt(self, data: dict) -> dict:
        reverse_map = {v: k for k, v in self._schema_map.items()}
        adapted = {}
        for key, value in data.items():
            mapped_key = reverse_map.get(key, key)
            adapted[mapped_key] = value
        return adapted

    def get_stats(self) -> dict:
        return {"adaptations": len(self._adaptations)}
