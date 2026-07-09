"""ReasoningAlignmentChecker — CARA 推理对齐检测 (arXiv 2606.08457).

论文核心方法：
一致性幻觉——多 Agent 答案一致但推理路径完全不同。
CARA 指标需统计检验：检测推理路径的显著分歧。
使用 Cohen's kappa 或相似度矩阵衡量推理对齐。
"""

from __future__ import annotations
import logging
import math
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
        """检查多推理路径的对齐程度。

        Args:
            paths: [{"answer": str, "reasoning": str, "agent": str}, ...]

        Returns:
            {"cara_score": float, "aligned": bool, "disagreements": list[dict],
             "answer_consensus": float, "reasoning_divergence": float,
             "n_paths": int}
        """
        self._total += 1
        if len(paths) < 2:
            return {"cara_score": 1.0, "aligned": True, "disagreements": [],
                    "answer_consensus": 1.0, "reasoning_divergence": 0.0, "n_paths": len(paths)}

        answers = [p.get("answer", "") for p in paths]
        reasonings = [p.get("reasoning", "") for p in paths]

        # Step 1: Answer consensus — Cohen's kappa-like measure
        unique_answers = len(set(a.lower().strip() for a in answers if a))
        answer_consensus = 1.0 if unique_answers <= 1 else 1.0 / unique_answers

        # Step 2: Reasoning divergence — pairwise n-gram overlap
        if any(r for r in reasonings):
            # 提取每个推理路径的关键推理步骤
            reasoning_steps = []
            for r in reasonings:
                steps = [s.strip() for s in r.replace(".", "\n").split("\n") if s.strip()]
                reasoning_steps.append(steps[:10])  # 取前 10 个步骤

            # 计算成对相似度
            pairwise_similarities = []
            for i in range(len(reasoning_steps)):
                for j in range(i + 1, len(reasoning_steps)):
                    steps_i = set(reasoning_steps[i])
                    steps_j = set(reasoning_steps[j])
                    if not steps_i or not steps_j:
                        continue
                    jaccard = len(steps_i & steps_j) / len(steps_i | steps_j)
                    pairwise_similarities.append(jaccard)

            reasoning_divergence = 1.0 - (sum(pairwise_similarities) / max(len(pairwise_similarities), 1)) if pairwise_similarities else 1.0
        else:
            reasoning_divergence = 0.0

        # Step 3: CARA = answer consensus × (1 - reasoning divergence)
        cara_score = answer_consensus * (1.0 - reasoning_divergence)

        # Step 4: 判断是否对齐
        aligned = cara_score >= 0.5
        if not aligned:
            self._misalignments += 1

        # Step 5: 找出分歧点
        disagreements = []
        if not aligned:
            for i in range(len(paths)):
                for j in range(i + 1, len(paths)):
                    if reasoning_steps[i] and reasoning_steps[j]:
                        diff_steps = list(set(reasoning_steps[i]) - set(reasoning_steps[j]))
                        if diff_steps:
                            disagreements.append({
                                "agent_a": paths[i].get("agent", i),
                                "agent_b": paths[j].get("agent", j),
                                "shared_steps": len(set(reasoning_steps[i]) & set(reasoning_steps[j])),
                                "diff_steps": diff_steps[:3],
                            })

        result = {
            "cara_score": round(cara_score, 4),
            "aligned": aligned,
            "answer_consensus": round(answer_consensus, 4),
            "reasoning_divergence": round(reasoning_divergence, 4),
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
