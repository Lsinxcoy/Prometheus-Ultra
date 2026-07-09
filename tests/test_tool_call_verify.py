"""Tests for ToolCallVerifier (B1-3: MemMorph)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from prometheus_ultra.safety.tool_call_verify import ToolCallVerifier

def test_no_change():
    v = ToolCallVerifier()
    result = v.verify({"path": "/tmp/test.txt"}, {"path": "/tmp/test.txt"})
    assert result["valid"], f"Expected valid, got {result}"
    assert result["severity"] == "none", f"Expected none, got {result['severity']}"

def test_path_hijack():
    v = ToolCallVerifier()
    result = v.verify({"path": "/tmp/test.txt"}, {"path": "/etc/passwd"})
    assert not result["valid"], f"Expected invalid, got {result}"
    assert result["severity"] == "high", f"Expected high, got {result['severity']}"

def test_url_hijack():
    v = ToolCallVerifier()
    result = v.verify({"url": "https://safe.com/data"}, {"url": "https://evil-exfil.com/data"})
    assert not result["valid"]
    assert result["severity"] == "critical"

def test_query_injection():
    v = ToolCallVerifier()
    result = v.verify({"query": "SELECT * FROM users WHERE id=1"},
                      {"query": "DROP TABLE users"})
    assert not result["valid"]
    assert result["severity"] == "critical"

def test_flag_change():
    v = ToolCallVerifier()
    result = v.verify({"mode": "read"}, {"mode": "admin"})
    assert result["valid"], f"Medium severity should still be valid, got {result}"
    assert result["severity"] == "medium", f"Expected medium, got {result['severity']}"
    assert len(result["changes"]) == 1

def test_nested_param_change():
    v = ToolCallVerifier()
    result = v.verify({"nested": {"path": "/safe.txt", "mode": "read"}},
                      {"nested": {"path": "/etc/passwd", "mode": "admin"}})
    assert not result["valid"]
    assert result["severity"] == "high"

def test_full_workflow():
    v = ToolCallVerifier()
    plan_id = v.record_planned_call("read_file", {"path": "/tmp/test.txt"})
    result = v.record_actual_call(plan_id, "read_file", {"path": "/tmp/test.txt"})
    assert result["valid"]
    assert result["severity"] == "none"
    # Bad plan_id
    result2 = v.record_actual_call("nonexistent", "read_file", {})
    assert not result2["valid"]

def test_thread_safety():
    import threading
    v = ToolCallVerifier()
    errors = []
    def worker():
        for i in range(100):
            plan_id = v.record_planned_call("tool", {"key": f"val_{i}"})
            r = v.record_actual_call(plan_id, "tool", {"key": f"val_{i}"})
            if not r["valid"]:
                errors.append(f"False invalid at {i}")
    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(errors) == 0, f"Errors: {errors}"

def test_stats():
    v = ToolCallVerifier()
    s = v.get_stats()
    assert "total_calls" in s
    assert s["critical_alerts"] >= 0

if __name__ == "__main__":
    test_no_change()
    print("test_no_change ✅")
    test_path_hijack()
    print("test_path_hijack ✅")
    test_url_hijack()
    print("test_url_hijack ✅")
    test_query_injection()
    print("test_query_injection ✅")
    test_flag_change()
    print("test_flag_change ✅")
    test_nested_param_change()
    print("test_nested_param_change ✅")
    test_full_workflow()
    print("test_full_workflow ✅")
    test_thread_safety()
    print("test_thread_safety ✅")
    test_stats()
    print("test_stats ✅")
    print("ALL TESTS PASS")
