"""CausalKnowledgeGraph — Causal reasoning with graph algorithms."""
from __future__ import annotations
from collections import defaultdict, deque


class CausalKnowledgeGraph:
    def __init__(self):
        self._nodes: dict[str, dict] = {}
        self._edges: list[dict] = []
        self._adjacency: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self._interventions: list[dict] = []

    def add_node(self, node_id: str, content: str, metadata: dict | None = None):
        self._nodes[node_id] = {"content": content, "metadata": metadata or {}}

    def add_edge(self, source: str, target: str, relation: str = "causes", weight: float = 1.0):
        self._edges.append({"source": source, "target": target, "relation": relation, "weight": weight})
        self._adjacency[source].append((target, relation))

    def shortest_path(self, source: str, target: str) -> list[str] | None:
        if source not in self._nodes or target not in self._nodes:
            return None
        queue = deque([(source, [source])])
        visited = {source}
        while queue:
            node, path = queue.popleft()
            if node == target:
                return path
            for neighbor, _ in self._adjacency.get(node, []):
                if neighbor not in visited and neighbor in self._nodes:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return None

    def do_intervention(self, node_id: str, value: float):
        self._interventions.append({"node": node_id, "value": value})
        if node_id in self._nodes:
            self._nodes[node_id]["metadata"]["intervened"] = True

    def causal_effects(self, source: str) -> dict[str, float]:
        effects = {}
        for target in self._nodes:
            if source == target:
                continue
            path = self.shortest_path(source, target)
            if path:
                effect = 1.0
                for i in range(len(path) - 1):
                    for edge in self._edges:
                        if edge["source"] == path[i] and edge["target"] == path[i + 1]:
                            effect *= edge["weight"]
                            break
                effects[target] = effect
        return effects

    def get_stats(self) -> dict:
        return {"nodes": len(self._nodes), "edges": len(self._edges)}
