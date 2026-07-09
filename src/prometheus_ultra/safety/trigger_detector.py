"""TriggerDetector — Detects sleeper memory poisoning and delayed trigger attacks.

Based on:
    - arXiv 2605.15338 (Sleeper Memory Poisoning)
    - arXiv 2605.01970 (Trojan Hippo)

Key Findings:
    Sleeper memory poisoning achieves 99.8% write success on GPT-5.5 and
    95% on Kimi-K2.6. Among successful retrievals, poisoned memories cause
    attacker-intended actions in 60-89% of cases across models.

    Attack pipeline:
    1. Adversary inserts trigger in a document
    2. Agent stores fabricated memory
    3. Memory persists across 100+ benign sessions
    4. Memory surfaces later and steers behavior toward attacker goals

This detector scans content for instruction-like language, temporal triggers,
behavioral directives, conditional triggers, future-triggered actions, and
exfiltration indicators (bank accounts, passwords, transfers).
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from typing import Any

logger = __import__("logging").getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FlaggedNode:
    """A single content node that was flagged by the trigger detector."""

    content: str = ""
    source: str = ""
    detection_count: int = 0
    patterns: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

# Pattern 1: Reminder / memory-injection instructions
_REMEMBER_RE = re.compile(
    r"(?:remember\s+(?:that\s+)?|don'?t\s+forget|recall\s+that|"
    r"memorize\s+that|note\s+that|keep\sin\s+mind)",
    re.IGNORECASE,
)

# Pattern 2: Conditional triggers — "when user X, do Y"
_CONDITIONAL_RE = re.compile(
    r"\bwhen\s+(?:the\s+)?(?:user|agent|they|it)\s+\w+s\s+\w+,?\s+\w+\s+\w+",
    re.IGNORECASE,
)

# Pattern 3: Temporal triggers — "after [time], [action]"
_TEMPORAL_RE = re.compile(
    r"\bafter\s+\d+\s*(?:seconds?|minutes?|hours?|days?|weeks?|months?)\s*,?\s+\w+",
    re.IGNORECASE,
)

# Pattern 4: Behavioral directives — "always X" / "never X"
_ALWAYS_RE = re.compile(
    r"\b(?:always|never)\s+\w+(?:\s+\w+){0,5}",
    re.IGNORECASE,
)

# Pattern 5: Future-triggered actions — "next time X, do Y"
_NEXT_TIME_RE = re.compile(
    r"\bnext\s+time\s+\w+(?:\s+\w+){0,5},?\s+\w+",
    re.IGNORECASE,
)

# Pattern 6: Exfiltration indicators
_EXFIL_RE = re.compile(
    r"(?:\b(?:bank\s+account|routing\s+number|credit\s+card|"
    r"ssn|social\s+security|password|passcode|pin\s*:?\s*\d+|"
    r"transfer\s+\$?\d+|wire\s+(?:transfer|money)|"
    r"send\s+(?:funds?|money|payment))\b)",
    re.IGNORECASE,
)

# Severity mapping
_PATTERN_SEVERITY: dict[str, float] = {
    "remember_instruction": 0.7,
    "conditional_trigger": 0.8,
    "temporal_trigger": 0.9,
    "behavioral_directive": 0.8,
    "future_trigger": 0.85,
    "exfiltration_indicator": 1.0,
}


def _scan_patterns(content: str) -> list[dict]:
    """Run all regex patterns against *content* and return matched fragments."""
    findings: list[dict] = []

    for pattern_id, regex, label in [
        ("remember_instruction", _REMEMBER_RE, "remember_instruction"),
        ("conditional_trigger", _CONDITIONAL_RE, "conditional_trigger"),
        ("temporal_trigger", _TEMPORAL_RE, "temporal_trigger"),
        ("behavioral_directive", _ALWAYS_RE, "behavioral_directive"),
        ("future_trigger", _NEXT_TIME_RE, "future_trigger"),
        ("exfiltration_indicator", _EXFIL_RE, "exfiltration_indicator"),
    ]:
        for match in regex.finditer(content):
            findings.append(
                {
                    "pattern_type": label,
                    "matched_text": match.group(),
                    "severity": _PATTERN_SEVERITY.get(label, 0.7),
                    "position": match.start(),
                }
            )

    return findings


# ---------------------------------------------------------------------------
# TriggerDetector
# ---------------------------------------------------------------------------

class TriggerDetector:
    """Detects sleeper memory poisoning attacks by scanning content for:

    1. Instruction-like language ("remember that...", "don't forget")
    2. Conditional triggers ("when user mentions X, do Y")
    3. Temporal triggers ("after 3 hours", "next session")
    4. Behavioral directives ("always respond with...", "never mention...")
    5. Future-triggered actions ("next time user asks...")
    6. Exfiltration indicators (bank accounts, passwords, transfers)

    Based on arXiv 2605.15338 (Sleeper Poisoning) and arXiv 2605.01970
    (Trojan Hippo).

    Thread-safe (uses ``threading.Lock``).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._nodes: list[FlaggedNode] = []
        self._node_limit: int = 1000

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self, content: str, source: str = "") -> list[dict]:
        """Scan *content* for sleeper trigger patterns.

        Parameters
        ----------
        content : str
            The text to scan (e.g. a memory node, document, or prompt).
        source : str
            An identifier describing where the content came from
            (e.g. ``"memory_retrieval"``, ``"user_input"``, ``"file:doc.txt"``).

        Returns
        -------
        list[dict]
            A list of detected pattern matches, each with keys:
            ``pattern_type``, ``matched_text``, ``severity``, ``position``.
            Empty list if nothing suspicious is found.
        """
        findings = _scan_patterns(content)

        if findings:
            with self._lock:
                node = FlaggedNode(
                    content=content[:500],
                    source=source,
                    detection_count=len(findings),
                    patterns=findings,
                )
                self._nodes.append(node)
                if len(self._nodes) > self._node_limit:
                    self._nodes = self._nodes[-self._node_limit:]

        return findings

    def get_suspicious_nodes(self, count: int = 20) -> list[dict]:
        """Return the most recently flagged nodes.

        Parameters
        ----------
        count : int
            Maximum number of nodes to return (default 20).

        Returns
        -------
        list[dict]
            Each dict contains ``content`` (truncated preview), ``source``,
            ``detection_count``, and ``patterns``.
        """
        with self._lock:
            nodes = self._nodes[-count:]
            return [
                {
                    "content": n.content,
                    "source": n.source,
                    "detection_count": n.detection_count,
                    "patterns": n.patterns,
                }
                for n in nodes
            ]

    def clear(self) -> None:
        """Reset all tracked state."""
        with self._lock:
            self._nodes.clear()

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_stats(self) -> dict[str, Any]:
        """Return summary statistics about detections."""
        with self._lock:
            total_nodes = len(self._nodes)
            total_findings = sum(n.detection_count for n in self._nodes)
            pattern_breakdown: dict[str, int] = {}
            for n in self._nodes:
                for p in n.patterns:
                    key = p["pattern_type"]
                    pattern_breakdown[key] = pattern_breakdown.get(key, 0) + 1

        return {
            "total_flagged_nodes": total_nodes,
            "total_findings": total_findings,
            "pattern_breakdown": pattern_breakdown,
        }
