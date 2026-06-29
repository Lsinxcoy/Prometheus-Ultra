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

        Uses tag index for O(K) candidate selection instead of O(N) full scan.
        """
        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        networks = [network] if network and network in self._networks else self.NETWORK_NAMES

        # Phase 1: Collect candidates via tag index (O(K) instead of O(N))
        candidate_entries = set()
        for tag in query_words:
            if tag in self._tag_index:
                for net_name, idx in self._tag_index[tag]:
                    if net_name in self._networks and idx < len(self._networks[net_name]):
                        candidate_entries.add((net_name, idx))

        # Also add recent entries (last 5 per network) for recency bonus
        for net_name in networks:
            net = self._networks[net_name]
            for i in range(max(0, len(net) - 5), len(net)):
                candidate_entries.add((net_name, i))

        # Phase 2: Score only candidates
        for net_name, idx in candidate_entries:
            entry = self._networks[net_name][idx]

            content_lower = entry["content"].lower()
            relevance = 0.0
            if query_lower in content_lower:
                relevance = 1.0
            content_words = set(content_lower.split())
            overlap = query_words & content_words
            if query_words:
                relevance += len(overlap) / len(query_words) * 0.5

            net_keywords = self.NETWORK_KEYWORDS.get(net_name, set())
            keyword_overlap = query_words & net_keywords
            if keyword_overlap:
                relevance *= 1.0 + len(keyword_overlap) * 0.1

            if relevance == 0:
                continue

            importance = entry.get("importance", 0.5)
            age = time.time() - entry.get("last_access", time.time())
            recency = math.exp(-age / 3600)

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

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def reflect(self, query: str, num_reflections: int = 3) -> list[str]:
        """Generate reflections from memories (from Generative Agents paper).

        "Reflections are higher-level, more abstract thoughts that
         synthesize and reason over raw memories"

        Enhanced with cross-network synthesis.
        """
        memories = self.recall(query, top_k=num_reflections * 3)
        reflections = []

        networks_used = set(m.get("network", "") for m in memories)
        high_importance = [m for m in memories if m.get("importance", 0) > 0.7]

        if high_importance:
            summary = "; ".join(m["content"][:60] for m in high_importance[:2])
            reflections.append(
                f"Key insight from {len(high_importance)} high-importance memories: {summary}"
            )

        if len(networks_used) > 1:
            reflections.append(
                f"Cross-network synthesis across {len(networks_used)} networks: "
                f"{', '.join(networks_used)}"
            )

        for i in range(min(num_reflections, len(memories))):
            mem = memories[i]
            reflection = (
                f"[{mem.get('network', 'unknown')}] "
                f"'{mem['content'][:80]}...' "
                f"(importance={mem.get('importance', 0):.2f}, "
                f"relevance={mem.get('relevance', 0):.2f}) — "
                f"relevant to {query} because of shared concepts."
            )
            reflections.append(reflection)

        return reflections[:num_reflections + 1]

    def get_stats(self) -> dict:
        return {
            **{name: len(entries) for name, entries in self._networks.items()},
            "total": self._total_retained,
            "unique_tags": len(self._tag_index),
        }


import time
