"""KnowledgeScanner — 多源知识扫描器.

基于:
- "Knowledge Acquisition for Knowledge-Based Systems" (Lenz, 2002)
  - 多源获取: Web, 文档, 数据库, 专家
  - 内容提取: 文本解析, 实体识别
  - 质量评估: 相关性, 权威性, 时效性

算法:
    scan(source, query, max_results):
        1. 选择扫描源 (Web/API/文档)
        2. 构建查询
        3. 获取结果
        4. 质量过滤
        5. 排序返回

复杂度:
    scan(): O(R log R) 其中 R = 原始结果数
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


import time
import re
import hashlib
from dataclasses import dataclass, field
from enum import Enum


class ScanSource(Enum):
    WEB = "web"
    DOCUMENT = "document"
    DATABASE = "database"
    API = "api"
    EXPERT = "expert"


@dataclass
class ScanResult:
    """扫描结果."""
    title: str = ""
    content: str = ""
    source: str = ""
    relevance: float = 0.0
    authority: float = 0.0
    freshness: float = 0.0
    tags: list[str] = field(default_factory=list)
    source_type: str = ""
    fingerprint: str = ""
    
    @property
    def quality_score(self) -> float:
        """综合质量评分."""
        return 0.4 * self.relevance + 0.35 * self.authority + 0.25 * self.freshness
    
    @property
    def id(self) -> str:
        """结果ID."""
        return self.fingerprint or hashlib.md5(f"{self.title}{self.source}".encode()).hexdigest()[:12]


class KnowledgeScanner:
    """多源知识扫描器.
    
    支持多源扫描、质量过滤、去重.
    """
    
    def __init__(self, min_quality: float = 0.3, dedup_window: int = 100):
        self.min_quality = min_quality
        self.dedup_window = dedup_window
        self._seen: list[str] = []
        self._scan_history: list[dict] = []
    
    def scan(self, source: ScanSource, query: str, max_results: int = 5, force: bool = False) -> list[ScanResult]:
        """执行知识扫描."""
        start = time.time()
        
        # 构建查询上下文
        context = self._build_context(source, query)
        
        # 获取原始结果
        raw_results = self._fetch_results(source, query, max_results * 3)  # 获取3倍用于过滤
        
        # 质量过滤
        filtered = [r for r in raw_results if r.quality_score >= self.min_quality]
        
        # 去重
        unique = self._deduplicate(filtered, force=force)
        
        # 按质量排序
        unique.sort(key=lambda r: r.quality_score, reverse=True)
        
        # 限制数量
        results = unique[:max_results]
        
        # 记录历史
        self._scan_history.append({
            "source": source.value,
            "query": query,
            "raw_count": len(raw_results),
            "filtered_count": len(filtered),
            "unique_count": len(unique),
            "returned_count": len(results),
            "duration_ms": (time.time() - start) * 1000,
        })
        
        return results
    
    def _build_context(self, source: ScanSource, query: str) -> dict:
        """构建查询上下文."""
        return {
            "source": source.value,
            "query": query,
            "timestamp": time.time(),
            "query_hash": hashlib.md5(query.encode()).hexdigest()[:8],
        }
    
    def _fetch_results(self, source: ScanSource, query: str, limit: int) -> list[ScanResult]:
        """获取原始结果（模拟多源扫描）."""
        results = []
        
        # 从查询中提取关键词
        keywords = re.findall(r'\b\w+\b', query.lower())
        
        # 生成模拟结果（实际实现应连接真实数据源）
        for i in range(min(limit, 10)):
            # 计算相关性（基于关键词匹配）
            relevance = self._compute_relevance(keywords, f"result_{i}")
            
            # 计算权威性
            authority = self._compute_authority(source)
            
            # 计算时效性
            freshness = self._compute_freshness()
            
            # 提取标签
            tags = self._extract_tags(f"result_{i} {query}")
            
            results.append(ScanResult(
                title=f"{query} - Result {i+1}",
                content=f"Content about {query} from {source.value} source, index {i+1}.",
                source=source.value,
                relevance=relevance,
                authority=authority,
                freshness=freshness,
                tags=tags,
                source_type=source.value,
                fingerprint=hashlib.md5(f"{query}_{i}_{source.value}".encode()).hexdigest()[:12],
            ))
        
        return results
    
    def _compute_relevance(self, keywords: list[str], content: str) -> float:
        """计算相关性评分."""
        if not keywords:
            return 0.5
        # 简单关键词密度计算
        content_words = set(content.lower().split())
        matches = sum(1 for k in keywords if k in content_words)
        return min(1.0, matches / max(len(keywords), 1))
    
    def _compute_authority(self, source: ScanSource) -> float:
        """计算权威性评分."""
        authority_map = {
            ScanSource.DATABASE: 0.9,
            ScanSource.API: 0.8,
            ScanSource.DOCUMENT: 0.7,
            ScanSource.WEB: 0.5,
            ScanSource.EXPERT: 0.85,
        }
        return authority_map.get(source, 0.5)
    
    def _compute_freshness(self) -> float:
        """计算时效性评分."""
        # 模拟：基于时间衰减
        import time
        # 假设内容创建时间在 0-30 天内均匀分布
        import random
        days_old = random.uniform(0, 30)
        # 指数衰减
        return max(0.0, 1.0 - (days_old / 30))
    
    def _extract_tags(self, text: str) -> list[str]:
        """从文本中提取标签."""
        # 简单关键词提取
        words = re.findall(r'\b\w{3,}\b', text.lower())
        from collections import Counter
        counts = Counter(words)
        return [word for word, _ in counts.most_common(5)]
    
    def _deduplicate(self, results: list[ScanResult], force: bool = False) -> list[ScanResult]:
        """去重."""
        if not results:
            return []
        
        # 维护去重窗口
        if not force:
            self._seen = self._seen[-self.dedup_window:]
        
        unique = []
        for r in results:
            if r.fingerprint not in self._seen:
                unique.append(r)
                self._seen.append(r.fingerprint)
        
        return unique
    
    def get_stats(self) -> dict:
        """获取扫描统计."""
        if not self._scan_history:
            return {"scans": 0}
        
        total_raw = sum(h["raw_count"] for h in self._scan_history)
        total_returned = sum(h["returned_count"] for h in self._scan_history)
        
        return {
            "scans": len(self._scan_history),
            "total_raw": total_raw,
            "total_returned": total_returned,
            "filter_rate": total_returned / max(total_raw, 1),
            "avg_duration_ms": sum(h["duration_ms"] for h in self._scan_history) / len(self._scan_history),
        }
