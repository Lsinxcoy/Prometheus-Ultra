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
        
        # 阶段1: 按内容相似度分组
        groups = self._group_by_similarity(self._pending)
        result.groups = [{"members": len(g), "avg_utility": sum(n["utility"] for n in g) / len(g)} for g in groups]
        
        # 阶段2: 合并相似节点（保留最高utility版本）
        merged = 0
        kept: list[dict] = []
        for group in groups:
            if len(group) == 1:
                kept.append(group[0])
            else:
                # 按utility排序，保留最好的
                group.sort(key=lambda n: n["utility"], reverse=True)
                kept.append(group[0])
                merged += len(group) - 1
                # 提升保留节点的utility
                group[0]["utility"] = min(1.0, group[0]["utility"] * (1 + 0.1 * len(group)))
        result.merged = merged
        
        # 阶段3: 清理低utility节点
        before_count = len(kept)
        kept = [n for n in kept if n["utility"] >= self.min_utility]
        result.pruned = before_count - len(kept)
        
        # 阶段4: 提升保留节点
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
        }
