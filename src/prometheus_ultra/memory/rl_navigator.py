"""RL Navigator — lightweight policy-gradient agent for HORMA hierarchy traversal.

Traverses a :class:`HierarchicalMemory` tree to select the minimal sufficient
context for a query.  Uses a simple linear policy:

    action = argmax(W · state)

Reward = task_success - token_penalty  (token_penalty ≈ number of nodes read).

Reference: arXiv 2606.11680 — HORMA: Hierarchical Organization and Retrieval
via Multi-agent Architecture.
"""

from __future__ import annotations

import logging
import math
import random
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)


class RLNavigator:
    """Lightweight RL agent for traversing a HORMA hierarchy.

    The navigator starts at a query-derived prefix and walks down the tree,
    deciding at each level whether to drill deeper or stop and return the
    accumulated context.  The policy is a linear softmax over a small
    feature vector describing the current node and the query.

    Reward = task_success - token_penalty
        where token_penalty penalises reading many nodes (encourages minimal
        sufficient context).

    Usage::

        from prometheus_ultra.memory.hierarchical_memory import HierarchicalMemory
        from prometheus_ultra.memory.rl_navigator import RLNavigator

        hm = HierarchicalMemory()
        hm.store("a1", "/tasks/explore", 0.9, content="alpha")
        hm.store("a2", "/tasks/explore/step1", 0.6, content="beta")

        nav = RLNavigator()
        context, actions = nav.navigate(hm, "/tasks/explore")
        nav.train(episodes=200)
    """

    def __init__(self, learning_rate: float = 0.01,
                 gamma: float = 0.99,
                 token_penalty: float = 0.05) -> None:
        self._lock = threading.RLock()

        # Policy parameters (linear softmax: 2 actions: STOP=0, DRILL=1)
        # Features: [shared_depth_norm, utility, path_len_norm, bias]
        self._n_features = 4
        self._W: list[list[float]] = [
            [random.gauss(0, 0.1) for _ in range(self._n_features)]
            for _ in range(2)  # STOP, DRILL
        ]

        self._lr = learning_rate
        self._gamma = gamma
        self._token_penalty = token_penalty

        # Training stats
        self._total_episodes = 0
        self._cumulative_reward = 0.0
        self._successes = 0
        self._total_tokens = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def navigate(self, hierarchy: Any, query: str,
                 max_depth: int = 5) -> tuple[list[dict[str, Any]], list[int]]:
        """Traverse *hierarchy* to find minimal sufficient context for *query*.

        Args:
            hierarchy: A :class:`HierarchicalMemory` instance (duck-typed;
                must support ``retrieve(query, ...)`` and ``get_path(id)``).
            query: Path to navigate from.
            max_depth: Maximum drill depth before forced stop.

        Returns:
            ``(context_nodes, actions)`` — a list of retrieved node dicts and
            the sequence of actions taken (0=STOP, 1=DRILL).
        """
        with self._lock:
            actions: list[int] = []
            context: list[dict[str, Any]] = []
            current_path = query
            depth = 0

            while depth < max_depth:
                # Retrieve candidates at current path level.
                hits = hierarchy.retrieve(current_path, max_results=5)
                if not hits:
                    break

                # Build state vector for the current situation.
                state = self._build_state(hits, current_path, depth)
                # Sample action from policy.
                action = self._sample_action(state)
                actions.append(action)

                if action == 0:  # STOP
                    context.extend(hits)
                    break
                else:  # DRILL
                    context.extend(hits)
                    # Move to the most promising child path.
                    next_path = self._select_child_path(hits, current_path)
                    if next_path == current_path:
                        # No deeper path available.
                        break
                    current_path = next_path
                    depth += 1

            # If we exhausted max_depth, include whatever we have.
            if depth >= max_depth:
                more = hierarchy.retrieve(current_path, max_results=5)
                context.extend(m for m in more if m not in context)

        return context, actions

    def train(self, episodes: int = 100,
              eval_hierarchy: Any = None,
              eval_queries: list[str] | None = None) -> dict[str, float]:
        """Train the navigator via policy gradient (REINFORCE).

        Args:
            episodes: Number of training episodes.
            eval_hierarchy: Optional hierarchy for eval (same as train if None).
            eval_queries: Queries to evaluate after training.

        Returns:
            Summary dict with reward, success rate, and average tokens.
        """
        # Create a training hierarchy if none provided.
        if eval_hierarchy is None:
            from prometheus_ultra.memory.hierarchical_memory import \
                HierarchicalMemory
            hm = HierarchicalMemory()
            self._populate_training_data(hm)
        else:
            hm = eval_hierarchy

        if eval_queries is None:
            queries = [
                "/tasks/explore",
                "/tasks/explore/step1",
                "/science/biology",
            ]
        else:
            queries = eval_queries

        episode_rewards: list[float] = []

        for ep in range(episodes):
            query = random.choice(queries)
            # Run navigation.
            context, actions = self.navigate(hm, query, max_depth=4)
            # Simulated task success: 1 if we found at least one relevant node.
            task_success = 1.0 if len(context) >= 1 else 0.0
            token_cost = len(context) * self._token_penalty
            reward = task_success - token_cost

            # Policy gradient update.
            self._policy_gradient_step(actions, reward)

            episode_rewards.append(reward)

            with self._lock:
                self._total_episodes += 1
                self._cumulative_reward += reward
                if task_success > 0.5:
                    self._successes += 1
                self._total_tokens += len(context)

        # Summary
        with self._lock:
            avg_reward = (self._cumulative_reward /
                          max(self._total_episodes, 1))
            success_rate = (self._successes /
                            max(self._total_episodes, 1))
            avg_tokens = (self._total_tokens /
                          max(self._total_episodes, 1))

        return {
            "avg_reward": round(avg_reward, 4),
            "success_rate": round(success_rate, 4),
            "avg_tokens": round(avg_tokens, 2),
            "episodes": self._total_episodes,
        }

    def get_stats(self) -> dict[str, Any]:
        """Return navigator training statistics."""
        with self._lock:
            total = max(self._total_episodes, 1)
            return {
                "total_episodes": self._total_episodes,
                "cumulative_reward": round(self._cumulative_reward, 4),
                "avg_reward": round(self._cumulative_reward / total, 4),
                "success_rate": round(self._successes / total, 4),
                "avg_tokens": round(self._total_tokens / total, 2),
                "learning_rate": self._lr,
                "gamma": self._gamma,
                "token_penalty": self._token_penalty,
            }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_state(self, hits: list[dict[str, Any]],
                     current_path: str, depth: int) -> list[float]:
        """Build a 4-dimensional feature vector.

        Features:
            0. normalised shared depth (0..1)
            1. average utility of hits
            2. normalised path length
            3. bias (always 1.0)
        """
        shared_depth = len(current_path.strip("/").split("/")) if current_path != "/" else 0
        max_depth = 10.0
        depth_norm = min(shared_depth / max_depth, 1.0)

        avg_utility = (
            sum(h.get("score", 0.0) for h in hits) / max(len(hits), 1)
        )

        path_len = len(current_path) / 100.0  # normalise

        return [depth_norm, avg_utility, path_len, 1.0]

    def _sample_action(self, state: list[float]) -> int:
        """Sample an action from the softmax policy."""
        logits = [
            sum(w * s for w, s in zip(weights, state))
            for weights in self._W
        ]
        # Softmax.
        max_logit = max(logits)
        exp_logits = [math.exp(l - max_logit) for l in logits]
        total = sum(exp_logits)
        probs = [e / total for e in exp_logits]

        # Stochastic sample.
        r = random.random()
        cumulative = 0.0
        for action, p in enumerate(probs):
            cumulative += p
            if r < cumulative:
                return action
        return 0  # fallback

    def _select_child_path(self, hits: list[dict[str, Any]],
                           current_path: str) -> str:
        """Pick the deepest unique path among *hits* as the next drill target."""
        best = current_path
        max_depth = len(current_path.strip("/").split("/")) if current_path != "/" else 0
        for h in hits:
            p = h.get("path", "")
            if p.startswith(current_path) and p != current_path:
                pd = len(p.strip("/").split("/"))
                if pd > max_depth:
                    max_depth = pd
                    best = p
        return best

    def _policy_gradient_step(self, actions: list[int],
                              reward: float) -> None:
        """Apply a REINFORCE-style update.

        For each timestep, approximate::

            dW[a] += lr * gamma^t * reward * state
        """
        # TODO: store full episode trajectories for proper REINFORCE.
        # For the minimal implementation, we update using the last action
        # as a simplified surrogate.
        if not actions:
            return
        last_action = actions[-1]
        lr = self._lr
        with self._lock:
            for i in range(self._n_features):
                # Crude surrogate gradient: nudge weights for the taken
                # action in the direction of the reward.
                self._W[last_action][i] += lr * self._gamma * reward * 0.01

    @staticmethod
    def _populate_training_data(hm: Any) -> None:
        """Fill a hierarchy with sample nodes for training."""
        samples = [
            ("node_1", "/tasks/explore", 0.9, "exploration task"),
            ("node_2", "/tasks/explore/step1", 0.6, "step 1 details"),
            ("node_3", "/tasks/explore/step2", 0.7, "step 2 details"),
            ("node_4", "/science/biology", 0.8, "biology overview"),
            ("node_5", "/science/biology/cell", 0.5, "cell biology"),
            ("node_6", "/science/physics", 0.7, "physics overview"),
            ("node_7", "/tasks/eval", 0.4, "evaluation task"),
        ]
        for nid, path, utility, content in samples:
            hm.store(nid, path, utility, content)
