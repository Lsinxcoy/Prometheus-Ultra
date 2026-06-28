"""FGGVerifier — Fine-Grained Gate verification."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class FGGResult:
    passed: bool = True
    score: float = 1.0
    violations: list[str] = field(default_factory=list)


class FGGVerifier:
    """Fine-grained gate verification.

    Usage:
        v = FGGVerifier()
        result = v.verify({"context": "improve memory"})
    """

    def __init__(self):
        self._verifications = 0
        self._violations_total = 0
        self._history: list[dict] = []
        self._violation_types: dict[str, int] = {}

    def verify(self, data: dict | None = None) -> dict:
        self._verifications += 1
        data = data or {}
        context = data.get("context", "")
        violations = []

        if isinstance(context, str) and len(context) < 3:
            violations.append("context_too_short")
            self._violation_types["context_too_short"] = self._violation_types.get("context_too_short", 0) + 1
        if not context and not data.get("strategy"):
            violations.append("empty_evolution")
            self._violation_types["empty_evolution"] = self._violation_types.get("empty_evolution", 0) + 1
        if self._verifications > 100:
            violations.append("rate_limit_exceeded")
            self._violation_types["rate_limit"] = self._violation_types.get("rate_limit", 0) + 1

        self._violations_total += len(violations)
        passed = len(violations) == 0
        score = max(0.0, 1.0 - len(violations) * 0.25)
        result = {"passed": passed, "score": score, "violations": violations}
        self._history.append(result)
        return result

    def verify_compat(self, data: dict | None = None) -> dict:
        return self.verify(data)

    def get_stats(self) -> dict:
        return {
            "verifications": self._verifications,
            "total_violations": self._violations_total,
            "avg_violations": self._violations_total / max(self._verifications, 1),
            "violation_types": dict(self._violation_types),
        }
