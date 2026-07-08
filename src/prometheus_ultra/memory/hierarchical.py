"""HierarchicalMemory — HORMA层级记忆模块（arXiv 2606.11680）。

文件系统式层级结构 > 扁平语义检索。token降78-97%，OOD泛化超过无限制baseline。

核心思想：将记忆组织为文件系统式的层级目录结构，
而不是平铺的语义空间。每个节点有路径标识，路径越近语义越相关。
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)


class HierarchicalMemory:
    """HORMA: 文件系统式层级记忆。

    将记忆组织为"/domain/category/topic/id"形式的层级路径。
    路径前缀越接近的记忆语义越相关。

    Usage:
        hm = HierarchicalMemory()
        hm.store("mem1", "/ai/memory/hierarchical", 0.8)
        hm.store("mem2", "/ai/memory/flat", 0.7)
        hm.store("mem3", "/biology/genetics/dna", 0.9)

        # 在 /ai 路径下检索
        results = hm.retrieve("/ai", max_results=5)
        # hits = ["mem1", "mem2"]  # OOD泛化更好

        stats = hm.get_stats()
    """

    def __init__(self):
        self._nodes: dict[str, dict] = {}
        self._tree: dict[str, set[str]] = defaultdict(set)
        self._access_count: dict[str, int] = defaultdict(int)

    def store(self, node_id: str, path: str, utility: float = 0.5,
              content: str = "") -> None:
        """存储节点到层级树。

        Args:
            node_id: 节点唯一ID
            path: 层级路径，如 "/ai/memory/hierarchical"
            utility: 重要度（影响检索排序）
            content: 节点内容
        """
        path = path.rstrip("/") if path != "/" else path
        if not path.startswith("/"):
            path = "/" + path

        self._nodes[node_id] = {
            "path": path,
            "utility": utility,
            "content": content,
            "ts": time.time(),
        }

        # 注册到所有层级节点
        parts = path.strip("/").split("/")
        for depth in range(len(parts) + 1):
            prefix = "/" + "/".join(parts[:depth])
            if prefix == "/" and depth == 0:
                prefix = "/"
            self._tree[prefix].add(node_id)

        logger.debug("HORMA stored %s at path %s", node_id, path)

    def retrieve(self, query_path: str, max_results: int = 10,
                 min_utility: float = 0.0) -> list[dict]:
        """沿层级路径检索最相关节点。

        优先级：精确路径匹配 > 父路径匹配 > 相近路径匹配。

        Args:
            query_path: 查询路径（如 "/ai/memory"）
            max_results: 最大返回数
            min_utility: 最小重要度过滤

        Returns:
            排序后的节点列表，每个包含 node_id, score, path, content
        """
        query_path = query_path.rstrip("/") if query_path != "/" else query_path
        if not query_path.startswith("/"):
            query_path = "/" + query_path

        # 路径匹配深度：缩短路径逐步扩大搜索范围
        parts = query_path.strip("/").split("/")
        candidates: dict[str, float] = {}

        for depth in range(len(parts), -1, -1):
            prefix = "/" + "/".join(parts[:depth])
            if prefix == "/" and depth == 0:
                prefix = "/"

            for nid in self._tree.get(prefix, set()):
                if nid in candidates:
                    continue
                info = self._nodes.get(nid)
                if not info:
                    continue
                if info["utility"] < min_utility:
                    continue

                # 匹配分数 = 共享路径深度 / 全部深度 + utility加成
                node_parts = info["path"].strip("/").split("/")
                shared = 0
                for i in range(min(len(parts), len(node_parts))):
                    if parts[i] == node_parts[i]:
                        shared += 1
                    else:
                        break
                depth_score = shared / max(len(node_parts), 1)
                score = depth_score * 0.6 + info["utility"] * 0.4
                candidates[nid] = score

        # 按分数排序
        sorted_nodes = sorted(candidates.items(), key=lambda x: -x[1])
        results = []
        for nid, score in sorted_nodes[:max_results]:
            info = self._nodes[nid]
            results.append({
                "node_id": nid,
                "score": round(score, 4),
                "path": info["path"],
                "content": info["content"][:200],
            })
            self._access_count[nid] += 1

        return results

    def get_stats(self) -> dict[str, Any]:
        """获取层级记忆统计。"""
        path_counts = {p: len(nds) for p, nds in self._tree.items()
                       if p != "/"}
        top_paths = sorted(path_counts.items(), key=lambda x: -x[1])[:10]

        return {
            "total_nodes": len(self._nodes),
            "total_paths": len(self._tree),
            "avg_access": round(sum(self._access_count.values()) / max(len(self._nodes), 1), 2),
            "top_paths": [{"path": p, "count": c} for p, c in top_paths],
            "nodes_per_path": round(len(self._nodes) / max(len(self._tree), 1), 1),
        }
