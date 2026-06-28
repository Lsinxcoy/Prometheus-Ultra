"""FiveOrganPipeline + DNAExtractor + ToolLoop — Organ system."""
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


class DNAExtractor:
    def __init__(self):
        self._extractions: list[dict] = []

    def extract(self, data: dict | None = None) -> dict:
        data = data or {}
        features = {}
        memories = data.get("memories", [])
        if isinstance(memories, int):
            features["memory_count"] = memories
            memories = []
        if memories:
            all_words = []
            for m in memories:
                content = m.get("content", "") if isinstance(m, dict) else ""
                all_words.extend(content.split())
            if all_words:
                features["word_diversity"] = len(set(all_words)) / max(len(all_words), 1)
        features["pattern_density"] = min(1.0, data.get("patterns", 0) / 20)
        utilities = [m.get("utility", 0.5) for m in memories if isinstance(m, dict)]
        if utilities:
            features["avg_utility"] = sum(utilities) / len(utilities)
        self._extractions.append({"features": features, "feature_count": len(features)})
        return {"extracted": True, "features": features, "feature_count": len(features)}

    def get_stats(self) -> dict:
        return {"extractions": len(self._extractions)}


class ToolLoop:
    def __init__(self, max_iterations: int = 5):
        self._max_iter = max_iterations
        self._loops: list[dict] = []

    def execute(self, action: str = "") -> dict:
        observations, thoughts, actions_taken = [], [], []
        for i in range(self._max_iter):
            observations.append({"iteration": i, "action": action, "ts": time.time()})
            should_continue = i < 2
            thoughts.append({"continue": should_continue})
            if not should_continue:
                break
            actions_taken.append({"iteration": i, "action": f"tool_{i}", "result": "success"})
        result = {"action": action, "iterations": len(observations), "completed": True}
        self._loops.append(result)
        return result

    def get_stats(self) -> dict:
        return {"loops": len(self._loops)}
