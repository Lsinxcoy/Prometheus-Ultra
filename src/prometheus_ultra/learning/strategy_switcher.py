"""Self-Observation 增强 — 高熵态策略切换 (arXiv 2601.00514).

"aha moment" 是幻觉，mid-reasoning shift 仅 6.31%。
高熵态才触发策略切换，不是自我洞察。
"""

from __future__ import annotations
import logging
import math
import random
from collections import Counter

logger = logging.getLogger(__name__)


def compute_strategy_entropy(actions: list[str]) -> float:
    """计算动作序列的熵值。高熵=不确定性高=应该切换策略。"""
    if not actions:
        return 0.0
    c = Counter(actions)
    total = len(actions)
    entropy = -sum((count / total) * math.log2(count / total) for count in c.values())
    return round(entropy / math.log2(max(len(c), 2)), 4)


def should_switch_strategy(recent_actions: list[str],
                           success_rate: float = 0.0,
                           entropy_threshold: float = 0.7) -> dict:
    """判断是否应该切换策略。

    论文依据 (arXiv 2601.00514):
    - Natural mid-reasoning shifts are rare (6.31%) and don't improve accuracy
    - Forced shifts at high entropy DO help
    """
    entropy = compute_strategy_entropy(recent_actions)
    if entropy >= entropy_threshold and success_rate < 0.5:
        return {
            "switch": True,
            "entropy": entropy,
            "reason": f"High entropy ({entropy}) + low success ({success_rate})",
        }
    return {
        "switch": False,
        "entropy": entropy,
        "reason": f"Entropy {entropy} < threshold {entropy_threshold}",
    }
