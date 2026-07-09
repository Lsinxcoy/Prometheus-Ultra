"""ReflectiveSampler — RareDxR1 反思增强推理 (arXiv 2607.00147).

RERS: 从失败路径学习，双层课程 RL。从失败路径中蒸馏知识。
"""

from __future__ import annotations
import logging
import random
from typing import Any

logger = logging.getLogger(__name__)


class ReflectiveSampler:
    """反思增强推理采样器。"""

    def __init__(self):
        self._samples: list[dict] = []
        self._total = 0

    def reflect_on_failure(self, path: dict) -> dict:
        """分析单条失败路径，提取反思。"""
        task = path.get("task", "")
        error = path.get("error", "")
        low_task = task.lower()

        # 提取反思
        reflections = []
        if "timeout" in str(error).lower():
            reflections.append("Task exceeded time limit — need faster approach")
        if "invalid" in str(error).lower() or "error" in str(error).lower():
            reflections.append("Task produced invalid output — need input validation")
        if not error and not task:
            reflections.append("Empty task or error — verify input completeness")

        if not reflections:
            reflections.append(f"Unknown failure — record for manual review")

        result = {
            "task": task[:100],
            "error": str(error)[:100],
            "reflections": reflections,
            "lessons": len(reflections),
        }
        self._samples.append(result)
        return result

    def sample_reflective(self, failure_paths: list[dict]) -> list[str]:
        """从多条失败路径中综合采样反思。"""
        all_reflections = []
        for fp in failure_paths:
            r = self.reflect_on_failure(fp)
            all_reflections.extend(r["reflections"])

        # 去重
        unique = list(set(all_reflections))
        self._total += len(failure_paths)
        return unique

    def get_stats(self) -> dict:
        return {
            "total_paths": self._total,
            "unique_reflections": len(set(
                r for s in self._samples for r in s.get("reflections", [])
            )) if self._samples else 0,
        }
