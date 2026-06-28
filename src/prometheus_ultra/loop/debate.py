"""DebateEngine — Multi-agent argumentation with position evaluation."""
from __future__ import annotations
import time


class DebateEngine:
    def __init__(self):
        self._debates: list[dict] = []

    def debate(self, topic: str, perspectives: list[str] | None = None) -> dict:
        perspectives = perspectives or []
        arguments = []
        for p in perspectives:
            words = p.split()
            length_score = min(1.0, len(words) / 20)
            evidence_words = {"because", "evidence", "data", "shows", "proves", "research", "analysis"}
            evidence_count = sum(1 for w in words if w.lower() in evidence_words)
            evidence_score = min(1.0, evidence_count * 0.3)
            specificity_score = min(1.0, len(set(w.lower() for w in words if len(w) > 5)) / max(len(words), 1))
            quality = length_score * 0.3 + evidence_score * 0.4 + specificity_score * 0.3
            arguments.append({"text": p, "quality": quality, "evidence_count": evidence_count})
        winner = max(arguments, key=lambda a: a["quality"]) if arguments else None
        synthesis = "No arguments presented"
        if len(arguments) >= 2:
            top_2 = sorted(arguments, key=lambda a: a["quality"], reverse=True)[:2]
            synthesis = f"Strongest: {top_2[0]['text'][:100]}. Supported by: {top_2[1]['text'][:100]}"
        elif arguments:
            synthesis = arguments[0]["text"]
        result = {"topic": topic, "argument_count": len(arguments),
                  "winner": winner["text"][:100] if winner else None,
                  "winner_quality": winner["quality"] if winner else 0, "synthesis": synthesis, "ts": time.time()}
        self._debates.append(result)
        return result

    def get_stats(self) -> dict:
        return {"debates": len(self._debates)}
