"""CIPEventBus — Publish-subscribe event bus with topic routing."""
from __future__ import annotations
from collections import defaultdict
import time


class CIPEventBus:
    def __init__(self):
        self._subscribers: dict[str, list] = defaultdict(list)
        self._events: list[dict] = []
        self._dead_letters: list[dict] = []
        self._delivery_count = 0

    def subscribe(self, topic: str, callback):
        self._subscribers[topic].append(callback)

    def publish(self, event: dict, topic: str = "default"):
        event["_topic"] = topic
        event["_timestamp"] = time.time()
        event["_sequence"] = len(self._events)
        self._events.append(event)
        delivered = False
        for topic_pattern, callbacks in self._subscribers.items():
            if topic_pattern == topic or topic_pattern == "*" or topic.startswith(topic_pattern):
                for cb in callbacks:
                    try:
                        cb(event)
                        self._delivery_count += 1
                        delivered = True
                    except Exception:
                        self._dead_letters.append(event)
        if not delivered and not self._subscribers:
            self._delivery_count += 1

    def get_recent(self, n: int = 10, topic: str | None = None) -> list[dict]:
        events = self._events
        if topic:
            events = [e for e in events if e.get("_topic") == topic]
        return events[-n:]

    def get_stats(self) -> dict:
        return {"events": len(self._events), "deliveries": self._delivery_count,
                "dead_letters": len(self._dead_letters)}
