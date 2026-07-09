"""GEPA — Gradient-Enhanced Parameter Adaptation.

Adaptive gradient-based hyperparameter optimization with momentum.
Performs finite-difference gradient estimation for continuous parameter
tuning across evolution rounds.

Key Concepts:
    1. Track parameter gradients across evolution rounds
    2. Use finite-difference approximation for gradient estimation
    3. Gradient-guided search direction (descent/ascent)
    4. Momentum accumulation for smoother convergence
    5. Adaptive learning rate with gradient clipping

References:
    - Bergstra et al. "Algorithms for Hyper-Parameter Optimization" NIPS 2011
    - "Population Based Training of Neural Networks" (PBT, arXiv:1711.09846)
    - Gradient descent with momentum (Polyak, 1964)

Algorithm:
    for each round:
        # Evaluate at current parameters
        fitness = evaluate(params)
        # Finite-difference gradient estimation
        for each param_i:
            params_plus = params.copy(); params_plus[i] += epsilon
            params_minus = params.copy(); params_minus[i] -= epsilon
            grad[i] = (evaluate(params_plus) - evaluate(params_minus)) / (2 * epsilon)
        # Update with momentum
        velocity = beta * velocity + lr * grad
        params -= velocity
        # Clip parameters to bounds
        params = clip(params, min, max)

Complexity: O(P * R) where P = parameters, R = rounds
"""
from __future__ import annotations



import logging

import math
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
logger = logging.getLogger(__name__)


@dataclass
class GradientRecord:
    """A single gradient computation record."""
    round_num: int = 0
    parameters: Dict[str, float] = field(default_factory=dict)
    gradient: Dict[str, float] = field(default_factory=dict)
    fitness: float = 0.0
    learning_rate: float = 0.0
    timestamp: float = 0.0


@dataclass
class GEPAEvolutionResult:
    """Result of a GEPA evolution step."""
    method: str = "gepa"
    improvement: float = 0.0
    fitness_before: float = 0.0
    fitness_after: float = 0.0
    gradient_norm: float = 0.0
    parameters: Dict[str, float] = field(default_factory=dict)
    gradient: Dict[str, float] = field(default_factory=dict)
    velocity: Dict[str, float] = field(default_factory=dict)
    details: str = ""


class GradientEnhancedParameterAdaptation:
    """Gradient-Enhanced Parameter Adaptation.

    Implements finite-difference gradient estimation with momentum
    for continuous parameter optimization. True gradient-based evolution
    instead of random search.

    Usage:
        gepa = GradientEnhancedParameterAdaptation(
            param_ranges={"lr": (0.001, 0.1), "batch_size": (16, 512)},
            evaluate_fn=my_fitness_fn,
        )
        result = gepa.evolve(context="optimize")
        print(f"Improvement: {result.improvement:.4f}")
    """

    def __init__(self, param_ranges: Optional[Dict[str, Tuple[float, float]]] = None,
                 evaluate_fn: Optional[Callable] = None,
                 learning_rate: float = 0.01, momentum: float = 0.9,
                 epsilon: float = 1e-4, max_gradient_norm: float = 1.0,
                 lr_decay: float = 0.99, lr_min: float = 1e-6):
        """Initialize GEPA.

        Args:
            param_ranges: Dict of param_name -> (min, max) bounds.
            evaluate_fn: Function that takes (context, params) -> fitness.
            learning_rate: Initial learning rate.
            momentum: Momentum coefficient (0-1).
            epsilon: Finite-difference step size.
            max_gradient_norm: Gradient clipping threshold.
            lr_decay: Learning rate decay per round.
            lr_min: Minimum learning rate.
        """
        self._param_ranges = param_ranges or self._default_param_ranges()
        self._evaluate_fn = evaluate_fn
        self._lr = learning_rate
        self._momentum = momentum
        self._epsilon = epsilon
        self._max_grad_norm = max_gradient_norm
        self._lr_decay = lr_decay
        self._lr_min = lr_min

        # Current parameters (initialized at midpoint)
        self._params: Dict[str, float] = {}
        for name, (lo, hi) in self._param_ranges.items():
            self._params[name] = (lo + hi) / 2.0

        # Velocity (momentum accumulator)
        self._velocity: Dict[str, float] = {name: 0.0 for name in self._params}

        # History tracking
        self._history: List[GradientRecord] = []
        self._fitness_history: List[float] = []
        self._best_fitness = float('-inf')
        self._best_params: Dict[str, float] = {}
        self._round = 0
        self._consecutive_no_improve = 0

    @staticmethod
    def _default_param_ranges() -> Dict[str, Tuple[float, float]]:
        """Default parameter ranges for general optimization."""
        return {
            "exploration_rate": (0.01, 0.5),
            "learning_rate": (0.001, 0.1),
            "temperature": (0.1, 1.0),
            "weight_decay": (0.0, 0.01),
            "attention_scale": (0.5, 2.0),
            "memory_weight": (0.1, 0.9),
            "innovation_rate": (0.01, 0.3),
            "stability_factor": (0.5, 1.0),
        }

    def evolve(self, context: str = "", evaluate_fn: Optional[Callable] = None,
               current_fitness: float = 0.0) -> GEPAEvolutionResult:
        """Perform one gradient-guided evolution step.

        Args:
            context: Task context for evaluation.
            evaluate_fn: Override evaluation function.
            current_fitness: Current fitness for comparison.

        Returns:
            GEPAEvolutionResult with improvement metrics.
        """
        self._round += 1
        eval_fn = evaluate_fn or self._evaluate_fn

        fitness_before = self._evaluate(context, eval_fn)
        self._fitness_history.append(fitness_before)

        # Compute gradient via finite differences
        gradient = self._compute_gradient(context, eval_fn)

        # Gradient clipping
        grad_norm = self._gradient_norm(gradient)
        if grad_norm > self._max_grad_norm:
            clip_ratio = self._max_grad_norm / grad_norm
            gradient = {k: v * clip_ratio for k, v in gradient.items()}

        # Update velocity and parameters
        new_params = {}
        new_velocity = {}
        for name in self._params:
            # Momentum update
            new_velocity[name] = (
                self._momentum * self._velocity[name]
                + self._lr * gradient.get(name, 0.0)
            )
            # Parameter update (ascent for maximization)
            new_params[name] = self._params[name] + new_velocity[name]
            # Clip to bounds
            lo, hi = self._param_ranges[name]
            new_params[name] = max(lo, min(hi, new_params[name]))

        self._params = new_params
        self._velocity = new_velocity

        # Evaluate new fitness
        fitness_after = self._evaluate(context, eval_fn)
        improvement = fitness_after - fitness_before

        # Adaptive learning rate
        if improvement > 0:
            self._consecutive_no_improve = 0
        else:
            self._consecutive_no_improve += 1
            # Reduce LR on stagnation
            if self._consecutive_no_improve >= 3:
                self._lr = max(self._lr_min, self._lr * 0.5)

        # Decay learning rate
        self._lr = max(self._lr_min, self._lr * self._lr_decay)

        # Track best
        if fitness_after > self._best_fitness:
            self._best_fitness = fitness_after
            self._best_params = dict(self._params)
            self._consecutive_no_improve = 0

        # Record
        record = GradientRecord(
            round_num=self._round,
            parameters=dict(self._params),
            gradient=dict(gradient),
            fitness=fitness_after,
            learning_rate=self._lr,
            timestamp=time.time(),
        )
        self._history.append(record)

        # Keep history bounded
        if len(self._history) > 1000:
            self._history = self._history[-500:]
            self._fitness_history = self._fitness_history[-500:]

        return GEPAEvolutionResult(
            method="gepa",
            improvement=improvement,
            fitness_before=fitness_before,
            fitness_after=fitness_after,
            gradient_norm=grad_norm,
            parameters=dict(self._params),
            gradient=dict(gradient),
            velocity=dict(self._velocity),
            details=f"lr={self._lr:.6f}, grad_norm={grad_norm:.4f}",
        )

    def _evaluate(self, context: str, evaluate_fn: Optional[Callable]) -> float:
        """Evaluate current parameters."""
        if evaluate_fn:
            try:
                result = evaluate_fn(context, self._params)
                if isinstance(result, (int, float)):
                    return float(result)
                if isinstance(result, dict):
                    return float(result.get("fitness", result.get("score", 0.0)))
            except Exception as e:
                logger.warning("GEPA fitness evaluation failed: %s", e)
        # Heuristic fallback: weighted sum of parameters with nonlinearity
        return self._heuristic_fitness()

    def _heuristic_fitness(self) -> float:
        """Heuristic fitness when no evaluation function is available.

        Rewards parameter configurations that are:
        - Near center (stability)
        - Diverse from previous rounds (exploration)
        """
        score = 0.0
        for name, val in self._params.items():
            lo, hi = self._param_ranges[name]
            normalized = (val - lo) / max(hi - lo, 1e-10)
            # Gaussian preference for center
            score += math.exp(-2.0 * (normalized - 0.5) ** 2)

        # Diversity bonus from recent history
        if len(self._fitness_history) >= 3:
            recent = self._fitness_history[-3:]
            recent_std = math.sqrt(sum((x - sum(recent) / 3) ** 2 for x in recent) / 3)
            score += recent_std * 0.1

        return score / len(self._params)

    def _compute_gradient(self, context: str, evaluate_fn: Optional[Callable]) -> Dict[str, float]:
        """Compute gradient via forward finite differences.

        Uses central difference where possible for O(epsilon^2) accuracy:
            f'(x) ≈ (f(x + epsilon) - f(x - epsilon)) / (2 * epsilon)
        """
        gradient = {}
        base_params = dict(self._params)

        for name in self._params:
            lo, hi = self._param_ranges[name]

            # Forward perturbation
            self._params[name] = min(hi, base_params[name] + self._epsilon)
            f_plus = self._evaluate(context, evaluate_fn)

            # Backward perturbation
            self._params[name] = max(lo, base_params[name] - self._epsilon)
            f_minus = self._evaluate(context, evaluate_fn)

            # Central difference
            delta = 2.0 * self._epsilon
            gradient[name] = (f_plus - f_minus) / delta

            # Restore
            self._params[name] = base_params[name]

        return gradient

    def _gradient_norm(self, gradient: Dict[str, float]) -> float:
        """L2 norm of gradient vector."""
        return math.sqrt(sum(v ** 2 for v in gradient.values()))

    def get_optimal_params(self) -> Dict[str, float]:
        """Get parameters that achieved best fitness."""
        return dict(self._best_params)

    def set_params(self, params: Dict[str, float]) -> None:
        """Set parameters directly."""
        for name, val in params.items():
            if name in self._params:
                lo, hi = self._param_ranges[name]
                self._params[name] = max(lo, min(hi, float(val)))

    def get_convergence_curve(self) -> List[float]:
        """Get fitness history for convergence analysis."""
        return list(self._fitness_history)

    def get_gradient_history(self, last_n: int = 50) -> List[GradientRecord]:
        """Get recent gradient records."""
        return self._history[-last_n:]

    def get_stats(self) -> Dict[str, Any]:
        """Get GEPA statistics."""
        if not self._fitness_history:
            return {"rounds": 0}

        recent = self._fitness_history[-50:] if len(self._fitness_history) >= 50 else self._fitness_history
        return {
            "rounds": self._round,
            "current_lr": self._lr,
            "best_fitness": self._best_fitness,
            "current_fitness": self._fitness_history[-1] if self._fitness_history else 0.0,
            "avg_recent_fitness": sum(recent) / len(recent),
            "params_count": len(self._params),
            "consecutive_no_improve": self._consecutive_no_improve,
            "gradient_magnitude": self._gradient_norm(self._velocity),
        }


# Backward compatibility alias (for existing life.py imports)
GEPA = GradientEnhancedParameterAdaptation
