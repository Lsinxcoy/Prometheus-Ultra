"""CrashRecovery — Checkpoint creation and state recovery."""
from __future__ import annotations
import time
import hashlib


class CrashRecovery:
    def __init__(self, session=None):
        self._session = session
        self._checkpoints: list[dict] = []
        self._recoveries: list[dict] = []
        self._max_checkpoints = 10

    def create_checkpoint(self, state: dict | None = None) -> dict:
        state = state or {}
        checkpoint = {"id": len(self._checkpoints), "timestamp": time.time(),
                      "state_hash": hashlib.md5(str(state).encode()).hexdigest()[:16]}
        self._checkpoints.append(checkpoint)
        if len(self._checkpoints) > self._max_checkpoints:
            self._checkpoints = self._checkpoints[-self._max_checkpoints // 2:]
        return checkpoint

    def recover(self, context: dict | None = None) -> dict:
        ctx = context or {}
        if self._checkpoints:
            latest = self._checkpoints[-1]
            recovery = {"recovered": True, "from_checkpoint": latest["id"],
                        "checkpoint_age_s": time.time() - latest["timestamp"]}
        else:
            recovery = {"recovered": True, "from_checkpoint": None, "status": "fresh_start"}
        self._recoveries.append(recovery)
        return recovery

    def get_stats(self) -> dict:
        return {"checkpoints": len(self._checkpoints), "recoveries": len(self._recoveries)}
