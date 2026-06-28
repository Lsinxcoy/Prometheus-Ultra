"""XMemoryAdapter — X-system memory format adapter."""
from __future__ import annotations


class XMemoryAdapter:
    def __init__(self):
        self._adaptations: list[dict] = []

    def adapt(self, data: dict | None = None) -> dict:
        result = {"adapted": True, "source": "X"}
        self._adaptations.append(result)
        return result

    def get_stats(self) -> dict:
        return {"adaptations": len(self._adaptations)}
