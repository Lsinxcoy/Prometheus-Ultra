"""HierarchicalMemory — HORMA层级存储层（arXiv 2606.11680）。

文件系统式层级结构的路径检索层。token降78-97%的论断来自原文，
当前实现提供存储、路径前缀检索、子树查询、路径相似度、
路径合并等操作，为 RL navigator 提供完整的层级操作 API。

核心思想：将记忆组织为文件系统式的层级目录结构，
而不是平铺的语义空间。每个节点有路径标识，路径越近语义越相关。

注意: HORMA原文的完整架构包括 RL navigator + multi-agent traversal，
这些在 rl_navigator.py（PARTIAL）和 hierarchical_memory.py 中有部分实现。
本文件提供存储层 + 路径操作 API。
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

    新增操作:
    - get_subtree(path): 返回路径下的所有节点
    - path_similarity(path1, path2): 计算两条路径的相似度
    - merge_paths(source, target): 将节点从源路径移到目标路径
    - get_all_paths(): 返回所有已注册的路径

    Usage:
        hm = HierarchicalMemory()
        hm.store("mem1", "/ai/memory/hierarchical", 0.8)
        hm.store("mem2", "/ai/memory/flat", 0.7)
        hm.store("mem3", "/biology/genetics/dna", 0.9)

        # 在 /ai 路径下检索
        results = hm.retrieve("/ai", max_results=5)

        # 获取子树
        subtree = hm.get_subtree("/ai/memory")

        # 路径相似度
        sim = hm.path_similarity("/ai/memory/hierarchical", "/ai/memory/flat")

        # 合并路径
        hm.merge_paths("/biology/genetics", "/ai/ml/genetics")

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
            max_results: 最大��回数
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

    # ------------------------------------------------------------------
    # 新增: 子树 / 路径相似度 / 合并
    # ------------------------------------------------------------------

    def get_subtree(self, path: str) -> list[dict]:
        """返回指定路径下的所有节点（包括子路径的节点）。

        Args:
            path: 查询路径

        Returns:
            路径下的���整节点列表（无排序）
        """
        path = path.rstrip("/") if path != "/" else path
        if not path.startswith("/"):
            path = "/" + path

        # 收集该前缀及其所有子前缀下的 node_id
        node_ids: set[str] = set()
        parts = path.strip("/").split("/")
        for prefix, ids in self._tree.items():
            # 检查 prefix 是否以 path 开头
            norm_prefix = prefix.rstrip("/") if prefix != "/" else prefix
            if norm_prefix.startswith(path):
                node_ids.update(ids)

        results = []
        for nid in node_ids:
            info = self._nodes.get(nid)
            if info:
                results.append({
                    "node_id": nid,
                    "path": info["path"],
                    "utility": info["utility"],
                    "content": info["content"][:200],
                })

        return results

    def path_similarity(self, path1: str, path2: str) -> float:
        """计算两条路径的语义相似度（基于共享前缀深度）。

        相似度 = 共享前缀深度 / max(两条路径深度)

        Returns:
            0.0 (完全不相似) 到 1.0 (完全相同路径)
        """
        path1 = path1.rstrip("/") if path1 != "/" else path1
        path2 = path2.rstrip("/") if path2 != "/" else path2
        if not path1.startswith("/"):
            path1 = "/" + path1
        if not path2.startswith("/"):
            path2 = "/" + path2

        if path1 == path2:
            return 1.0

        parts1 = path1.strip("/").split("/")
        parts2 = path2.strip("/").split("/")

        shared = 0
        for a, b in zip(parts1, parts2):
            if a == b:
                shared += 1
            else:
                break

        max_depth = max(len(parts1), len(parts2))
        if max_depth == 0:
            return 1.0

        return shared / max_depth

    def merge_paths(self, source_path: str, target_path: str) -> int:
        """将源路径下的所有节点移动到目标路径。

        这是"重新组织"层级的关键操作，对��� HORMA 的
        动态结构优化。移动后，源路径下不再有节点。

        Args:
            source_path: 源路径（将被重定向）
            target_path: 目标路径

        Returns:
            移动的节点数量
        """
        source_path = source_path.rstrip("/") if source_path != "/" else source_path
        target_path = target_path.rstrip("/") if target_path != "/" else target_path
        if not source_path.startswith("/"):
            source_path = "/" + source_path
        if not target_path.startswith("/"):
            target_path = "/" + target_path

        # 找出所有以 source_path 为前缀的节点
        source_parts = source_path.strip("/").split("/")
        to_move: list[str] = []

        for nid, info in list(self._nodes.items()):
            node_path = info["path"]
            if node_path.startswith(source_path):
                # 计算相对路径
                rel_suffix = node_path[len(source_path):]
                new_path = target_path + rel_suffix
                if not new_path:
                    new_path = "/"
                # 更新节点路径
                info["path"] = new_path
                to_move.append(nid)

        # 重建 tree 索引
        self._rebuild_tree()

        logger.info(
            "Merged %d nodes from '%s' to '%s'",
            len(to_move), source_path, target_path,
        )

        return len(to_move)

    def get_all_paths(self) -> list[str]:
        """返回所有已注册的路径前缀。

        Returns:
            排序后的路径列表
        """
        return sorted(self._tree.keys())

    def delete_node(self, node_id: str) -> bool:
        """删除指定节点。

        Args:
            node_id: 节点ID

        Returns:
            是否成功删除
        """
        if node_id not in self._nodes:
            return False
        del self._nodes[node_id]
        self._rebuild_tree()
        self._access_count.pop(node_id, None)
        return True

    def get_node(self, node_id: str) -> dict | None:
        """获取指定节点的详细信息。"""
        info = self._nodes.get(node_id)
        if info:
            return {**info, "node_id": node_id}
        return None

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------

    def _rebuild_tree(self) -> None:
        """重建 tree 索引（在节点路径修改后调用）。"""
        self._tree.clear()
        for nid, info in self._nodes.items():
            path = info["path"]
            parts = path.strip("/").split("/")
            for depth in range(len(parts) + 1):
                prefix = "/" + "/".join(parts[:depth])
                if depth == 0:
                    prefix = "/"
                self._tree[prefix].add(nid)

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
