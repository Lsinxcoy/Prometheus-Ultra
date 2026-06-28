"""life.py — Prometheus Ultra main controller.

Unified from Genesis(99 mechanisms), Omega-Omega(branch system),
and Z:\Prometheus Ω(deep evolution + 4-layer defense).

107 mechanisms across 15 subsystems.
7 pipelines: remember, recall, evolve, learn, reflect, dream, maintain.
Branch system for parallel experimentation.
"""
from __future__ import annotations

import logging
import time

from prometheus_ultra.foundation.schema import (
    Node, Edge, NodeType, EdgeType, MemoryTier, TrustLevel,
    ProvenanceType, GateResult, EvolutionResult,
    SearchHit, SearchResults, DreamResult, EvolutionOutcome,
    SystemStatus, ZConfig, generate_uuidv7, AlertLevel, LoopState,
)
from prometheus_ultra.foundation.store import MinervaStore, IronLawViolation

# Memory
from prometheus_ultra.memory.dopamine import DopamineWriteGate, DopamineGateConfig
from prometheus_ultra.memory.polyphonic import PolyphonicRetriever
from prometheus_ultra.memory.graph_memory import GraphMemory, EpisodeEvent
from prometheus_ultra.memory.four_network import FourNetworkMemory
from prometheus_ultra.memory.feedback import NodeFeedbackTracker, FailureLogTracker
from prometheus_ultra.memory.cache import RTKCache
from prometheus_ultra.memory.shmr import SHMRGenerator
from prometheus_ultra.memory.trajectory import TrajectoryStore
from prometheus_ultra.memory.disposition import DispositionLearner
from prometheus_ultra.memory.stream import MemoryStream
from prometheus_ultra.memory.bridge import KnowledgeBridge

# Lifecycle
from prometheus_ultra.lifecycle.bank import MemoryBank, Tier
from prometheus_ultra.lifecycle.forgetting import WeibullForgetting
from prometheus_ultra.lifecycle.consolidation import ConsolidationPipeline
from prometheus_ultra.lifecycle.gravity import MemoryGravity
from prometheus_ultra.lifecycle.veracity import VeracityBayesian, Evidence
from prometheus_ultra.lifecycle.dream_cycle import DreamCycle
from prometheus_ultra.lifecycle.consolidator import ConsolidationEngine
from prometheus_ultra.lifecycle.convergence import ConvergenceDetector
from prometheus_ultra.lifecycle.state_machine import LoopStateMachine
from prometheus_ultra.lifecycle.thermodynamic import ThermodynamicIntelligence
from prometheus_ultra.lifecycle.rare_valid import RareValidDetector
from prometheus_ultra.lifecycle.mars import MARS

# Evolution
from prometheus_ultra.evolution.eval_driven import EvalDrivenEngine, EvolutionContext
from prometheus_ultra.evolution.anti_evolution_gate import AntiEvolutionGate
from prometheus_ultra.evolution.iron_law import VerificationIronLaw
from prometheus_ultra.evolution.ucb1 import UCB1Bandit
from prometheus_ultra.evolution.fggm import FGGVerifier
from prometheus_ultra.evolution.dag_scheduler import DAGScheduler
from prometheus_ultra.evolution.coevolve import CoEvolution
from prometheus_ultra.evolution.speculative import SpeculativeEvolution
from prometheus_ultra.evolution.evolution_engine import EvolutionEngine

# Safety
from prometheus_ultra.safety.instincts import InstinctsRegistry, register_default_instincts
from prometheus_ultra.safety.five_gates import FiveGates, CascadeResult
from prometheus_ultra.safety.loop_guard import LoopGuard
from prometheus_ultra.safety.equilibrium_guard import EquilibriumGuard
from prometheus_ultra.safety.rl_pathology import RLPathologyDetector
from prometheus_ultra.safety.circuit_breaker import CircuitBreaker
from prometheus_ultra.safety.drift_detector import DriftDetector
from prometheus_ultra.safety.zscore import ZScoreAnomaly
from prometheus_ultra.safety.trend import TrendPredictor
from prometheus_ultra.safety.self_healing import SelfHealingEngine
from prometheus_ultra.safety.constitution import Constitution

# Evaluation
from prometheus_ultra.evaluation.five_view import FiveViewEvaluator
from prometheus_ultra.evaluation.marginal import MarginalAdvantageAccumulator
from prometheus_ultra.evaluation.seagym import SEAGym
from prometheus_ultra.evaluation.harness import HarnessX
from prometheus_ultra.evaluation.bootstrap import BootstrapCI

# Loop
from prometheus_ultra.loop.reflexion import ReflexionEngine
from prometheus_ultra.loop.coala import CoALAArchitecture
from prometheus_ultra.loop.debate import DebateEngine
from prometheus_ultra.loop.info_gain import InformationGainTracker
from prometheus_ultra.loop.agent_forest import AgentForest
from prometheus_ultra.loop.dynamic_scaler import DynamicScaler

# Prompt
from prometheus_ultra.prompt.cot import CoTPrompter
from prometheus_ultra.prompt.few_shot import DynamicFewShot
from prometheus_ultra.prompt.extended_thinking import ExtendedThinking
from prometheus_ultra.prompt.knowledge_gen import KnowledgeGenerator
from prometheus_ultra.prompt.consistency import SelfConsistencyVoter
from prometheus_ultra.prompt.refiner import SelfRefiner

# Learning
from prometheus_ultra.learning.scanner import KnowledgeScanner, ScanSource
from prometheus_ultra.learning.curiosity import CuriosityQueue
from prometheus_ultra.learning.utility_tracker import UtilityTracker
from prometheus_ultra.learning.five_step import FiveStepEvolution
from prometheus_ultra.learning.deep_retrofit import DeepRetrofit

# Harness
from prometheus_ultra.harness.compressor import ContextCompressor
from prometheus_ultra.harness.guardrail import InputGuardrail, OutputGuardrail
from prometheus_ultra.harness.router import ModelRouter, ModelConfig
from prometheus_ultra.harness.session import Session
from prometheus_ultra.harness.brain import Brain
from prometheus_ultra.harness.hands import Hands
from prometheus_ultra.harness.crash_recovery import CrashRecovery

# Collaboration
from prometheus_ultra.collaboration.multi_agent import MultiAgentSystem
from prometheus_ultra.collaboration.event_bus import CIPEventBus
from prometheus_ultra.collaboration.vector_clock import VectorClock
from prometheus_ultra.collaboration.causal_graph import CausalKnowledgeGraph
from prometheus_ultra.collaboration.behavior_mirror import BehaviorMirror

# Ecosystem
from prometheus_ultra.ecosystem.lotka_volterra import LotkaVolterra
from prometheus_ultra.ecosystem.speculative_fork import SpeculativeFork
from prometheus_ultra.ecosystem.tool_fitness import ToolFitnessPredictor
from prometheus_ultra.ecosystem.community_tree import CommunityTree
from prometheus_ultra.ecosystem.edre import EDREReplicator

# Execution
from prometheus_ultra.execution.dag_executor import DAGExecutor, ParallelDAG, RetryableDAG, MonitoredDAG

# Governance
from prometheus_ultra.governance.autonomy import AutonomyLevel, ConfidenceGate, EvolutionGrill

# Organs
from prometheus_ultra.organs.organ_pipeline import FiveOrganPipeline
from prometheus_ultra.organs.dna_extractor import DNAExtractor
from prometheus_ultra.organs.tool_loop import ToolLoop

# Skills
from prometheus_ultra.skills.registry import SkillRegistry
from prometheus_ultra.skills.curator import Curator
from prometheus_ultra.skills.skill_claw import SkillClaw

# Mechanisms
from prometheus_ultra.mechanisms.registry import MechanismRegistry
from prometheus_ultra.mechanisms.x_adapter import XMemoryAdapter
from prometheus_ultra.mechanisms.y_adapter import YBankAdapter

# Monitor + Services
from prometheus_ultra.monitor.system_monitor import SystemMonitor
from prometheus_ultra.services.server import OmegaServer

logger = logging.getLogger(__name__)


class Omega:
    """Prometheus Ultra — 99-mechanism self-evolving AI agent system.

    Composes all subsystems into a unified interface with 7 pipelines.
    Supports branch-based parallel experimentation.
    """

    def __init__(self, config: ZConfig | None = None, db_path: str | None = None) -> None:
        self._cfg = config if config is not None else ZConfig()
        if db_path:
            self._cfg.database_path = db_path
        self._start_time = time.time()

        # ===== Foundation (1) =====
        self.store = MinervaStore(self._cfg)
        self.store.connect()

        # ===== Memory (12) =====
        self.dopamine = DopamineWriteGate(DopamineGateConfig())
        self.search = PolyphonicRetriever()
        self.graph_memory = GraphMemory()
        self.four_network = FourNetworkMemory()
        self.feedback = NodeFeedbackTracker()
        self.failure_log = FailureLogTracker()
        self.cache = RTKCache()
        self.shmr = SHMRGenerator()
        self.trajectory = TrajectoryStore()
        self.disposition = DispositionLearner()
        self.stream = MemoryStream()
        self.bridge = KnowledgeBridge()

        # ===== Lifecycle (12) =====
        self.bank = MemoryBank(db_path=":memory:")
        self.forgetting = WeibullForgetting()
        self.consolidation = ConsolidationPipeline()
        self.gravity = MemoryGravity()
        self.veracity = VeracityBayesian()
        self.dream = DreamCycle()
        self.consolidation_engine = ConsolidationEngine()
        self.convergence = ConvergenceDetector()
        self.state_machine = LoopStateMachine()
        self.thermodynamic = ThermodynamicIntelligence()
        self.rare_valid = RareValidDetector()
        self.mars = MARS()

        # ===== Evolution (9) =====
        self.eval_engine = EvalDrivenEngine(max_iterations=10, convergence_threshold=0.95)
        self.anti_evolution = AntiEvolutionGate()
        self.iron_law = VerificationIronLaw(strict_fuzzy_rejection=True)
        self.ucb1 = UCB1Bandit(arm_names=["dopamine", "graph", "consolidation", "fggm"])
        self.fggm = FGGVerifier()
        self.dag_scheduler = DAGScheduler()
        self.coevolve = CoEvolution()
        self.speculative = SpeculativeEvolution()
        self.evolution_engine = EvolutionEngine(eval_fn=lambda c: self._compute_fitness())

        # ===== Safety (11) =====
        self.instincts = InstinctsRegistry()
        register_default_instincts(self.instincts)
        self.five_gates = FiveGates(dopamine_gate=self.dopamine)
        self.constitution = Constitution()
        self.loop_guard = LoopGuard()
        self.equilibrium = EquilibriumGuard()
        self.rl_pathology = RLPathologyDetector()
        self.circuit_breaker = CircuitBreaker()
        self.drift_detector = DriftDetector()
        self.zscore = ZScoreAnomaly()
        self.trend = TrendPredictor()
        self.self_healing = SelfHealingEngine()

        # ===== Learning (5) =====
        self.knowledge_scanner = KnowledgeScanner()
        self.curiosity_queue = CuriosityQueue()
        self.utility_tracker = UtilityTracker()
        self.five_step = FiveStepEvolution(omega=self)
        self.retrofit = DeepRetrofit(omega=self)

        # ===== Evaluation (5) =====
        self.five_view = FiveViewEvaluator()
        self.marginal = MarginalAdvantageAccumulator()
        self.seagym = SEAGym()
        self.harness_x = HarnessX()
        self.bootstrap = BootstrapCI()

        # ===== Loop (6) =====
        self.reflexion = ReflexionEngine()
        self.coala = CoALAArchitecture()
        self.debate = DebateEngine()
        self.info_gain = InformationGainTracker()
        self.agent_forest = AgentForest()
        self.dynamic_scaler = DynamicScaler()

        # ===== Prompt (6) =====
        self.cot = CoTPrompter()
        self.few_shot = DynamicFewShot()
        self.extended_thinking = ExtendedThinking()
        self.knowledge_gen = KnowledgeGenerator()
        self.consistency = SelfConsistencyVoter()
        self.refiner = SelfRefiner()

        # ===== Harness (7) =====
        self.compressor = ContextCompressor()
        self.input_guardrail = InputGuardrail()
        self.output_guardrail = OutputGuardrail()
        self.model_router = ModelRouter({"default": ModelConfig()})
        self.session = Session()
        self.brain = Brain()
        self.hands = Hands()
        self.crash_recovery = CrashRecovery(self.session)

        # ===== Collaboration (5) =====
        self.multi_agent = MultiAgentSystem()
        self.event_bus = CIPEventBus()
        self.vector_clock = VectorClock()
        self.causal_graph = CausalKnowledgeGraph()
        self.behavior_mirror = BehaviorMirror()

        # ===== Ecosystem (5) =====
        self.lotka_volterra = LotkaVolterra()
        self.speculative_fork = SpeculativeFork()
        self.tool_fitness = ToolFitnessPredictor()
        self.community_tree = CommunityTree()
        self.edre = EDREReplicator()

        # ===== Execution (4) =====
        self.dag_executor = DAGExecutor()
        self.parallel_dag = ParallelDAG()
        self.retryable_dag = RetryableDAG()
        self.monitored_dag = MonitoredDAG()

        # ===== Governance (2) =====
        self.autonomy = AutonomyLevel.L2_SUPERVISED
        self.trust = TrustLevel.VERIFIED
        self.confidence_gate = ConfidenceGate()
        self.evolution_grill = EvolutionGrill()

        # ===== Organs (3) =====
        self.organ_pipeline = FiveOrganPipeline()
        self.dna_extractor = DNAExtractor()
        self.tool_loop = ToolLoop()

        # ===== Skills (3) =====
        self.skill_registry = SkillRegistry()
        self.curator = Curator(self.skill_registry)
        self.skill_claw = SkillClaw()

        # ===== Mechanisms (3) =====
        self.mechanism_registry = MechanismRegistry()
        self.x_adapter = XMemoryAdapter()
        self.y_adapter = YBankAdapter()

        # ===== Monitor + Services (2) =====
        self.monitor = SystemMonitor()
        self.server = OmegaServer(omega=self)

        logger.info("Prometheus Ultra initialized: 102 mechanisms across 17 subsystems")

    # ============================================================
    # remember pipeline (11 stages)
    # ============================================================
    def remember(self, content: str, utility: float = 0.5, tags: list[str] | None = None,
                 branch: str = "main") -> str:
        tags = tags or []
        surprise = max(0.3, utility * 0.6)

        # Gate 0: InputGuardrail
        gr = self.input_guardrail.check(content)
        if not gr.passed:
            return ""

        # Gate 1: DopamineWriteGate
        gate = self.dopamine.evaluate(utility=utility, surprise=surprise)
        if gate.decision == "reject":
            return ""

        # Create node
        node = Node(id=generate_uuidv7(), type=NodeType.FACT, content=content,
                     tags=tags, utility=utility, surprise=surprise, branch=branch)

        # Gate 2: FiveGates
        cascade = self.five_gates.evaluate(node, {"current_node_count": self.store.get_node_count()})
        if not cascade.passed:
            return ""

        # Gate 2.5: Constitution (22 principles)
        violations = self.constitution.evaluate({
            "content": content, "utility": utility, "surprise": surprise,
            "action": "remember", "branch": branch,
        })
        blocking = [v for v in violations if not v.passed and "S" in v.gate_name]
        if blocking:
            return ""

        # Gate 3: InstinctsRegistry
        instinct_results = self.instincts.evaluate_all({
            "utility": utility, "surprise": surprise, "content": content,
        })
        for triggered in instinct_results:
            if triggered.get("result", {}).get("action") == "block":
                return ""

        # Gate 4: VeracityBayesian
        self.veracity.compute_posterior_compat(
            prior=0.5,
            evidence=Evidence(source_confidence=0.5, consistency=utility, corroboration=surprise),
        )

        # Store
        self.store.create_node(node)

        # GraphMemory
        self.graph_memory.add_episode(EpisodeEvent(episode_id=node.id, content=content,
                                                   tags=set(tags), importance=utility))

        # FourNetwork
        self.four_network.retain(content, network="experience")

        # Bank
        self.bank.store(content, tier=Tier.WORKING, importance=utility)

        # CoALA
        self.coala.add_to_working_memory({"id": node.id, "content": content[:100], "utility": utility})

        # DriftDetector
        self.drift_detector.observe_semantic(utility)

        # Edges
        existing = self.store.get_active_nodes(limit=100)
        for ex in existing:
            common = set(ex.tags) & set(tags)
            if common:
                edge = Edge(source_id=node.id, target_id=ex.id, type=EdgeType.SEMANTIC_SIMILAR,
                            weight=len(common) / max(len(tags), len(ex.tags), 1))
                self.store.create_edge(edge)
                self.graph_memory.add_edge(node.id, ex.id, "SEMANTIC_SIMILAR", edge.weight)

        # Side effects
        self.trajectory.record("remember", [{"node_id": node.id, "utility": utility}])
        self.stream.add("remember", content[:200], importance=utility)
        self.disposition.learn("remember_utility", utility)
        self.bridge.bridge(content, "memory", relationship="stored")
        self.vector_clock.increment()
        self.event_bus.publish({"type": "remember", "node_id": node.id})
        self.x_adapter.adapt({"node_id": node.id, "content": content})
        self.y_adapter.adapt({"node_id": node.id, "utility": utility})

        # Feedback + FailureLog
        self.feedback.record(node.id, "remember", utility)
        self.monitor.record("remember", utility)

        logger.info("Remembered: %s", node.id[:8])
        return node.id

    # ============================================================
    # recall pipeline (6 routes)
    # ============================================================
    def recall(self, query: str, limit: int = 10, branch: str = "main") -> SearchResults:
        start = time.time()
        all_hits: list[SearchHit] = []

        # Route 1: FTS
        fts_nodes = self.store.search(query, limit=limit * 2, branch=branch)
        all_hits.extend(SearchHit(node_id=n.id, score=n.utility, content=n.content,
                                  snippet=n.content[:200]) for n in fts_nodes)

        # Route 2: GraphMemory
        for r in self.graph_memory.search(query, limit=limit):
            r_dict = r if isinstance(r, dict) else {"id": r.episode_id, "score": r.score, "content": r.content}
            all_hits.append(SearchHit(node_id=r_dict["id"], score=r_dict["score"] * 1.1,
                                      content=r_dict["content"], snippet=r_dict["content"][:200]))

        # Route 3: FourNetwork
        for r in self.four_network.recall(query, top_k=limit):
            all_hits.append(SearchHit(node_id="", score=0.5, content=r.get("content", ""),
                                      snippet=r.get("content", "")[:200]))

        # Route 4: RTKCache
        cached = self.cache.get(key=query)
        if cached:
            all_hits.append(SearchHit(node_id="", score=0.8, content=str(cached)))

        # Route 5: Polyphonic
        for r in self.search.search(query, store=self.store, graph_memory=self.graph_memory, limit=limit):
            all_hits.append(SearchHit(node_id=r.get("id", ""), score=r.get("score", 0.5),
                                      content=r.get("content", "")))

        # Deduplicate + sort
        seen = set()
        unique = []
        for h in all_hits:
            if h.node_id not in seen:
                seen.add(h.node_id)
                unique.append(h)
        unique.sort(key=lambda h: h.score, reverse=True)
        unique = unique[:limit]

        duration = (time.time() - start) * 1000

        # Side effects
        if unique:
            self.cache.put(key=query, value=unique[0].content)
        self.compressor.compress(query)
        self.model_router.route(query)
        self.session.create(f"recall_{int(time.time())}")
        self.brain.decide({"action": "recall", "query": query, "result_count": len(unique)})

        return SearchResults(hits=unique, total_count=len(unique), query=query, duration_ms=duration)

    # ============================================================
    # evolve pipeline (10 stages)
    # ============================================================
    def evolve(self, context: str = "", branch: str = "main") -> EvolutionOutcome:
        start = time.time()

        # Step 0: LoopGuard
        self.loop_guard.start()
        loop_state = self.loop_guard.check()
        if loop_state in (LoopState.CIRCUIT_BREAKER,):
            return EvolutionOutcome(result=EvolutionResult.BLOCKED, details="LoopGuard")

        # Step 1: EquilibriumGuard
        if self.equilibrium.get_alert_level() == AlertLevel.RED:
            return EvolutionOutcome(result=EvolutionResult.BLOCKED, details="Equilibrium RED")

        # Step 2: AntiEvolutionGate
        anti = self.anti_evolution.check(hypothesis=context or "auto-evolution")
        if not anti.passed:
            return EvolutionOutcome(result=EvolutionResult.BLOCKED, details=f"AntiEvolution: {anti.verdict}")

        # Step 3: VerificationIronLaw
        self.iron_law.verify(claim=context or "auto-evolution")

        # Step 4: RLPathology
        self.rl_pathology.detect_all()

        # Step 4.5: UCB1
        try:
            strategy = self.ucb1.select()
            self.ucb1.update(strategy, 0.5)
        except Exception:
            strategy = "default"

        # Step 4.6: FGG
        self.fggm.verify_compat({"context": context})

        # Step 4.7: EvalDriven
        self.eval_engine.evaluate({"context": context, "strategy": strategy})

        # Step 4.8: DAG scheduling
        self.dag_scheduler.add_task(f"evolve_{int(time.time())}", {"context": context})

        # Step 4.9: ConfidenceGate
        self.confidence_gate.check({"context": context})

        # Step 5: Execute evolution
        fitness_before = self._compute_fitness()

        # CoEvolution
        self.coevolve.evolve([context or "auto"])

        # SpeculativeEvolution
        self.speculative.fork(context)

        # SpeculativeFork
        self.speculative_fork.fork(context or "auto")

        # LotkaVolterra
        self.lotka_volterra.add_species(context or "auto", initial_pop=fitness_before * 100)
        self.lotka_volterra.simulate(dt=0.1)

        # ToolFitness
        self.tool_fitness.predict(context or "auto", "evolve")

        # CommunityTree
        self.community_tree.add_child(None, {"context": context, "fitness": fitness_before})

        # EDRE
        self.edre.replicate({"context": context, "fitness": fitness_before})

        # FiveStepEvolution
        self.five_step.evolve(context)

        # DeepRetrofit
        self.retrofit.retrofit(context)

        # Main evolution (eval_engine + evolution_engine)
        evo_ctx = EvolutionContext()
        evo_ctx.metadata = {"context": context, "branch": branch}
        result = self.eval_engine.evolve(evo_ctx)
        self.evolution_engine.evolve(context)
        fitness_after = self._compute_fitness()

        # Reflexion
        self.reflexion.reflect(context or "evolve", f"delta={fitness_after - fitness_before:.4f}", fitness_after)

        # Debate
        self.debate.debate(context or "evolution", [f"before={fitness_before:.4f}", f"after={fitness_after:.4f}"])

        # MultiAgent
        self.multi_agent.register_agent(f"evolver_{int(time.time())}")

        # BootstrapCI
        self.bootstrap.compute([fitness_before, fitness_after])

        # SEAGym
        self.seagym.evaluate(context or "evolve", f"delta={fitness_after - fitness_before:.4f}", fitness_after)

        # EvolutionGrill
        self.evolution_grill.review({"context": context, "delta": fitness_after - fitness_before})

        # Marginal
        delta = fitness_after - fitness_before
        self.marginal.record(delta, "evolution", context)

        # AntiEvolution record
        self.anti_evolution.record_score(fitness_after)

        return EvolutionOutcome(
            result=EvolutionResult.SUCCESS,
            fitness_before=fitness_before, fitness_after=fitness_after,
            duration_ms=(time.time() - start) * 1000,
            details=f"delta={delta:.4f}",
        )

    # ============================================================
    # learn pipeline
    # ============================================================
    def learn(self, source: str = "web", query: str = "AI", max_results: int = 5) -> dict:
        # Step 1: KnowledgeScanner
        scan_source = ScanSource(source) if source in [s.value for s in ScanSource] else ScanSource.WEB
        results = self.knowledge_scanner.scan(scan_source, query, max_results, force=True)

        # Step 2-3: remember each result
        new_nodes = []
        for r in results:
            node_id = self.remember(content=f"{r.title}: {r.content}",
                                    utility=0.7, tags=r.tags)
            if node_id:
                new_nodes.append(node_id)

        # Step 4: CuriosityQueue
        for r in results:
            self.curiosity_queue.add(f"What is {r.title}?", priority=5)

        # Step 5: UtilityTracker
        for node_id in new_nodes:
            self.utility_tracker.register(node_id)

        self.skill_registry.register(type("Skill", (), {"name": f"learn_{source}_{query}"})())
        self.curator.evaluate(type("Skill", (), {"name": f"learn_{source}_{query}", "content": query})())
        self.skill_claw.route(query)
        self.mechanism_registry.register(f"learn_{source}", {"query": query, "count": len(new_nodes)})
        self.cot.generate(f"Learned from {source}: {query}")
        for r in results[:3]:
            self.few_shot.add_example(r.title, r.content[:200])
        self.knowledge_gen.generate({"source": source, "query": query, "results": len(new_nodes)})
        self.refiner.refine({"action": "learn", "source": source, "query": query})

        return {"source": source, "query": query, "total_results": len(new_nodes), "new_nodes": len(new_nodes)}

    # ============================================================
    # reflect pipeline
    # ============================================================
    def reflect(self) -> dict:
        fv = self.five_view.evaluate()
        hv = self.harness_x.evaluate()
        drift = self.drift_detector.detect()
        self.thermodynamic.update(0.1)
        self.convergence.observe(fv.composite_score)
        self.coala.observe({"five_view": fv.composite_score, "harness": hv.composite_score})
        self.info_gain.record_gain("reflect", fv.composite_score)
        self.agent_forest.add_agent(f"reflector_{int(time.time())}", {"score": fv.composite_score})
        self.dynamic_scaler.scale("reflect", fv.composite_score)
        self.behavior_mirror.mirror("self", "reflect", {"score": fv.composite_score})

        # CausalKnowledgeGraph
        self.causal_graph.add_node(f"reflect_{int(time.time())}", f"score={fv.composite_score:.2f}",
                                   {"drift": len(drift)})

        # Feedback + FailureLog
        worst = self.feedback.get_worst_performers(top_k=5)
        avoidance = self.failure_log.get_avoidance_list()

        return {
            "five_view": {"score": fv.composite_score, "grade": fv.grade},
            "harness": {"score": hv.composite_score, "grade": hv.grade},
            "drift_alerts": len(drift),
            "thermodynamic": self.thermodynamic.get_stats(),
            "convergence": self.convergence.is_converged(),
            "worst_performers": len(worst),
            "avoidance_list": len(avoidance),
        }

    # ============================================================
    # dream pipeline
    # ============================================================
    def dream_cycle(self, branch: str = "main") -> DreamResult:
        nodes = self.store.get_branch_nodes(branch)
        for node in nodes:
            self.dream.register_memory(node)

        dream_result = self.dream.run_cycle(branch=branch)
        self.shmr.generate(entities=[], context="dream")
        self.consolidation_engine.run()
        self.rare_valid.detect()
        self.mars.create_belief("dream_belief", "Dream synthesis", 0.5)
        self.gravity.add_node("dream", mass=0.5)
        self.forgetting.compute_retention_compat("dream", age=1.0)
        self.state_machine.transition(LoopState.RUNNING)
        self.consistency.vote([n.content[:100] for n in nodes[:10]])
        self.extended_thinking.think({"context": "dream", "memory_count": len(nodes)})
        self.dna_extractor.extract({"memories": len(nodes), "patterns": dream_result.patterns_found})

        return dream_result

    # ============================================================
    # maintain pipeline
    # ============================================================
    def maintain(self) -> dict:
        start = time.time()

        self.bank.run_migration()
        self.bank.run_aging()
        self.consolidation_engine.run()
        self.convergence.update(self.bank.count())
        self.thermodynamic.update(0.1)
        self.circuit_breaker.record_success()
        self.self_healing.heal({"bank_count": self.bank.count()})
        self.mars.update_belief("dream_belief", 0.6)
        self.crash_recovery.recover({"status": "maintain", "bank_count": self.bank.count()})
        self.tool_loop.execute("maintain")
        self.organ_pipeline.execute({"action": "maintain"})
        self.hands.execute({"action": "maintain"})

        nodes = self.store.get_active_nodes(limit=20)
        for n in nodes:
            self.forgetting.compute_retention_compat(n.id, age=1.0)
            self.gravity.add_node(n.id, mass=n.utility)
            self.zscore.observe(n.utility)
        self.zscore.detect()
        self.drift_detector.observe_behavioral(0.5)

        return {
            "consolidation": self.consolidation.get_stats(),
            "convergence": self.convergence.get_stats(),
            "thermodynamic": self.thermodynamic.get_stats(),
            "duration_ms": (time.time() - start) * 1000,
        }

    # ============================================================
    # Branch system (from Omega-Omega)
    # ============================================================
    def branch_create(self, name: str, parent: str = "main") -> None:
        self.store.create_branch(name, parent)

    def branch_merge(self, source: str, target: str = "main") -> str:
        token = self.store.request_write_token(source, "omega", "merge")
        result = self.store.merge_branch(source, target, token=token)
        return result.write_id

    def branch_list(self) -> list[str]:
        return self.store.list_branches()

    # ============================================================
    # Status & Fitness
    # ============================================================
    def status(self) -> SystemStatus:
        return SystemStatus(
            node_count=self.store.get_node_count(),
            edge_count=self.store.get_edge_count(),
            active_sessions=1,
            uptime_seconds=time.time() - self._start_time,
            health=self._compute_health(),
            version="1.0.0",
            mechanisms=102,
            details={
                "bank_count": self.bank.count(),
                "convergence": self.convergence.is_converged(),
                "dopamine": self.dopamine.get_stats(),
                "five_gates": self.five_gates.get_stats(),
                "constitution": self.constitution.get_stats(),
                "graph_memory": self.graph_memory.get_stats(),
                "four_network": self.four_network.get_stats(),
                "utility_tracker": self.utility_tracker.get_stats(),
                "curiosity_queue": self.curiosity_queue.get_stats(),
                "knowledge_scanner": self.knowledge_scanner.get_stats(),
                "mars": self.mars.get_stats(),
                "evolution_engine": self.evolution_engine.get_stats(),
            },
        )

    def _compute_fitness(self) -> float:
        node_count = max(self.store.get_node_count(), 1)
        edge_count = self.store.get_edge_count()
        bank_count = max(self.bank.count(), 1)
        return min(1.0, (node_count * 0.001 + edge_count * 0.001 + bank_count * 0.01) / 3.0)

    def _compute_health(self) -> str:
        try:
            if self.store.get_node_count() == 0:
                return "empty"
            eq = self.equilibrium.get_alert_level()
            if eq == AlertLevel.RED:
                return "critical"
            if eq == AlertLevel.ORANGE:
                return "degraded"
            return "healthy"
        except Exception:
            return "unknown"

    def close(self):
        self.bank.close()
        self.cache.close()
        self.store.close()
        logger.info("Prometheus Ultra closed")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
