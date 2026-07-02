"""MemoryStream — Real-time memory event stream with windowing.

基于:
- Kleppmann (2017) Designing Data-Intensive Applications: 不可变日志 + 滑动窗口
  - 追加日志: 事件按时间戳顺序追加, 不可修改
  - 滑动窗口: max_size限制, 超限时头部截断并同步更新计数器
  - 事件类型过滤: 按event_type快速检索, 支持recent(n, type)
  - 重要性聚合: total_importance累加, 支持avg_importance统计

算法:
    add(event_type, content, importance):
        1. 创建StreamEvent(含时间戳)
        2. 追加到stream, 更新type_counts
        3. 超过max_size→截断头部, 同步修正计数器

来源: Omega系统 memory stream 实时记忆流模块 + 数据密集型应用设计
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StreamEvent:
    """A memory stream event."""
    event_type: str = ""
    content: str = ""
    importance: float = 0.5
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class MemoryStream:
    """Real-time memory event stream.

    Usage:
        stream = MemoryStream(max_size=10000)
        stream.add("remember", "AI research finding", importance=0.8)
        stream.add("recall", "Found relevant paper", importance=0.6)

        recent = stream.recent(10)
        count = stream.get_count("remember")
        stats = stream.get_stats()
    """

    def __init__(self, max_size: int = 10000):
        """Initialize the memory stream.

        Args:
            max_size: Maximum events to keep.
        """
        self._max_size = max_size
        self._stream: list[StreamEvent] = []
        self._type_counts: dict[str, int] = {}
        self._total_importance = 0.0

    def add(self, event_type: str, content: str, importance: float = 0.5,
            metadata: dict | None = None) -> None:
        """Add an event to the stream.

        Args:
            event_type: Event category (e.g., "remember", "recall").
            content: Event content.
            importance: Importance score [0, 1].
            metadata: Additional metadata.
        """
        event = StreamEvent(
            event_type=event_type, content=content,
            importance=importance, timestamp=time.time(),
            metadata=metadata or {},
        )
        self._stream.append(event)
        self._type_counts[event_type] = self._type_counts.get(event_type, 0) + 1
        self._total_importance += importance

        # Window truncation
        if len(self._stream) > self._max_size:
            removed = self._stream[:len(self._stream) - self._max_size]
            self._stream = self._stream[-self._max_size:]
            for r in removed:
                self._type_counts[r.event_type] = self._type_counts.get(r.event_type, 0) - 1
                self._total_importance -= r.importance

    def recent(self, n: int = 10, event_type: str | None = None) -> list[dict]:
        """Get recent events.

        Args:
            n: Maximum events to return.
            event_type: Filter by event type.

        Returns:
            List of event dicts.
        """
        events = self._stream
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return [{"type": e.event_type, "content": e.content[:200],
                 "importance": e.importance, "ts": e.timestamp,
                 "metadata": e.metadata}
                for e in events[-n:]]

    def get_count(self, event_type: str | None = None) -> int:
        """Get event count.

        Args:
            event_type: If specified, count only this type.

        Returns:
            Event count.
        """
        if event_type:
            return self._type_counts.get(event_type, 0)
        return len(self._stream)

    def get_type_distribution(self) -> dict[str, int]:
        """Get event type distribution."""
        return dict(self._type_counts)

    def get_avg_importance(self) -> float:
        """Get average importance across all events."""
        return self._total_importance / max(len(self._stream), 1)

    def search_content(self, query: str, limit: int = 10) -> list[dict]:
        """Search events by content.

        Args:
            query: Search query.
            limit: Maximum results.

        Returns:
            List of matching events.
        """
        query_lower = query.lower()
        matches = []
        for e in self._stream:
            if query_lower in e.content.lower():
                matches.append({"type": e.event_type, "content": e.content[:200],
                                "importance": e.importance, "ts": e.timestamp})
        return matches[-limit:]

    def get_stats(self) -> dict:
        return {
            "stream_size": len(self._stream),
            "max_size": self._max_size,
            "type_counts": dict(self._type_counts),
            "total_events": sum(self._type_counts.values()),
            "avg_importance": self.get_avg_importance(),
        }
