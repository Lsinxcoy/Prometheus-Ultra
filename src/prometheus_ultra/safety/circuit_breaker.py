"""CircuitBreaker — Circuit breaker with half-open state."""
from __future__ import annotations
import time


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, cooldown: float = 30.0, half_open_max: int = 3):
        self._failure_threshold = failure_threshold
        self._cooldown = cooldown
        self._half_open_max = half_open_max
        self._failures = 0
        self._successes = 0
        self._state = "CLOSED"
        self._last_failure_time = 0.0
        self._half_open_count = 0
        self._total_failures = 0
        self._total_successes = 0
        self._trips = 0

    def record_success(self):
        self._total_successes += 1
        if self._state == "HALF_OPEN":
            self._successes += 1
            if self._successes >= self._half_open_max:
                self._state = "CLOSED"
                self._failures = 0
                self._successes = 0
                self._half_open_count = 0
        elif self._state == "CLOSED":
            self._failures = max(0, self._failures - 1)

    def record_failure(self):
        self._total_failures += 1
        self._last_failure_time = time.time()
        if self._state == "HALF_OPEN":
            self._half_open_count += 1
            if self._half_open_count >= self._half_open_max:
                self._state = "OPEN"
                self._trips += 1
        elif self._state == "CLOSED":
            self._failures += 1
            if self._failures >= self._failure_threshold:
                self._state = "OPEN"
                self._trips += 1

    def allow_request(self) -> bool:
        if self._state == "CLOSED":
            return True
        if self._state == "OPEN":
            if time.time() - self._last_failure_time >= self._cooldown:
                self._state = "HALF_OPEN"
                self._half_open_count = 0
                self._successes = 0
                return True
            return False
        if self._state == "HALF_OPEN":
            return self._half_open_count < self._half_open_max
        return False

    def get_state(self) -> str:
        if self._state == "OPEN" and time.time() - self._last_failure_time >= self._cooldown:
            self._state = "HALF_OPEN"
        return self._state

    def get_stats(self) -> dict:
        return {"state": self.get_state(), "failures": self._failures,
                "total_failures": self._total_failures, "trips": self._trips}
