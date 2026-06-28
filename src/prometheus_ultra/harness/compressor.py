"""ContextCompressor — Semantic-aware context compression."""
from __future__ import annotations
import re


class ContextCompressor:
    def __init__(self, target_ratio: float = 0.5):
        self._target_ratio = target_ratio
        self._compressions = 0
        self._total_saved = 0

    def compress(self, text: str) -> str:
        self._compressions += 1
        if len(text) <= 500:
            return text
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) <= 3:
            return text[:500] + "..." + text[-200:]
        scored = []
        important_words = {"key", "important", "result", "conclusion", "therefore", "however", "critical"}
        for i, sent in enumerate(sentences):
            score = 0.0
            if i == 0 or i == len(sentences) - 1:
                score += 0.5
            words = sent.split()
            if 5 <= len(words) <= 30:
                score += 0.3
            if any(w.lower() in important_words for w in words):
                score += 0.4
            if sent.strip().endswith("?"):
                score += 0.2
            scored.append((score, i, sent))
        target_count = max(3, int(len(sentences) * self._target_ratio))
        scored.sort(key=lambda x: x[0], reverse=True)
        selected = sorted(scored[:target_count], key=lambda x: x[1])
        result = " ".join(s for _, _, s in selected)
        self._total_saved += len(text) - len(result)
        return result

    def get_stats(self) -> dict:
        return {"compressions": self._compressions, "total_saved": self._total_saved}
