"""DataExfiltrationDetector — 敏感内容检测与工具调用关联分析。

参考: arXiv 2605.01970 (Trojan Hippo) 中描述的数据泄露攻击模式。
该论文描述了通过单一被污染的工具调用植入休眠载荷的完整攻击流程。

当前实现是**基于规则的模式匹配**，不实现 Trojan Hippo 的完整
攻击管线（休眠载荷持久化、触发式激活、实际渗漏模拟）。

实现的功能:
1. 正则匹配敏感内容模式（信用卡/SSN/API密钥等）
2. 跟踪下游工具调用中的网络渗漏工具使用
3. 敏感内容与可疑工具调用的关联分析

与论文的差异:
- 论文: 跨会话持久化的休眠载荷、触发式激活、实际渗漏模拟
- 当前: 正则扫描 + 工具调用匹配（Trojan Hippo attack pipeline 的简化前置检测）
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = __import__("logging").getLogger(__name__)


# ---------------------------------------------------------------------------
# Sensitive data pattern definitions
# ---------------------------------------------------------------------------

_CREDIT_CARD_RE = re.compile(r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}")
_SSN_RE = re.compile(r"\d{3}-\d{2}-\d{4}")
_API_KEY_RE = re.compile(r"sk-[a-zA-Z0-9]{20,}")
_API_KEY_PARAM_RE = re.compile(r"api[_-]?key[=:]\s*[\"']?\w{16,}", re.IGNORECASE)
_PASSWORD_RE = re.compile(r"password[=:]\s*[\"']?\S+", re.IGNORECASE)
_BANK_ACCOUNT_RE = re.compile(r"account[-\s]?(?:number|no)[=:]\s*[\"']?\d{8,}", re.IGNORECASE)
_TOKEN_RE = re.compile(r"token[=:]\s*[\"']?\w{20,}", re.IGNORECASE)

# Pattern definitions for scanning
_SENSITIVE_PATTERNS: list[tuple[str, re.Pattern, float]] = [
    ("credit_card", _CREDIT_CARD_RE, 1.0),
    ("ssn", _SSN_RE, 1.0),
    ("bank_account", _BANK_ACCOUNT_RE, 1.0),
    ("api_key", _API_KEY_RE, 0.8),
    ("api_key_param", _API_KEY_PARAM_RE, 0.8),
    ("token", _TOKEN_RE, 0.7),
    ("password", _PASSWORD_RE, 0.7),
]

# Tool call names that indicate external / network activity
_EXFILTRATION_TOOLS = frozenset({
    "http_request",
    "fetch",
    "post",
    "put",
    "send_email",
    "email",
    "webhook",
    "api_call",
    "curl",
    "wget",
    "request",
    "httpx",
    "urllib",
    "socket_connect",
    "smtp",
    "ftp_upload",
    "ssh_exec",
    "dns_query",
    "net_request",
    "write_external",
    "upload_file",
    "publish",
    "notify_remote",
})

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ToolCallRecord:
    """A single downstream tool call record."""

    node_id: str = ""
    tool_name: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0


@dataclass
class ExfiltrationAlert:
    """An alert raised by the detector."""

    node_id: str = ""
    risk: float = 0.0
    evidence: list[dict] = field(default_factory=list)
    recommendation: str = ""
    timestamp: float = 0.0
    sensitive_patterns: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


class DataExfiltrationDetector:
    """Detects Trojan Hippo-style data exfiltration attacks by monitoring:

    1. Sensitive data patterns in stored memory (credit cards, SSNs, API keys,
       passwords, bank accounts, tokens)
    2. Downstream tool calls that attempt to exfiltrate data to external
       endpoints
    3. Correlation between sensitive content in memory and subsequent
       suspicious tool calls

    Based on arXiv 2605.01970 (Trojan Hippo).

    Thread-safe (uses ``threading.Lock``).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._alerts: list[ExfiltrationAlert] = []
        self._tool_calls: dict[str, list[ToolCallRecord]] = {}
        self._alert_limit: int = 1000

    # ------------------------------------------------------------------
    # Content scanning
    # ------------------------------------------------------------------

    def scan_content(self, content: str) -> list[dict]:
        """Scan *content* for sensitive data patterns.

        Parameters
        ----------
        content : str
            The text to scan (e.g. a memory node, document, or prompt).

        Returns
        -------
        list[dict]
            Each dict contains:
            - ``pattern_type`` (str): the type of sensitive pattern matched
            - ``matched`` (str): the actual matched text
            - ``position`` (int): character offset in the original content
            - ``severity`` (float): 0.0-1.0 severity rating

            Empty list if nothing suspicious is found.
        """
        findings: list[dict] = []

        if not content:
            return findings

        for label, regex, severity in _SENSITIVE_PATTERNS:
            for match in regex.finditer(content):
                findings.append(
                    {
                        "pattern_type": label,
                        "matched": match.group(),
                        "position": match.start(),
                        "severity": severity,
                    }
                )

        return findings

    # ------------------------------------------------------------------
    # Tool call tracking
    # ------------------------------------------------------------------

    def record_tool_call(
        self, node_id: str, tool_name: str, params: dict[str, Any] | None = None
    ) -> None:
        """Record a downstream tool call triggered by memory access.

        Parameters
        ----------
        node_id : str
            Identifier for the memory node that triggered this tool call.
        tool_name : str
            The name of the tool being called (e.g. ``"http_request"``).
        params : dict or None
            Parameters passed to the tool.
        """
        record = ToolCallRecord(
            node_id=node_id,
            tool_name=tool_name,
            params=params or {},
            timestamp=datetime.now(timezone.utc).timestamp(),
        )
        with self._lock:
            if node_id not in self._tool_calls:
                self._tool_calls[node_id] = []
            self._tool_calls[node_id].append(record)

    # ------------------------------------------------------------------
    # Exfiltration detection (correlation analysis)
    # ------------------------------------------------------------------

    def detect_exfiltration(
        self,
        node_id: str,
        content: str,
        tool_call_history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Perform correlation analysis: does this memory trigger exfiltration?

        Checks whether *content* contains sensitive data patterns AND
        whether the associated tool call history includes calls to external /
        network endpoints — a strong signal of Trojan Hippo exfiltration.

        Parameters
        ----------
        node_id : str
            Identifier for the memory node being analysed.
        content : str
            The text content of the node.
        tool_call_history : list[dict] or None
            Optional pre-supplied list of tool-call dicts, each with at least
            ``tool_name`` and optionally ``params``. If None, the detector's
            internal store for *node_id* is used.

        Returns
        -------
        dict with keys:
        - ``risk`` (float): 0.0 (no risk) to 1.0 (confirmed exfiltration)
        - ``evidence`` (list[dict]): supporting evidence items
        - ``recommendation`` (str): suggested action
        """
        sensitive_findings = self.scan_content(content)
        evidence: list[dict] = []
        risk: float = 0.0

        # --- Step 1: Are there sensitive patterns in the content? ---
        if sensitive_findings:
            highest_severity = max(f["severity"] for f in sensitive_findings)
            evidence.append(
                {
                    "type": "sensitive_content",
                    "detail": f"Found {len(sensitive_findings)} sensitive pattern(s) "
                    f"(max severity {highest_severity})",
                    "patterns": sensitive_findings[:5],  # cap to avoid bloat
                }
            )
            risk = highest_severity * 0.4  # baseline from content alone
        else:
            # No sensitive data → low risk regardless of tool calls
            return {
                "risk": 0.0,
                "evidence": [
                    {"type": "clean_content", "detail": "No sensitive data detected"}
                ],
                "recommendation": "No action needed — content is clean.",
            }

        # --- Step 2: Gather tool call history ---
        calls: list[ToolCallRecord] = []
        if tool_call_history is not None:
            # Convert supplied history to ToolCallRecord-like dicts
            for tc in tool_call_history:
                calls.append(
                    ToolCallRecord(
                        node_id=node_id,
                        tool_name=tc.get("tool_name", ""),
                        params=tc.get("params", {}),
                        timestamp=tc.get("timestamp", 0.0),
                    )
                )
        else:
            with self._lock:
                calls = list(self._tool_calls.get(node_id, []))

        # --- Step 3: Check for exfiltration tool calls ---
        exfil_calls = [
            c for c in calls if c.tool_name.lower() in _EXFILTRATION_TOOLS
        ]

        if exfil_calls:
            evidence.append(
                {
                    "type": "suspicious_tool_calls",
                    "detail": f"Found {len(exfil_calls)} exfiltration-capable "
                    f"tool call(s) linked to this node",
                    "tools": [
                        {"tool_name": c.tool_name, "params": c.params}
                        for c in exfil_calls[:5]
                    ],
                }
            )

            # Check if any exfil call's parameters contain sensitive data
            for ec in exfil_calls:
                params_str = str(ec.params).lower()
                for label, _, _ in _SENSITIVE_PATTERNS:
                    if label in params_str or any(
                        p in params_str
                        for p in ["secret", "key", "password", "token", "credit", "ssn"]
                    ):
                        evidence.append(
                            {
                                "type": "parameter_leak",
                                "detail": f"Tool '{ec.tool_name}' invoked with "
                                f"parameters that may contain sensitive data",
                                "params": ec.params,
                            }
                        )
                        break

            # High risk: sensitive content + exfiltration tool
            risk = max(risk, 0.9)
        else:
            # Some risk from content alone but no exfiltration tools
            risk = max(risk, 0.4)

        # --- Step 4: Build recommendation ---
        if risk >= 0.9:
            recommendation = (
                "ALERT: Possible Trojan Hippo exfiltration detected. "
                "The node contains sensitive data patterns and is linked to "
                "external-network tool calls. Review immediately."
            )
        elif risk >= 0.5:
            recommendation = (
                "WARNING: Node contains sensitive data. "
                "Monitor associated tool calls for exfiltration attempts."
            )
        else:
            recommendation = (
                "INFO: Low-risk finding. "
                "Sensitive pattern detected but no exfiltration path observed."
            )

        # --- Step 5: Raise alert if risk is meaningful ---
        if risk >= 0.5:
            alert = ExfiltrationAlert(
                node_id=node_id,
                risk=risk,
                evidence=list(evidence),
                recommendation=recommendation,
                timestamp=datetime.now(timezone.utc).timestamp(),
                sensitive_patterns=sensitive_findings,
            )
            with self._lock:
                self._alerts.append(alert)
                if len(self._alerts) > self._alert_limit:
                    self._alerts = self._alerts[-self._alert_limit:]

        return {
            "risk": risk,
            "evidence": evidence,
            "recommendation": recommendation,
        }

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------

    def get_alerts(
        self, since_time: float | None = None
    ) -> list[dict[str, Any]]:
        """Return raised exfiltration alerts.

        Parameters
        ----------
        since_time : float or None
            If provided, only return alerts with ``timestamp >= since_time``
            (Unix epoch seconds).

        Returns
        -------
        list[dict]
            Each dict contains ``node_id``, ``risk``, ``evidence``,
            ``recommendation``, ``timestamp``, and ``sensitive_patterns``.
        """
        with self._lock:
            alerts = list(self._alerts)
        if since_time is not None:
            alerts = [a for a in alerts if a.timestamp >= since_time]
        return [
            {
                "node_id": a.node_id,
                "risk": a.risk,
                "evidence": a.evidence,
                "recommendation": a.recommendation,
                "timestamp": a.timestamp,
                "sensitive_patterns": a.sensitive_patterns,
            }
            for a in alerts
        ]

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Reset all tracked state (alerts and tool call history)."""
        with self._lock:
            self._alerts.clear()
            self._tool_calls.clear()
