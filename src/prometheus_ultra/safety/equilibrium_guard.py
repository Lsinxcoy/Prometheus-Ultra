"""EquilibriumGuard — Multi-metric equilibrium monitoring with hysteresis."""
from __future__ import annotations
from prometheus_ultra.foundation.schema import AlertLevel


class EquilibriumGuard:
    def __init__(self, window: int = 20, hysteresis_threshold: int = 3):
        self._window = window
        self._hysteresis_threshold = hysteresis_threshold
        self._level = AlertLevel.GREEN
        self._prev_level = AlertLevel.GREEN
        self._metrics: dict[str, list[float]] = {"entropy": [], "diversity": [], "fitness_balance": []}
        self._hysteresis_counter = 0

    def get_alert_level(self) -> AlertLevel:
        return self._level

    def observe(self, metric: float, metric_name: str = "entropy"):
        if metric_name not in self._metrics:
            self._metrics[metric_name] = []
        self._metrics[metric_name].append(metric)
        if len(self._metrics[metric_name]) > self._window:
            self._metrics[metric_name] = self._metrics[metric_name][-self._window:]
        self._update_level()

    def _update_level(self):
        scores = []
        for values in self._metrics.values():
            if len(values) >= 5:
                avg = sum(values) / len(values)
                variance = sum((v - avg) ** 2 for v in values) / len(values)
                scores.append(min(1.0, variance * 4))
        if not scores:
            return
        composite = sum(scores) / len(scores)
        new_level = (AlertLevel.RED if composite > 0.8 else AlertLevel.ORANGE if composite > 0.6
                     else AlertLevel.YELLOW if composite > 0.4 else AlertLevel.GREEN)
        if new_level != self._level:
            self._hysteresis_counter += 1
            if self._hysteresis_counter >= self._hysteresis_threshold:
                self._prev_level = self._level
                self._level = new_level
                self._hysteresis_counter = 0
        else:
            self._hysteresis_counter = 0

    def get_stats(self) -> dict:
        return {"level": self._level.value, "prev_level": self._prev_level.value,
                "metrics": {k: len(v) for k, v in self._metrics.items()}}
