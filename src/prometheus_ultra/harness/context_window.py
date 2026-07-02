"""ContextWindowManager — Manages context window size limits.

Based on: "Long Context RAG Performance of LLMs" (Databricks, 2025)

Key Finding:
    Llama 3.1 405b accuracy drops after 32k tokens.
    Million-token windows have much lower practical usability than theoretical.
    Longer context ≠ better performance.

Algorithm:
    1. Track total token usage across context components
    2. Enforce per-component token budgets
    3. Trigger compression when budget exceeded
    4. Priority-based eviction: keep high-value content
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


from dataclasses import dataclass, field


@dataclass
class ContextBudget:
    total_tokens: int = 128000
    system_prompt_tokens: int = 4000
    history_tokens: int = 32000
    retrieval_tokens: int = 16000
    tool_results_tokens: int = 8000
    reserved_tokens: int = 2000

    @property
    def available_tokens(self) -> int:
        return (self.total_tokens - self.system_prompt_tokens -
                self.reserved_tokens)


@dataclass
class ComponentUsage:
    name: str = ""
    tokens_used: int = 0
    tokens_budget: int = 0
    priority: int = 0


@dataclass
class WindowReport:
    total_used: int = 0
    total_budget: int = 0
    utilization: float = 0.0
    components: list[ComponentUsage] = field(default_factory=list)
    needs_compression: bool = False
    overflow_components: list[str] = field(default_factory=list)


class ContextWindowManager:
    """Manages context window size limits.

    Based on Databricks findings (2025).

    Usage:
        mgr = ContextWindowManager(ContextBudget(total_tokens=128000))
        mgr.register_component("system", 2500, priority=10)
        mgr.register_component("history", 15000, priority=5)
        mgr.register_component("retrieval", 8000, priority=7)
        report = mgr.check()
        if report.needs_compression:
            print(f"Overflow: {report.overflow_components}")
    """

    def __init__(self, budget: ContextBudget | None = None):
        self._budget = budget or ContextBudget()
        self._components: dict[str, ComponentUsage] = {}
        self._reports: list[dict] = []

    def register_component(self, name: str, tokens_used: int, priority: int = 5):
        budget_map = {
            "system": self._budget.system_prompt_tokens,
            "history": self._budget.history_tokens,
            "retrieval": self._budget.retrieval_tokens,
            "tool_results": self._budget.tool_results_tokens,
        }
        budget = budget_map.get(name, self._budget.available_tokens // 4)
        self._components[name] = ComponentUsage(
            name=name, tokens_used=tokens_used,
            tokens_budget=budget, priority=priority,
        )

    def update_usage(self, name: str, tokens_used: int):
        if name in self._components:
            self._components[name].tokens_used = tokens_used

    def check(self) -> WindowReport:
        total_used = sum(c.tokens_used for c in self._components.values())
        total_budget = self._budget.total_tokens - self._budget.reserved_tokens
        utilization = total_used / max(total_budget, 1)

        overflow = []
        for name, comp in self._components.items():
            if comp.tokens_used > comp.tokens_budget:
                overflow.append(name)

        needs_compression = utilization > 0.85 or len(overflow) > 0

        report = WindowReport(
            total_used=total_used,
            total_budget=total_budget,
            utilization=utilization,
            components=list(self._components.values()),
            needs_compression=needs_compression,
            overflow_components=overflow,
        )

        self._reports.append({
            "utilization": utilization,
            "overflow": len(overflow),
        })
        return report

    def suggest_compression(self) -> list[dict]:
        suggestions = []
        sorted_comps = sorted(self._components.values(), key=lambda c: c.priority)
        for comp in sorted_comps:
            if comp.tokens_used > comp.tokens_budget:
                excess = comp.tokens_used - comp.tokens_budget
                suggestions.append({
                    "component": comp.name,
                    "excess_tokens": excess,
                    "action": "compress" if comp.priority < 5 else "evict_low_priority",
                })
        return suggestions

    def get_stats(self) -> dict:
        return {
            "components": len(self._components),
            "total_used": sum(c.tokens_used for c in self._components.values()),
            "budget": self._budget.total_tokens,
        }
