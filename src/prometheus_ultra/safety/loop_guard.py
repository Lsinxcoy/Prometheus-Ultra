"""LoopGuard — Loop detection with pattern analysis."""
from __future__ import annotations
from prometheus_ultra.foundation.schema import LoopState
import time


class LoopGuard:
    def __init__(self, max_iterations: int = 100, timeout: float = 60.0, repetition_window: int = 10):
        self._max_iter = max_iterations
        self._timeout = timeout
        self._repetition_window = repetition_window
        self._iterations = 0
        self._state = LoopState.IDLE
        self._start_time = 0.0
        self._history: list[str] = []

    def start(self):
        self._iterations = 0
        self._state = LoopState.RUNNING
        self._start_time = time.time()
        self._history.clear()

    def record_action(self, action: str):
        self._history.append(action)
        if len(self._history) > self._repetition_window * 2:
            self._history = self._history[-self._repetition_window * 2:]

    def check(self) -> LoopState:
        self._iterations += 1
        if self._iterations >= self._max_iter:
            self._state = LoopState.CIRCUIT_BREAKER
            return self._state
        if time.time() - self._start_time > self._timeout:
            self._state = LoopState.CIRCUIT_BREAKER
            return self._state
        if len(self._history) >= self._repetition_window:
            window = self._history[-self._repetition_window:]
            if len(set(window)) == 1:
                self._state = LoopState.CIRCUIT_BREAKER
                return self._state
        if len(self._history) >= 6:
            last_6 = self._history[-6:]
            if last_6[0] == last_6[2] == last_6[4] and last_6[1] == last_6[3] == last_6[5] and last_6[0] != last_6[1]:
                self._state = LoopState.CIRCUIT_BREAKER
                return self._state
        self._state = LoopState.RUNNING
        return self._state

    def reset(self):
        self._iterations = 0
        self._state = LoopState.IDLE
        self._history.clear()

    def get_stats(self) -> dict:
        return {"state": self._state.value, "iterations": self._iterations}
