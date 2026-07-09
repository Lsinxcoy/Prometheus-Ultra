"""IntentAwareRetrieval — 意图分类检索基类。

基于关键词对查询进行意图分类（factual/conceptual/operational/affective），
使用首尾截断作为压缩方式。

注意: 本文件曾引用 arXiv 2601.02553 (SimpleMem) 的三层压缩管线
（语义结构化压缩→在线语义合成→意图感知检索规划）。

当前实现的差异:
- "压缩"为首尾截断，非论文的语义无损压缩
- 意图分类基于简单关键词匹配
- 多视图检索（entity/event/time）使用正则提取
- 不包含论文的完整三层管线
"""

from __future__ import annotations
import logging
import re
from typing import Any
from collections import Counter

logger = logging.getLogger(__name__)

_INTENT_PATTERNS = {
    "factual": ["what is", "who is", "where is", "when did", "how many", "define", "explain", "describe"],
    "conceptual": ["how does", "why does", "what causes", "relationship between", "compare", "difference"],
    "operational": ["how to", "steps to", "procedure", "instructions", "guide", "tutorial", "way to"],
    "affective": ["i feel", "i think", "opinion", "recommend", "suggest", "prefer", "like"],
}

_ENTITY_PATTERNS = re.compile(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b')
_TEMPORAL_PATTERNS = re.compile(r'\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|\d{4})\b')


class IntentAwareRetrieval:
    """SimpleMem 意向感知检索 + 三阶段压缩。"""

    def __init__(self, retriever: Any | None = None):
        self._retriever = retriever
        self._intent_counts: dict[str, int] = {}
        self._total_queries = 0

    def classify_intent(self, query: str) -> str:
        """多模式意向分类。"""
        q = query.lower().strip()
        best_intent = "factual"
        best_score = 0
        for intent, patterns in _INTENT_PATTERNS.items():
            score = sum(1 for p in patterns if p in q)
            if score > best_score:
                best_score = score
                best_intent = intent
        self._intent_counts[best_intent] = self._intent_counts.get(best_intent, 0) + 1
        self._total_queries += 1
        return best_intent

    # A. 语义结构化压缩
    def compress(self, content: str) -> str:
        """压缩内容：保留关键结构，移除冗余。"""
        if len(content) < 100:
            return content
        lines = content.split('\n')
        if len(lines) > 5:
            return '\n'.join([lines[0], lines[1], f'... ({len(lines)-4} lines omitted) ...', lines[-1]])
        words = content.split()
        if len(words) > 100:
            return ' '.join(words[:50]) + '...' + ' '.join(words[-10:])
        return content

    # B. 多视图索引（实体/事件/时间）
    def extract_entities(self, content: str) -> list[str]:
        return list(set(_ENTITY_PATTERNS.findall(content)))[:10]

    def extract_temporal(self, content: str) -> list[str]:
        return list(set(_TEMPORAL_PATTERNS.findall(content)))[:5]

    # C. 意向感知检索
    def retrieve(self, query: str, limit: int = 10, **kwargs) -> dict:
        """推断意图后检索。"""
        intent = self.classify_intent(query)
        entities = self.extract_entities(query)
        temporal = self.extract_temporal(query)

        if self._retriever:
            results = self._retriever(query, limit=limit, **kwargs)
        else:
            results = []

        return {
            "intent": intent,
            "results": results,
            "query": query,
            "entities": entities,
            "temporal": temporal,
        }

    def get_stats(self) -> dict:
        return {
            "total_queries": self._total_queries,
            "intent_distribution": dict(self._intent_counts),
        }
