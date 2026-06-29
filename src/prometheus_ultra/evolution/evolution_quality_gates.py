"""EvolutionQualityGates — Quality gates for 5-step evolution loop.

Based on: MiMo Daily Learning #2.1 (五步进化循环)

Key rules from MiMo:
    - Each step must have concrete output, no skipping
    - Implementation must have verification method
    - 3 steps with no progress → stop and return current state
    - 3 consecutive identical outputs → force termination
    - Information gain = 0 → stop scanning
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class StepResult:
    step_name: str = ""
    output: str = ""
    has_progress: bool = True
    information_gain: float = 0.0
    timestamp: float = 0.0


class EvolutionQualityGates:
    """Quality gates for 5-step evolution loop.

    Based on MiMo Daily Learning System.

    Usage:
        gates = EvolutionQualityGates()

        # Before each step
        allowed, reason = gates.check_step("reasoning", step_num=3)
        if not allowed:
            print(f"Blocked: {reason}")

        # After each step
        gates.record_step("learning", output="found 3 insights", gain=0.8)

        # Check if should continue
        should_continue, reason = gates.should_continue()
    """

    def __init__(self):
        self._steps: list[StepResult] = []
        self._consecutive_no_progress = 0
        self._consecutive_zero_gain = 0
        self._consecutive_identical = 0
        self._last_output = ""
        self._stats = {"steps_taken": 0, "forced_stops": 0}

    def check_step(self, step_name: str, step_num: int,
                   max_steps: int = 5) -> tuple[bool, str]:
        """Check if a step should be allowed.

        Rules from MiMo:
        - Max steps exceeded → block
        - 3 consecutive no-progress → block
        - 3 consecutive identical outputs → block
        """
        if step_num > max_steps:
            return False, "max_steps_exceeded (%d > %d)" % (step_num, max_steps)

        if self._consecutive_no_progress >= 3:
            return False, "3_consecutive_no_progress"

        if self._consecutive_identical >= 3:
            return False, "3_consecutive_identical_outputs"

        return True, "ok"

    def record_step(self, step_name: str, output: str,
                    information_gain: float = 0.0) -> StepResult:
        """Record step result and update counters."""
        has_progress = len(output) > 10 and information_gain > 0

        result = StepResult(
            step_name=step_name,
            output=output[:200],
            has_progress=has_progress,
            information_gain=information_gain,
            timestamp=time.time(),
        )
        self._steps.append(result)
        self._stats["steps_taken"] += 1

        # Update no-progress counter
        if has_progress:
            self._consecutive_no_progress = 0
        else:
            self._consecutive_no_progress += 1

        # Update zero-gain counter
        if information_gain <= 0:
            self._consecutive_zero_gain += 1
        else:
            self._consecutive_zero_gain = 0

        # Update identical output counter
        if output[:100] == self._last_output[:100] and len(output) > 10:
            self._consecutive_identical += 1
        else:
            self._consecutive_identical = 0
        self._last_output = output

        return result

    def should_continue(self) -> tuple[bool, str]:
        """Check if the evolution loop should continue.

        From MiMo: "连续3次相同输出 → 强制终止"
        From MiMo: "信息增益 = 0 连续 2 轮 → 停止扫描"
        """
        if self._consecutive_no_progress >= 3:
            self._stats["forced_stops"] += 1
            return False, "3 consecutive steps with no progress"

        if self._consecutive_identical >= 3:
            self._stats["forced_stops"] += 1
            return False, "3 consecutive identical outputs"

        if self._consecutive_zero_gain >= 2:
            self._stats["forced_stops"] += 1
            return False, "2 consecutive rounds with zero information gain"

        return True, "ok"

    def get_stats(self) -> dict:
        return dict(self._stats)
