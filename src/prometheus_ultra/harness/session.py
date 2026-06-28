"""Session — Session lifecycle management."""
from __future__ import annotations
import time


class Session:
    def __init__(self, idle_timeout: float = 3600.0):
        self._idle_timeout = idle_timeout
        self._sessions: list[dict] = []
        self._active: dict[str, dict] = {}

    def create(self, name: str) -> dict:
        now = time.time()
        session = {"name": name, "created_at": now, "last_accessed": now, "state": "active", "operations": 0}
        self._sessions.append(session)
        self._active[name] = session
        return session

    def access(self, name: str):
        if name in self._active:
            self._active[name]["last_accessed"] = time.time()
            self._active[name]["operations"] += 1

    def expire_idle(self) -> int:
        now = time.time()
        expired = 0
        for name, session in list(self._active.items()):
            if now - session["last_accessed"] > self._idle_timeout:
                session["state"] = "expired"
                del self._active[name]
                expired += 1
        return expired

    def get_stats(self) -> dict:
        return {"total_sessions": len(self._sessions), "active_sessions": len(self._active)}
