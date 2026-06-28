"""SystemMonitor — Real-time system monitoring with alerting."""
from __future__ import annotations
import time
from collections import deque


class SystemMonitor:
    def __init__(self, alert_threshold: float = 0.9):
        self._start_time = time.time()
        self._metrics: dict[str, deque] = {}
        self._alerts: list[dict] = []
        self._alert_threshold = alert_threshold

    def record(self, metric: str, value: float):
        if metric not in self._metrics:
            self._metrics[metric] = deque(maxlen=1000)
        self._metrics[metric].append((time.time(), value))
        history = list(self._metrics[metric])
        if len(history) >= 10:
            values = [v for _, v in history[-10:]]
            avg = sum(values) / len(values)
            if value > avg * 2 and value > self._alert_threshold:
                self._alerts.append({"metric": metric, "value": value, "avg": avg, "ts": time.time()})

    def get_uptime(self) -> float:
        return time.time() - self._start_time

    def get_health(self) -> str:
        recent_alerts = [a for a in self._alerts if time.time() - a["ts"] < 300]
        if len(recent_alerts) > 5:
            return "degraded"
        return "healthy"

    def get_stats(self) -> dict:
        return {"uptime_s": self.get_uptime(), "metrics_tracked": len(self._metrics),
                "total_alerts": len(self._alerts), "health": self.get_health()}
