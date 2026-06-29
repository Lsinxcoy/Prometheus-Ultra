"""FileChecksum — Core file tamper detection.

From MiMo Self-Evolution: "核心文件hash监控防篡改"
"""
from __future__ import annotations
import hashlib, os, json, time


class FileChecksum:
    """Monitor core file integrity via SHA-256 checksums."""
    def __init__(self, path: str = "E:/Prometheus-Ultra/file_checksums.json"):
        self._path = path
        self._checksums: dict[str, str] = {}
        self._load()

    def _load(self):
        if os.path.exists(self._path):
            try:
                with open(self._path, 'r') as f:
                    self._checksums = json.load(f)
            except: self._checksums = {}

    def _flush(self):
        with open(self._path, 'w') as f:
            json.dump(self._checksums, f, indent=2)

    def register(self, file_path: str):
        if os.path.exists(file_path):
            h = hashlib.sha256(open(file_path, 'rb').read()).hexdigest()
            self._checksums[file_path] = h

    def verify(self, file_path: str) -> bool:
        if file_path not in self._checksums or not os.path.exists(file_path):
            return False
        current = hashlib.sha256(open(file_path, 'rb').read()).hexdigest()
        return current == self._checksums[file_path]

    def verify_all(self) -> list[dict]:
        results = []
        for path, expected in self._checksums.items():
            if os.path.exists(path):
                actual = hashlib.sha256(open(path, 'rb').read()).hexdigest()
                results.append({"path": path, "ok": actual == expected})
            else:
                results.append({"path": path, "ok": False, "reason": "missing"})
        return results

    def update_all(self):
        for path in list(self._checksums.keys()):
            if os.path.exists(path):
                self._checksums[path] = hashlib.sha256(open(path, 'rb').read()).hexdigest()
        self._flush()

    def get_stats(self) -> dict:
        return {"files": len(self._checksums)}
