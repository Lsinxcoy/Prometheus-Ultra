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

import logging

logger = logging.getLogger(__name__)

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
    direction: str = ""
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
        # Extended rules for learned knowledge topics — params that actually exist
        {
            "pattern": r"agent.*architectur|multi.?agent|agent.*orchestrat|agent.*pipeline|agent.*memory",
            "module": "dopamine",
            "param": "threshold",
            "direction": "decrease",
            "description": "Lower dopamine threshold when learning agent architecture — make system more receptive",
        },
        {
            "pattern": r"memory.*system|memory.*autonom|external.*memory|working.*memory|memory.*consolidat",
            "module": "forgetting",
            "param": "shape",
            "direction": "decrease",
            "description": "Soften forgetting curve when learning memory system patterns — retain longer",
        },
        {
            "pattern": r"dopamine|reinforcement.*learn|reward.*signal|rl.*mechanism",
            "module": "dopamine",
            "param": "threshold",
            "direction": "decrease",
            "description": "Tune dopamine sensitivity based on RL knowledge",
        },
        {
            "pattern": r"knowledge.*graph|graph.*construct|entity.*relation|graph.*reason",
            "module": "forgetting",
            "param": "scale",
            "direction": "increase",
            "description": "Extend forgetting scale when learning graph construction — broader retention window",
        },
        {
            "pattern": r"self.?evolving|self.?improving|autonomous.*evolution|meta.*learning",
            "module": "dopamine",
            "param": "threshold",
            "direction": "decrease",
            "description": "Lower acceptance threshold when learning self-evolving patterns",
        },
        {
            "pattern": r"exploration|curiosity|intrinsic.*motivat|exploit.*explore",
            "module": "tool_drift",
            "param": "drift_threshold",
            "direction": "decrease",
            "description": "Increase drift sensitivity when learning exploration patterns",
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
                    direction=rule.get("direction", ""),
                )
                mappings.append(mapping)

        self._mappings.extend(mappings)
        return mappings

    def apply_mapping(self, mapping: MechanismMapping, omega) -> bool:
        """Apply a parameter change to the Omega system.

        Writes to omega._learned_config as the persistent parameter layer,
        since most modules are stateless and expose params via get_stats().
        """
        try:
            # First try direct attribute on the target module
            target = getattr(omega, mapping.target_module, None)
            if target is not None and hasattr(target, mapping.target_param):
                old_value = getattr(target, mapping.target_param)
                if isinstance(old_value, (int, float)):
                    new_value = self._compute_new_value(old_value, mapping.direction)
                    mapping.old_value = old_value
                    mapping.new_value = new_value
                    setattr(target, mapping.target_param, new_value)
                    mapping.applied = True
                    self._applied_count += 1
                    return True

            # Fallback: write to omega._learned_config persistent layer
            # Key format: "module:param"
            config_key = f"{mapping.target_module}:{mapping.target_param}"
            learned_cfg = getattr(omega, "_learned_config", {})
            if learned_cfg is None:
                return False

            old_value = learned_cfg.get(config_key)
            if old_value is None:
                # First time: get default from module stats if available
                if target is not None:
                    stats = getattr(target, "get_stats", lambda: {})()
                    old_value = stats.get(mapping.target_param, 0.5)
                else:
                    old_value = 0.5

            if isinstance(old_value, (int, float)):
                new_value = self._compute_new_value(old_value, mapping.direction)
                mapping.old_value = old_value
                mapping.new_value = new_value
                learned_cfg[config_key] = new_value
                mapping.applied = True
                self._applied_count += 1
                return True

            return False
        except Exception:
            return False

    @staticmethod
    def _compute_new_value(old_value: float, direction: str) -> float:
        """Compute adjusted value based on direction."""
        if direction == "decrease":
            return old_value * 0.8
        elif direction == "increase":
            return old_value * 1.2
        return old_value

    def get_stats(self) -> dict:
        return {
            "total_mappings": len(self._mappings),
            "applied": self._applied_count,
        }
