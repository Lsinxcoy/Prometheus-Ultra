"""SubAgentContract — Result contract for sub-agent execution.

From MiMo Self-Evolution: "三层压缩+进度锚点+自检指令"
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ContractSpec:
    max_steps: int = 50
    progress_check_interval: int = 3
    max_output_tokens: int = 500
    compression_layers: int = 3
    force_stop_on_repetition: int = 3


@dataclass
class ContractResult:
    status: str = "completed"
    summary: str = ""
    insights: list[str] = field(default_factory=list)
    modifications: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


class SubAgentContract:
    """Enforce contracts on sub-agent execution."""
    def __init__(self, spec: ContractSpec | None = None):
        self._spec = spec or ContractSpec()
        self._history: list[dict] = []

    def generate_task(self, task: str, role: str = "researcher") -> str:
        return ("## Task: %s\n\n"
                "Role: %s\n\n"
                "### Contract\n"
                "- Max steps: %d\n"
                "- Progress check every %d steps\n"
                "- Max output: %d tokens\n"
                "- Repetition limit: %d consecutive identical outputs\n\n"
                "### Output Format\n"
                "1. Summary (<=100 tokens)\n"
                "2. Key insights (3-5 items)\n"
                "3. Behavior modifications (if any)\n" % (
                    task, role, self._spec.max_steps,
                    self._spec.progress_check_interval,
                    self._spec.max_output_tokens,
                    self._spec.force_stop_on_repetition))

    def check_progress(self, steps_used: int, consecutive_repetitions: int) -> tuple[bool, str]:
        if steps_used >= self._spec.max_steps:
            return False, "max_steps_exceeded"
        if consecutive_repetitions >= self._spec.force_stop_on_repetition:
            return False, "repetition_limit"
        return True, "ok"

    def get_stats(self) -> dict:
        return {"max_steps": self._spec.max_steps, "history": len(self._history)}
