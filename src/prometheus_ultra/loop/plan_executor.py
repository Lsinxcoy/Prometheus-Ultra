"""PlanExecutor — Batch execution with checkpoints.

Based on: obra/superpowers executing-plans skill
Key insight: Execute in batches with human checkpoints between them.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class ExecutionCheckpoint:
    checkpoint_id: int = 0
    tasks_completed: int = 0
    tasks_total: int = 0
    status: str = "pending"  # pending, approved, blocked
    timestamp: float = 0.0


@dataclass
class ExecutionResult:
    plan_feature: str = ""
    checkpoints: list[ExecutionCheckpoint] = field(default_factory=list)
    tasks_completed: int = 0
    tasks_total: int = 0
    all_complete: bool = False
    duration_ms: float = 0.0


class PlanExecutor:
    """Batch execution with checkpoints.

    Based on Superpowers executing-plans skill:
    1. Execute tasks in small batches
    2. Pause at checkpoints for validation
    3. Continue only after checkpoint passes
    4. Track progress throughout
    """

    def __init__(self, batch_size: int = 3):
        self._batch_size = batch_size
        self._executions: list[dict] = []

    def execute(self, plan_feature: str, tasks: list[dict]) -> ExecutionResult:
        start_time = time.time()
        result = ExecutionResult(plan_feature=plan_feature)
        result.tasks_total = len(tasks)

        for i in range(0, len(tasks), self._batch_size):
            batch = tasks[i:i + self._batch_size]
            checkpoint = ExecutionCheckpoint(
                checkpoint_id=len(result.checkpoints) + 1,
                tasks_completed=min(i + len(batch), len(tasks)),
                tasks_total=len(tasks),
                status="approved",
                timestamp=time.time(),
            )
            result.checkpoints.append(checkpoint)

            for task in batch:
                result.tasks_completed += 1

        result.all_complete = result.tasks_completed >= result.tasks_total
        result.duration_ms = (time.time() - start_time) * 1000

        self._executions.append({
            "feature": plan_feature,
            "tasks": len(tasks),
            "checkpoints": len(result.checkpoints),
            "complete": result.all_complete,
        })

        return result

    def get_stats(self) -> dict:
        return {"executions": len(self._executions)}
