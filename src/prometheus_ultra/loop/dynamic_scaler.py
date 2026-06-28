"""DynamicScaler — Resource-aware dynamic scaling."""
from __future__ import annotations
import time


class DynamicScaler:
    def __init__(self, scale_up_threshold: float = 0.8, scale_down_threshold: float = 0.3):
        self._scale_up_threshold = scale_up_threshold
        self._scale_down_threshold = scale_down_threshold
        self._scales: list[dict] = []
        self._current_scale: dict[str, float] = {"compute": 1.0, "memory": 1.0, "tokens": 1.0}
        self._load_history: list[dict] = []

    def scale(self, dimension: str, value: float):
        self._scales.append({"dimension": dimension, "value": value, "ts": time.time()})
        if len(self._scales) > 500:
            self._scales = self._scales[-250:]
        self._load_history.append({"dim": dimension, "value": value, "ts": time.time()})
        if len(self._load_history) > 100:
            self._load_history = self._load_history[-50:]
        recent = [h["value"] for h in self._load_history if h["dim"] == dimension][-10:]
        if recent:
            avg_load = sum(recent) / len(recent)
            if avg_load > self._scale_up_threshold:
                self._current_scale[dimension] = min(4.0, self._current_scale.get(dimension, 1.0) * 1.5)
            elif avg_load < self._scale_down_threshold:
                self._current_scale[dimension] = max(0.25, self._current_scale.get(dimension, 1.0) * 0.7)

    def get_stats(self) -> dict:
        return {"scale_events": len(self._scales), "current_scales": dict(self._current_scale)}
