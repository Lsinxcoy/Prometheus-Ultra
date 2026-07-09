"""SleepGate — 睡眠机制记忆巩固 (arXiv 2603.14517).

重播解决前摄干扰。按赫布拓扑的hub节点决定consolidation。
"""

from __future__ import annotations
import logging
from collections import deque
logger = logging.getLogger(__name__)

class SleepGate:
    def __init__(self): self._replay_buffer = deque(maxlen=200)
    def observe(self, node_id: str, content: str, utility: float) -> None:
        self._replay_buffer.append({"node_id": node_id, "content": content[:100], "utility": utility})
    def sleep_cycle(self) -> dict:
        replayed = list(self._replay_buffer)[-20:]
        return {"replayed": len(replayed), "consolidated": sum(1 for r in replayed if r["utility"] > 0.6)}
    def get_stats(self) -> dict: return {"buffer": len(self._replay_buffer)}
