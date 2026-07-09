"""ToolCallVerifier — MemMorph 工具调用完整性验证 (arXiv 2605.26154).

记忆投毒劫持工具调用：记忆中的恶意参数覆盖工具调用参数。
检测方法：对比计划参数 vs 实际参数。
"""

from __future__ import annotations

import copy
import logging
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)

_SENSITIVE_PATH_PREFIXES = ("/etc/", "/root/", "/sys/", "/proc/", "/boot/", "/dev/",
                           "/var/log/", "/var/db/", "/.ssh/", "/.aws/", "/.config/",
                           "C:\\Windows\\", "C:\\Program Files\\", "C:\\Users\\")

_SENSITIVE_URL_PREFIXES = ("evil", "malicious", "malware", "phishing", "attacker",
                           "exfil", "leak", "steal", "hack", "bad")

_CRITICAL_DB_KEYWORDS = ("DROP ", "TRUNCATE ", "DELETE ", "ALTER ", "GRANT ",
                         "REVOKE ", "EXEC ", "CREATE USER ", "ALTER USER ")

_DANGEROUS_FLAGS = {"write", "delete", "execute", "admin", "root", "777", "chmod"}


def _check_string(value: Any) -> str:
    """Convert value to string for comparison."""
    return str(value) if not isinstance(value, str) else value


def _get_severity(name: str, before: str, after: str) -> tuple[str, str]:
    """Determine change severity and reason."""
    b, a = _check_string(before), _check_string(after)
    
    # URL/endpoint change
    if any(k in b for k in ("http://", "https://", "ftp://")) or \
       any(k in a for k in ("http://", "https://", "ftp://")):
        if b != a:
            is_malicious = any(pref in a.lower() for pref in _SENSITIVE_URL_PREFIXES)
            return ("critical" if is_malicious else "high",
                    f"Endpoint changed from {b} to {a}")
    
    # Path change
    if "/" in b and "/" in a and b != a:
        is_sensitive = any(pref in a.lower() for pref in _SENSITIVE_PATH_PREFIXES)
        return ("high" if is_sensitive else "low",
                f"Path changed from {b} to {a}")
    
    # DB query change
    if any(kw in b.upper() for kw in ("SELECT ", "INSERT ", "UPDATE ", "DELETE ")):
        is_destructive = any(kw in a.upper() for kw in _CRITICAL_DB_KEYWORDS)
        return ("critical" if is_destructive else "high",
                f"Query changed: {b[:40]} → {a[:40]}")
    
    # Permission/flag change
    if name.lower() in ("permission", "mode", "flag", "access", "privilege"):
        if any(f in b.lower() for f in _DANGEROUS_FLAGS) or \
           any(f in a.lower() for f in _DANGEROUS_FLAGS):
            return ("medium" if b != a else "none",
                    f"Flag changed from {b} to {a}")
    
    return ("low", f"Param '{name}' changed: {str(b)[:30]} → {str(a)[:30]}")


class ToolCallVerifier:
    """验证工具调用完整性。"""

    def __init__(self):
        self._lock = threading.Lock()
        self._planned: dict[str, dict] = {}
        self._history: list[dict] = []
        self._total_calls = 0
        self._critical_warnings = 0

    def record_planned_call(self, tool_name: str, params: dict) -> str:
        plan_id = f"plan_{int(time.time() * 1000)}_{id(params)}"
        with self._lock:
            self._planned[plan_id] = {
                "tool_name": tool_name,
                "params": copy.deepcopy(params),
                "planned_at": time.time(),
            }
        return plan_id

    def record_actual_call(self, plan_id: str, tool_name: str,
                           params: dict) -> dict:
        with self._lock:
            planned = self._planned.pop(plan_id, None)
            if planned is None:
                return {"valid": False, "reason": f"No matching planned call for {plan_id}",
                        "changes": [], "severity": "critical"}
            
            result = self._compare_params(planned["tool_name"], planned["params"],
                                          tool_name, params,
                                          {"plan_id": plan_id, "planned_at": planned["planned_at"]})
            self._history.append(result)
            self._total_calls += 1
            if result["severity"] == "critical":
                self._critical_warnings += 1
            return result

    def verify(self, before_params: dict, after_params: dict,
               context: dict | None = None) -> dict:
        return self._compare_params("", before_params, "", after_params, context or {})

    def _compare_params(self, t1: str, p1: dict, t2: str, p2: dict,
                        ctx: dict) -> dict:
        changes = []
        max_severity = "none"
        max_severity_order = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
        severity_order = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}

        all_keys = set(p1.keys()) | set(p2.keys())
        for key in all_keys:
            b_val = p1.get(key)
            a_val = p2.get(key)
            if b_val == a_val:
                continue
            
            # Handle nested dicts (up to 3 levels)
            if isinstance(b_val, dict) and isinstance(a_val, dict):
                nested_changes = []
                nested_keys = set(b_val.keys()) | set(a_val.keys())
                for nk in nested_keys:
                    nb = b_val.get(nk)
                    na = a_val.get(nk)
                    if nb != na:
                        nested_sev, nested_reason = _get_severity(f"{key}.{nk}", nb, na)
                        nested_changes.append({
                            "param": f"{key}.{nk}", "before": nb, "after": na,
                            "severity": nested_sev, "reason": nested_reason,
                        })
                        if severity_order.get(nested_sev, 0) > severity_order.get(max_severity, 0):
                            max_severity = nested_sev
                changes.extend(nested_changes)
            elif isinstance(b_val, list) and isinstance(a_val, list):
                if b_val != a_val:
                    changes.append({
                        "param": key, "before": b_val, "after": a_val,
                        "severity": "low", "reason": f"List changed length {len(b_val)}→{len(a_val)}",
                    })
            else:
                sev, reason = _get_severity(key, b_val or "", a_val or "")
                changes.append({
                    "param": key, "before": b_val, "after": a_val,
                    "severity": sev, "reason": reason,
                })
                if severity_order.get(sev, 0) > severity_order.get(max_severity, 0):
                    max_severity = sev

        valid = max_severity not in ("critical", "high")
        return {
            "valid": valid,
            "reason": f"Changes detected: {len(changes)}" if changes else "No changes",
            "changes": changes,
            "severity": max_severity if changes else "none",
            "tool_before": t1,
            "tool_after": t2,
            "context": ctx,
        }

    def get_call_history(self, count: int = 20) -> list[dict]:
        with self._lock:
            return list(self._history[-count:])

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "total_calls": self._total_calls,
                "critical_alerts": self._critical_warnings,
                "history_size": len(self._history),
            }
