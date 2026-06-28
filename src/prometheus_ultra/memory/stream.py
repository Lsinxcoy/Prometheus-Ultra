"""MemoryStream — Real-time memory event stream with windowing.

Architecture:
    Append-only log with timestamp and event type.
    Sliding window truncation for memory efficiency.
    Event type filtering and counting.
    Recent N retrieval with optional type filter.

Algorithm:
    add(event_type, content, importance):
        1. Create StreamEvent with timestamp
        2. Append to stream
        3. Update type counts
        4. Truncate if over max_size

    recent(n, event_type):
        1. Filter by event_type if specified
        2. Return last N events

    get_count(event_type):
        Return count for specific type or total

Complexity:
    add(): O(1) amortized
    recent(): O(n) where n = requested count
    get_count(): O(1)

Edge Cases:
    - Empty stream: returns empty list
    - Very large stream: truncated to max_size
    - Unknown event type: returns 0 count
"""
from __future__ import annotations

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
            removed = self._stream[-self._max_size // 2:]
            self._stream = self._stream[-self._max_size // 2:]
            for r in removed:
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
