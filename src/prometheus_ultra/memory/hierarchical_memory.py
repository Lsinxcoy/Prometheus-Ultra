"""HORMA hierarchical memory — file-system-like hierarchy (arXiv 2606.11680).

Structure: root / task / episode / action / raw
Thread-safe, path-based organization beats flat semantic retrieval.
Token usage drops to ~22% of baseline; OOD generalization exceeds
unconstrained baselines.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)


class HierarchicalMemory:
    """File-system-like hierarchical memory with path-based organization.

    Structure: root → task → episode → action → raw

    Each node is stored at a path (e.g. ``/tasks/exploration/episode_3``).
    Retrieval walks ancestor prefixes from most-specific to least-specific,
    scoring by path-depth overlap + utility.  Thread-safe via a reentrant lock.

    Usage::

        hm = HierarchicalMemory()
        hm.store("node_1", "/tasks/exploration/episode_3", 0.9,
                 content="found a cave")
        hits = hm.retrieve("/tasks/exploration")
        path = hm.get_path("node_1")
        stats = hm.get_stats()
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # node_id → {path, utility, content, ts}
        self._nodes: dict[str, dict[str, Any]] = {}
        # path_prefix → set[node_id]
        self._tree: dict[str, set[str]] = {}
        # node_id → access count
        self._access_count: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store(self, node_id: str, path: str, utility: float = 0.5,
              content: str = "") -> None:
        """Store a node at *path*.

        Args:
            node_id: Unique identifier for the node.
            path: Hierarchical path, e.g. ``"/tasks/exploration/episode_3"``.
            utility: Importance weight in ``[0, 1]`` (affects retrieval rank).
            content: Arbitrary string payload.
        """
        path = self._normalise(path)

        with self._lock:
            self._nodes[node_id] = {
                "path": path,
                "utility": utility,
                "content": content,
                "ts": time.time(),
            }

            # Register under every ancestor prefix so that a query for a parent
            # directory naturally discovers this child.
            parts = path.strip("/").split("/")
            for depth in range(len(parts) + 1):
                prefix = "/" + "/".join(parts[:depth])
                if depth == 0:
                    prefix = "/"
                self._tree.setdefault(prefix, set()).add(node_id)

            logger.debug("HORMA stored %s at %s (utility=%.2f)",
                         node_id, path, utility)

    def retrieve(self, query: str, context: str | None = None,
                 max_results: int = 10,
                 min_utility: float = 0.0) -> list[dict[str, Any]]:
        """Retrieve nodes relevant to *query* (interpreted as a path).

        The method searches from most-specific to broadest ancestor prefixes,
        scoring by shared-path depth (60 %) + utility (40 %).  The optional
        *context* string is currently reserved for future semantic refinement
        (e.g. an LLM-generated summary to disambiguate).

        Args:
            query: Path to query, e.g. ``"/tasks/exploration"``.
            context: Optional semantic hint (reserved).
            max_results: Maximum number of results to return.
            min_utility: Minimum utility threshold.

        Returns:
            List of dicts with keys ``node_id``, ``score``, ``path``, ``content``.
        """
        query_path = self._normalise(query)
        parts = query_path.strip("/").split("/")

        with self._lock:
            candidates: dict[str, float] = {}

            # Walk from deepest prefix up to root.
            for depth in range(len(parts), -1, -1):
                prefix = "/" + "/".join(parts[:depth])
                if depth == 0:
                    prefix = "/"

                for nid in self._tree.get(prefix, set()):
                    if nid in candidates:
                        continue
                    info = self._nodes.get(nid)
                    if info is None or info["utility"] < min_utility:
                        continue

                    node_parts = info["path"].strip("/").split("/")
                    shared = sum(
                        1 for a, b in zip(parts, node_parts) if a == b
                    )
                    depth_score = shared / max(len(node_parts), 1)
                    score = depth_score * 0.6 + info["utility"] * 0.4
                    candidates[nid] = score

            sorted_nodes = sorted(candidates.items(),
                                  key=lambda x: (-x[1], x[0]))
            results: list[dict[str, Any]] = []
            for nid, score in sorted_nodes[:max_results]:
                info = self._nodes[nid]
                results.append({
                    "node_id": nid,
                    "score": round(score, 4),
                    "path": info["path"],
                    "content": info["content"][:200],
                })
                self._access_count[nid] = self._access_count.get(nid, 0) + 1

        return results

    def get_path(self, node_id: str) -> str | None:
        """Return the hierarchical path for *node_id*, or ``None``."""
        with self._lock:
            info = self._nodes.get(node_id)
            return info["path"] if info else None

    def get_stats(self) -> dict[str, Any]:
        """Return summary statistics."""
        with self._lock:
            total_nodes = len(self._nodes)
            total_paths = len(self._tree)
            avg_access = (
                round(sum(self._access_count.values()) / max(total_nodes, 1), 2)
                if total_nodes else 0.0
            )
            path_counts = {
                p: len(nds) for p, nds in self._tree.items() if p != "/"
            }
            top_paths = sorted(path_counts.items(),
                               key=lambda x: -x[1])[:10]

        return {
            "total_nodes": total_nodes,
            "total_paths": total_paths,
            "avg_access": avg_access,
            "top_paths": [{"path": p, "count": c} for p, c in top_paths],
            "nodes_per_path": round(total_nodes / max(total_paths, 1), 1),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(path: str) -> str:
        """Ensure *path* starts with ``/`` and has no trailing slash (except root)."""
        path = path.strip().rstrip("/") if path != "/" else path
        if not path.startswith("/"):
            path = "/" + path
        return path
