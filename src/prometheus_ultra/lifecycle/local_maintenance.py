"""LocalMaintenance — Per-node maintenance instead of global scan.

Based on: Zhou 2026 "localized maintenance is more cost-efficient than global reorganization"

Key insight: maintaining individual nodes on-demand is cheaper than scanning all nodes.
"""
from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class MaintenanceAction:
    node_id: str = ""
    action: str = ""  # consolidate, prune, migrate, verify
    priority: float = 0.0
    timestamp: float = 0.0


class LocalMaintenance:
    """Per-node maintenance instead of global scan.

    Based on Zhou 2026: localized > global.

    Usage:
        lm = LocalMaintenance(aging_hours=168)
        actions = lm.check_node(node_id, importance=0.3, age_hours=200)
        for action in actions:
            execute(action)
    """

    def __init__(self, aging_hours: float = 168, consolidation_threshold: float = 0.5,
                 prune_threshold: float = 0.2):
        self._aging_hours = aging_hours
        self._consolidation_threshold = consolidation_threshold
        self._prune_threshold = prune_threshold
        self._stats = {"checked": 0, "actions": 0}

    def check_node(self, node_id: str, importance: float = 0.5,
                   age_hours: float = 0.0, access_count: int = 0) -> list[MaintenanceAction]:
        self._stats["checked"] += 1
        actions = []

        if importance < self._prune_threshold and age_hours > self._aging_hours:
            actions.append(MaintenanceAction(
                node_id=node_id, action="prune",
                priority=0.9, timestamp=time.time(),
            ))
        elif importance < self._consolidation_threshold and age_hours > self._aging_hours / 2:
            actions.append(MaintenanceAction(
                node_id=node_id, action="consolidate",
                priority=0.5, timestamp=time.time(),
            ))
        elif access_count == 0 and age_hours > self._aging_hours:
            actions.append(MaintenanceAction(
                node_id=node_id, action="verify",
                priority=0.3, timestamp=time.time(),
            ))

        self._stats["actions"] += len(actions)
        return actions

    def get_stats(self) -> dict:
        return dict(self._stats)
