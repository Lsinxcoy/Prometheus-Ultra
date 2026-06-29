"""RuleExpirationAudit — Mark inert rules for deletion.

From MiMo: "30天未触发→标记inert，规则过期审计"
"""
from __future__ import annotations
import time


class RuleExpirationAudit:
    """Audit rules for expiration based on trigger frequency."""
    def __init__(self, security_expires: bool = False, engineering_expiry_days: int = 30):
        self._security_expires = security_expires
        self._expiry_days = engineering_expiry_days
        self._rules: dict[str, dict] = {}

    def register_rule(self, rule_id: str, rule_type: str = "engineering",
                      last_triggered: float = 0.0):
        self._rules[rule_id] = {"type": rule_type, "last_triggered": last_triggered or time.time()}

    def trigger_rule(self, rule_id: str):
        if rule_id in self._rules:
            self._rules[rule_id]["last_triggered"] = time.time()

    def audit(self) -> list[dict]:
        results = []
        now = time.time()
        for rule_id, rule in self._rules.items():
            if rule["type"] == "security" and not self._security_expires:
                continue
            days_since = (now - rule["last_triggered"]) / 86400
            if days_since > self._expiry_days:
                results.append({"rule": rule_id, "type": rule["type"],
                               "days_since_trigger": int(days_since),
                               "action": "inert_candidate"})
        return results

    def get_stats(self) -> dict:
        return {"rules": len(self._rules)}
