"""WAL — Write-Ahead Log for session continuity.

From MiMo Self-Evolution: "每次唤醒先写WAL确认上次做了什么"
"""
from __future__ import annotations
import time, json, os
from dataclasses import dataclass, field


@dataclass
class WALEntry:
    timestamp: float = 0.0
    source: str = ""  # user/cron/heartbeat
    status: str = "normal"
    pending: list[str] = field(default_factory=list)
    payload: dict = field(default_factory=dict)


class WriteAheadLog:
    """WAL for crash recovery and session continuity."""
    def __init__(self, path: str | None = None):
        if path is None:
            path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "wal.json")
            path = os.path.normpath(path)
        self._path = path
        self._entries: list[dict] = []
        self._load()

    def _load(self):
        if os.path.exists(self._path):
            try:
                with open(self._path, 'r') as f:
                    self._entries = json.load(f)
            except: self._entries = []

    def write(self, source: str, status: str = "normal", pending: list[str] = None, payload: dict = None):
        entry = {"ts": time.time(), "source": source, "status": status,
                 "pending": pending or [], "payload": payload or {}}
        self._entries.append(entry)
        if len(self._entries) > 200:
            self._entries = self._entries[-100:]
        self._flush()

    def _flush(self):
        parent = os.path.dirname(self._path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(self._path, 'w') as f:
            json.dump(self._entries[-50:], f)

    def last_entry(self) -> dict | None:
        return self._entries[-1] if self._entries else None

    def get_stats(self) -> dict:
        return {"entries": len(self._entries)}
