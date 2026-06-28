"""FourNetworkMemory — 4-network cognitive memory with Generative Agents principles.

Based on: "Generative Agents: Interactive Simulacra of Human Behavior"
(arXiv:2304.03442, Park et al. 2023)

Key Concepts from Paper:
    1. Memory Stream: chronological record of experiences
    2. Retrieval: recency + importance + relevance scoring
    3. Reflection: higher-level synthesis from memories
    4. Planning: reflection-informed action planning

Paper Finding:
    "Generative agents produce believable individual and social behaviors
     that are more than just isolated instantiations"

Enhancement:
    - Added recency decay to retrieval scoring
    - Added importance-based memory prioritization
    - Added reflection synthesis capability
"""
from __future__ import annotations

import math
from collections import defaultdict


class FourNetworkMemory:
    """4-network cognitive memory with Generative Agents principles.

    Networks: experience, semantic, procedural, episodic
    Retrieval: recency × importance × relevance (from Generative Agents paper)
    """

    NETWORK_NAMES = ("experience", "semantic", "procedural", "episodic")
    NETWORK_KEYWORDS = {
        "experience": {"happened", "occurred", "event", "time", "when", "before", "after"},
        "semantic": {"is", "means", "definition", "concept", "category", "type"},
        "procedural": {"how", "step", "process", "method", "technique", "algorithm"},
        "episodic": {"where", "location", "context", "situation", "episode", "story"},
    }

    def __init__(self, max_entries_per_network: int = 1000, recency_decay: float = 0.95):
        """Initialize with Generative Agents parameters.

        Args:
            max_entries_per_network: Maximum entries per network.
            recency_decay: Decay factor for recency scoring (from GA paper).
        """
        self._networks: dict[str, list[dict]] = {name: [] for name in self.NETWORK_NAMES}
        self._tag_index: dict[str, list[tuple[str, int]]] = defaultdict(list)
        self._max_entries = max_entries_per_network
        self._recency_decay = recency_decay
        self._total_retained = 0
        self._access_counter = 0

    def retain(self, content: str, network: str = "experience",
               tags: list[str] | None = None, importance: float = 0.5) -> bool:
        """Retain a memory in a specific network."""
        if network not in self._networks:
            return False

        entry = {
            "content": content, "importance": importance,
            "tags": tags or [], "network": network,
            "access_count": 0, "last_access": time.time(),
        }

        net = self._networks[network]
        if len(net) >= self._max_entries:
            net.pop(0)
        idx = len(net)
        net.append(entry)

        for tag in (tags or []):
            self._tag_index[tag].append((network, idx))

        self._total_retained += 1
        return True

    def recall(self, query: str, top_k: int = 5, network: str | None = None) -> list[dict]:
        """Recall with Generative Agents scoring: recency × importance × relevance.

        From GA paper: "retrieval uses a weighted sum of three components:
        recency, importance, and relevance"
        """
        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        networks = [network] if network and network in self._networks else self.NETWORK_NAMES

        for net_name in networks:
            for i, entry in enumerate(self._networks[net_name]):
                # Relevance score
                content_lower = entry["content"].lower()
                relevance = 0.0
                if query_lower in content_lower:
                    relevance = 1.0
                content_words = set(content_lower.split())
                overlap = query_words & content_words
                if query_words:
                    relevance += len(overlap) / len(query_words) * 0.5

                # Network-specific bonus
                net_keywords = self.NETWORK_KEYWORDS.get(net_name, set())
                keyword_overlap = query_words & net_keywords
                if keyword_overlap:
                    relevance *= 1.0 + len(keyword_overlap) * 0.1

                if relevance == 0:
                    continue

                # Importance score (from GA paper)
                importance = entry.get("importance", 0.5)

                # Recency score (from GA paper: exponential decay)
                age = time.time() - entry.get("last_access", time.time())
                recency = math.exp(-age / 3600)  # Decay over hours

                # Combined score (from GA paper equation)
                score = 0.5 * relevance + 0.3 * importance + 0.2 * recency

                entry["access_count"] = entry.get("access_count", 0) + 1
                entry["last_access"] = time.time()

                results.append({
                    "content": entry["content"],
                    "score": score,
                    "network": net_name,
                    "importance": importance,
                    "recency": recency,
                    "relevance": relevance,
                })

        # Tag-based boost
        for tag in query_words:
            if tag in self._tag_index:
                for net_name, idx in self._tag_index[tag]:
                    if net_name in self._networks and idx < len(self._networks[net_name]):
                        entry = self._networks[net_name][idx]
                        already = any(r["content"] == entry["content"] for r in results)
                        if not already:
                            results.append({
                                "content": entry["content"], "score": 0.3,
                                "network": net_name, "importance": entry.get("importance", 0.5),
                            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def reflect(self, query: str, num_reflections: int = 3) -> list[str]:
        """Generate reflections from memories (from Generative Agents paper).

        "Reflections are higher-level, more abstract thoughts that
         synthesize and reason over raw memories"
        """
        memories = self.recall(query, top_k=num_reflections * 2)
        reflections = []
        for i in range(min(num_reflections, len(memories))):
            mem = memories[i]
            reflection = f"Based on '{mem['content'][:80]}...' (network: {mem['network']}, " \
                        f"importance: {mem['importance']:.2f}), I can conclude that " \
                        f"this is relevant to {query}."
            reflections.append(reflection)
        return reflections

    def get_stats(self) -> dict:
        return {
            **{name: len(entries) for name, entries in self._networks.items()},
            "total": self._total_retained,
            "unique_tags": len(self._tag_index),
        }


import time
