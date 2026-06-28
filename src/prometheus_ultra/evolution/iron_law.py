"""VerificationIronLaw — Iron law verification for evolution claims.

Checks:
    1. Claim repetition detection
    2. Vagueness detection (maybe, perhaps, stuff)
    3. Length quality (too short = rejected)
    4. Specificity scoring
    5. Confidence computation

Algorithm:
    verify(claim):
        1. Hash claim → check repetition count
        2. If repeated > 3 times → reject (confidence=0.2)
        3. If vague words ratio > 0.3 → reject (confidence=0.3)
        4. If len < 5 → reject (confidence=0.4)
        5. Else: compute specificity + confidence

Complexity: O(1) amortized
"""
from __future__ import annotations
import hashlib
from prometheus_ultra.foundation.schema import VerificationResult


class VerificationIronLaw:
    """Verify evolution claims.

    Usage:
        law = VerificationIronLaw(strict_fuzzy_rejection=True)
        result = law.verify("improve memory retrieval algorithm")
        print(f"Passed: {result.passed}, Confidence: {result.confidence:.2f}")
    """

    def __init__(self, strict_fuzzy_rejection: bool = False):
        self._strict = strict_fuzzy_rejection
        self._verifications: list[dict] = []
        self._claims_seen: dict[str, int] = {}
        self._rejection_reasons: Counter = Counter()

    def verify(self, claim: str = "") -> VerificationResult:
        claim_hash = hashlib.md5(claim.encode()).hexdigest()[:16]
        self._claims_seen[claim_hash] = self._claims_seen.get(claim_hash, 0) + 1

        # Repetition penalty
        if self._claims_seen[claim_hash] > 3:
            self._verifications.append({"claim": claim[:50], "passed": False, "reason": "repetition"})
            self._rejection_reasons["repetition"] += 1
            return VerificationResult(passed=False, reason="Claim repeated too many times", confidence=0.2)

        # Vagueness detection
        vague_words = {"something", "maybe", "perhaps", "might", "could", "stuff", "things"}
        words = set(claim.lower().split())
        vague_ratio = len(words & vague_words) / max(len(words), 1)
        if self._strict and vague_ratio > 0.3:
            self._rejection_reasons["vague"] += 1
            return VerificationResult(passed=False, reason="Claim too vague", confidence=0.3)

        # Length quality
        if len(claim.strip()) < 5:
            self._rejection_reasons["too_short"] += 1
            return VerificationResult(passed=False, reason="Claim too short", confidence=0.4)

        # Specificity scoring
        specificity = min(1.0, len(claim) / 100)
        repetition_penalty = max(0, 1.0 - (self._claims_seen[claim_hash] - 1) * 0.1)
        confidence = min(0.95, 0.5 + specificity * 0.3 + repetition_penalty * 0.15)

        self._verifications.append({"claim": claim[:50], "passed": True, "confidence": confidence})
        return VerificationResult(passed=True, reason="IronLaw verified", confidence=confidence)

    def get_stats(self) -> dict:
        passed = sum(1 for v in self._verifications if v.get("passed"))
        return {
            "verifications": len(self._verifications),
            "passed": passed,
            "pass_rate": passed / max(len(self._verifications), 1),
            "unique_claims": len(self._claims_seen),
            "rejection_reasons": dict(self._rejection_reasons),
        }


from collections import Counter
