"""ConvergenceDetector — Sliding window convergence detection.

Algorithm:
    observe(value):
        1. Append to history
        2. Trim to window size
        3. If window full:
           a. Compute mean of window
           b. Check if all values within threshold of mean
           c. If yes: converged = True
           d. If no: converged = False

    update(value): alias for observe()

    is_converged(): return converged flag

Complexity: O(W) where W = window size
"""
from __future__ import annotations


class ConvergenceDetector:
    """Detect convergence in a time series.

    Usage:
        cd = ConvergenceDetector(window=10, threshold=0.01)
        for value in values:
            cd.observe(value)
        if cd.is_converged():
            print("System has converged!")
    """

    def __init__(self, window: int = 10, threshold: float = 0.01):
        self._window = window
        self._threshold = threshold
        self._history: list[float] = []
        self._converged = False

    def observe(self, value: float) -> None:
        self._history.append(value)
        if len(self._history) > self._window:
            self._history = self._history[-self._window:]
        if len(self._history) >= self._window:
            avg = sum(self._history) / len(self._history)
            new_converged = all(abs(v - avg) < self._threshold for v in self._history)
            if not new_converged:
                self._converged = False
            else:
                self._converged = True

    def update(self, value: float) -> None:
        self.observe(value)

    def is_converged(self) -> bool:
        return self._converged

    def get_history(self) -> list[float]:
        return list(self._history)

    def get_stats(self) -> dict:
        return {
            "converged": self._converged,
            "history_len": len(self._history),
            "threshold": self._threshold,
            "window": self._window,
        }
