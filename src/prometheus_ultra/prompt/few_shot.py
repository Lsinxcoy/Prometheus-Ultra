"""DynamicFewShot — Similarity-based few-shot example selection."""
from __future__ import annotations
import math
from collections import Counter


class DynamicFewShot:
    def __init__(self, max_examples: int = 5):
        self._max = max_examples
        self._examples: list[dict] = []
        self._word_doc_freq: Counter = Counter()

    def add_example(self, input_text: str, output_text: str):
        words = set(input_text.lower().split())
        for w in words:
            self._word_doc_freq[w] += 1
        self._examples.append({"input": input_text, "output": output_text, "words": words, "idx": len(self._examples)})
        if len(self._examples) > self._max * 5:
            self._examples = self._examples[-self._max * 3:]

    def select(self, query: str) -> list[dict]:
        if not self._examples:
            return []
        query_words = set(query.lower().split())
        n_docs = len(self._examples)
        scored = []
        for ex in self._examples:
            overlap = query_words & ex["words"]
            if overlap:
                tf = len(overlap) / max(len(query_words), 1)
                idf_sum = sum(1 for e in self._examples if any(w in e["words"] for w in overlap))
                idf = math.log(n_docs / max(1, idf_sum))
                relevance = tf * max(idf, 0.1)
            else:
                relevance = 0.0
            recency = 1.0 - (ex["idx"] / max(len(self._examples), 1)) * 0.3
            scored.append((relevance * 0.7 + recency * 0.3, ex))
        scored.sort(key=lambda x: x[0], reverse=True)
        selected = []
        seen = set()
        for _, ex in scored:
            key = ex["input"][:50]
            if key not in seen or len(selected) < 2:
                selected.append(ex)
                seen.add(key)
            if len(selected) >= self._max:
                break
        return selected

    def get_stats(self) -> dict:
        return {"examples": len(self._examples)}
