"""MemPO — Memory Policy Optimization.

Learned utility policy through interaction: which memories are actually retrieved
and used gets positive reinforcement, while unused memories decay faster.

Based on: Self-Evolving Agent Systems (mempo module)

Instead of a fixed utility function (like "last accessed time" or "frequency"),
MemPO learns a utility policy through interaction.
"""
from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)

_DEFAULT_POLICY_PARAMS: dict = {
    "alpha": 0.3,
    "gamma": 0.5,
    "epsilon": 0.1,
}


class MemPO:
    """Memory Policy Optimization — learned utility through interaction.

    Tracks access events, reinforcement signals, and learns a utility score
    per memory node. Utility is used to prioritise which memories should be
    retained, retrieved, or pruned.

    Usage:
        mempo = MemPO()

        # Record an access
        mempo.observe_access("node_001")

        # Record reinforcement
        mempo.observe_reinforcement("node_001", reward=1.0)

        # Query learned utility (with time-decay applied)
        score = mempo.get_utility("node_001")

        # Batch operations
        utilities = mempo.batch_get_utilities(["node_001", "node_002"])
        stats = mempo.batch_update_utilities(["node_001"], [True])

        # Configuration
        mempo.set_policy_params({"alpha": 0.2})
    """

    def __init__(self, policy_params: dict | None = None) -> None:
        self._utility_scores: dict[str, float] = {}
        self._access_history: dict[str, list[float]] = {}
        self._reinforcement_signals: dict[str, list[float]] = {}
        self._usage_count: dict[str, int] = {}
        self._policy_params: dict = dict(_DEFAULT_POLICY_PARAMS)
        if policy_params is not None:
            self._validate_params(policy_params)
            self._policy_params.update(policy_params)
        self._decay_base: float = 0.99

        # Adaptive learning rate (M1)
        self._prediction_error_history: list[float] = []
        self._base_alpha: float = self._policy_params["alpha"]
        self._error_window: int = 10

        # Per-node adaptive alpha cache (M3)
        self._node_alpha: dict[str, float] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def observe_access(self, node_id: str, timestamp: float | None = None) -> dict:
        """Record an access event for a node and boost its utility.

        Utility update:  utility = min(1.0, utility + alpha * (1.0 - utility))

        Args:
            node_id: Unique identifier for the memory node.
            timestamp: Unix timestamp (defaults to time.time()).

        Returns:
            Dict with node_id, utility_before, utility_after.
        """
        if timestamp is None:
            timestamp = time.time()

        utility_before = self._utility_scores.get(node_id, 0.0)
        alpha = self._policy_params["alpha"]

        # Update utility
        utility_after = min(1.0, utility_before + alpha * (1.0 - utility_before))
        self._utility_scores[node_id] = utility_after

        # Track history
        if node_id not in self._access_history:
            self._access_history[node_id] = []
        self._access_history[node_id].append(timestamp)

        # Increment usage count
        self._usage_count[node_id] = self._usage_count.get(node_id, 0) + 1

        logger.debug(
            "MemPO access: node=%s utility=%.3f->%.3f",
            node_id, utility_before, utility_after,
        )

        return {
            "node_id": node_id,
            "utility_before": utility_before,
            "utility_after": utility_after,
        }

    def observe_reinforcement(self, node_id: str, reward: float) -> dict:
        """Record a reinforcement signal (TD-learning style update).

        Utility update:  utility += effective_alpha * (reward - utility)

        Where effective_alpha combines adaptive learning rate (M1) with
        surprise-based boosting (M2).

        Args:
            node_id: Unique identifier for the memory node.
            reward: Reinforcement signal (positive for useful, negative for
                    irrelevant).

        Returns:
            Dict with node_id, utility_before, utility_after.
        """
        utility_before = self._utility_scores.get(node_id, 0.0)

        # M1: Adaptive alpha from prediction error history
        adaptive_alpha = self._get_adaptive_alpha()

        # M2: Surprise-based adjustment
        # Compute prediction error before signal is appended for surprise calc
        prediction_error = abs(reward - utility_before)

        # Append the signal first so _compute_surprise has up-to-date history
        if node_id not in self._reinforcement_signals:
            self._reinforcement_signals[node_id] = []
        self._reinforcement_signals[node_id].append(reward)

        surprise = self._compute_surprise(node_id, reward)

        # M3: Per-node adaptive alpha based on signal volatility
        per_node_alpha = self._get_node_alpha(node_id)

        # Combine: effective_alpha = max(adaptive, boosted, per_node_alpha)
        boosted = self._base_alpha * (1.0 + surprise * 0.5)
        effective_alpha = max(adaptive_alpha, boosted, per_node_alpha)

        # TD-learning style update
        utility_after = utility_before + effective_alpha * (reward - utility_before)
        # Clamp to [0.0, 1.0]
        utility_after = max(0.0, min(1.0, utility_after))
        self._utility_scores[node_id] = utility_after

        # M1: Track prediction error and trim window
        self._prediction_error_history.append(prediction_error)
        if len(self._prediction_error_history) > self._error_window:
            self._prediction_error_history = (
                self._prediction_error_history[-self._error_window :]
            )

        logger.debug(
            "MemPO reinforce: node=%s reward=%.3f utility=%.3f->%.3f "
            "adaptive_alpha=%.3f surprise=%.3f eff_alpha=%.3f",
            node_id, reward, utility_before, utility_after,
            adaptive_alpha, surprise, effective_alpha,
        )

        return {
            "node_id": node_id,
            "utility_before": utility_before,
            "utility_after": utility_after,
            "adaptive_alpha": round(adaptive_alpha, 4),
            "surprise": round(surprise, 4),
            "effective_alpha": round(effective_alpha, 4),
        }

    def get_utility(self, node_id: str) -> float:
        """Get the current learned utility for a node.

        Applies time-decay based on last access:
            utility *= decay_base ** elapsed_hours

        Args:
            node_id: Unique identifier for the memory node.

        Returns:
            Utility score in [0.0, 1.0], or 0.0 if node_id unknown.
        """
        if node_id not in self._utility_scores:
            return 0.0

        utility = self._utility_scores[node_id]
        history = self._access_history.get(node_id, [])

        if history:
            last_access = history[-1]
            elapsed_hours = (time.time() - last_access) / 3600.0
            if elapsed_hours > 0:
                utility *= self._decay_base ** elapsed_hours

        return max(0.0, min(1.0, utility))

    def batch_get_utilities(self, node_ids: list[str]) -> dict[str, float]:
        """Get utilities for multiple nodes in one call.

        Args:
            node_ids: List of node identifiers.

        Returns:
            Dict mapping node_id -> utility score.
        """
        return {nid: self.get_utility(nid) for nid in node_ids}

    def batch_update_utilities(
        self, node_ids: list[str], usage_scores: list[float],
    ) -> dict:
        """Update utilities for a batch of nodes based on usage feedback.

        Each score in usage_scores is a float in [-1.0, 1.0]:
          -  1.0 = perfectly useful retrieval
          -  0.0 = neutral
          - -1.0 = completely irrelevant

        Backward compat: if all values are bools, treat True=1.0, False=0.0
        with a warning log.

        Args:
            node_ids: List of node identifiers.
            usage_scores: Parallel list of floats indicating how useful
                          each retrieved node was.

        Returns:
            Dict with updated count, avg_utility.
        """
        # Backward compat: bool → float
        if usage_scores and all(isinstance(s, bool) for s in usage_scores):
            logger.warning(
                "batch_update_utilities received booleans — converting "
                "True→1.0, False→0.0. Prefer float scores in [-1.0, 1.0]."
            )
            usage_scores = [1.0 if s else 0.0 for s in usage_scores]

        updated = 0
        total_utility = 0.0

        for node_id, score in zip(node_ids, usage_scores):
            self.observe_reinforcement(node_id, reward=score)
            total_utility += self.get_utility(node_id)
            updated += 1

        avg_utility = total_utility / max(updated, 1)

        logger.debug(
            "MemPO batch_update: %d nodes, avg_utility=%.3f",
            updated, avg_utility,
        )

        return {
            "updated": updated,
            "avg_utility": avg_utility,
        }

    def apply_rule_guidance(self, rule: dict, related_node_ids: list[str]) -> dict:
        """Boost utilities of nodes related to a high-confidence RIMRULE rule.

        Args:
            rule: RIMRULE rule dict with at least 'confidence' key.
            related_node_ids: Node IDs that match this rule's condition.

        Returns:
            Dict with boosted_count, avg_boost, max_boost.
        """
        boost = rule.get("confidence", 0.5) * 0.2  # max 0.2 utility boost
        boosted_count = 0
        total_boost = 0.0
        max_boost = 0.0

        for node_id in related_node_ids:
            current = self._utility_scores.get(node_id, 0.0)
            new_utility = min(1.0, current + boost)
            self._utility_scores[node_id] = new_utility
            self._usage_count[node_id] = self._usage_count.get(node_id, 0) + 1
            boosted_count += 1
            actual_boost = new_utility - current
            total_boost += actual_boost
            max_boost = max(max_boost, actual_boost)

        return {
            "boosted_count": boosted_count,
            "avg_boost": round(total_boost / max(boosted_count, 1), 4),
            "max_boost": round(max_boost, 4),
        }

    def get_utility_for_condition(self, condition: str) -> float:
        """Get MemPO utility for a condition string (via hash-to-pseudo-node mapping).

        Used by RIMRULE to weight observations by MemPO utility.

        Args:
            condition: A condition string from a RIMRULE rule.

        Returns:
            Utility score in [0.0, 1.0], defaulting to 0.5 if untracked.
        """
        if not condition:
            return 0.5
        pseudo_id = f"_cond_{hash(condition) % (2**31)}"
        # Track this pseudo-node if not already
        if pseudo_id not in self._utility_scores:
            self._utility_scores[pseudo_id] = 0.5
        return self._utility_scores.get(pseudo_id, 0.5)

    def get_stats(self) -> dict:
        """Get aggregate statistics about the MemPO state.

        Returns:
            Dict with total_nodes, avg_utility, total_usage_count,
            policy_params.
        """
        n = len(self._utility_scores)
        if n > 0:
            avg_utility = sum(self._utility_scores.values()) / n
        else:
            avg_utility = 0.0

        total_usage = sum(self._usage_count.values())

        return {
            "total_nodes": n,
            "avg_utility": round(avg_utility, 4),
            "total_usage_count": total_usage,
            "policy_params": dict(self._policy_params),
        }

    def set_policy_params(self, params: dict) -> dict:
        """Update learning parameters.

        Validates:
          - 0 < alpha <= 1
          - 0 <= gamma <= 1
          - 0 <= epsilon <= 1

        Args:
            params: Dict with optional keys: alpha, gamma, epsilon.

        Returns:
            Dict with updated status and current params.
        """
        self._validate_params(params)
        self._policy_params.update(params)

        logger.debug("MemPO policy_params updated: %s", self._policy_params)

        return {
            "updated": True,
            "params": dict(self._policy_params),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_adaptive_alpha(self) -> float:
        """Compute an adaptive learning rate based on recent prediction errors.

        When prediction errors are small, alpha stays near base_alpha.
        When errors are large (the model is surprised), alpha increases
        to learn faster from unexpected outcomes.

        Returns:
            Alpha in [0.05, 0.9].
        """
        if len(self._prediction_error_history) < 5:
            return self._base_alpha
        window = self._prediction_error_history[-self._error_window :]
        mean_error = sum(window) / len(window)
        alpha = self._base_alpha * (1.0 + mean_error)
        return max(0.05, min(0.9, alpha))

    def _compute_surprise(self, node_id: str, reward: float) -> float:
        """Compute surprise level for a reinforcement event.

        Surprise = absolute deviation of current reward from the mean of
        recent rewards for the same node.

        Args:
            node_id: The memory node identifier.
            reward: The current reinforcement reward.

        Returns:
            Surprise value (>= 0). Returns 0.0 if not enough history.
        """
        signals = self._reinforcement_signals.get(node_id, [])
        recent = signals[-3:]  # last 3 (may include the just-appended reward)
        # Note: the current reward was already appended to
        # self._reinforcement_signals by the time this is called.
        if len(recent) < 3:
            return 0.0
        mean_reward = sum(recent) / len(recent)
        surprise = abs(reward - mean_reward)
        return surprise

    def _get_node_alpha(self, node_id: str) -> float:
        """Compute per-node adaptive alpha based on volatility of signals.

        More volatile reward patterns → higher alpha (learn faster).
        Uses coefficient of variation over recent signals.

        Args:
            node_id: The memory node identifier.

        Returns:
            Per-node alpha in [base, 0.9].
        """
        base = self._node_alpha.get(node_id, self._policy_params["alpha"])
        node_history = self._reinforcement_signals.get(node_id, [])
        if len(node_history) >= 3:
            recent = node_history[-5:]  # up to 5 most recent
            if len(recent) >= 2:
                mean_val = sum(recent) / len(recent)
                # coefficient of variation (volatility / mean)
                volatility = abs(max(recent) - min(recent)) / max(
                    abs(mean_val), 0.01
                )
            else:
                volatility = 0.1
            adjusted = base * (1.0 + volatility * 0.5)
            self._node_alpha[node_id] = min(0.9, adjusted)
        return self._node_alpha.get(node_id, self._policy_params["alpha"])

    @staticmethod
    def _validate_params(params: dict) -> None:
        """Validate learning parameter bounds, raising on invalid values."""
        if "alpha" in params:
            alpha = params["alpha"]
            if not (0 < alpha <= 1):
                raise ValueError(
                    f"alpha must satisfy 0 < alpha <= 1, got {alpha}"
                )
        if "gamma" in params:
            gamma = params["gamma"]
            if not (0 <= gamma <= 1):
                raise ValueError(
                    f"gamma must satisfy 0 <= gamma <= 1, got {gamma}"
                )
        if "epsilon" in params:
            epsilon = params["epsilon"]
            if not (0 <= epsilon <= 1):
                raise ValueError(
                    f"epsilon must satisfy 0 <= epsilon <= 1, got {epsilon}"
                )
