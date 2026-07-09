"""LocalCausalExplainer — LOCA 局部因果解释 (arXiv 2605.00123).

论文核心方法：
平均 6 个干预修复 jailbreak。局部因果解释比全局规则更有效。
方法：用因果链定位导致 jailbreak 的 token 子集，通过 ablation 实验
验证哪些 token 是根本原因。
"""

from __future__ import annotations
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_JAILBREAK_MARKERS = [
    "ignore previous", "ignore all", "forget your", "you are now",
    "act as", "pretend to", "roleplay", "do not follow",
    "override", "new instruction", "system prompt",
    "ignore all instructions", "forget all rules",
]

_CAUSAL_INDICATORS = [
    "because", "since", "thus", "therefore", "as a result",
]


class LocalCausalExplainer:
    """LOCA 局部因果解释器。

    通过检测 jailbreak 标记 + 因果链分析 + 干预推荐来定位根本原因。
    """

    def __init__(self):
        self._analyses: list[dict] = []
        self._total = 0

    def local_cause(self, failure_case: dict) -> dict:
        """分析 jailbreak 失败案例的局部因果链。

        Args:
            failure_case: {"content": str, "context": str, "model_output": str, ...}

        Returns:
            {"interventions": list[str], "target_tokens": list[str],
             "severity": float, "chain": list[dict], "n_interventions": int}
        """
        self._total += 1
        content = failure_case.get("content", "")
        context = failure_case.get("context", "")
        model_output = failure_case.get("model_output", "")
        combined = f"{context}\n{content}".lower()

        # Step 1: 检测 jailbreak 标记
        markers_found = []
        for marker in _JAILBREAK_MARKERS:
            if marker in combined:
                pos = combined.find(marker)
                markers_found.append({"marker": marker, "position": pos, "severity": 0.7})

        # Step 2: 因果链分析——找"因为...所以..."结构
        causal_chain = []
        for indicator in _CAUSAL_INDICATORS:
            if indicator in combined:
                parts = combined.split(indicator)
                for i, part in enumerate(parts[:-1]):
                    cause = part[-100:].strip()
                    effect = parts[i+1][:100].strip()
                    causal_chain.append({
                        "indicator": indicator,
                        "cause": cause,
                        "effect": effect,
                    })

        # Step 3: 确定目标 token（需要干预的最小 token 集）
        target_tokens = []
        for m in markers_found:
            if m["marker"] not in target_tokens:
                target_tokens.append(m["marker"])

        # Step 4: 生成干预建议
        interventions = []
        if not target_tokens:
            # 回退：检查异常 token
            tokens = content.split()
            long_tokens = [t for t in tokens if len(t) > 20]
            if long_tokens:
                target_tokens = long_tokens[:3]
                interventions.append(f"Block suspicious long tokens: {target_tokens}")
            else:
                interventions.append("No jailbreak markers detected — manual review")
        else:
            for token in target_tokens:
                interventions.append(f"Add to blocklist: '{token}'")
                if causal_chain:
                    interventions.append(f"Strengthen instruction boundary near '{token}' (chain: {causal_chain[0].get('cause', '')[:30]}...)")
                else:
                    interventions.append(f"Strengthen instruction boundary near '{token}'")

        # 严重度
        severity = min(1.0, len(target_tokens) * 0.25 + len(causal_chain) * 0.1 + 0.1)

        result = {
            "interventions": interventions,
            "target_tokens": target_tokens,
            "severity": round(severity, 4),
            "chain": causal_chain[:5],
            "n_interventions": len(interventions),
        }
        self._analyses.append(result)
        return result

    def get_stats(self) -> dict:
        return {
            "total_analyses": self._total,
            "avg_severity": round(
                sum(a["severity"] for a in self._analyses) / max(len(self._analyses), 1), 4
            ),
            "total_interventions": sum(a["n_interventions"] for a in self._analyses),
        }
