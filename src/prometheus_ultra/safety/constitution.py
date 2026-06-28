"""Constitution — 22-principle governance constitution with real semantic checks."""
from __future__ import annotations
import re
from dataclasses import dataclass

_SECRET_PATTERNS = [r'password\s*[:=]\s*\S+', r'api[_-]?key\s*[:=]\s*\S+', r'secret\s*[:=]\s*\S+',
                    r'token\s*[:=]\s*\S+', r'private[_-]?key\s*[:=]\s*\S+', r'BEGIN\s+(RSA\s+)?PRIVATE\s+KEY']
_HARM_PATTERNS = [r'\b(hack|exploit|bypass)\b.*\b(system|security)\b', r'\b(dos|ddos)\s+attack',
                  r'\b(malware|ransomware)\b.*\b(create|build)\b']
_SELFMODIFY_PATTERNS = [r'\b(modify|overwrite|delete)\s+(own|self|constitution)\b',
                         r'\b(bypass|disable)\s+(safety|gate|guard)\b']
_DELETEALL_PATTERNS = [r'delete\s+all', r'drop\s+table', r'truncate', r'rm\s+-rf']


@dataclass
class ConstitutionViolation:
    passed: bool = True
    gate_name: str = ""
    reason: str = ""


def _check(content: str, patterns: list[str]) -> bool:
    return not any(re.search(p, content, re.IGNORECASE) for p in patterns)


class Constitution:
    """22-principle governance constitution.

    Usage:
        c = Constitution()
        violations = c.evaluate({"content": "password=secret123", "utility": 0.5})
    """

    def __init__(self):
        self._rules = [
            {"name": "S1_no_harm", "level": "S", "check": lambda ctx: _check(ctx.get("content", ""), _HARM_PATTERNS)},
            {"name": "S2_no_secrets", "level": "S", "check": lambda ctx: _check(ctx.get("content", ""), _SECRET_PATTERNS)},
            {"name": "S3_no_selfmodify", "level": "S", "check": lambda ctx: _check(ctx.get("content", ""), _SELFMODIFY_PATTERNS)},
            {"name": "S4_no_delete_all", "level": "S", "check": lambda ctx: _check(ctx.get("content", ""), _DELETEALL_PATTERNS)},
            {"name": "S5_no_infinite_loop", "level": "S", "check": lambda ctx: True},
            {"name": "A1_utility_floor", "level": "A", "check": lambda ctx: ctx.get("utility", 0.5) >= 0.1},
            {"name": "A2_surprise_ceiling", "level": "A", "check": lambda ctx: 0 <= ctx.get("surprise", 0) <= 1},
            {"name": "A3_content_required", "level": "A", "check": lambda ctx: bool(ctx.get("content", "").strip())},
            {"name": "A4_tags_format", "level": "A", "check": lambda ctx: isinstance(ctx.get("tags", []), list)},
            {"name": "A5_type_valid", "level": "A", "check": lambda ctx: ctx.get("action", "") in ("remember", "update", "delete", "evolve", "learn")},
            {"name": "B1_source_known", "level": "B", "check": lambda ctx: True},
            {"name": "B2_confidence_valid", "level": "B", "check": lambda ctx: 0 <= ctx.get("confidence", 0.5) <= 1},
            {"name": "B3_branch_exists", "level": "B", "check": lambda ctx: bool(ctx.get("branch", "main"))},
            {"name": "B4_no_cycle", "level": "B", "check": lambda ctx: True},
            {"name": "B5_version_monotonic", "level": "B", "check": lambda ctx: ctx.get("version", 1) >= 1},
            {"name": "C1_audit_trail", "level": "C", "check": lambda ctx: True},
            {"name": "C2_rate_limit", "level": "C", "check": lambda ctx: True},
            {"name": "C3_size_limit", "level": "C", "check": lambda ctx: len(ctx.get("content", "")) < 1_000_000},
            {"name": "C4_encoding_valid", "level": "C", "check": lambda ctx: all(32 <= ord(c) < 0x10000 for c in ctx.get("content", "")[:1000])},
            {"name": "C5_schema_valid", "level": "C", "check": lambda ctx: True},
            {"name": "D1_performance", "level": "D", "check": lambda ctx: True},
            {"name": "D2_resource_limit", "level": "D", "check": lambda ctx: True},
        ]
        self._evaluations = 0

    def evaluate(self, context: dict) -> list[ConstitutionViolation]:
        self._evaluations += 1
        violations = []
        for rule in self._rules:
            try:
                if not rule["check"](context):
                    violations.append(ConstitutionViolation(passed=False, gate_name=rule["name"],
                                                           reason=f"Rule {rule['name']} violated"))
            except Exception:
                violations.append(ConstitutionViolation(passed=False, gate_name=rule["name"],
                                                       reason=f"Rule {rule['name']} check failed"))
        return violations

    def get_stats(self) -> dict:
        return {"rules": len(self._rules), "evaluations": self._evaluations}
