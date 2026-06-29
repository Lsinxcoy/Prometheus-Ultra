"""ExplorerState — Track exploration rounds and focus areas.

From MiMo Self-Evolution: "轮次计数/焦点领域索引"
"""
from __future__ import annotations
import time, json, os
from dataclasses import dataclass, field


@dataclass
class ExplorationRound:
    round_num: int = 0
    topic: str = ""
    domain: str = ""
    info_gain: float = 0.0
    timestamp: float = 0.0


class ExplorerState:
    """Track exploration progress and focus areas."""
    def __init__(self, path: str = "E:/Prometheus-Ultra/explorer_state.json"):
        self._path = path
        self._today_rounds: list[dict] = []
        self._domain_counts: dict[str, int] = {}
        self._total_rounds: int = 0
        self._load()

    def _load(self):
        if os.path.exists(self._path):
            try:
                with open(self._path, 'r') as f:
                    data = json.load(f)
                self._today_rounds = data.get("today", [])
                self._domain_counts = data.get("domains", {})
                self._total_rounds = data.get("total", 0)
            except: pass

    def _flush(self):
        with open(self._path, 'w') as f:
            json.dump({"today": self._today_rounds[-50:],
                       "domains": self._domain_counts,
                       "total": self._total_rounds}, f)

    def record_round(self, topic: str, domain: str, info_gain: float):
        r = {"topic": topic, "domain": domain, "gain": info_gain, "ts": time.time()}
        self._today_rounds.append(r)
        self._domain_counts[domain] = self._domain_counts.get(domain, 0) + 1
        self._total_rounds += 1
        self._flush()

    def today_count(self) -> int:
        today = time.strftime('%Y-%m-%d')
        return sum(1 for r in self._today_rounds if time.strftime('%Y-%m-%d', time.localtime(r['ts'])) == today)

    def should_insert_revision(self) -> bool:
        return self.today_count() >= 10

    def should_stop(self) -> bool:
        return self.today_count() >= 20

    def get_focus_domain(self) -> str:
        if not self._domain_counts:
            return ""
        return max(self._domain_counts, key=self._domain_counts.get)

    def reset_today(self):
        self._today_rounds = []
        self._flush()

    def get_stats(self) -> dict:
        return {"today": self.today_count(), "total": self._total_rounds,
                "domains": len(self._domain_counts)}
