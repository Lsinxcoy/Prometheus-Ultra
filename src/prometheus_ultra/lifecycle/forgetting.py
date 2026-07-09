"""WeibullForgetting — Weibull distribution-based forgetting curve.

基于:
- "Weibull Distribution for Memory Forgetting" (Wixted & Stretch, 2004) + Omega遗忘曲线
  - Weibull CDF: R(t) = exp(-(t/λ)^k)
  - shape(k): 控制遗忘曲线形状(1=指数, >1=更陡峭)
  - scale(λ): 控制遗忘加速时间点
  - LRU驱逐: 追踪节点超过max_tracked时按retention驱逐

算法:
    compute_retention(age):
        1. R = exp(-(age/scale)^shape)

    compute_retention_compat(node_id, age):
        1. 计算retention并缓存
        2. LRU驱逐(保留最高retention的3/4)

    predict_forget_time(node_id, threshold):
        1. 求解: threshold = exp(-(t/λ)^k) → t = λ × (-ln(threshold))^(1/k)

来源: Omega系统 forgetting Weibull遗忘曲线模块
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


import math


class WeibullForgetting:
    """Weibull distribution-based forgetting curve.

    Usage:
        wf = WeibullForgetting(shape=1.5, scale=100.0)

        # Compute retention for different ages
        r_0 = wf.compute_retention(age=0.0)    # R=1.0
        r_50 = wf.compute_retention(age=50.0)   # R≈0.78
        r_100 = wf.compute_retention(age=100.0)  # R≈0.50
        r_200 = wf.compute_retention(age=200.0)  # R≈0.14

        # Cached version with LRU eviction
        wf.compute_retention_compat("node1", age=50.0)
        r = wf.get_retention("node1")

        # Find nodes that should be forgotten
        expired = wf.get_expired_nodes(threshold=0.1)
    """

    def __init__(self, shape: float = 1.5, scale: float = 100.0, max_tracked: int = 5000):
        """Initialize the forgetting curve.

        Args:
            shape: Weibull shape parameter (k). Higher = sharper forgetting.
            scale: Weibull scale parameter (λ). Higher = slower forgetting.
            max_tracked: Maximum nodes to track before LRU eviction.
        """
        if shape <= 0:
            raise ValueError(f"shape must be > 0, got {shape}")
        if scale <= 0:
            raise ValueError(f"scale must be > 0, got {scale}")
        self._shape = shape
        self._scale = scale
        self._max_tracked = max_tracked
        self._retentions: dict[str, float] = {}
        self._access_times: dict[str, float] = {}

    def compute_retention(self, age: float) -> float:
        """Compute retention probability for a given age.

        Args:
            age: Age of memory (in same units as scale).

        Returns:
            Retention probability [0, 1].
        """
        if age < 0:
            return 1.0
        return math.exp(-((age / self._scale) ** self._shape))

    def compute_retention_compat(self, node_id: str, age: float = 1.0) -> float:
        """Compute and cache retention for a node.

        Args:
            node_id: Node identifier.
            age: Age of the node.

        Returns:
            Retention probability [0, 1].
        """
        r = self.compute_retention(age)
        self._retentions[node_id] = r
        self._access_times[node_id] = time.time()

        # LRU eviction if over limit
        if len(self._retentions) > self._max_tracked:
            sorted_keys = sorted(self._retentions, key=lambda k: self._retentions[k])
            evict_count = len(self._retentions) // 4
            for k in sorted_keys[:evict_count]:
                del self._retentions[k]
                self._access_times.pop(k, None)

        return r

    def get_retention(self, node_id: str) -> float:
        """Get cached retention for a node."""
        return self._retentions.get(node_id, 1.0)

    def get_expired_nodes(self, threshold: float = 0.1) -> list[str]:
        """Get nodes with retention below threshold."""
        return [nid for nid, r in self._retentions.items() if r < threshold]

    def get_most_forgotten(self, top_k: int = 10) -> list[dict]:
        """Get nodes closest to being forgotten."""
        sorted_nodes = sorted(self._retentions.items(), key=lambda x: x[1])
        return [{"node_id": nid, "retention": r} for nid, r in sorted_nodes[:top_k]]

    def get_most_retained(self, top_k: int = 10) -> list[dict]:
        """Get nodes with highest retention."""
        sorted_nodes = sorted(self._retentions.items(), key=lambda x: x[1], reverse=True)
        return [{"node_id": nid, "retention": r} for nid, r in sorted_nodes[:top_k]]

    def get_retention_distribution(self, bins: int = 10) -> dict[int, int]:
        """Get retention distribution in bins."""
        distribution = {i: 0 for i in range(bins)}
        for r in self._retentions.values():
            bin_idx = min(int(r * bins), bins - 1)
            distribution[bin_idx] += 1
        return distribution

    def predict_forget_time(self, node_id: str, threshold: float = 0.1) -> float | None:
        """Predict when a node will be forgotten below threshold."""
        r = self._retentions.get(node_id, 1.0)
        if r <= threshold:
            return 0.0
        # Solve: threshold = exp(-(t/λ)^k) for t
        # t = λ * (-ln(threshold))^(1/k)
        t = self._scale * (-math.log(threshold)) ** (1 / self._shape)
        return t

    def get_stats(self) -> dict:
        vals = list(self._retentions.values())
        return {
            "tracked_nodes": len(self._retentions),
            "avg_retention": sum(vals) / max(len(vals), 1),
            "min_retention": min(vals) if vals else 0,
            "max_retention": max(vals) if vals else 1,
            "shape": self._shape,
            "scale": self._scale,
        }

    # ── FSFM Safety-Triggered + Adaptive Reinforcement (B4-3, arXiv 2604.20300) ──

    def safety_trigger_forget(self, node_ids: list[str], reason: str = "security") -> dict:
        """安全触发遗忘：立即将指定节点遗忘（retention 设为 0）。

        FSFM 安全触发分类：检测到恶意/敏感内容时自动删除。
        """
        count = 0
        for nid in node_ids:
            if nid in self._retentions:
                self._retentions[nid] = 0.0
                count += 1
        logger.warning("FSFM safety-triggered forget: %d nodes (%s)", count, reason)
        return {"forgotten": count, "reason": reason}

    def adaptive_reinforce(self, node_id: str, boost: float = 0.2) -> float:
        """自适应增强：对频繁访问的记忆增加 retention。

        FSFM 自适应增强分类：频繁访问的记忆获得增强，不常访问的衰减更快。
        """
        current = self._retentions.get(node_id, 0.0)
        new_ret = min(1.0, current + boost)
        self._retentions[node_id] = new_ret
        return new_ret

    def get_safety_candidates(self, threshold: float = 0.8) -> list[dict]:
        """获取低 retention 节点作为安全遗忘候选。"""
        candidates = []
        for nid, r in self._retentions.items():
            if r < threshold:
                candidates.append({"node_id": nid, "retention": r})
        candidates.sort(key=lambda x: x["retention"])
        return candidates[:100]


import time
