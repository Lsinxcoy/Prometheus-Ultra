"""ExternalNotebook — 外部化私有笔记本。

在 multi-agent 场景中持久化线程安全的私有键值存储，
记录协调中建立的共享约定、符号映射、或任意状态。

参考: "From Signals to Structure" (arXiv 2607.00233) 中关于
私有笔记本架构的讨论——persistent private notebook 在有状态
interaction 中防止高容量信道下的协调崩溃。

当前实现:
- 纯 KV store（不支持论文中完整的 Lewis signaling game 框架）
- 提供 read/write/get_all_keys/clear 操作
- 线程安全（threading.Lock）
"""

from __future__ import annotations

import logging
import threading
import time

logger = logging.getLogger(__name__)


class ExternalNotebook:
    """外部化私有笔记本，持久化协调约定。"""

    def __init__(self):
        self._lock = threading.Lock()
        self._store: dict[str, str] = {}
        self._history: list[dict] = []
        self._read_count = 0
        self._write_count = 0

    def write(self, key: str, value: str) -> dict:
        """写入一条约定。"""
        with self._lock:
            old = self._store.get(key)
            self._store[key] = value
            self._write_count += 1
            self._history.append({
                "action": "write", "key": key, "old_value": old,
                "new_value": value[:50], "ts": time.time(),
            })
            return {"ack": True, "key": key}

    def read(self, key: str) -> str | None:
        """读取一条约定。"""
        with self._lock:
            self._read_count += 1
            return self._store.get(key)

    def get_all_keys(self) -> list[str]:
        with self._lock:
            return list(self._store.keys())

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._history.clear()

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "entries": len(self._store),
                "reads": self._read_count,
                "writes": self._write_count,
            }
