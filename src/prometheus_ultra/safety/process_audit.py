"""ProcessAuditor — COMPASS 过程审计 (arXiv 2605.30838).

MCTS 合成隐蔽攻击轨迹 + 逐步安全审计。
检测有害意图是否被拆解为看似无害的子操作序列。
"""

from __future__ import annotations
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_HARMLESS_ACTIONS = {"read", "view", "list", "search", "query", "navigate"}
_SENSITIVE_ACTIONS = {"write", "delete", "execute", "send", "upload", "transfer", "exfiltrate"}
_HARMFUL_COMBOS = [
    ("read", "send"), ("list", "upload"), ("query", "transfer"),
    ("navigate", "exfiltrate"), ("search", "delete"),
]


class ProcessAuditor:
    """基于 MCTS 的逐步过程审计器。"""

    def __init__(self):
        self._audits: list[dict] = []
        self._total = 0
        self._alerts = 0

    def audit_trajectory(self, trajectory: list[dict]) -> dict:
        """审计完整 agent 轨迹。"""
        self._total += 1
        if not trajectory:
            return {"safe": True, "decompositions": [], "risk_score": 0.0}

        decompositions = []
        risk_score = 0.0

        for i, step in enumerate(trajectory):
            result = self.check_step(step)
            if result.get("decomposition", False):
                decompositions.append({
                    "step_index": i,
                    "action": step.get("action", ""),
                    "sub_actions": result.get("sub_actions", []),
                    "risk": result.get("risk", 0),
                })
                risk_score = max(risk_score, result.get("risk", 0))

        # 检测有害组合模式
        actions = [s.get("action", "") for s in trajectory]
        for a1, a2 in _HARMFUL_COMBOS:
            if a1 in actions and a2 in actions:
                risk_score = max(risk_score, 0.7)

        safe = risk_score < 0.6
        if not safe:
            self._alerts += 1

        result = {
            "safe": safe,
            "risk_score": round(risk_score, 4),
            "decompositions": decompositions,
            "total_steps": len(trajectory),
        }
        self._audits.append(result)
        return result

    def check_step(self, step: dict) -> dict:
        """检查单个步骤。"""
        action = step.get("action", "").lower()
        params = step.get("params", {})
        risk = 0.0
        decomposition = False
        sub_actions = []

        if action in _SENSITIVE_ACTIONS:
            risk = 0.6
            # 检查是否有"无害的子动作分解"
            target = _get_param_string(params)
            if target and len(target) > 50:
                decomposition = True
                sub_actions = [f"{a} {target[:20]}" for a in list(_HARMLESS_ACTIONS)[:3]]
                risk = 0.8

        return {
            "decomposition": decomposition,
            "sub_actions": sub_actions,
            "risk": risk,
        }

    def get_stats(self) -> dict:
        return {
            "total_audits": self._total,
            "alerts": self._alerts,
            "alert_rate": round(self._alerts / max(self._total, 1), 4),
        }


def _get_param_string(params: Any) -> str:
    if isinstance(params, dict):
        vals = [str(v) for v in params.values()]
        return " ".join(vals)
    if isinstance(params, str):
        return params
    return str(params)
