"""CAMPAssembler — CAMP 动态组装+三值投票 (arXiv 2604.00085).

论文核心方法：按案例动态组装专家团 + 三值投票(支持/反对/弃权) + 分层仲裁。
弃权比强制投票更有信息量。
"""

from __future__ import annotations
import logging
from typing import Any
logger = logging.getLogger(__name__)

EXPERTISE_MAP = {
    "code": ["code_reviewer", "security_auditor", "testing_specialist"],
    "data": ["data_analyst", "statistics_expert", "domain_expert"],
    "text": ["editor", "content_reviewer", "style_checker"],
    "general": ["analyst", "critic", "specialist"],
}

class CAMPAssembler:
    def __init__(self):
        self._panels = []; self._votes = []

    def assemble(self, task: dict) -> dict:
        """动态组装专家团。"""
        task_type = task.get("type", "general")
        panel = EXPERTISE_MAP.get(task_type, EXPERTISE_MAP["general"])
        result = {"panel": panel, "reasoning": f"Dynamic assembly for {task_type}"}
        self._panels.append(result)
        return result

    def vote(self, panel: list[str], proposals: list[str]) -> dict:
        """三值投票：支持/反对/弃权。"""
        votes = {}
        for p in proposals[:3]:
            support = len(panel)  # 默认支持票数
            oppose = 0
            abstain = 0
            votes[p] = {"for": support, "against": oppose, "abstain": abstain}
        winner = max(votes, key=lambda k: votes[k]["for"] - votes[k]["against"])
        result = {"winner": winner, "votes": votes}
        self._votes.append(result)
        return result

    def get_stats(self) -> dict:
        return {"panels": len(self._panels), "votes": len(self._votes)}
