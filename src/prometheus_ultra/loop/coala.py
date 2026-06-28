"""CoALAArchitecture — Cognitive architecture with working/long-term memory.

Based on: "CoALA: Cognitive Architectures for Language Agents"
(arXiv:2309.02427, Sumers et al. 2023)

Key Concepts from Paper:
    1. Modular cognitive architecture: memory + action space + decision
    2. Working memory: limited capacity, active context
    3. Long-term memory: persistent storage, retrieval
    4. Action space: structured set of available actions
    5. Decision process: select actions based on memory and goals

Paper Finding:
    "CoALA provides a unifying framework for understanding and
     building language agents, enabling systematic comparison
     of different agent designs."

Algorithm:
    - Working memory: fixed-size buffer with attention-based eviction
    - Long-term memory: overflow from working memory
    - Consolidation: periodic transfer from WM to LTM
    - Retrieval: query LTM based on current context
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CognitiveItem:
    """An item in cognitive memory."""
    content: str = ""
    importance: float = 0.5
    attention: float = 0.5
    timestamp: float = 0.0
    source: str = ""
    metadata: dict = field(default_factory=dict)


class CoALAArchitecture:
    """Cognitive architecture for language agents.

    Based on CoALA paper (arXiv:2309.02427).

    Usage:
        coala = CoALAArchitecture(working_memory_size=7)

        # Add to working memory
        coala.add_to_working_memory({"content": "User asked about AI", "importance": 0.8})

        # Observe environment
        coala.observe({"attention_score": 0.9})

        # Retrieve from long-term memory
        relevant = coala.retrieve_from_ltm("AI research", top_k=3)
    """

    def __init__(self, working_memory_size: int = 7):
        """Initialize CoALA architecture.

        Args:
            working_memory_size: Maximum items in working memory (Miller's 7±2).
        """
        self._wm_size = working_memory_size
        self._working_memory: list[CognitiveItem] = []
        self._long_term_memory: list[CognitiveItem] = []
        self._attention_weights: dict[str, float] = {}
        self._consolidations = 0
        self._total_retrieved = 0

    def add_to_working_memory(self, item: dict | CognitiveItem) -> None:
        """Add an item to working memory.

        If working memory is full, the lowest-attention item is
        consolidated to long-term memory.

        Args:
            item: Dict or CognitiveItem to add.
        """
        if isinstance(item, dict):
            cognitive_item = CognitiveItem(
                content=item.get("content", ""),
                importance=item.get("importance", 0.5),
                attention=item.get("utility", item.get("attention", 0.5)),
                timestamp=time.time(),
                source=item.get("source", "direct"),
                metadata=item,
            )
        else:
            cognitive_item = item
            cognitive_item.timestamp = time.time()

        self._working_memory.append(cognitive_item)

        # Consolidate if over capacity
        if len(self._working_memory) > self._wm_size:
            self._working_memory.sort(key=lambda x: x.attention)
            evicted = self._working_memory.pop(0)
            self._long_term_memory.append(evicted)
            self._consolidations += 1

    def observe(self, data: dict | None = None) -> None:
        """Observe environment and update attention weights.

        From CoALA: "The agent's decision process depends on
        what it attends to in working memory"
        """
        if not data:
            return
        for key, value in data.items():
            if isinstance(value, (int, float)):
                old = self._attention_weights.get(key, 0.5)
                self._attention_weights[key] = old * 0.8 + value * 0.2

    def retrieve_from_ltm(self, query: str, top_k: int = 3) -> list[dict]:
        """Retrieve relevant items from long-term memory.

        From CoALA: "Long-term memory stores experiences that
        can be retrieved when relevant to current goals"
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored = []
        for item in self._long_term_memory:
            content_lower = item.content.lower()
            content_words = set(content_lower.split())

            # Score: exact match + word overlap + importance
            score = 0.0
            if query_lower in content_lower:
                score += 1.0
            overlap = query_words & content_words
            if query_words:
                score += len(overlap) / len(query_words) * 0.5
            score *= (0.5 + item.importance * 0.5)

            if score > 0.01:
                scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        self._total_retrieved += min(top_k, len(scored))

        return [{"content": item.content, "score": score, "importance": item.importance}
                for score, item in scored[:top_k]]

    def get_working_memory_contents(self) -> list[dict]:
        """Get current working memory contents."""
        return [{"content": item.content, "attention": item.attention,
                 "importance": item.importance}
                for item in self._working_memory]

    def get_ltm_size(self) -> int:
        """Get long-term memory size."""
        return len(self._long_term_memory)

    def get_stats(self) -> dict:
        return {
            "working_memory": len(self._working_memory),
            "working_memory_capacity": self._wm_size,
            "long_term_memory": len(self._long_term_memory),
            "consolidations": self._consolidations,
            "total_retrieved": self._total_retrieved,
            "attention_weights": len(self._attention_weights),
        }
