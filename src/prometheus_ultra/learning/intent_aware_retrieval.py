"""IntentAwareRetrieval — SimpleMem 意向感知检索 (arXiv 2601.02553).

在检索前推断查询意图类型，根据意图选择检索策略。
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_INTENT_PATTERNS = {
    "factual": ["what is", "who is", "where is", "when did", "how many", "define", "explain"],
    "conceptual": ["how does", "why does", "what causes", "relationship between", "compare"],
    "operational": ["how to", "steps to", "procedure", "instructions", "guide", "tutorial"],
    "affective": ["i feel", "i think", "opinion", "recommend", "suggest", "prefer"],
}


class IntentAwareRetrieval:
    """检索前推断意图类型的包装器。"""

    def __init__(self, retriever: Any | None = None):
        self._retriever = retriever
        self._intent_counts: dict[str, int] = {}
        self._total_queries = 0

    def classify_intent(self, query: str) -> str:
        """推断查询意图类型。"""
        q = query.lower().strip()
        best_intent = "factual"  # default
        best_score = 0
        for intent, patterns in _INTENT_PATTERNS.items():
            score = sum(1 for p in patterns if p in q)
            if score > best_score:
                best_score = score
                best_intent = intent
        self._intent_counts[best_intent] = self._intent_counts.get(best_intent, 0) + 1
        self._total_queries += 1
        return best_intent

    def retrieve(self, query: str, limit: int = 10, **kwargs) -> dict:
        """推断意图后检索。"""
        intent = self.classify_intent(query)
        if self._retriever:
            results = self._retriever(query, limit=limit, **kwargs)
        else:
            results = []
        return {"intent": intent, "results": results, "query": query}

    def get_stats(self) -> dict:
        return {
            "total_queries": self._total_queries,
            "intent_distribution": dict(self._intent_counts),
        }
