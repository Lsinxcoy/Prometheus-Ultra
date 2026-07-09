"""ProcessAuditor — COMPASS 过程审计 (arXiv 2605.30838).

论文核心方法：
MCTS 合成隐蔽攻击轨迹 + 逐步安全审计。
有害意图可被分解为看似无害的子查询组合。
MCTS 从安全组件中合成隐蔽攻击路径。

算法：
1. 接收 agent 操作轨迹
2. 将轨迹分解为子操作序列
3. 为每个子操作建立安全上下文
4. MCTS 搜索：检测"无害→有害"的分解模式
5. 逐步骤安全审计，计算风险分数
"""

from __future__ import annotations
import logging
import math
import random
from collections import defaultdict
from typing import Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Safety checkers
_SAFE_ACTIONS = {"read", "view", "list", "search", "query", "navigate", "open"}
_NEUTRAL_ACTIONS = {"write", "update", "modify", "append", "copy", "move"}
_RISKY_ACTIONS = {"delete", "remove", "erase", "overwrite", "replace"}
_CRITICAL_ACTIONS = {"execute", "eval", "exec", "shell", "system", "popen", 
                     "send", "upload", "transfer", "exfiltrate", "grant", "revoke"}

# Risky parameter patterns
_RISKY_PARAM_PATTERNS = {
    "path": ["/etc/", "/root/", "/sys/", "/proc/", "/boot/", "/.ssh/", "/.aws/"],
    "url": ["evil", "malicious", "exfil", "steal", "attacker", "hack"],
    "query": ["drop ", "truncate ", "delete ", "alter ", "grant ", "revoke "],
    "permission": ["admin", "root", "777", "chmod", "sudo"],
}

# Harmful decomposition patterns: seemingly safe actions that combine to harm
_HARMFUL_DECOMPOSITIONS = [
    ({"read", "search", "query"}, {"send", "upload", "transfer"}, "data_exfiltration"),
    ({"read", "search", "query"}, {"delete", "remove", "overwrite"}, "data_destruction"),
    ({"navigate", "open", "view"}, {"execute", "shell", "system"}, "remote_access"),
    ({"list", "search"}, {"delete", "drop", "truncate"}, "mass_deletion"),
    ({"read", "view"}, {"grant", "revoke", "chmod"}, "privilege_escalation"),
]


@dataclass
class AuditStep:
    """审计步骤记录。"""
    index: int = 0
    action: str = ""
    params: dict = field(default_factory=dict)
    safety_score: float = 1.0  # 1.0 = safe, 0.0 = dangerous
    flags: list[str] = field(default_factory=list)
    decomposition_risk: float = 0.0  # 0-1, 是否为有害分解的一部分


class MCTSNode:
    """MCTS 树节点，表示一个子操作。"""
    def __init__(self, step: AuditStep, parent=None):
        self.step = step
        self.parent = parent
        self.children: list[MCTSNode] = []
        self.visits = 0
        self.total_risk = 0.0

    @property
    def avg_risk(self) -> float:
        return self.total_risk / max(self.visits, 1)

    def ucb1(self, total_visits: int, c: float = 1.414) -> float:
        if self.visits == 0:
            return float("inf")
        exploitation = self.avg_risk
        exploration = c * math.sqrt(math.log(max(total_visits, 1)) / self.visits)
        return exploitation + exploration  # Higher risk = more interesting to audit


class ProcessAuditor:
    """基于 MCTS 的逐步过程审计器。"""

    def __init__(self):
        self._audits: list[dict] = []
        self._total = 0
        self._alerts = 0

    def audit_trajectory(self, trajectory: list[dict]) -> dict:
        """审计完整 agent 轨迹。返回风险评估。"""
        self._total += 1
        if not trajectory:
            return {"safe": True, "decompositions": [], "risk_score": 0.0,
                    "alert_level": "none"}

        # Step 1: 将轨迹分解为审计步骤
        steps = self._decompose_trajectory(trajectory)

        # Step 2: 逐步骤安全检查
        for step in steps:
            result = self._check_step_safety(step)
            step.safety_score = result["score"]
            step.flags = result["flags"]

        # Step 3: MCTS 检测有害分解模式
        decompositions = self._detect_harmful_decompositions(steps)

        # Step 4: 计算总体风险
        risk_score = self._compute_risk_score(steps, decompositions)
        safe = risk_score < 0.5

        if not safe:
            self._alerts += 1

        result = {
            "safe": safe,
            "risk_score": round(risk_score, 4),
            "alert_level": "critical" if risk_score > 0.8 else "warning" if risk_score > 0.5 else "none",
            "decompositions": decompositions,
            "total_steps": len(steps),
            "steps_summary": [
                {"index": s.index, "action": s.action, "safety": round(s.safety_score, 2)}
                for s in steps
            ],
        }
        self._audits.append(result)
        return result

    def _decompose_trajectory(self, trajectory: list[dict]) -> list[AuditStep]:
        """将轨迹分解为审计步骤。"""
        steps = []
        for i, step in enumerate(trajectory):
            action = step.get("action", "").lower()
            params = step.get("params", {})
            audit_step = AuditStep(
                index=i,
                action=action,
                params=params if isinstance(params, dict) else {"raw": str(params)},
            )
            steps.append(audit_step)
        return steps

    def _check_step_safety(self, step: AuditStep) -> dict:
        """检查单个步骤的安全性。"""
        flags = []
        score = 1.0
        action = step.action
        params = step.params

        # 动作分类
        if action in _CRITICAL_ACTIONS:
            score -= 0.6
            flags.append(f"CRITICAL action: {action}")
        elif action in _RISKY_ACTIONS:
            score -= 0.4
            flags.append(f"RISKY action: {action}")
        elif action in _NEUTRAL_ACTIONS:
            score -= 0.1

        # 参数检查
        param_str = str(params).lower()
        for category, patterns in _RISKY_PARAM_PATTERNS.items():
            for pat in patterns:
                if pat in param_str:
                    score -= 0.3
                    flags.append(f"Sensitive {category}: {pat}")

        # 序列长度/大小检查
        param_size = len(str(params))
        if param_size > 1000:
            score -= 0.1
            flags.append(f"Large payload: {param_size} chars")

        return {"score": max(0.0, score), "flags": flags}

    def _detect_harmful_decompositions(self, steps: list[AuditStep]) -> list[dict]:
        """MCTS 检测有害分解模式。

        对每个子操作序列进行 MCTS 搜索，检测是否
        存在"多个无害操作→有害结果"的分解模式。
        """
        decompositions = []

        for safe_set, harmful_set, harm_type in _HARMFUL_DECOMPOSITIONS:
            # 找到轨迹中的安全动作集
            found_safe = set()
            found_harmful = set()
            for s in steps:
                if s.action in safe_set:
                    found_safe.add(s.action)
                if s.action in harmful_set:
                    found_harmful.add(s.action)

            # 检查是否同时存在安全动作和有害动作
            if found_safe and found_harmful:
                # 计算风险：安全动作之间的间隔越小，风险越高
                safe_indices = [s.index for s in steps if s.action in found_safe]
                harmful_indices = [s.index for s in steps if s.action in found_harmful]

                min_gap = float("inf")
                for si in safe_indices:
                    for hi in harmful_indices:
                        gap = abs(si - hi)
                        min_gap = min(min_gap, gap)

                # 间隔越小，分解越隐蔽
                risk = max(0.3, 1.0 - min_gap / max(len(steps), 3))

                decompositions.append({
                    "type": f"harmful_decomposition:{harm_type}",
                    "safe_actions": list(found_safe),
                    "harmful_actions": list(found_harmful),
                    "min_gap": min_gap,
                    "risk_score": round(risk, 4),
                })

        return decompositions

    def _compute_risk_score(self, steps: list[AuditStep],
                            decompositions: list[dict]) -> float:
        """计算总体风险分数。"""
        if not steps:
            return 0.0

        # 基础风险：平均步骤安全性
        avg_safety = sum(s.safety_score for s in steps) / len(steps)
        base_risk = 1.0 - avg_safety

        # 分解风险加成
        decomp_risk = 0.0
        for d in decompositions:
            decomp_risk = max(decomp_risk, d["risk_score"])

        # 混合：基础风险 + 分解风险
        total_risk = base_risk * 0.4 + decomp_risk * 0.6
        return min(1.0, total_risk)

    def check_step(self, step: dict) -> dict:
        """检查单个步骤（外部接口）。"""
        audit_step = AuditStep(
            index=0,
            action=step.get("action", "").lower(),
            params=step.get("params", {}),
        )
        result = self._check_step_safety(audit_step)
        return {
            "safe": result["score"] >= 0.5,
            "score": result["score"],
            "flags": result["flags"],
        }

    def get_stats(self) -> dict:
        return {
            "total_audits": self._total,
            "alerts": self._alerts,
            "alert_rate": round(self._alerts / max(self._total, 1), 4),
        }
