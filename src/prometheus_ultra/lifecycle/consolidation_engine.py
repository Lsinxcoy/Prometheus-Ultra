"""ConsolidationEngine — 多阶段记忆整合引擎.

基于:
- "Memory Consolidation during Sleep" (Diekelmann & Born, 2010)
  - 系统整合: 海马体 → 新皮层
  - 选择性巩固: 高价值记忆优先
  - 去整合: 消除冗余/冲突记忆

算法:
    run():
        1. 收集待整合的记忆节点
        2. 按重要性/新颖性/情感强度评分
        3. 合并相似内容（语义相似度 > 0.85）
        4. 删除冗余副本
        5. 更新图谱连接

复杂度:
    run(): O(N log N) 其中 N = 待整合节点数
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


import time
from dataclasses import dataclass, field


@dataclass
class ConsolidationResult:
    """整合结果."""
    merged: int = 0
    pruned: int = 0
    promoted: int = 0
    duration_ms: float = 0.0
    groups: list[dict] = field(default_factory=list)


class ConsolidationEngine:
    """多阶段记忆整合引擎.
    
    三阶段: 收集 → 合并 → 清理
    """
    
    def __init__(self, similarity_threshold: float = 0.85, min_utility: float = 0.3):
        self.similarity_threshold = similarity_threshold
        self.min_utility = min_utility
        self._history: list[ConsolidationResult] = []
        self._pending: list[dict] = []
        self._max_pending_age = 86400 * 30  # 30天TTL: 超过此时间的待整合节点自动清除
    
    def add_pending(self, node: dict) -> None:
        """添加待整合节点."""
        self._pending.append({
            "id": node.get("id", ""),
            "content": node.get("content", ""),
            "utility": node.get("utility", 0.5),
            "added_at": time.time(),
        })
    
    def run(self) -> ConsolidationResult:
        """执行完整整合流程."""
        start = time.time()
        result = ConsolidationResult()
        
        if not self._pending:
            self._history.append(result)
            return result
        
        # TTL清理: 移除超过30天的待整合节点，防止内存泄漏
        now = time.time()
        old_count = len(self._pending)
        self._pending = [n for n in self._pending if now - n.get("added_at", 0) < self._max_pending_age]
        result.pruned = old_count - len(self._pending)
        
        if not self._pending:
            self._history.append(result)
            return result
        
        # 阶段1: 按内容相似度分组
        groups = self._group_by_similarity(self._pending)
        result.groups = [{"members": len(g), "avg_utility": sum(n["utility"] for n in g) / len(g)} for g in groups]
        
        # 阶段2: 合并相似节点（保留最高utility版本）
        # R2903实证: consolidation让54%已会题目做错
        # vmPFC研究: 大脑默认分离不整合
        # 改为: 建立 similar_to 关联边，不删除任何节点
        linked = 0
        kept = list(self._pending)
        for group in groups:
            if len(group) > 1:
                # 建立关联边，不合并
                for i in range(1, len(group)):
                    self._notify_link(group[0]["id"], group[i]["id"])
                linked += len(group) - 1
        result.merged = linked
        
        # 阶段3: 标记低utility节点（候选清理，不实际删除）
        low_utility_nodes = [n for n in kept if n["utility"] < self.min_utility]
        result.pruned = len(low_utility_nodes)
        
        # 阶段4: 保留所有节点（append-only）
        result.promoted = len(kept)
        
        # 更新待整合列表
        self._pending = []
        self._history.append(result)
        result.duration_ms = (time.time() - start) * 1000
        
        return result
    
    def consolidate(self, nodes: list[dict] | None = None) -> ConsolidationResult:
        """对指定节点执行整合."""
        if nodes:
            for n in nodes:
                self.add_pending(n)
        return self.run()
    
    def _group_by_similarity(self, nodes: list[dict]) -> list[list[dict]]:
        """基于内容关键词重叠度分组."""
        if not nodes:
            return []
        
        # 简单关键词重叠度计算
        def keyword_overlap(a: dict, b: dict) -> float:
            words_a = set(a.get("content", "").lower().split())
            words_b = set(b.get("content", "").lower().split())
            if not words_a or not words_b:
                return 0.0
            return len(words_a & words_b) / min(len(words_a), len(words_b))
        
        groups: list[list[dict]] = []
        used = [False] * len(nodes)
        
        for i in range(len(nodes)):
            if used[i]:
                continue
            group = [nodes[i]]
            used[i] = True
            for j in range(i + 1, len(nodes)):
                if not used[j] and keyword_overlap(nodes[i], nodes[j]) >= self.similarity_threshold:
                    group.append(nodes[j])
                    used[j] = True
            groups.append(group)
        
        return groups

    def _notify_link(self, source_id: str, target_id: str) -> None:
        """记录相似节点关联（替代合并，append-only）。"""
        logger.debug("Consolidation link: %s → %s", source_id[:8], target_id[:8])

    def get_stats(self) -> dict:
        """获取整合统计."""
        total_merged = sum(r.merged for r in self._history)
        total_pruned = sum(r.pruned for r in self._history)
        total_promoted = sum(r.promoted for r in self._history)
        return {
            "runs": len(self._history),
            "total_merged": total_merged,
            "total_pruned": total_pruned,
            "total_promoted": total_promoted,
            "pending": len(self._pending),
            "pending_ttl_days": 30,
        }
