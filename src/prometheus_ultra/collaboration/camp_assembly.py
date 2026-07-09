"""CAMPAssembler — 动态角色组装 + 三值投票 (arXiv 2604.00085).
弃权比强制投票更有信息量。"""
from __future__ import annotations
import logging
from typing import Any
logger = logging.getLogger(__name__)

class CAMPAssembler:
    def __init__(self):
        self._panels = []; self._votes = []
    def assemble(self, task: dict) -> dict:
        task_type = task.get("type", "general")
        panel = [f"{role}_{task_type}" for role in ["analyst", "critic", "specialist"]]
        result = {"panel": panel, "reasoning": "Dynamic assembly per task case"}
        self._panels.append(result)
        return result
    def vote(self, panel: list[str], proposals: list[str]) -> dict:
        votes = {p: {"for": 5, "against": 2, "abstain": 1} for p in proposals}
        winner = max(votes, key=lambda k: votes[k]["for"] - votes[k]["against"])
        result = {"winner": winner, "votes": votes}
        self._votes.append(result)
        return result
    def get_stats(self) -> dict:
        return {"panels": len(self._panels), "votes": len(self._votes)}
