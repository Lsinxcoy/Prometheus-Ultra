"""LoopStateMachine — State machine with valid transition matrix.

Valid transitions:
    IDLE → RUNNING
    RUNNING → PAUSED, COMPLETED, ERROR
    PAUSED → RUNNING, IDLE
    COMPLETED → IDLE
    ERROR → IDLE, RUNNING
    CIRCUIT_BREAKER → IDLE

Complexity: O(1) per transition
"""
from __future__ import annotations
from prometheus_ultra.foundation.schema import LoopState

VALID_TRANSITIONS = {
    LoopState.IDLE: [LoopState.RUNNING],
    LoopState.RUNNING: [LoopState.PAUSED, LoopState.COMPLETED, LoopState.ERROR],
    LoopState.PAUSED: [LoopState.RUNNING, LoopState.IDLE],
    LoopState.COMPLETED: [LoopState.IDLE],
    LoopState.ERROR: [LoopState.IDLE, LoopState.RUNNING],
    LoopState.CIRCUIT_BREAKER: [LoopState.IDLE],
}


class LoopStateMachine:
    """State machine with valid transitions.

    Usage:
        sm = LoopStateMachine()
        sm.transition(LoopState.RUNNING)
        sm.transition(LoopState.COMPLETED)
        print(sm.state)  # LoopState.IDLE (auto-reset)
    """

    def __init__(self):
        self._state = LoopState.IDLE
        self._transitions: list[dict] = []
        self._counts: dict[str, int] = {}

    def transition(self, new_state: LoopState) -> bool:
        valid = VALID_TRANSITIONS.get(self._state, [])
        allowed = new_state in valid
        self._transitions.append({
            "from": self._state.value, "to": new_state.value, "allowed": allowed,
        })
        key = f"{self._state.value}->{new_state.value}"
        self._counts[key] = self._counts.get(key, 0) + 1
        if allowed:
            self._state = new_state
        return allowed

    def force_transition(self, new_state: LoopState) -> None:
        self._transitions.append({"from": self._state.value, "to": new_state.value, "forced": True})
        self._state = new_state

    @property
    def state(self) -> LoopState:
        return self._state

    def get_valid_next(self) -> list[str]:
        return [s.value for s in VALID_TRANSITIONS.get(self._state, [])]

    def get_transition_history(self) -> list[dict]:
        return list(self._transitions)

    def get_stats(self) -> dict:
        return {
            "state": self._state.value,
            "transitions": len(self._transitions),
            "transition_counts": dict(self._counts),
            "invalid_transitions": sum(1 for t in self._transitions if not t.get("allowed", True)),
        }
