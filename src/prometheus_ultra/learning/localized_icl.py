"""LocalizedICL — L-ICL 定向修正 (arXiv 2602.00276).

论文核心方法：
2000 字符定向修正 > 20000 字符完整轨迹检索。
30-60 样本达峰值性能。
找到首个约束违反步骤 → 注入该步骤的 ICL 修正示例。
"""

from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)


class LocalizedICL:
    """L-ICL 定向修正器。"""

    def __init__(self):
        self._corrections: list[dict] = []
        self._total = 0

    def generate_correction(self, trajectory: list[dict], state: dict = None) -> dict:
        """生成定向修正。

        Args:
            trajectory: [{"step": int, "action": str, "success": bool, "constraint": str, ...}]
            state: 当前状态（可选）

        Returns:
            {"patch_step": int, "patch_example": str, "reason": str, "violation_type": str}
        """
        self._total += 1
        if not trajectory:
            return {"patch_step": -1, "patch_example": "No trajectory to correct",
                    "reason": "empty", "violation_type": "none"}

        # 找到第一个约束违反步骤
        for i, step in enumerate(trajectory):
            if not step.get("success", True):
                violation_type = step.get("constraint", "unknown")
                action = step.get("action", "")
                params = step.get("params", {})

                # 生成定向 ICL 修正示例
                patch_example = self._build_patch_example(violation_type, action, params)

                result = {
                    "patch_step": i,
                    "patch_example": patch_example,
                    "reason": f"Step {i}: {action} failed due to {violation_type}",
                    "violation_type": violation_type,
                }
                self._corrections.append(result)
                return result

        result = {
            "patch_step": -1,
            "patch_example": "",
            "reason": "All steps successful",
            "violation_type": "none",
        }
        self._corrections.append(result)
        return result

    def _build_patch_example(self, violation_type: str, action: str, params: dict) -> str:
        """基于违反类型生成 ICL 修正示例。"""
        examples = {
            "syntax": f"# Incorrect: {action}({params})\n# Correct: proper_{action}({params})",
            "permission": f"# Permission denied for {action}\n# Solution: check access before {action}",
            "timeout": f"# {action} timed out\n# Solution: reduce scope or increase timeout",
            "not_found": f"# {action} target not found\n# Solution: verify target exists before {action}",
            "unknown": f"# {action} failed\n# Solution: retry with validated parameters",
        }
        return examples.get(violation_type, examples["unknown"])

    def get_stats(self) -> dict:
        corrections_made = sum(1 for c in self._corrections if c["patch_step"] >= 0)
        return {
            "total": self._total,
            "corrections_made": corrections_made,
            "correction_rate": round(corrections_made / max(self._total, 1), 4),
        }
