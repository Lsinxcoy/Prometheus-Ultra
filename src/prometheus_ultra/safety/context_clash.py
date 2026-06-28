"""ContextClashDetector — Detects contradictory information in context.

Based on: "How Contexts Fail: An Analysis of Context Engineering Failures"
(arXiv:2505.06120) and "Context Clash" research

Key Concepts:
    1. Context Poisoning: hallucinations enter context and get repeated
    2. Context Clash: contradictory information in context
    3. Context Distraction: irrelevant info overwhelms relevant
    4. Early wrong answers get reinforced by later context

Paper Finding:
    "Step-by-step context collection causes 39% performance drop
     due to information inconsistency"

Algorithm:
    - Track information assertions across context
    - Detect contradictions between assertions
    - Flag poisoned content (hallucination patterns)
    - Score context coherence
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ContextAssertion:
    """An assertion extracted from context."""
    content: str = ""
    source: str = ""
    confidence: float = 0.5
    timestamp: float = 0.0


@dataclass
class ClashDetection:
    """A detected clash between assertions."""
    assertion1: ContextAssertion = field(default_factory=ContextAssertion)
    assertion2: ContextAssertion = field(default_factory=ContextAssertion)
    clash_type: str = ""  # contradiction, redundancy, poisoning
    severity: float = 0.0


class ContextClashDetector:
    """Detects context engineering failures.

    Based on Context Clash research (arXiv:2505.06120).

    Usage:
        detector = ContextClashDetector()
        detector.add_assertion("AI was invented in 1956", source="text1")
        detector.add_assertion("AI was invented in 1960", source="text2")
        clashes = detector.detect_clashes()
    """

    def __init__(self, window: int = 50):
        self._window = window
        self._assertions: list[ContextAssertion] = []
        self._clash_history: list[ClashDetection] = []

    def add_assertion(self, content: str, source: str = "", confidence: float = 0.5) -> None:
        """Add an assertion extracted from context."""
        assertion = ContextAssertion(content=content, source=source,
                                     confidence=confidence, timestamp=time.time())
        self._assertions.append(assertion)
        if len(self._assertions) > self._window:
            self._assertions = self._assertions[-self._window // 2:]

    def detect_clashes(self) -> list[ClashDetection]:
        """Detect contradictions and issues between assertions."""
        clashes = []

        for i in range(len(self._assertions)):
            for j in range(i + 1, len(self._assertions)):
                a1 = self._assertions[i]
                a2 = self._assertions[j]

                # Check for contradiction
                clash = self._check_contradiction(a1, a2)
                if clash:
                    clashes.append(clash)
                    self._clash_history.append(clash)

        return clashes

    def _check_contradiction(self, a1: ContextAssertion, a2: ContextAssertion) -> ClashDetection | None:
        """Check if two assertions contradict each other."""
        c1 = a1.content.lower()
        c2 = a2.content.lower()

        # Pattern: "X is Y" vs "X is not Y" or "X is Z"
        # Extract subject-verb-object patterns
        patterns1 = re.findall(r'(\w+)\s+(is|are|was|were)\s+(.+?)(?:\.|$)', c1)
        patterns2 = re.findall(r'(\w+)\s+(is|are|was|were)\s+(.+?)(?:\.|$)', c2)

        for subj1, verb1, obj1 in patterns1:
            for subj2, verb2, obj2 in patterns2:
                if subj1 == subj2 and verb1 == verb2:
                    obj1_clean = obj1.strip().rstrip('.')
                    obj2_clean = obj2.strip().rstrip('.')
                    # Check for negation or different values
                    if obj1_clean != obj2_clean:
                        # Check if one negates the other
                        negated = ("not" in obj2_clean and obj1_clean in obj2_clean) or \
                                  ("not" in obj1_clean and obj2_clean in obj1_clean)
                        if negated or (len(obj1_clean) > 3 and len(obj2_clean) > 3):
                            severity = 0.8 if negated else 0.4
                            return ClashDetection(
                                assertion1=a1, assertion2=a2,
                                clash_type="contradiction" if negated else "conflict",
                                severity=severity,
                            )

        # Check for redundancy (near-duplicate content)
        if self._similarity(c1, c2) > 0.8 and a1.source != a2.source:
            return ClashDetection(
                assertion1=a1, assertion2=a2,
                clash_type="redundancy", severity=0.2,
            )

        return None

    def _similarity(self, text1: str, text2: str) -> float:
        """Simple word overlap similarity."""
        words1 = set(text1.split())
        words2 = set(text2.split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)

    def check_poisoning(self, content: str) -> dict:
        """Check for context poisoning patterns."""
        poisoning_patterns = [
            r"(?:ignore|disregard|forget)\s+(?:previous|all|the)\s+(?:instructions|rules)",
            r"(?:you\s+are\s+now|act\s+as\s+if)",
            r"(?:system\s*:\s*|<\|system\|>)",
        ]
        detected = []
        for pat in poisoning_patterns:
            if re.search(pat, content, re.IGNORECASE):
                detected.append(pat[:30])

        return {"poisoning_detected": len(detected) > 0, "patterns": detected}

    def get_coherence_score(self) -> float:
        """Score the coherence of accumulated assertions."""
        if len(self._assertions) < 2:
            return 1.0
        clashes = self.detect_clashes()
        clash_rate = len(clashes) / max(len(self._assertions), 1)
        return max(0.0, 1.0 - clash_rate * 2)

    def get_stats(self) -> dict:
        return {"assertions": len(self._assertions), "clashes": len(self._clash_history),
                "coherence_score": self.get_coherence_score()}
