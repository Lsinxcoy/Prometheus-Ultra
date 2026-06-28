"""DispositionLearner — Behavioral disposition learning from value patterns.

Architecture:
    Track value distributions per pattern key.
    Compute running statistics (mean, variance, skewness).
    Detect disposition shifts (mean change > threshold).
    Learn behavioral dispositions for prediction.

Algorithm:
    For each pattern_key:
        1. Append value to history
        2. Compute running mean and variance (Welford's algorithm)
        3. Detect shifts: |new_mean - old_mean| > threshold
        4. Predict: return current mean disposition

    Disposition = average behavioral tendency for a pattern.
    Shift detection usesCUSUM-like mechanism.

Complexity:
    learn(): O(1) amortized
    get_disposition(): O(1)
    get_variance(): O(N) where N = values for pattern
    detect_shifts(): O(N)

Edge Cases:
    - Single value: variance = 0
    - All identical values: no shifts detected
    - Very long history: truncated to max_values
"""
from __future__ import annotations

import math
import time
from collections import defaultdict


class DispositionLearner:
    """Behavioral disposition learning.

    Usage:
        learner = DispositionLearner()
        learner.learn("response_quality", 0.8)
        learner.learn("response_quality", 0.9)
        learner.learn("response_quality", 0.3)  # shift!

        disp = learner.get_disposition("response_quality")
        shifts = learner.detect_shifts("response_quality")
    """

    def __init__(self, max_values: int = 100, shift_threshold: float = 0.1):
        """Initialize the disposition learner.

        Args:
            max_values: Maximum values to track per pattern.
            shift_threshold: Threshold for detecting disposition shifts.
        """
        self._max_values = max_values
        self._shift_threshold = shift_threshold
        self._values: dict[str, list[float]] = defaultdict(list)
        self._means: dict[str, float] = {}
        self._variances: dict[str, float] = {}
        self._shifts: dict[str, int] = defaultdict(int)
        self._shift_history: dict[str, list[dict]] = defaultdict(list)

    def learn(self, pattern_key: str, value: float) -> None:
        """Record a value for a behavioral pattern.

        Args:
            pattern_key: Pattern identifier (e.g., "response_quality").
            value: Observed value [0, 1].
        """
        values = self._values[pattern_key]
        old_mean = self._means.get(pattern_key, value)

        values.append(value)
        if len(values) > self._max_values:
            values[:] = values[-self._max_values // 2:]

        # Update running statistics
        new_mean = sum(values) / len(values)
        self._means[pattern_key] = new_mean

        if len(values) >= 2:
            variance = sum((v - new_mean) ** 2 for v in values) / len(values)
            self._variances[pattern_key] = variance

        # Detect shift
        if abs(new_mean - old_mean) > self._shift_threshold:
            self._shifts[pattern_key] += 1
            self._shift_history[pattern_key].append({
                "old_mean": old_mean,
                "new_mean": new_mean,
                "delta": new_mean - old_mean,
                "timestamp": time.time(),
            })

    def get_disposition(self, pattern_key: str) -> float:
        """Get current mean disposition for a pattern."""
        return self._means.get(pattern_key, 0.5)

    def get_variance(self, pattern_key: str) -> float:
        """Get variance of values for a pattern."""
        return self._variances.get(pattern_key, 0.0)

    def get_std(self, pattern_key: str) -> float:
        """Get standard deviation for a pattern."""
        return math.sqrt(self._variances.get(pattern_key, 0.0))

    def get_shift_count(self, pattern_key: str) -> int:
        """Get number of disposition shifts detected."""
        return self._shifts.get(pattern_key, 0)

    def get_shift_history(self, pattern_key: str) -> list[dict]:
        """Get shift history for a pattern."""
        return self._shift_history.get(pattern_key, [])

    def detect_shifts(self, pattern_key: str) -> list[dict]:
        """Detect all shifts for a pattern."""
        return self._shift_history.get(pattern_key, [])

    def get_all_dispositions(self) -> dict[str, float]:
        """Get dispositions for all patterns."""
        return dict(self._means)

    def get_most_volatile(self, top_k: int = 5) -> list[dict]:
        """Get patterns with highest variance (most volatile)."""
        ranked = sorted(self._variances.items(), key=lambda x: x[1], reverse=True)
        return [{"pattern": k, "variance": v, "std": math.sqrt(v)}
                for k, v in ranked[:top_k]]

    def get_most_stable(self, top_k: int = 5) -> list[dict]:
        """Get patterns with lowest variance (most stable)."""
        ranked = sorted(self._variances.items(), key=lambda x: x[1])
        return [{"pattern": k, "variance": v, "std": math.sqrt(v)}
                for k, v in ranked[:top_k]]

    def predict(self, pattern_key: str) -> dict:
        """Predict next value based on disposition and trend."""
        values = self._values.get(pattern_key, [])
        if len(values) < 2:
            return {"prediction": self.get_disposition(pattern_key), "confidence": 0.3}

        # Simple linear trend
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        den = sum((i - x_mean) ** 2 for i in range(n))
        slope = num / den if den != 0 else 0

        prediction = values[-1] + slope
        confidence = min(1.0, n / 20)  # More data = more confidence

        return {"prediction": max(0.0, min(1.0, prediction)), "confidence": confidence,
                "trend": "increasing" if slope > 0.01 else "decreasing" if slope < -0.01 else "stable"}

    def get_stats(self) -> dict:
        total_values = sum(len(v) for v in self._values.values())
        return {
            "patterns": len(self._values),
            "total_values": total_values,
            "total_shifts": sum(self._shifts.values()),
            "avg_variance": sum(self._variances.values()) / max(len(self._variances), 1),
        }
