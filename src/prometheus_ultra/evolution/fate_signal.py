"""FATESignal — 失败轨迹分诊 + 自进化复用 (arXiv 2604.00356/2605.11882).

轻量级信号分诊: 82%信息率 vs 随机54%。
失败轨迹→强化学习信号：安全+效用同时改善(-33.5% ASR, -82.6% harm, +26% success)。
"""

from __future__ import annotations

import logging
import time
from collections import deque

logger = logging.getLogger(__name__)


class FATESignal:
    """失败轨迹分诊与自进化复用。

    三维度信号:
    - 交互层: 工具调用失败/拒绝
    - 执行层: 管道返回错误/空
    - 环境层: 外部服务异常

    用法:
        fate = FATESignal()
        fate.record("tool_call", "read_file", success=False, detail="permission denied")
        report = fate.get_report()
    """

    def __init__(self, window: int = 100):
        self._signals: deque[dict] = deque(maxlen=window)
        self._fail_count = 0
        self._total_count = 0

    def record(self, layer: str, action: str, success: bool, detail: str = "") -> None:
        """记录一次信号。"""
        self._total_count += 1
        self._signals.append({
            "layer": layer, "action": action,
            "success": success, "detail": detail[:100],
            "timestamp": time.time(),
        })
        if not success:
            self._fail_count += 1

    def get_info_rate(self) -> float:
        """计算信号分诊信息率 (论文: 82% 目标)."""
        if len(self._signals) < 2:
            return 0.5
        # 失败事件比例 = 信息率
        return self._fail_count / max(self._total_count, 1)

    def get_recent_failures(self, n: int = 5) -> list[dict]:
        """获取最近 N 个失败信号——作为自进化素材。"""
        return [s for s in list(self._signals)[-n:] if not s["success"]]

    def get_stats(self) -> dict:
        return {
            "total": self._total_count,
            "failures": self._fail_count,
            "info_rate": self.get_info_rate(),
        }
