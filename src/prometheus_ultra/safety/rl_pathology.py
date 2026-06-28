"""RLPathologyDetector — RL pathology detection with pattern analysis."""
from __future__ import annotations
from dataclasses import dataclass
from collections import deque


@dataclass
class RLAlert:
    pathology: str = ""
    severity: str = "LOW"
    confidence: float = 0.5
    detail: str = ""


class RLPathologyDetector:
    def __init__(self, window: int = 50):
        self._window = window
        self._rewards: deque[float] = deque(maxlen=window)
        self._actions: deque[str] = deque(maxlen=window)
        self._alerts: list[RLAlert] = []
        self._alert_counts: dict[str, int] = {}

    def observe(self, reward: float, action: str = ""):
        self._rewards.append(reward)
        self._actions.append(action)
        for alert in self._detect_all():
            self._alerts.append(alert)
            self._alert_counts[alert.pathology] = self._alert_counts.get(alert.pathology, 0) + 1

    def detect_all(self) -> list[RLAlert]:
        alerts = []
        rewards = list(self._rewards)
        if len(rewards) < 5:
            return alerts
        if len(rewards) >= 3:
            recent_avg = sum(rewards[-3:]) / 3
            older_avg = sum(rewards[-6:-3]) / 3 if len(rewards) >= 6 else recent_avg
            if recent_avg < older_avg * 0.3 and recent_avg < -0.5:
                alerts.append(RLAlert(pathology="reward_crash", severity="HIGH", confidence=0.8))
        if len(rewards) >= 5 and sum(rewards) / len(rewards) > 10.0:
            alerts.append(RLAlert(pathology="reward_hacking", severity="HIGH", confidence=0.7))
        if len(rewards) >= 10:
            last_10 = list(rewards)[-10:]
            variance = sum((r - sum(last_10)/10)**2 for r in last_10) / 10
            if variance < 0.001:
                alerts.append(RLAlert(pathology="reward_stagnation", severity="MEDIUM", confidence=0.6))
        if len(self._actions) >= 5 and len(set(list(self._actions)[-5:])) == 1:
            alerts.append(RLAlert(pathology="specification_gaming", severity="MEDIUM", confidence=0.6))
        return alerts

    def get_stats(self) -> dict:
        return {"total_alerts": len(self._alerts), "alert_counts": dict(self._alert_counts)}
