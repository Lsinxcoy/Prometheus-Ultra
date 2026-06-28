"""InformationGainTracker — Shannon entropy-based information gain tracking."""
from __future__ import annotations
import math
from collections import Counter


class InformationGainTracker:
    def __init__(self, window: int = 100):
        self._window = window
        self._gains: list[dict] = []
        self._entropy_history: list[float] = []
        self._cumulative = 0.0

    def record_gain(self, source: str, value: float):
        self._gains.append({"source": source, "value": value})
        if len(self._gains) > self._window * 3:
            self._gains = self._gains[-self._window * 2:]
        self._cumulative += value
        if len(self._gains) >= 10:
            recent_values = [g["value"] for g in self._gains[-self._window:]]
            n_bins = min(10, max(3, len(recent_values) // 5))
            min_v, max_v = min(recent_values), max(recent_values)
            if max_v > min_v:
                bin_width = (max_v - min_v) / n_bins
                counts = Counter()
                for v in recent_values:
                    counts[min(int((v - min_v) / bin_width), n_bins - 1)] += 1
                total = len(recent_values)
                entropy = -sum((c / total) * math.log2(c / total) for c in counts.values() if c > 0)
                self._entropy_history.append(entropy)
                if len(self._entropy_history) > self._window:
                    self._entropy_history = self._entropy_history[-self._window:]

    def diminishing_returns(self) -> bool:
        if len(self._entropy_history) < 10:
            return False
        recent_avg = sum(self._entropy_history[-5:]) / 5
        older_avg = sum(self._entropy_history[-15:-5]) / 10 if len(self._entropy_history) >= 15 else recent_avg
        return recent_avg < older_avg * 0.5

    def get_stats(self) -> dict:
        return {"gains": len(self._gains), "cumulative": self._cumulative,
                "current_entropy": self._entropy_history[-1] if self._entropy_history else 0,
                "diminishing_returns": self.diminishing_returns()}
