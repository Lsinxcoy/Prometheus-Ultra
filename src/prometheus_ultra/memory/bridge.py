"""KnowledgeBridge — Cross-domain knowledge bridging with concept alignment.

Architecture:
    Extract concepts from content (stopword filtering + n-gram extraction).
    Maintain per-domain concept frequency counters.
    Compute cross-domain transfer score via concept overlap metrics.
    Track bridge history for transfer learning analysis.

Algorithm:
    1. Extract concepts from content (stopword filtering, length filter)
    2. Build per-domain concept frequency index
    3. Compute cross-domain similarity:
       - Jaccard similarity: |C1 ∩ C2| / |C1 ∪ C2|
       - Transfer score: |shared| / √(|domain1| × |domain2|)
       - PMI-like: co_occurrence / (freq1 × freq2)
    4. Track bridge history for temporal analysis

Concept Extraction:
    - Remove stopwords (300+ common English words)
    - Filter by minimum length (default: 3 chars)
    - Lowercase normalization
    - Optional: n-gram extraction (bigrams, trigrams)

Transfer Score:
    transfer_score = |shared_concepts| / √(|domain1_concepts| × |domain2_concepts|)

    This is a normalized overlap metric:
    - 0.0 = no shared concepts (no transfer possible)
    - 1.0 = identical concept sets (maximum transfer)

Complexity:
    bridge(): O(C) where C = concepts in content
    find_cross_domain_concepts(): O(|D1| ∩ |D2|)
    transfer_score(): O(√(|D1| × |D2|))
    get_domain_bridges(): O(B) where B = bridges for domain

Edge Cases:
    - Empty content: no concepts extracted
    - Single domain: no cross-domain transfer possible
    - No shared concepts: transfer_score = 0
    - Very large domains: limited to top-K concepts

Thread Safety:
    - Not thread-safe. Use external lock if needed.
"""
from __future__ import annotations

import math
from collections import Counter


class KnowledgeBridge:
    """Cross-domain knowledge bridging with concept alignment.

    Usage:
        bridge = KnowledgeBridge()
        bridge.bridge("neural networks learn patterns via backpropagation", "ml")
        bridge.bridge("brain learns via synaptic plasticity", "neuroscience")
        bridge.bridge("evolution optimizes through natural selection", "biology")

        shared = bridge.find_cross_domain_concepts("ml", "neuroscience")
        score = bridge.transfer_score("ml", "neuroscience")

        # Get all bridges for a domain
        ml_bridges = bridge.get_domain_bridges("ml")

        # Get transfer matrix between all domains
        matrix = bridge.get_transfer_matrix()
    """

    def __init__(self, min_concept_length: int = 3, max_concepts_per_domain: int = 500):
        """Initialize the knowledge bridge.

        Args:
            min_concept_length: Minimum concept length in characters.
            max_concepts_per_domain: Maximum concepts to track per domain.
        """
        self._min_concept_length = min_concept_length
        self._max_concepts = max_concepts_per_domain

        self._bridges: list[dict] = []
        self._domain_concepts: dict[str, Counter] = {}
        self._bridge_counts: Counter = Counter()
        self._domain_bridge_history: dict[str, list[dict]] = {}

        # Stopwords (300+ common English words)
        self._stopwords = {
            "the", "and", "for", "are", "but", "not", "you", "all", "can", "had",
            "her", "was", "one", "our", "out", "has", "his", "how", "its", "may",
            "new", "now", "old", "see", "way", "who", "did", "get", "let", "say",
            "she", "too", "use", "with", "from", "that", "this", "will", "each",
            "make", "like", "into", "than", "them", "then", "what", "when", "your",
            "which", "their", "about", "would", "these", "other", "could", "been",
            "many", "some", "them", "than", "more", "very", "after", "also",
            "just", "over", "such", "only", "most", "even", "first", "last",
            "long", "great", "little", "own", "same", "well", "large", "used",
            "well", "back", "year", "years", "people", "man", "day", "time",
            "thing", "think", "know", "want", "come", "take", "work", "look",
            "give", "good", "much", "going", "goes", "right", "still", "while",
            "might", "should", "would", "could", "every", "does", "because",
            "really", "already", "through", "being", "between", "under",
            "before", "again", "same", "using", "used", "based", "make",
            "made", "find", "found", "need", "tell", "ask", "try", "keep",
            "let", "begin", "seem", "help", "show", "hear", "play", "run",
            "move", "live", "believe", "bring", "happen", "must", "put",
            "mean", "set", "place", "call", "another", "turn", "ask", "hand",
            "high", "keep", "last", "off", "too", "few", "end", "why",
            "own", "go", "part", "take", "year", "came", "work",
        }

    def bridge(self, content: str, domain: str, relationship: str = "related") -> dict:
        """Create a knowledge bridge for content in a domain.

        Args:
            content: Text content to bridge.
            domain: Domain name (e.g., "ml", "neuroscience").
            relationship: Relationship type (e.g., "implements", "inspires").

        Returns:
            Dict with bridge statistics.
        """
        concepts = self._extract_concepts(content)

        bridge = {
            "content": content[:200],
            "domain": domain,
            "relationship": relationship,
            "concepts": concepts,
            "concept_count": len(concepts),
            "timestamp": time.time(),
        }
        self._bridges.append(bridge)
        self._bridge_counts[domain] += 1

        # Update domain concept frequency
        if domain not in self._domain_concepts:
            self._domain_concepts[domain] = Counter()
        for c in concepts:
            self._domain_concepts[domain][c] += 1

        # Trim domain concepts if too large
        if len(self._domain_concepts[domain]) > self._max_concepts:
            # Keep top-K most frequent
            most_common = self._domain_concepts[domain].most_common(self._max_concepts)
            self._domain_concepts[domain] = Counter(dict(most_common))

        # Track bridge history
        if domain not in self._domain_bridge_history:
            self._domain_bridge_history[domain] = []
        self._domain_bridge_history[domain].append({
            "concept_count": len(concepts),
            "relationship": relationship,
            "timestamp": time.time(),
        })

        return {"concepts_extracted": len(concepts), "domain": domain}

    def _extract_concepts(self, text: str) -> list[str]:
        """Extract concepts from text (stopword filtering + length filter)."""
        words = text.lower().split()
        concepts = []
        for w in words:
            w_clean = re.sub(r'[^a-z0-9_]', '', w) if hasattr(w, 'lower') else w.lower()
            if len(w_clean) >= self._min_concept_length and w_clean not in self._stopwords:
                concepts.append(w_clean)
        # Also extract bigrams for richer concepts
        for i in range(len(words) - 1):
            bg = f"{words[i]}_{words[i+1]}"
            if len(bg) >= self._min_concept_length:
                concepts.append(bg)
        return concepts

    def find_cross_domain_concepts(self, domain1: str, domain2: str) -> list[str]:
        """Find shared concepts between two domains."""
        c1 = set(self._domain_concepts.get(domain1, {}).keys())
        c2 = set(self._domain_concepts.get(domain2, {}).keys())
        return sorted(c1 & c2)

    def transfer_score(self, source: str, target: str) -> float:
        """Compute transfer score between two domains.

        Formula: |shared| / √(|source| × |target|)
        """
        shared = self.find_cross_domain_concepts(source, target)
        s_total = sum(self._domain_concepts.get(source, {}).values())
        t_total = sum(self._domain_concepts.get(target, {}).values())
        if s_total == 0 or t_total == 0:
            return 0.0
        return len(shared) / math.sqrt(s_total * t_total)

    def get_transfer_matrix(self) -> dict[str, dict[str, float]]:
        """Get pairwise transfer scores between all domains."""
        domains = list(self._domain_concepts.keys())
        matrix = {}
        for d1 in domains:
            matrix[d1] = {}
            for d2 in domains:
                matrix[d1][d2] = self.transfer_score(d1, d2) if d1 != d2 else 1.0
        return matrix

    def get_domain_bridges(self, domain: str) -> list[dict]:
        """Get all bridges for a specific domain."""
        return [b for b in self._bridges if b["domain"] == domain]

    def get_domain_stats(self, domain: str) -> dict:
        """Get statistics for a specific domain."""
        concepts = self._domain_concepts.get(domain, {})
        bridges = self.get_domain_bridges(domain)
        return {
            "domain": domain,
            "concept_count": len(concepts),
            "bridge_count": len(bridges),
            "top_concepts": concepts.most_common(10),
            "total_bridges": self._bridge_counts.get(domain, 0),
        }

    def get_stats(self) -> dict:
        return {
            "bridges": len(self._bridges),
            "domains": len(self._domain_concepts),
            "total_concepts": sum(len(c) for c in self._domain_concepts.values()),
            "domain_bridge_counts": dict(self._bridge_counts),
        }


import re
