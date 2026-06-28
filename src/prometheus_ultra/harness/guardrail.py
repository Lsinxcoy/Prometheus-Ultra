"""InputGuardrail + OutputGuardrail — Content safety gates."""
from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass
class GuardrailResult:
    passed: bool = True
    reason: str = ""
    score: float = 1.0


_TOXIC_PATTERNS = [r'\b(hate|kill|die|murder)\b.*\b(you|him|her|them)\b',
                   r'\b(racist|sexist|homophobic)\b', r'\b(go\s+to\s+hell)\b']


class InputGuardrail:
    def __init__(self):
        self._checks = 0
        self._blocked = 0

    def check(self, content: str) -> GuardrailResult:
        self._checks += 1
        if not content or not content.strip():
            self._blocked += 1
            return GuardrailResult(passed=False, reason="Empty content")
        if len(content) > 1_000_000:
            self._blocked += 1
            return GuardrailResult(passed=False, reason="Content too large")
        return GuardrailResult(passed=True)

    def get_stats(self) -> dict:
        return {"checks": self._checks, "blocked": self._blocked}


class OutputGuardrail:
    def __init__(self, max_length: int = 100_000):
        self._max_length = max_length
        self._checks = 0
        self._blocked = 0
        self._violations: list[dict] = []

    def check(self, content: str) -> GuardrailResult:
        self._checks += 1
        violations = []
        if len(content) > self._max_length:
            violations.append({"check": "length"})
        for pat in _TOXIC_PATTERNS:
            if re.search(pat, content, re.IGNORECASE):
                violations.append({"check": "toxicity"})
                break
        for ch in content[:1000]:
            if ch == '\x00' or (ord(ch) < 32 and ch not in '\n\r\t'):
                violations.append({"check": "encoding"})
                break
        passed = len(violations) == 0
        score = max(0.0, 1.0 - len(violations) * 0.3)
        if not passed:
            self._blocked += 1
            self._violations.extend(violations)
        return GuardrailResult(passed=passed, score=score,
                               reason="; ".join(v["check"] for v in violations) if violations else "")

    def get_stats(self) -> dict:
        return {"checks": self._checks, "blocked": self._blocked}
