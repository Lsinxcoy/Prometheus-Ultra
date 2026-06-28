"""FiveOrganPipeline — 5-organ cognitive pipeline."""
from __future__ import annotations
import time


class FiveOrganPipeline:
    def __init__(self):
        self._executions: list[dict] = []
        self._organ_states: dict[str, dict] = {o: {"status": "idle", "processed": 0}
                                                 for o in ["perception", "processing", "memory", "decision", "action"]}

    def execute(self, data: dict | None = None) -> dict:
        data = data or {}
        start = time.time()
        organs_processed = []
        for organ_name in ["perception", "processing", "memory", "decision", "action"]:
            self._organ_states[organ_name]["status"] = "processing"
            self._organ_states[organ_name]["processed"] += 1
            self._organ_states[organ_name]["status"] = "idle"
            organs_processed.append(organ_name)
        elapsed = (time.time() - start) * 1000
        result = {"executed": True, "organs_processed": organs_processed, "elapsed_ms": elapsed}
        self._executions.append(result)
        return result

    def get_stats(self) -> dict:
        return {"executions": len(self._executions)}
