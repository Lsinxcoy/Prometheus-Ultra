"""LocalizedICL — L-ICL 定向修正 (arXiv 2602.00276).

2000 字符定向修正 > 20000 字符完整轨迹检索。
找到失败步骤 → 注入该步骤的修正。
"""
from __future__ import annotations
import logging
logger = logging.getLogger(__name__)

class LocalizedICL:
    def __init__(self):
        self._corrections = []
        self._total = 0
    def generate_correction(self, trajectory: list[dict], state: dict = None) -> dict:
        self._total += 1
        if not trajectory:
            return {"patch_step": -1, "patch_example": "No trajectory to correct", "reason": "empty"}
        # 找到第一个失败步骤
        for i, step in enumerate(trajectory):
            if not step.get("success", True):
                result = {"patch_step": i, "patch_example": f"Corrected step {i}: {step.get('action', '')}", "reason": f"Step {i} failed"}
                self._corrections.append(result)
                return result
        result = {"patch_step": -1, "patch_example": "", "reason": "All steps successful"}
        self._corrections.append(result)
        return result
    def get_stats(self) -> dict:
        return {"total": self._total, "correction_rate": round(sum(1 for c in self._corrections if c["patch_step"] >= 0) / max(self._total, 1), 4)}
