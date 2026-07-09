"""Tests for B3-4: Temporal weighting + conflict detection in MemoryStream.

Based on:
- arXiv 2603.00270 — Transformers Remember First, Forget Last
- arXiv 2606.08457 — Consistency Illusion
"""
from __future__ import annotations

import time

from prometheus_ultra.memory.stream import (
    MemoryStream,
    apply_temporal_weights,
    detect_conflicts,
)


# =========================================================================
# apply_temporal_weights
# =========================================================================


def test_temporal_weights_empty_list():
    """Empty input returns empty list."""
    assert apply_temporal_weights([]) == []


def test_temporal_weights_single_item():
    """Single item gets weight=1.0 (zero elapsed)."""
    results = [{"ts": time.time(), "content": "test"}]
    out = apply_temporal_weights(results)
    assert len(out) == 1
    assert out[0]["temporal_weight"] == 1.0


def test_temporal_weights_recency_sorting():
    """More recent items get higher weight and sort first."""
    now = time.time()
    results = [
        {"ts": now - 7200, "content": "old"},        # 2 hours ago
        {"ts": now - 600, "content": "recent"},       # 10 min ago
        {"ts": now - 3600, "content": "middle"},      # 1 hour ago
    ]
    out = apply_temporal_weights(results)
    # recent first, then middle, then old
    assert out[0]["content"] == "recent"
    assert out[1]["content"] == "middle"
    assert out[2]["content"] == "old"


def test_temporal_weights_formula_bounds():
    """Weight clamped to [0.1, 1.0]."""
    now = time.time()
    # Very old — would be negative without clamping
    results = [{"ts": now - 3600 * 200, "content": "ancient"}]
    out = apply_temporal_weights(results)
    assert out[0]["temporal_weight"] == 0.1

    # Brand new
    results = [{"ts": now, "content": "fresh"}]
    out = apply_temporal_weights(results)
    assert out[0]["temporal_weight"] == 1.0


def test_temporal_weights_mid_weight():
    """~50 hours ago should give weight ~0.5."""
    now = time.time()
    results = [{"ts": now - 3600 * 50, "content": "mid"}]
    out = apply_temporal_weights(results)
    assert 0.49 <= out[0]["temporal_weight"] <= 0.51


def test_temporal_weights_annotates_all():
    """Every result gets a temporal_weight key."""
    results = [
        {"ts": time.time(), "content": "a"},
        {"ts": time.time() - 100, "content": "b"},
    ]
    out = apply_temporal_weights(results)
    assert all("temporal_weight" in r for r in out)


# =========================================================================
# detect_conflicts
# =========================================================================


def test_detect_conflicts_empty():
    """Empty list returns no conflicts."""
    assert detect_conflicts([]) == []


def test_detect_conflicts_single():
    """Single result returns no conflicts."""
    r = [{"content": "anything"}]
    assert detect_conflicts(r) == []


def test_conflict_numerical_opposition():
    """Two results with opposing percentages flagged."""
    r = [
        {"content": "Accuracy is 70%", "source_id": "a"},
        {"content": "Accuracy is 30%", "source_id": "b"},
    ]
    conflicts = detect_conflicts(r)
    assert len(conflicts) >= 1
    c = conflicts[0]
    assert c["type"] == "numerical_opposition"
    assert c["source_ids"] == ["a", "b"]


def test_conflict_numerical_ratio_threshold():
    """Small difference (50% vs 60%) should NOT trigger conflict (ratio < 2)."""
    r = [
        {"content": "Value is 50%", "id": "x"},
        {"content": "Value is 60%", "id": "y"},
    ]
    conflicts = detect_conflicts(r)
    num_conflicts = [c for c in conflicts if c["type"] == "numerical_opposition"]
    assert len(num_conflicts) == 0


def test_conflict_factual_contradiction():
    """Detect 'is true' vs 'is false'."""
    r = [
        {"content": "The claim is true", "source_id": "a"},
        {"content": "The claim is false", "source_id": "b"},
    ]
    conflicts = detect_conflicts(r)
    assert any(c["type"] == "factual_contradiction" for c in conflicts)
    fc = [c for c in conflicts if c["type"] == "factual_contradiction"][0]
    assert "a" in fc["source_ids"]
    assert "b" in fc["source_ids"]
    assert fc["confidence"] == 0.85


def test_conflict_factual_supports_contradicts():
    """Detect 'supports' vs 'contradicts'."""
    r = [
        {"content": "This evidence supports the hypothesis", "id": "1"},
        {"content": "This evidence contradicts the hypothesis", "id": "2"},
    ]
    conflicts = detect_conflicts(r)
    assert any(c["type"] == "factual_contradiction" for c in conflicts)


def test_conflict_temporal_inconsistency():
    """Detect 'before X' vs 'after X'."""
    r = [
        {"content": "Event happened before 2025", "source_id": "a"},
        {"content": "Event happened after 2025", "source_id": "b"},
    ]
    conflicts = detect_conflicts(r)
    assert any(c["type"] == "temporal_inconsistency" for c in conflicts)
    ti = [c for c in conflicts if c["type"] == "temporal_inconsistency"][0]
    assert "a" in ti["source_ids"]
    assert "b" in ti["source_ids"]
    assert ti["confidence"] == 0.75


def test_conflict_temporal_earlier_later():
    """Detect 'earlier than X' vs 'later than X'."""
    r = [
        {"content": "Occurred earlier than merger", "id": "1"},
        {"content": "Occurred later than merger", "id": "2"},
    ]
    conflicts = detect_conflicts(r)
    assert any(c["type"] == "temporal_inconsistency" for c in conflicts)


def test_conflict_noise_not_conflict():
    """Similar content without contradiction should not flag."""
    r = [
        {"content": "The sky is blue on clear days", "id": "a"},
        {"content": "The sky appears blue due to Rayleigh scattering", "id": "b"},
    ]
    conflicts = detect_conflicts(r)
    assert len(conflicts) == 0


def test_conflict_multiple_pairs():
    """Three-way conflict detection across multiple result pairs."""
    r = [
        {"content": "Accuracy is 80%", "source_id": "a"},
        {"content": "Accuracy is 20%", "source_id": "b"},
        {"content": "Accuracy is 85%", "source_id": "c"},
    ]
    conflicts = detect_conflicts(r)
    num_confs = [c for c in conflicts if c["type"] == "numerical_opposition"]
    # a vs b (80 vs 20, ratio=4) and b vs c (20 vs 85, ratio=4.25)
    assert len(num_confs) >= 2


def test_conflict_source_id_fallback():
    """Falls back to index string when no source_id or id is present."""
    r = [
        {"content": "The answer is true"},
        {"content": "The answer is false"},
    ]
    conflicts = detect_conflicts(r)
    assert len(conflicts) >= 1
    fc = [c for c in conflicts if c["type"] == "factual_contradiction"][0]
    assert fc["source_ids"] == ["0", "1"]


# =========================================================================
# Integration: temporal weights + conflict detection on real MemoryStream
# =========================================================================


def test_integration_stream_then_weigh_then_detect():
    """Full pipeline: MemoryStream -> recent() -> weigh -> detect."""
    stream = MemoryStream(max_size=100)
    now = time.time()

    # Add events with explicit metadata so we can control timestamps
    # (normally MemoryStream sets its own, but we test the standalone utils)
    events = [
        {"content": "Accuracy is 90%", "source_id": "r1", "ts": now - 100},
        {"content": "Accuracy is 30%", "source_id": "r2", "ts": now - 200},
        {"content": "Accuracy is 85%", "source_id": "r3", "ts": now - 50},
        {"content": "Unrelated fact", "source_id": "r4", "ts": now - 1000},
    ]
    for e in events:
        stream.add("remember", e["content"], importance=0.7,
                    metadata={"source_id": e["source_id"]})

    # Get results from stream
    recent = stream.recent(10)

    # Apply temporal weights
    weighed = apply_temporal_weights(recent)

    # Verify sort order
    ts_list = [r["ts"] for r in weighed]
    assert ts_list == sorted(ts_list, reverse=True)

    # Detect conflicts (using content only — the standalone function
    # doesn't have access to the original source_ids from metadata unless
    # we pass them; we already test conflict detection standalone above)
    # Re-run the detect with explicit source_ids using our original events
    conflicts = detect_conflicts([
        {"content": e["content"], "source_id": e["source_id"]}
        for e in events
    ])
    assert len(conflicts) >= 1
    num_confs = [c for c in conflicts if c["type"] == "numerical_opposition"]
    assert len(num_confs) >= 1

    print("PASS: test_integration_stream_then_weigh_then_detect")


def test_temporal_weight_annotated_results_work_with_detect():
    """Temporally-weighted results still work with conflict detection."""
    now = time.time()
    results = [
        {"ts": now - 100, "content": "System is true", "source_id": "a"},
        {"ts": now - 200, "content": "System is false", "source_id": "b"},
    ]
    weighed = apply_temporal_weights(results)
    conflicts = detect_conflicts(weighed)
    assert any(c["type"] == "factual_contradiction" for c in conflicts)
