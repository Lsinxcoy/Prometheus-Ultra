"""SleepGate — 睡眠机制记忆巩固 (arXiv 2603.14517).

论文核心方法：
99.5% 检索准确率（PI depth 5），97.0%（depth 10），
全部基线 < 18%。冲突感知时序标记检测 supersession。
熵触发的微睡眠周期——监控上下文复杂度。
"""

from __future__ import annotations
import logging
import math
import random
import threading
import time
from collections import deque, Counter

logger = logging.getLogger(__name__)


class SleepGate:
    """睡眠启发的记忆巩固机制。"""

    def __init__(self, replay_count: int = 20, similarity_threshold: float = 0.4):
        self._lock = threading.Lock()
        self._replay_count = replay_count
        self._similarity_threshold = similarity_threshold
        self._observations: deque[dict] = deque(maxlen=500)
        self._conflict_tags: dict[str, list[str]] = {}
        self._sleep_cycles = 0
        self._total_replayed = 0

    def observe(self, node_id: str, content: str, utility: float = 0.5) -> None:
        with self._lock:
            self._observations.append({
                "node_id": node_id, "content": content[:200],
                "utility": utility, "timestamp": time.time(),
            })

    def compute_entropy(self, context_tokens: int = 0, conflict_count: int = 0) -> float:
        """计算上下文熵值。使用正式的信息熵公式。"""
        token_ratio = min(1.0, context_tokens / 10000.0) if context_tokens > 0 else 0.3
        conflict_ratio = min(1.0, conflict_count / 10.0)
        # 如果 token 或冲突为 0，用观测多样性作为熵源
        if context_tokens == 0 and conflict_count == 0:
            with self._lock:
                if self._observations:
                    utilities = [o["utility"] for o in self._observations]
                    c = Counter(utilities)
                    total = len(utilities)
                    entropy = -sum((cnt / total) * math.log2(cnt / total) for cnt in c.values())
                    return round(entropy / math.log2(max(len(c), 2)), 4)
        return round(token_ratio * 0.6 + conflict_ratio * 0.4, 4)

    def should_sleep(self, context_tokens: int = 0, conflict_count: int = 0) -> bool:
        entropy = self.compute_entropy(context_tokens, conflict_count)
        return entropy >= 0.7

    def sleep_cycle(self, context_tokens: int = 0, conflict_count: int = 0) -> dict:
        """执行一个睡眠周期。

        1. 计算当前熵值
        2. 如果熵值低于阈值，跳过
        3. 随机采样最近记忆进行重播
        4. 冲突感知标记：检测被新信息 supersede 的旧信息
        """
        with self._lock:
            entropy_before = self.compute_entropy(context_tokens, conflict_count)
            if entropy_before < 0.7:
                return {"replayed": 0, "consolidated": 0, "entropy_before": entropy_before,
                        "reason": "entropy_below_threshold"}

            n_available = len(self._observations)
            if n_available == 0:
                return {"replayed": 0, "consolidated": 0, "entropy_before": entropy_before,
                        "reason": "no_data"}

            # 可配置的重播数量
            if n_available < self._replay_count:
                n_replay = n_available
                samples = list(self._observations)
            else:
                n_replay = self._replay_count
                samples = random.sample(list(self._observations), n_replay)

            # 冲突感知标记：检测 supersession（新内容覆盖旧内容）
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

    def _check_supersession(self, old_text: str, new_text: str) -> bool:
        """检查新文本是否 supersede 旧文本。基于内容重叠和长度比。"""
        old_words = set(old_text.lower().split()[:20])
        new_words = set(new_text.lower().split()[:20])
        if not old_words or not new_words:
            return False
        overlap = len(old_words & new_words)
        return overlap / max(len(old_words), 1) > self._similarity_threshold and len(new_text) >= len(old_text) * 0.5

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "sleep_cycles": self._sleep_cycles,
                "total_replayed": self._total_replayed,
                "conflict_tags": sum(len(v) for v in self._conflict_tags.values()),
                "observations": len(self._observations),
            }
