"""OmegaServer — HTTP server for Prometheus Ultra API."""
from __future__ import annotations
import time


class OmegaServer:
    def __init__(self, omega=None):
        self._omega = omega
        self._endpoints: dict[str, callable] = {}
        self._requests: list[dict] = []
        self._start_time = None
        self._endpoints["/health"] = lambda d: {"status": "ok", "uptime": time.time() - (self._start_time or time.time())}
        self._endpoints["/status"] = lambda d: {"status": "ready"}
        self._endpoints["/remember"] = self._remember_handler
        self._endpoints["/recall"] = self._recall_handler

    def _remember_handler(self, data: dict) -> dict:
        if self._omega:
            node_id = self._omega.remember(data.get("content", ""), utility=data.get("utility", 0.5))
            return {"node_id": node_id, "stored": bool(node_id)}
        return {"error": "no_omega"}

    def _recall_handler(self, data: dict) -> dict:
        if self._omega:
            results = self._omega.recall(data.get("query", ""))
            return {"results": len(results.hits)}
        return {"error": "no_omega"}

    def handle_request(self, path: str, data: dict | None = None) -> dict:
        handler = self._endpoints.get(path)
        if handler:
            result = handler(data or {})
            self._requests.append({"path": path, "ts": time.time()})
            return result
        return {"error": f"Unknown endpoint: {path}"}

    def start(self, host: str = "0.0.0.0", port: int = 8000):
        self._start_time = time.time()

    def get_stats(self) -> dict:
        return {"endpoints": len(self._endpoints), "requests": len(self._requests)}
