"""CommunityTree — Community-based skill organization."""
from __future__ import annotations


class CommunityTree:
    def __init__(self):
        self._tree: dict[str, list[str]] = {"root": []}
        self._node_data: dict[str, dict] = {}
        self._pruned = 0

    def add_child(self, parent: str | None, data: dict | None = None):
        parent = parent or "root"
        node_id = f"node_{len(self._node_data)}"
        self._tree.setdefault(parent, []).append(node_id)
        self._tree.setdefault(node_id, [])
        self._node_data[node_id] = data or {}

    def find_communities(self) -> list[list[str]]:
        communities, visited = [], set()
        def dfs(node, community):
            if node in visited: return
            visited.add(node)
            community.append(node)
            for child in self._tree.get(node, []):
                dfs(child, community)
        for node in self._tree:
            if node not in visited:
                community = []
                dfs(node, community)
                if len(community) > 1:
                    communities.append(community)
        return communities

    def get_stats(self) -> dict:
        return {"nodes": len(self._node_data), "communities": len(self.find_communities())}
