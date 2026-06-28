"""ZScoreAnomaly — Streaming anomaly detection with Welford's algorithm."""
from __future__ import annotations
import math


class ZScoreAnomaly:
    def __init__(self, threshold: float = 3.0, window: int = 200):
        self._threshold = threshold
        self._window = window
        self._values: list[float] = []
        self._n = 0
        self._mean = 0.0
        self._m2 = 0.0
        self._anomalies: list[dict] = []

    def observe(self, value: float):
        self._values.append(value)
        if len(self._values) > self._window:
            self._values = self._values[-self._window:]
        self._n += 1
        delta = value - self._mean
        self._mean += delta / self._n
        delta2 = value - self._mean
        self._m2 += delta * delta2

    def detect(self) -> list[float]:
        if self._n < 10:
            return []
        variance = self._m2 / self._n
        std = math.sqrt(variance) if variance > 0 else 0.0
        if std == 0:
            return []
        anomalies = []
        for v in self._values[-20:]:
            z = abs((v - self._mean) / std)
            if z > self._threshold:
                anomalies.append(v)
                self._anomalies.append({"value": v, "z_score": z})
        return anomalies

    def get_stats(self) -> dict:
        variance = self._m2 / self._n if self._n > 0 else 0
        return {"n": self._n, "mean": self._mean, "std": math.sqrt(variance) if variance > 0 else 0,
                "threshold": self._threshold, "total_anomalies": len(self._anomalies)}
