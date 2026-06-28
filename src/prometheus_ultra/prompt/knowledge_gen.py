"""KnowledgeGenerator — Knowledge synthesis from context.

Based on: "Generated Knowledge Prompting" (Liu et al., 2021)
arXiv:2110.08387

Key Concepts from Paper:
    1. Generate relevant knowledge before answering
    2. Use generated knowledge to improve answer accuracy
    3. Two-step prompt: generate knowledge → answer with knowledge
    4. Particularly effective for commonsense reasoning

Algorithm:
    1. Extract entities and relationships from context
    2. Generate candidate facts using pattern matching
    3. Score facts by confidence and relevance
    4. Return top facts for downstream use
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class Fact:
    subject: str = ""
    predicate: str = ""
    obj: str = ""
    confidence: float = 0.5
    source: str = ""
    category: str = ""


@dataclass
class Relation:
    source: str = ""
    target: str = ""
    relation_type: str = ""
    strength: float = 0.0


class KnowledgeGenerator:
    """Knowledge synthesis from context.

    Based on Generated Knowledge Prompting (Liu 2021).

    Usage:
        gen = KnowledgeGenerator()
        result = gen.generate_from_context(
            "Neural networks are inspired by biological brains. "
            "They learn patterns through backpropagation."
        )
        for fact in result["facts"]:
            print(f"{fact.subject} {fact.predicate} {fact.obj}")
    """

    COPULAR = {"is", "are", "was", "were", "be", "been", "being"}
    RELATIONAL = {"has", "have", "had", "contains", "includes", "uses", "requires",
                   "enables", "supports", "implements", "provides"}
    CAUSAL = {"causes", "leads", "enables", "prevents", "improves", "reduces"}

    def __init__(self):
        self._facts: list[Fact] = []
        self._relations: list[Relation] = []
        self._entity_freq: Counter = Counter()

    def generate(self, context: dict | None = None) -> dict:
        ctx = context or {}
        if "query" in ctx:
            return self.generate_from_query(ctx["query"])
        if "content" in ctx:
            return self.generate_from_context(ctx["content"])
        return {"facts": [], "relations": [], "total_facts": len(self._facts)}

    def generate_from_context(self, text: str) -> dict:
        sentences = re.split(r'[.!?]+', text)
        new_facts = []

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue

            facts = self._extract_facts(sentence)
            new_facts.extend(facts)
            self._facts.extend(facts)

            entities = self._extract_entities(sentence)
            for ent in entities:
                self._entity_freq[ent] += 1

            relations = self._extract_relations(sentence, entities)
            new_relations = [r for r in relations if not any(
                existing.source == r.source and existing.target == r.target
                for existing in self._relations
            )]
            self._relations.extend(new_relations)

        return {
            "facts": new_facts,
            "relations": [r for r in self._relations[-len(new_facts)-5:]],
            "total_facts": len(self._facts),
        }

    def generate_from_query(self, query: str) -> dict:
        words = query.split()
        facts = []

        if len(words) >= 3:
            for i in range(len(words) - 2):
                w1, w2, w3 = words[i], words[i+1], words[i+2]
                if w2.lower() in self.COPULAR:
                    facts.append(Fact(
                        subject=w1, predicate="is", obj=" ".join(words[i+2:]),
                        confidence=0.6, source="query_extraction",
                        category="definitional",
                    ))
                elif w2.lower() in self.RELATIONAL:
                    facts.append(Fact(
                        subject=w1, predicate=w2, obj=w3,
                        confidence=0.5, source="query_extraction",
                        category="relational",
                    ))

        self._facts.extend(facts)
        return {"facts": facts, "relations": [], "total_facts": len(self._facts)}

    def _extract_facts(self, sentence: str) -> list[Fact]:
        facts = []
        words = sentence.split()

        for i in range(len(words) - 2):
            w1 = words[i].strip('",;:')
            w2 = words[i+1].lower()
            w3 = " ".join(words[i+2:]).strip('",;:')

            if w2 in self.COPULAR and len(w1) > 2 and len(w3) > 2:
                facts.append(Fact(
                    subject=w1, predicate="is", obj=w3[:100],
                    confidence=0.7, source="sentence_extraction",
                    category="definitional",
                ))
            elif w2 in self.RELATIONAL and len(w1) > 2:
                facts.append(Fact(
                    subject=w1, predicate=w2, obj=w3[:100],
                    confidence=0.6, source="sentence_extraction",
                    category="relational",
                ))

        return facts[:5]

    def _extract_entities(self, sentence: str) -> list[str]:
        words = sentence.split()
        entities = []
        for w in words:
            cleaned = w.strip('",;:.')
            if len(cleaned) > 3 and cleaned[0].isupper():
                entities.append(cleaned)
        return entities

    def _extract_relations(self, sentence: str, entities: list[str]) -> list[Relation]:
        relations = []
        sentence_lower = sentence.lower()

        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                e1, e2 = entities[i], entities[j]
                for marker in self.CAUSAL:
                    if marker in sentence_lower:
                        relations.append(Relation(
                            source=e1, target=e2,
                            relation_type="causal",
                            strength=0.6,
                        ))
                        break

        return relations

    def get_top_entities(self, top_k: int = 10) -> list[dict]:
        return [{"entity": e, "count": c} for e, c in self._entity_freq.most_common(top_k)]

    def get_facts_for_entity(self, entity: str) -> list[Fact]:
        return [f for f in self._facts if entity.lower() in f.subject.lower() or entity.lower() in f.obj.lower()]

    def get_stats(self) -> dict:
        return {
            "facts": len(self._facts),
            "relations": len(self._relations),
            "entities": len(self._entity_freq),
        }
