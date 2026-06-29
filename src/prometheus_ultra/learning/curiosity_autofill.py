"""CuriosityAutoFill — Auto-populate curiosity queue from knowledge gaps.

From MiMo: "Heartbeat检测队列空时自动补充问题"
"""
from __future__ import annotations
import time


class CuriosityAutoFill:
    """Auto-fill curiosity queue when empty or low."""
    def __init__(self, queue, knowledge_index=None):
        self._queue = queue
        self._knowledge_index = knowledge_index
        self._templates = [
            "What are the latest advances in {domain}?",
            "How does {domain} compare to alternative approaches?",
            "What are the practical limitations of {domain}?",
            "Can {domain} be combined with {other}?",
            "What open problems remain in {domain}?",
        ]

    def auto_fill(self, domains: list[str] = None, count: int = 3):
        if not domains:
            domains = ["agent memory", "LLM safety", "multi-agent coordination"]
        filled = 0
        for domain in domains:
            if filled >= count:
                break
            for tmpl in self._templates[:count - filled]:
                question = tmpl.format(domain=domain, other="other domains")
                self._queue.add(question, priority=3)
                filled += 1
        return filled

    def get_stats(self) -> dict:
        return {"queued": len(self._queue._queue)}
