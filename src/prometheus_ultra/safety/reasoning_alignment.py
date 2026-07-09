"""ReasoningAlignmentChecker — CARA 推理对齐检测 (arXiv 2606.08457).

一致性幻觉：多个 Agent 答案一致但推理路径完全不同。
CARA 指标衡量推理对齐程度。
"""

from __future__ import annotations
import logging
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)


class ReasoningAlignmentChecker:
    """CARA — Consistency-Aware Reasoning Alignment。"""

    def __init__(self):
        self._checks: list[dict] = []
        self._total = 0
        self._misalignments = 0

    def check_alignment(self, paths: list[dict]) -> dict:
        """检查多推理路径的对齐程度。"""
        self._total += 1
        if len(paths) < 2:
            return {"cara_score": 1.0, "aligned": True, "disagreements": []}

        answers = [p.get("answer", "") for p in paths]
        reasonings = [p.get("reasoning", "") for p in paths]

        # 答案一致性
        unique_answers = len(set(a.lower().strip() for a in answers if a))
        answer_agreement = 1.0 if unique_answers <= 1 else 1.0 / unique_answers

        # 推理路径分歧度
        reasoning_sigs = []
        for r in reasonings:
            words = r.lower().split()[:50]
            reasoning_sigs.append(" ".join(words[:10]))

        unique_reasoning = len(set(reasoning_sigs))
        reasoning_divergence = min(1.0, unique_reasoning / max(len(reasoning_sigs), 1))

        # CARA = 答案一致但推理不同
        if answer_agreement == 1.0 and reasoning_divergence > 0.5:
            cara_score = 1.0 - reasoning_divergence
            aligned = False
            self._misalignments += 1
        else:
            cara_score = answer_agreement
            aligned = answer_agreement >= 0.5

        disagreements = []
        if not aligned:
            for i in range(len(paths)):
                for j in range(i + 1, len(paths)):
                    if reasoning_sigs[i][:20] != reasoning_sigs[j][:20]:
                        disagreements.append({
                            "agent_a": i, "agent_b": j,
                            "reasoning_a": reasonings[i][:100],
                            "reasoning_b": reasonings[j][:100],
                        })

        result = {
            "cara_score": round(cara_score, 4),
            "aligned": aligned,
            "disagreements": disagreements[:5],
            "n_paths": len(paths),
        }
        self._checks.append(result)
        return result

    def get_stats(self) -> dict:
        return {
            "total_checks": self._total,
            "misalignments": self._misalignments,
            "misalignment_rate": round(
                self._misalignments / max(self._total, 1), 4
            ),
        }
