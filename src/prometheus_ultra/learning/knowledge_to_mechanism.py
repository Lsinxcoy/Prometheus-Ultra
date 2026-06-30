"""KnowledgeToMechanism — Maps learned knowledge to mechanism parameters.

From MiMo: "学了就用，不用不学"

When knowledge is stored, check if it can be applied to system parameters:
- Memory parameters (forgetting curves, consolidation thresholds)
- Safety parameters (gate thresholds, drift detection sensitivity)
- Loop parameters (step budgets, convergence thresholds)
- Harness parameters (timeout, retry counts)

This closes the learning→application loop.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class MechanismMapping:
    knowledge_id: str = ""
    target_module: str = ""
    target_param: str = ""
    old_value: float = 0.0
    new_value: float = 0.0
    reason: str = ""
    applied: bool = False


class KnowledgeToMechanism:
    """Maps learned knowledge to mechanism parameter changes.

    Usage:
        km = KnowledgeToMechanism()
        mappings = km.analyze_knowledge(
            knowledge="Semantic early-stopping reduces tokens by 38%",
            tags=["loop_engineering", "early_stopping"],
        )
        for m in mappings:
            print(f"Would change {m.target_module}.{m.target_param}: {m.old_value} -> {m.new_value}")
    """

    # Knowledge pattern → parameter mapping rules
    MAPPING_RULES = [
        {
            "pattern": r"early.?stop|convergence.*threshold",
            "module": "loop_guard",
            "param": "repetition_window",
            "direction": "decrease",
            "description": "Reduce repetition window for faster convergence detection",
        },
        {
            "pattern": r"memory.*depth|parametric.*consolidation|surprise.*gated",
            "module": "memory_bank",
            "param": "migration_threshold",
            "direction": "decrease",
            "description": "Lower consolidation threshold for surprise-gated writes",
        },
        {
            "pattern": r"co.?failure|ensemble.*limit|beta.*ceiling",
            "module": "agent_forest",
            "param": "max_agents",
            "direction": "decrease",
            "description": "Limit agent count based on co-failure ceiling",
        },
        {
            "pattern": r"forgetting.*curve|retention|decay",
            "module": "forgetting",
            "param": "shape",
            "direction": "adjust",
            "description": "Tune forgetting curve parameters",
        },
        {
            "pattern": r"utility.*decay|reference.*boost|deletion.*threshold",
            "module": "utility_decay",
            "param": "DELETION_THRESHOLD",
            "direction": "adjust",
            "description": "Adjust utility decay rules",
        },
        {
            "pattern": r"drift.*detect|tool.*drift|behavior.*shift",
            "module": "tool_drift",
            "param": "drift_threshold",
            "direction": "decrease",
            "description": "Lower drift detection threshold for earlier alerts",
        },
    ]

    def __init__(self):
        self._mappings: list[MechanismMapping] = []
        self._applied_count = 0

    def analyze_knowledge(self, knowledge: str, tags: list[str] = None) -> list[MechanismMapping]:
        """Analyze if knowledge can be mapped to mechanism parameters."""
        mappings = []
        text = knowledge.lower() + " " + " ".join(tags or [])

        for rule in self.MAPPING_RULES:
            if re.search(rule["pattern"], text, re.IGNORECASE):
                mapping = MechanismMapping(
                    target_module=rule["module"],
                    target_param=rule["param"],
                    reason=rule["description"],
                )
                mappings.append(mapping)

        self._mappings.extend(mappings)
        return mappings

    def apply_mapping(self, mapping: MechanismMapping, omega) -> bool:
        """Apply a parameter change to the Omega system via setattr."""
        try:
            target = getattr(omega, mapping.target_module, None)
            if target is None:
                return False

            if hasattr(target, mapping.target_param):
                old_value = getattr(target, mapping.target_param)
                if isinstance(old_value, (int, float)):
                    if mapping.direction == "decrease":
                        new_value = old_value * 0.8
                    elif mapping.direction == "increase":
                        new_value = old_value * 1.2
                    else:
                        new_value = old_value

                    mapping.old_value = old_value
                    mapping.new_value = new_value
                    setattr(target, mapping.target_param, new_value)
                    mapping.applied = True
                    self._applied_count += 1
                    return True

            return False
        except Exception:
            return False

    def get_stats(self) -> dict:
        return {
            "total_mappings": len(self._mappings),
            "applied": self._applied_count,
        }
