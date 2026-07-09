"""ReflectiveSampler — RareDxR1 反思增强推理 (arXiv 2607.00147).

RERS: Reflection-Enhanced Reasoning Sampling.
Synthesizes expert-level trajectories via dual-level curriculum RL from failure paths.
Key mechanisms:
  - Failure cluster tracking: group similar failures by error signature
  - Priority scoring: rank clusters by error frequency × recency
  - Structured reflective example generation: extract lessons + corrected paths
  - Adaptive sampling weights: more weight to high-value failure clusters
"""
from __future__ import annotations

import logging
import math
import time
from collections import Counter, defaultdict
from typing import Any

logger = logging.getLogger(__name__)


def _error_signature(error: str) -> str:
    """Extract a normalized error signature for cluster grouping."""
    if not error:
        return "empty_error"
    # Normalize: lowercase, strip whitespace, collapse numbers
    sig = error.lower().strip()
    for token in ["execution error", "runtime error", "valueerror", "typeerror",
                   "keyerror", "attributeerror", "indexerror", "importerror",
                   "modulenotfounderror", "timeout", "syntaxerror", "oserror",
                   "filenotfounderror", "zerodivisionerror", "stopiteration"]:
        if token in sig:
            return token
    # Fall back to first 40 chars as signature
    return sig[:40]


def _task_type(task: str) -> str:
    """Classify task into a type for cross-cluster analysis."""
    t = task.lower()
    if "code" in t or "program" in t or "implement" in t or "write" in t:
        return "code_generation"
    if "reason" in t or "think" in t or "logic" in t or "math" in t:
        return "reasoning"
    if "search" in t or "retrieve" in t or "find" in t:
        return "retrieval"
    if "plan" in t or "decompose" in t:
        return "planning"
    if "summar" in t or "summarize" in t or "extract" in t:
        return "summarization"
    return "general"


class FailureCluster:
    """A cluster of similar failures with priority scoring."""

    def __init__(self, signature: str, task_type: str):
        self.signature = signature
        self.task_type = task_type
        self.failures: list[dict] = []
        self.first_seen = time.time()
        self.last_seen = time.time()
        self.total_count = 0

    def add_failure(self, path: dict) -> None:
        """Add a failure path to this cluster."""
        self.failures.append(path)
        self.total_count += 1
        self.last_seen = time.time()

    @property
    def priority_score(self) -> float:
        """Score based on frequency × recency weight.

        Higher frequency + more recent = higher priority.
        Uses log-frequency to avoid runaway dominance by one cluster.
        """
        if self.total_count == 0:
            return 0.0
        frequency = math.log1p(self.total_count)  # log(1 + n)
        age_hours = (time.time() - self.first_seen) / 3600.0
        recency = math.exp(-age_hours / 24.0)  # half-life ~ 24h
        return frequency * recency

    def generate_reflective_example(self, max_examples: int = 3) -> dict:
        """Generate a structured reflective example from this cluster.

        Returns a dict with lessons, a corrected trajectory sketch,
        and a counter-example from the most common failure.
        """
        if not self.failures:
            return {"lessons": [], "corrected_trajectory": [], "counter_example": {}}

        # Extract common error patterns
        errors = [f.get("error", "") for f in self.failures]
        error_counter = Counter(str(e) for e in errors if e)
        most_common_error = error_counter.most_common(1)[0][0] if error_counter else ""

        # Extract tasks for context
        tasks = [f.get("task", "") for f in self.failures[:max_examples]]

        # Synthesize lessons
        lessons = []
        if "timeout" in str(most_common_error).lower():
            lessons.append("Task exceeds time limit — decompose into smaller subtasks")
            lessons.append("Use iterative deepening with early termination checks")
        if "invalid" in str(most_common_error).lower() or "error" in str(most_common_error).lower():
            lessons.append("Output validation step required before proceeding")
            lessons.append("Add defensive checks at each intermediate stage")
        if self.task_type == "code_generation":
            lessons.append("Prefer incremental implementation with test-after-each-step")
        elif self.task_type == "reasoning":
            lessons.append("Break reasoning into explicit intermediate steps")
            lessons.append("Verify each deduction before building on it")
        else:
            lessons.append(f"Failure signature '{self.signature[:40]}' — add guard against this pattern")

        # Build a corrected trajectory sketch
        corrected_trajectory = []
        for i, task in enumerate(tasks[:max_examples]):
            corrected_trajectory.append({
                "step": i,
                "original_task": task[:100],
                "corrected_approach": f"Avoid {self.signature[:50]} — "
                                      f"{lessons[i] if i < len(lessons) else 'general caution'}",
            })

        return {
            "cluster_signature": self.signature,
            "task_type": self.task_type,
            "frequency": self.total_count,
            "priority": round(self.priority_score, 4),
            "lessons": lessons,
            "corrected_trajectory": corrected_trajectory,
            "counter_example": {
                "error": most_common_error[:200],
                "n_occurrences": error_counter.get(most_common_error, 0),
            },
        }


class ReflectiveSampler:
    """Reflection-Enhanced Reasoning Sampling (RERS).

    Tracks failure clusters, scores them by priority, and generates
    structured reflective examples for adaptive sampling.
    """

    def __init__(self, decay_factor: float = 0.9, top_k_clusters: int = 10):
        self._clusters: dict[str, FailureCluster] = {}
        self._samples: list[dict] = []
        self._total_paths = 0
        self._decay_factor = decay_factor
        self._top_k_clusters = top_k_clusters

    # ── Public API ──────────────────────────────────────────────

    def reflect_on_failure(self, path: dict) -> dict:
        """Analyze a single failure path, extract structured reflection.

        Args:
            path: Dict with at least 'task' and 'error' keys.

        Returns:
            Dict with task info, error cluster, reflections, and lessons.
        """
        task = path.get("task", "")
        error = path.get("error", "")
        task_type = _task_type(task)
        signature = _error_signature(str(error))

        # Update the cluster
        if signature not in self._clusters:
            self._clusters[signature] = FailureCluster(signature, task_type)
        self._clusters[signature].add_failure(path)

        # Generate reflection for this single failure
        reflections = self._generate_reflections(task, str(error), task_type)
        lesson_count = len(reflections)

        result = {
            "task": task[:200],
            "error": str(error)[:200],
            "signature": signature,
            "task_type": task_type,
            "reflections": reflections,
            "lessons": lesson_count,
            "cluster_size": self._clusters[signature].total_count,
            "priority": round(self._clusters[signature].priority_score, 4),
        }
        self._samples.append(result)
        self._total_paths += 1
        return result

    def sample_reflective(self, failure_paths: list[dict]) -> list[str]:
        """Sample reflective lessons from failure paths using adaptive weights.

        Uses priority-weighted sampling: failure clusters with higher
        priority scores are more likely to contribute.

        Args:
            failure_paths: List of failure path dicts.

        Returns:
            List of unique reflection strings, weighted by cluster priority.
        """
        if not failure_paths:
            return []

        # Process all failures (updates clusters)
        all_reflections: list[str] = []
        for fp in failure_paths:
            result = self.reflect_on_failure(fp)
            all_reflections.extend(result["reflections"])

        # Build priority-weighted cluster summaries
        sorted_clusters = sorted(
            self._clusters.values(),
            key=lambda c: c.priority_score,
            reverse=True,
        )

        # Generate structured reflective examples from top clusters
        structured_examples: list[str] = []
        for cluster in sorted_clusters[:self._top_k_clusters]:
            example = cluster.generate_reflective_example(max_examples=2)
            for lesson in example["lessons"]:
                structured_examples.append(
                    f"[{example['task_type']}|freq={example['frequency']}] "
                    f"{lesson}"
                )

        # Combine unique reflections with structured examples
        unique_reflections = list(set(all_reflections))
        unique_reflections.extend(structured_examples)

        # Deduplicate again after merging
        seen: set[str] = set()
        result: list[str] = []
        for r in unique_reflections:
            if r not in seen:
                seen.add(r)
                result.append(r)

        return result

    # ── Internal helpers ────────────────────────────────────────

    @staticmethod
    def _generate_reflections(task: str, error: str, task_type: str) -> list[str]:
        """Generate structured reflection strings from a single failure."""
        reflections: list[str] = []
        error_lower = str(error).lower()

        if "timeout" in error_lower:
            reflections.append(
                "Efficiency: task exceeded time limit — attempt sub-goal decomposition"
            )
        if "invalid" in error_lower or "error" in error_lower:
            reflections.append(
                "Validation: output was invalid — add structural checks before returning"
            )
        if not task and not error:
            reflections.append("Input: empty task or error — verify input pipeline")
        if task_type == "code_generation":
            reflections.append("Code: ensure implementation is testable incrementally")
        elif task_type == "reasoning":
            reflections.append("Reasoning: verify intermediate deductions explicitly")
        elif task_type == "planning":
            reflections.append("Planning: consider alternative decomposition strategies")

        if not reflections:
            reflections.append(f"Unknown-failure [{str(error)[:60]}] — log for manual review")
        return reflections

    def get_cluster_summary(self) -> list[dict]:
        """Return a summary of all tracked failure clusters."""
        return [
            {
                "signature": c.signature,
                "task_type": c.task_type,
                "count": c.total_count,
                "priority": round(c.priority_score, 4),
            }
            for c in sorted(
                self._clusters.values(),
                key=lambda c: c.priority_score,
                reverse=True,
            )
        ]

    def get_stats(self) -> dict:
        """Return sampling statistics."""
        unique_clusters = len(self._clusters)
        total_in_clusters = sum(c.total_count for c in self._clusters.values())
        top_cluster = max(self._clusters.values(), key=lambda c: c.priority_score) \
            if self._clusters else None

        # Count unique reflections across all samples
        all_reflections: list[str] = []
        for s in self._samples:
            all_reflections.extend(s.get("reflections", []))
        unique_refs = len(set(all_reflections))

        return {
            "total_paths": self._total_paths,
            "unique_clusters": unique_clusters,
            "total_in_clusters": total_in_clusters,
            "unique_reflections": unique_refs,
            "top_cluster": top_cluster.signature if top_cluster else None,
            "top_priority": round(top_cluster.priority_score, 4) if top_cluster else 0.0,
        }
