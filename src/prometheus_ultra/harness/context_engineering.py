"""ContextEngineering — Unified orchestration of Write/Select/Compress/Isolate.

Based on:
- "Context Engineering for Agents" (LangChain, 2025)
- "Don't Build Multi-Agents" (Cognition, 2025): "Context engineering is the #1 job"
- "How We Built Our Multi-Agent Research System" (Anthropic, 2025)
- "How Long Contexts Fail" (Breunig, 2025)
- Andrej Karpathy: "Context engineering is the delicate art and science of filling
  the context window with just the right information for the next step"

Four Strategies:
    1. Write: Save context to external storage (scratchpad, memory)
    2. Select: Retrieve relevant context from storage
    3. Compress: Reduce context size while preserving key information
    4. Isolate: Separate context for parallel sub-agent execution

Context Types:
    - Instructions: System prompts, rules, tool descriptions
    - Knowledge: Facts, memories, retrieved information
    - Tools: Tool descriptions, call results

Algorithm:
    manage_context(task, history):
        1. Write: snapshot current state to external storage
        2. Select: retrieve relevant memories/knowledge
        3. Compress: reduce history if too long
        4. Isolate: create sub-contexts for parallel tasks
        5. Assemble final context for next step

Complexity:
    manage(): O(S + R + C) where S=selection, R=retrieval, C=compression
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContextComponent:
    """A component of the context window."""
    name: str = ""
    type: str = ""  # instruction, knowledge, tool, history
    content: str = ""
    priority: int = 5  # 1=highest, 10=lowest
    tokens: int = 0
    timestamp: float = 0.0
    metadata: dict = field(default_factory=dict)


@dataclass
class ContextSnapshot:
    """A snapshot of context state for Write strategy."""
    snapshot_id: str = ""
    task: str = ""
    components: list[ContextComponent] = field(default_factory=list)
    total_tokens: int = 0
    timestamp: float = 0.0


@dataclass
class ContextResult:
    """Result of context engineering."""
    components: list[ContextComponent] = field(default_factory=list)
    total_tokens: int = 0
    write_saved: int = 0
    select_retrieved: int = 0
    compressed_tokens: int = 0
    isolated_contexts: int = 0
    strategy_used: str = ""


class ContextEngineering:
    """Unified orchestration of Write/Select/Compress/Isolate.

    Based on Context Engineering research (LangChain, Anthropic, Cognition 2025).

    Usage:
        ce = ContextEngineering(max_tokens=128000)

        # Write: save context externally
        snapshot = ce.write(task="answer question", components=[
            ContextComponent(name="system", type="instruction", content="Be helpful"),
            ContextComponent(name="history", type="history", content="Previous Q&A"),
        ])

        # Select: retrieve relevant context
        selected = ce.select(query="AI safety", storage=memory_store, limit=5)

        # Compress: reduce context size
        compressed = ce.compress(context_components, target_ratio=0.5)

        # Isolate: create sub-contexts
        isolated = ce.isolate(parent_context, sub_task="research topic")

        # Full pipeline
        result = ce.manage_context(task, history, memory_store)
    """

    def __init__(self, max_tokens: int = 128000):
        self._max_tokens = max_tokens
        self._snapshots: list[ContextSnapshot] = []
        self._stats = {
            "writes": 0, "selects": 0, "compressions": 0, "isolations": 0,
            "total_tokens_saved": 0, "total_components": 0,
        }

    def write(self, task: str, components: list[ContextComponent]) -> ContextSnapshot:
        """Write: Save context to external storage for later retrieval.

        From LangChain: "Scratchpad (temporary notes), Memory (cross-session storage)"
        From Anthropic: "LeadResearcher writes plan to Memory to prevent truncation loss"

        Args:
            task: Current task description.
            components: Context components to save.

        Returns:
            ContextSnapshot with saved state.
        """
        total_tokens = sum(c.tokens for c in components)
        snapshot = ContextSnapshot(
            snapshot_id=f"snap_{int(time.time() * 1000)}",
            task=task,
            components=components,
            total_tokens=total_tokens,
            timestamp=time.time(),
        )
        self._snapshots.append(snapshot)
        self._stats["writes"] += 1
        return snapshot

    def select(self, query: str, storage: Any = None, limit: int = 5) -> list[ContextComponent]:
        """Select: Retrieve relevant context from external storage.

        From Karpathy: "filling the context window with just the right information"
        From Anthropic: "CLAUDE.md as programmatic memory automatically injected"

        Args:
            query: Search query for retrieval.
            storage: External storage (memory store, knowledge base).
            limit: Maximum components to retrieve.

        Returns:
            List of retrieved ContextComponents.
        """
        results = []

        # Try to retrieve from memory store if available
        if storage and hasattr(storage, 'recall'):
            try:
                recall_results = storage.recall(query, limit=limit)
                for r in recall_results.hits:
                    results.append(ContextComponent(
                        name=f"memory_{r.node_id[:8]}",
                        type="knowledge",
                        content=r.content,
                        priority=3,
                        tokens=len(r.content.split()) * 2,
                        metadata={"source": "memory", "score": r.score},
                    ))
            except Exception:
                pass

        # Try to retrieve from graph memory if available
        if storage and hasattr(storage, 'search'):
            try:
                graph_results = storage.search(query, limit=limit)
                for r in graph_results:
                    content = r.content if hasattr(r, 'content') else str(r)
                    results.append(ContextComponent(
                        name=f"graph_{hash(content) % 10000}",
                        type="knowledge",
                        content=content[:500],
                        priority=4,
                        tokens=len(content.split()) * 2,
                        metadata={"source": "graph"},
                    ))
            except Exception:
                pass

        # Sort by priority and limit
        results.sort(key=lambda c: c.priority)
        results = results[:limit]

        self._stats["selects"] += 1
        self._stats["total_components"] += len(results)
        return results

    def compress(self, components: list[ContextComponent],
                 target_ratio: float = 0.5) -> list[ContextComponent]:
        """Compress: Reduce context size while preserving key information.

        From Cognition: "Compression is the #1 job of engineers building AI agents"
        From Anthropic: "Subagents facilitate compression by operating in parallel"

        Args:
            components: Components to compress.
            target_ratio: Target compression ratio (0.5 = keep 50%).

        Returns:
            Compressed list of components.
        """
        if not components:
            return []

        total_tokens = sum(c.tokens for c in components)
        target_tokens = int(total_tokens * target_ratio)

        if total_tokens <= target_tokens:
            return components

        # Sort by priority (lower = more important)
        sorted_components = sorted(components, key=lambda c: c.priority)

        # Keep high-priority components, compress low-priority ones
        kept = []
        kept_tokens = 0

        for comp in sorted_components:
            if kept_tokens + comp.tokens <= target_tokens:
                kept.append(comp)
                kept_tokens += comp.tokens
            else:
                # Compress this component
                compressed_content = self._compress_text(comp.content, target_ratio)
                compressed_tokens = len(compressed_content.split()) * 2
                if kept_tokens + compressed_tokens <= target_tokens:
                    kept.append(ContextComponent(
                        name=comp.name,
                        type=comp.type,
                        content=compressed_content,
                        priority=comp.priority,
                        tokens=compressed_tokens,
                        timestamp=comp.timestamp,
                        metadata={**comp.metadata, "compressed": True},
                    ))
                    kept_tokens += compressed_tokens

        saved = total_tokens - kept_tokens
        self._stats["compressions"] += 1
        self._stats["total_tokens_saved"] += saved

        return kept

    def isolate(self, parent_components: list[ContextComponent],
                sub_task: str, max_tokens: int = 32000) -> tuple[list[ContextComponent], list[ContextComponent]]:
        """Isolate: Create separate context for sub-agent execution.

        From Anthropic: "Subagents facilitate compression by operating in
        parallel with their own context windows"
        From Claude Code: "Sub-agents only do investigation, never modify code"

        Args:
            parent_components: Parent context components.
            sub_task: Description of sub-task for isolation.
            max_tokens: Maximum tokens for isolated context.

        Returns:
            Tuple of (isolated_context, remaining_parent_context).
        """
        # Select relevant components for isolation
        isolated = []
        remaining = []

        task_words = set(sub_task.lower().split())

        for comp in parent_components:
            relevance = self._compute_relevance(comp.content, task_words)
            if relevance > 0.3:
                isolated.append(comp)
            else:
                remaining.append(comp)

        # Ensure isolated context fits within budget
        total_tokens = sum(c.tokens for c in isolated)
        if total_tokens > max_tokens:
            isolated.sort(key=lambda c: c.priority)
            kept = []
            kept_tokens = 0
            for comp in isolated:
                if kept_tokens + comp.tokens <= max_tokens:
                    kept.append(comp)
                    kept_tokens += comp.tokens
                else:
                    remaining.append(comp)
            isolated = kept

        self._stats["isolations"] += 1
        return isolated, remaining

    def manage_context(self, task: str, history: list[str],
                       memory_store: Any = None,
                       max_tokens: int = 128000) -> ContextResult:
        """Full context engineering pipeline.

        Orchestrates Write → Select → Compress → Isolate for optimal context.

        Args:
            task: Current task description.
            history: Conversation history.
            memory_store: External memory store.
            max_tokens: Maximum context window size.

        Returns:
            ContextResult with assembled components and metrics.
        """
        components = []

        # 1. Write: snapshot current state
        history_content = "\n".join(history[-10:])  # Keep last 10 turns
        history_tokens = len(history_content.split()) * 2

        # 2. Select: retrieve relevant context from memory
        if memory_store:
            selected = self.select(task, memory_store, limit=5)
            components.extend(selected)

        # 3. Add history as component
        if history_content:
            components.append(ContextComponent(
                name="history",
                type="history",
                content=history_content,
                priority=2,
                tokens=history_tokens,
            ))

        # 4. Add task as component
        components.append(ContextComponent(
            name="task",
            type="instruction",
            content=task,
            priority=1,
            tokens=len(task.split()) * 2,
        ))

        # 5. Compress if over budget
        total_tokens = sum(c.tokens for c in components)
        compressed_tokens = 0
        if total_tokens > max_tokens:
            before = total_tokens
            components = self.compress(components, target_ratio=max_tokens / total_tokens)
            compressed_tokens = before - sum(c.tokens for c in components)

        # 6. Write snapshot for future retrieval
        self.write(task, components)

        final_tokens = sum(c.tokens for c in components)

        return ContextResult(
            components=components,
            total_tokens=final_tokens,
            select_retrieved=len([c for c in components if c.metadata.get("source")]),
            compressed_tokens=compressed_tokens,
            strategy_used="write_select_compress",
        )

    def _compute_relevance(self, content: str, query_words: set) -> float:
        """Compute relevance score between content and query."""
        if not content or not query_words:
            return 0.0
        content_words = set(content.lower().split())
        overlap = query_words & content_words
        return len(overlap) / max(len(query_words), 1)

    def _compress_text(self, text: str, ratio: float) -> str:
        """Compress text by keeping key sentences."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) <= 2:
            return text[:int(len(text) * ratio)]

        # Keep first and last sentence, plus most relevant middle sentences
        important_words = {"key", "important", "result", "conclusion", "therefore"}
        scored = []
        for i, sent in enumerate(sentences):
            score = 0.0
            if i == 0 or i == len(sentences) - 1:
                score += 0.5
            words = set(sent.lower().split())
            if words & important_words:
                score += 0.4
            scored.append((score, sent))

        scored.sort(key=lambda x: -x[0])
        keep_count = max(2, int(len(sentences) * ratio))
        kept = [s for _, s in scored[:keep_count]]

        return " ".join(kept)

    def get_stats(self) -> dict:
        return dict(self._stats)
