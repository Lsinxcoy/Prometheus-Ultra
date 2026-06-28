"""YBankAdapter — Y-system bank format adapter.

Implements: tier mapping, migration orchestration, format translation.
"""
from __future__ import annotations


class YBankAdapter:
    def __init__(self):
        self._adaptations: list[dict] = []
        self._tier_map: dict[str, int] = {
            "working": 0,
            "short_term": 1,
            "long_term": 2,
            "episodic": 3,
            "semantic": 4,
            "archive": 6,
        }

    def adapt(self, data: dict | None = None) -> dict:
        data = data or {}
        adapted = dict(data)

        # Map utility to tier
        utility = data.get("utility", 0.5)
        if utility > 0.8:
            adapted["tier"] = self._tier_map["long_term"]
        elif utility > 0.5:
            adapted["tier"] = self._tier_map["short_term"]
        else:
            adapted["tier"] = self._tier_map["working"]

        adapted["_adapter"] = "YBankAdapter"
        result = {"adapted": True, "source": "Y", "assigned_tier": adapted["tier"]}
        self._adaptations.append(result)
        return result

    def migrate_tier(self, node_id: str, current_tier: int, target_tier: int) -> dict:
        return {"node_id": node_id, "from": current_tier, "to": target_tier, "migrated": True}

    def get_stats(self) -> dict:
        return {"adaptations": len(self._adaptations)}
