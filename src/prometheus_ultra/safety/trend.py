"""TrendPredictor — Time series trend prediction with exponential smoothing."""
from __future__ import annotations
import math


class TrendPredictor:
    def __init__(self, alpha: float = 0.3, window: int = 100):
        self._alpha = alpha
        self._window = window
        self._series: dict[str, list[float]] = {}
        self._smoothed: dict[str, float] = {}
        self._slopes: dict[str, float] = {}

    def observe(self, key: str, value: float):
        if key not in self._series:
            self._series[key] = []
        self._series[key].append(value)
        if len(self._series[key]) > self._window:
            self._series[key] = self._series[key][-self._window:]
        prev = self._smoothed.get(key, value)
        self._smoothed[key] = self._alpha * value + (1 - self._alpha) * prev
        self._update_slope(key)

    def _update_slope(self, key: str):
        vals = self._series.get(key, [])
        n = len(vals)
        if n < 3:
            self._slopes[key] = 0.0
            return
        x_mean = (n - 1) / 2
        y_mean = sum(vals) / n
        num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(vals))
        den = sum((i - x_mean) ** 2 for i in range(n))
        self._slopes[key] = num / den if den != 0 else 0.0

    def predict(self, key: str, steps: int = 1) -> float:
        vals = self._series.get(key, [])
        if not vals:
            return 0.0
        return self._smoothed.get(key, vals[-1]) + self._slopes.get(key, 0.0) * steps

    def get_stats(self) -> dict:
        return {"series_count": len(self._series), "avg_slope": sum(self._slopes.values()) / max(len(self._slopes), 1)}
