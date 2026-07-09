"""SleepGate — 睡眠机制记忆巩固 (arXiv 2603.14517).

熵触发的微睡眠周期，解决 Transformer 前摄干扰问题。
论文：99.5% 检索准确率 vs 全部基线 < 18%。
"""

from __future__ import annotations
import logging
import math
import random
import threading
import time
from collections import deque

logger = logging.getLogger(__name__)


class SleepGate:
    """睡眠启发的记忆巩固机制。"""

    def __init__(self, entropy_threshold: float = 0.7, replay_count: int = 20):
        self._lock = threading.Lock()
        self._entropy_threshold = entropy_threshold
        self._replay_count = replay_count
        self._observations: deque[dict] = deque(maxlen=500)
        self._sleep_cycles = 0
        self._total_replayed = 0
        self._conflict_tags: dict[str, list[str]] = {}  # node_id -> [superseded_by]

    def observe(self, node_id: str, content: str, utility: float = 0.5) -> None:
        """记录一次记忆操作。"""
        with self._lock:
            self._observations.append({
                "node_id": node_id, "content": content[:200],
                "utility": utility, "timestamp": time.time(),
            })

    def compute_entropy(self, context_tokens: int = 0, conflict_count: int = 0) -> float:
        """计算当前上下文复杂度熵值。"""
        token_factor = min(1.0, context_tokens / 10000.0) if context_tokens > 0 else 0.3
        conflict_factor = min(1.0, conflict_count / 5.0)
        return min(1.0, token_factor * 0.6 + conflict_factor * 0.4)

    def should_sleep(self, context_tokens: int = 0, conflict_count: int = 0) -> bool:
        """判断是否触发睡眠周期。"""
        entropy = self.compute_entropy(context_tokens, conflict_count)
        return entropy >= self._entropy_threshold

    def sleep_cycle(self, context_tokens: int = 0, conflict_count: int = 0) -> dict:
        """执行一个睡眠周期。"""
        with self._lock:
            entropy_before = self.compute_entropy(context_tokens, conflict_count)
            if entropy_before < self._entropy_threshold:
                return {"replayed": 0, "consolidated": 0, "entropy_before": entropy_before,
                        "reason": "entropy_below_threshold"}

            n_available = len(self._observations)
            if n_available == 0:
                return {"replayed": 0, "consolidated": 0, "entropy_before": entropy_before,
                        "reason": "no_observations"}

            n_replay = min(self._replay_count, n_available)
            samples = random.sample(list(self._observations), n_replay)

            # 冲突感知标记：检测被新内容 supersede 的旧内容
            consolidated = 0
            for s in samples:
                for o in self._observations:
                    if o["node_id"] != s["node_id"] and o["timestamp"] > s["timestamp"]:
                        if self._check_supersession(s["content"], o["content"]):
                            self._conflict_tags.setdefault(o["node_id"], [])
                            if s["node_id"] not in self._conflict_tags[o["node_id"]]:
                                self._conflict_tags[o["node_id"]].append(s["node_id"])
                                consolidated += 1

            self._sleep_cycles += 1
            self._total_replayed += n_replay

            return {
                "replayed": n_replay,
                "consolidated": consolidated,
                "entropy_before": round(entropy_before, 4),
                "reason": "completed",
            }

    def _check_supersession(self, old_content: str, new_content: str) -> bool:
        """检查新内容是否 supersede 旧内容。"""
        old_words = set(old_content.lower().split()[:20])
        new_words = set(new_content.lower().split()[:20])
        overlap = len(old_words & new_words)
        return overlap > 3 and len(new_content) > len(old_content) * 0.8

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "sleep_cycles": self._sleep_cycles,
                "total_replayed": self._total_replayed,
                "conflict_tags": sum(len(v) for v in self._conflict_tags.values()),
                "observations": len(self._observations),
                "entropy_threshold": self._entropy_threshold,
            }
