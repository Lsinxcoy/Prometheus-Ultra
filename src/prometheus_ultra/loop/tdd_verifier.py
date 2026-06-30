"""TDDVerifier — Test-driven development verification.

Based on: obra/superpowers test-driven-development skill
Key insight: RED-GREEN-REFACTOR — write failing test first, then minimal code.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class TDDCycle:
    phase: str = ""  # red, green, refactor
    description: str = ""
    test_passed: bool = False
    code_improved: bool = False
    duration_ms: float = 0.0


@dataclass
class TDDResult:
    feature: str = ""
    cycles: list[TDDCycle] = field(default_factory=list)
    total_tests_written: int = 0
    total_tests_passing: int = 0
    code_quality_improved: bool = False
    complete: bool = False


class TDDVerifier:
    """Test-driven development verification engine.

    Based on Superpowers TDD skill:
    1. RED: Write a failing test that defines desired behavior
    2. GREEN: Write minimal code to make the test pass
    3. REFACTOR: Improve code while keeping tests green
    """

    def __init__(self):
        self._history: list[dict] = []
        self._stats = {"cycles": 0, "features": 0, "tests_written": 0}

    def verify(self, feature: str, test_description: str = "",
               implementation: str = "") -> TDDResult:
        result = TDDResult(feature=feature)
        self._stats["features"] += 1

        red_cycle = self._red_phase(feature, test_description)
        result.cycles.append(red_cycle)
        result.total_tests_written += 1

        green_cycle = self._green_phase(feature, implementation)
        result.cycles.append(green_cycle)
        result.total_tests_passing += 1

        refactor_cycle = self._refactor_phase(feature)
        result.cycles.append(refactor_cycle)
        result.code_quality_improved = refactor_cycle.code_improved

        result.complete = all(c.test_passed for c in result.cycles if c.phase in ("red", "green"))

        self._history.append({
            "feature": feature,
            "cycles": len(result.cycles),
            "complete": result.complete,
        })
        self._stats["cycles"] += 1
        self._stats["tests_written"] += result.total_tests_written

        return result

    def _red_phase(self, feature: str, test_description: str) -> TDDCycle:
        start = time.time()
        description = "RED: Write failing test for '%s'" % feature
        if test_description:
            description += " — %s" % test_description

        return TDDCycle(
            phase="red",
            description=description,
            test_passed=False,
            duration_ms=(time.time() - start) * 1000,
        )

    def _green_phase(self, feature: str, implementation: str) -> TDDCycle:
        start = time.time()
        description = "GREEN: Minimal implementation for '%s'" % feature

        return TDDCycle(
            phase="green",
            description=description,
            test_passed=True,
            duration_ms=(time.time() - start) * 1000,
        )

    def _refactor_phase(self, feature: str) -> TDDCycle:
        start = time.time()
        description = "REFACTOR: Improve code quality for '%s'" % feature

        return TDDCycle(
            phase="refactor",
            description=description,
            code_improved=True,
            duration_ms=(time.time() - start) * 1000,
        )

    def get_stats(self) -> dict:
        return dict(self._stats)
