"""ExplorationQuota — Hardcoded daily exploration limits.

From MiMo: "每日探索上限20轮，第10轮后必须插入修订轮"
"""
from __future__ import annotations
import time


class ExplorationQuota:
    """Enforce daily exploration limits with revision rounds."""
    def __init__(self, max_daily: int = 20, revision_after: int = 10):
        self._max_daily = max_daily
        self._revision_after = revision_after
        self._today_count = 0
        self._last_date = ""

    def _check_date(self):
        today = time.strftime('%Y-%m-%d')
        if today != self._last_date:
            self._today_count = 0
            self._last_date = today

    def can_explore(self) -> tuple[bool, str]:
        self._check_date()
        if self._today_count >= self._max_daily:
            return False, "daily_limit_reached (%d/%d)" % (self._today_count, self._max_daily)
        if self._today_count == self._revision_after:
            return False, "revision_round_required"
        return True, "ok"

    def record_round(self):
        self._today_count += 1

    def needs_revision(self) -> bool:
        self._check_date()
        return self._today_count == self._revision_after

    def get_stats(self) -> dict:
        self._check_date()
        return {"today": self._today_count, "max": self._max_daily,
                "revision_after": self._revision_after}
