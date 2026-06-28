"""DebateEngine — Multi-round debate with rebuttal and synthesis.

Based on: "Improving Factuality and Reasoning through Multiagent Debate"
(arXiv:2305.14325, Du et al., 2023)

Key Concepts from Paper:
    1. Multiple LLM instances debate across multiple rounds
    2. Each agent sees others' arguments and generates rebuttals
    3. Debate converges toward consensus or identifies strongest position
    4. "Society of Minds" approach reduces hallucination

Algorithm:
    for round in range(max_rounds):
        for each agent:
            generate argument considering others' previous arguments
        evaluate argument quality
        if consensus reached: break
    synthesize final position from best arguments
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class Argument:
    agent_id: int = 0
    text: str = ""
    round_num: int = 0
    quality: float = 0.0
    evidence_count: int = 0
    is_rebuttal: bool = False
    targets: list[int] = field(default_factory=list)


@dataclass
class DebateRound:
    round_num: int = 0
    arguments: list[Argument] = field(default_factory=list)
    avg_quality: float = 0.0


@dataclass
class DebateResult:
    topic: str = ""
    rounds: list[DebateRound] = field(default_factory=list)
    winner: Argument | None = None
    synthesis: str = ""
    consensus_reached: bool = False
    total_arguments: int = 0
    duration_ms: float = 0.0


class DebateEngine:
    """Multi-round debate with rebuttal and synthesis.

    Based on Multiagent Debate paper (arXiv:2305.14325).

    Usage:
        engine = DebateEngine(max_rounds=3, num_agents=3)
        result = engine.debate(
            topic="Is AI safety achievable?",
            initial_positions=["Yes, via alignment research", "No, alignment is unsolvable", "Partially, with governance"],
        )
        print(result.winner.text)
        print(result.synthesis)
    """

    EVIDENCE_WORDS = {
        "because", "evidence", "data", "shows", "proves", "research",
        "analysis", "study", "result", "demonstrate", "according", "source",
    }
    REBUTTAL_WORDS = {"however", "but", "although", "counter", "反驳", "disagree", "wrong", "incorrect"}

    def __init__(self, max_rounds: int = 3, num_agents: int = 3):
        self._max_rounds = max_rounds
        self._num_agents = num_agents
        self._debates: list[dict] = []

    def debate(self, topic: str, initial_positions: list[str] | None = None) -> DebateResult:
        start = time.time()
        rounds: list[DebateRound] = []

        positions = initial_positions or [f"Position {i+1}" for i in range(self._num_agents)]

        current_positions = {}
        for i, pos in enumerate(positions[:self._num_agents]):
            current_positions[i] = pos

        consensus_reached = False

        for round_num in range(self._max_rounds):
            round_args = []

            for agent_id in range(self._num_agents):
                if agent_id not in current_positions:
                    continue

                if round_num == 0:
                    text = current_positions[agent_id]
                    is_rebuttal = False
                    targets = []
                else:
                    text = self._generate_rebuttal(
                        topic, agent_id, current_positions, round_num
                    )
                    is_rebuttal = True
                    targets = [i for i in current_positions if i != agent_id]

                arg = Argument(
                    agent_id=agent_id,
                    text=text,
                    round_num=round_num,
                    is_rebuttal=is_rebuttal,
                    targets=targets,
                )
                arg.quality = self._score_argument(arg, topic)
                arg.evidence_count = self._count_evidence(arg.text)
                round_args.append(arg)

                current_positions[agent_id] = text

            avg_quality = sum(a.quality for a in round_args) / max(len(round_args), 1)
            debate_round = DebateRound(
                round_num=round_num,
                arguments=round_args,
                avg_quality=avg_quality,
            )
            rounds.append(debate_round)

            if self._check_consensus(current_positions):
                consensus_reached = True
                break

        all_args = [a for r in rounds for a in r.arguments]
        winner = max(all_args, key=lambda a: a.quality) if all_args else None
        synthesis = self._synthesize(topic, rounds)

        result = DebateResult(
            topic=topic,
            rounds=rounds,
            winner=winner,
            synthesis=synthesis,
            consensus_reached=consensus_reached,
            total_arguments=len(all_args),
            duration_ms=(time.time() - start) * 1000,
        )

        self._debates.append({
            "topic": topic,
            "rounds": len(rounds),
            "consensus": consensus_reached,
            "winner_quality": winner.quality if winner else 0,
        })

        return result

    def _generate_rebuttal(self, topic: str, agent_id: int,
                            positions: dict[int, str], round_num: int) -> str:
        my_position = positions.get(agent_id, "")
        others = [positions[i] for i in positions if i != agent_id]
        other_summary = "; ".join(o[:80] for o in others[:2])

        if any(w in my_position.lower() for w in self.REBUTTAL_WORDS):
            return my_position

        rebuttal = f"R{round_num} Rebuttal (Agent {agent_id}): "
        if others:
            rebuttal += f"While others argue '{other_summary[:50]}...', "
        rebuttal += f"my position remains: {my_position[:100]}. "
        rebuttal += "The evidence supports this because of empirical data and logical consistency."

        return rebuttal

    def _score_argument(self, arg: Argument, topic: str) -> float:
        words = arg.text.split()
        word_count = len(words)

        length_score = min(1.0, word_count / 30)

        evidence_count = sum(1 for w in words if w.lower() in self.EVIDENCE_WORDS)
        evidence_score = min(1.0, evidence_count * 0.25)

        unique_long = set(w.lower() for w in words if len(w) > 5)
        specificity_score = min(1.0, len(unique_long) / max(word_count, 1))

        topic_words = set(topic.lower().split())
        relevance_score = len(set(w.lower() for w in words) & topic_words) / max(len(topic_words), 1)

        rebuttal_bonus = 0.1 if arg.is_rebuttal else 0.0

        quality = (length_score * 0.2 + evidence_score * 0.35 +
                   specificity_score * 0.25 + relevance_score * 0.1 + rebuttal_bonus)
        return min(1.0, quality)

    def _count_evidence(self, text: str) -> int:
        return sum(1 for w in text.split() if w.lower() in self.EVIDENCE_WORDS)

    def _check_consensus(self, positions: dict[int, str]) -> bool:
        if len(positions) < 2:
            return True
        texts = [p.lower().split() for p in positions.values()]
        common_words = set(texts[0])
        for t in texts[1:]:
            common_words &= set(t)
        return len(common_words) > 5

    def _synthesize(self, topic: str, rounds: list[DebateRound]) -> str:
        if not rounds:
            return "No debate occurred"

        last_round = rounds[-1]
        if not last_round.arguments:
            return "No arguments presented"

        best = max(last_round.arguments, key=lambda a: a.quality)

        if len(last_round.arguments) >= 2:
            sorted_args = sorted(last_round.arguments, key=lambda a: a.quality, reverse=True)
            synthesis = (f"On '{topic}', the strongest position is: "
                        f"'{best.text[:150]}...' "
                        f"(quality={best.quality:.2f}, evidence={best.evidence_count})")
        else:
            synthesis = f"Single position on '{topic}': {best.text[:200]}"

        return synthesis

    def get_stats(self) -> dict:
        if not self._debates:
            return {"debates": 0}
        consensuses = sum(1 for d in self._debates if d["consensus"])
        return {
            "debates": len(self._debates),
            "consensus_rate": consensuses / len(self._debates),
            "avg_rounds": sum(d["rounds"] for d in self._debates) / len(self._debates),
        }
