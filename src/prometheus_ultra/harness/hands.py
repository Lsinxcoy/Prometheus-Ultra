"""Hands — Execution engine with retry and timeout."""
from __future__ import annotations
import time


class Hands:
    def __init__(self, max_retries: int = 3, timeout: float = 30.0):
        self._max_retries = max_retries
        self._timeout = timeout
        self._executions: list[dict] = []
        self._success_count = 0
        self._failure_count = 0

    def execute(self, action: dict | None = None, executor=None) -> dict:
        action = action or {}
        start = time.time()
        for attempt in range(self._max_retries):
            try:
                result = executor(action) if executor else self._default_execute(action)
                elapsed = (time.time() - start) * 1000
                execution = {"executed": True, "result": result, "attempts": attempt + 1, "elapsed_ms": elapsed}
                self._executions.append(execution)
                self._success_count += 1
                return execution
            except Exception as e:
                if time.time() - start > self._timeout:
                    break
        elapsed = (time.time() - start) * 1000
        execution = {"executed": False, "error": "execution_failed", "attempts": self._max_retries, "elapsed_ms": elapsed}
        self._executions.append(execution)
        self._failure_count += 1
        return execution

    def _default_execute(self, action: dict) -> dict:
        return {"status": "completed", "action_type": action.get("action", "unknown")}

    def get_stats(self) -> dict:
        return {"executions": len(self._executions), "successes": self._success_count,
                "failures": self._failure_count,
                "success_rate": self._success_count / max(self._success_count + self._failure_count, 1)}
