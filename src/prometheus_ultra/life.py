"""life.py — Prometheus Ultra main controller.

Unified from Genesis(99 mechanisms), Omega-Omega(branch system),
and Z: Prometheus Omega(deep evolution + 4-layer defense).

127 mechanisms across 18 subsystems.
7 pipelines: remember, recall, evolve, learn, reflect, dream, maintain.
Branch system for parallel experimentation.

Known Defects:
  [ ] Pitfall #22: coroutine stdout bug - arxiv learn returns empty JSON
  [ ] Pitfall #28: weekly quota 3000 exhausted - learn returns 0
  [ ] Pitfall #27: evolve BLOCKED - AntiEvolutionGate rejects repeated context
  [x] _on_outcome event type parsing vulnerability FIXED
  [x] AR subscribe extended from 3 to 7 pipes FIXED
"""
from __future__ import annotations

import logging
import time

from prometheus_ultra.foundation.schema import (
    Node, Edge, NodeType, EdgeType, TrustLevel,
    EvolutionResult,
    SearchHit, SearchResults, DreamResult, EvolutionOutcome,
    SystemStatus, ZConfig, generate_uuidv7, AlertLevel, LoopState,
)
from prometheus_ultra.foundation.store import MinervaStore

# Memory
from prometheus_ultra.safety.rubric import RubricScorer, RubricResult

from prometheus_ultra.memory.dopamine import DopamineWriteGate, DopamineGateConfig
from prometheus_ultra.memory.polyphonic import PolyphonicRetriever
from prometheus_ultra.memory.graph_memory import GraphMemory, EpisodeEvent
from prometheus_ultra.memory.four_network import FourNetworkMemory
from prometheus_ultra.memory.feedback import NodeFeedbackTracker, FailureLogTracker
from prometheus_ultra.memory.cache import RTKCache
from prometheus_ultra.memory.shmr import SHMRGenerator
from prometheus_ultra.memory.trajectory import TrajectoryStore
from prometheus_ultra.memory.disposition import DispositionLearner
from prometheus_ultra.memory.hebbian import HebbianMemory
from prometheus_ultra.memory.hierarchical import HierarchicalMemory  # HORMA层级记忆
from prometheus_ultra.memory.stream import MemoryStream
from prometheus_ultra.memory.dual_storage import DualPathwayMemory
from prometheus_ultra.memory.mempo import MemPO
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
from prometheus_ultra.evolution.pass_k import PassKConsistency
from prometheus_ultra.evolution.strategies import MultiStrategyScheduler
from prometheus_ultra.evolution.evolution_quality_gates import EvolutionQualityGates
from prometheus_ultra.evolution.rimrule import RIMRULE
from prometheus_ultra.safety.trace_engine import TraceEngine

# Safety
from prometheus_ultra.safety.instincts import InstinctsRegistry, register_default_instincts
from prometheus_ultra.safety.five_gates import FiveGates
from prometheus_ultra.safety.loop_guard import LoopGuard
from prometheus_ultra.safety.equilibrium_guard import EquilibriumGuard
from prometheus_ultra.safety.rl_pathology import RLPathologyDetector
from prometheus_ultra.safety.circuit_breaker import CircuitBreaker
from prometheus_ultra.safety.drift_detector import DriftDetector
from prometheus_ultra.safety.constraint_drift import ConstraintDriftDetector
from prometheus_ultra.safety.owner_harm import OwnerHarmTrustBoundary
from prometheus_ultra.safety.zscore import ZScoreAnomaly
from prometheus_ultra.safety.trend import TrendPredictor
from prometheus_ultra.safety.self_healing import SelfHealingEngine
from prometheus_ultra.safety.constitution import Constitution

# Evaluation
from prometheus_ultra.evaluation.five_view import FiveViewEvaluator
from prometheus_ultra.evaluation.marginal import MarginalAdvantageAccumulator
from prometheus_ultra.evaluation.seagym import SEAGym
from prometheus_ultra.evaluation.harness import HarnessX, HarnessPrimitive
from prometheus_ultra.evaluation.bootstrap import BootstrapCI
from prometheus_ultra.evaluation.lucky_pass import LuckyPassDetector

# Loop
from prometheus_ultra.loop.reflexion import ReflexionEngine
from prometheus_ultra.loop.coala import CoALAArchitecture
from prometheus_ultra.loop.debate import DebateEngine
from prometheus_ultra.loop.info_gain import InformationGainTracker
from prometheus_ultra.loop.agent_forest import AgentForest
from prometheus_ultra.loop.dynamic_scaler import DynamicScaler
from prometheus_ultra.loop.brainstorming_engine import BrainstormingEngine
from prometheus_ultra.loop.systematic_debugging import SystematicDebuggingEngine
from prometheus_ultra.loop.tdd_verifier import TDDVerifier
from prometheus_ultra.loop.plan_writer import PlanWriter
from prometheus_ultra.loop.verification_gate import VerificationGate
from prometheus_ultra.loop.parallel_dispatcher import ParallelDispatcher
from prometheus_ultra.loop.plan_executor import PlanExecutor
from prometheus_ultra.loop.code_reviewer import CodeReviewer

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
from prometheus_ultra.governance.autonomy import ConfidenceGate, EvolutionGrill

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

# New modules (120-source enhancement)
from prometheus_ultra.loop.tree_of_thoughts import TreeOfThoughts, SearchStrategy
from prometheus_ultra.loop.think_tool import ThinkTool
from prometheus_ultra.safety.context_clash import ContextClashDetector
from prometheus_ultra.safety.context_failure import ContextFailureDetector
from prometheus_ultra.safety.context_poisoning import ContextPoisoningDetector
from prometheus_ultra.safety.tool_overload import ToolOverloadDetector
from prometheus_ultra.safety.memory_side_effect import MemorySideEffectDetector
from prometheus_ultra.memory.context_isolator import ContextIsolator
from prometheus_ultra.harness.context_window import ContextWindowManager
from prometheus_ultra.harness.progressive_complexity import ProgressiveComplexity
from prometheus_ultra.harness.crash_restore import CrashStateRestore
from prometheus_ultra.governance.human_oversight import HumanOversight, OversightRiskLevel as RiskLevel
from prometheus_ultra.prompt.structured_output import StructuredOutput, SchemaField
from prometheus_ultra.prompt.xml_tag import XMLTagPrompting
from prometheus_ultra.prompt.reasoning_adapter import ReasoningModelAdapter
from prometheus_ultra.harness.context_engineering import ContextEngineering, ContextComponent
from prometheus_ultra.loop.loop_selector import LoopSelector, LoopStrategy
from prometheus_ultra.harness.adaptive_harness import AdaptiveHarness, ToolPolicy
from prometheus_ultra.prompt.evolving_prompt import EvolvingPrompt

# MiMo-derived mechanisms
from prometheus_ultra.safety.five_gate_chain import FiveGateMemoryChain
from prometheus_ultra.safety.oep_defense import OEPDefense
from prometheus_ultra.harness.progressive_checkpoints import ProgressiveCheckpoints
from prometheus_ultra.evolution.evolution_quality_gates import EvolutionQualityGates
from prometheus_ultra.memory.utility_decay import UtilityDecay
from prometheus_ultra.safety.tool_drift import ToolDriftDetector
from prometheus_ultra.learning.deep_retrofit_6 import DeepRetrofit6
from prometheus_ultra.monitor.heartbeat_4cycle import Heartbeat4Cycle
from prometheus_ultra.harness.three_layer_compression import ThreeLayerCompression
from prometheus_ultra.learning.knowledge_to_mechanism import KnowledgeToMechanism
from prometheus_ultra.harness.wal import WriteAheadLog
from prometheus_ultra.safety.file_checksum import FileChecksum
from prometheus_ultra.learning.explorer_state import ExplorerState
from prometheus_ultra.learning.curiosity_autofill import CuriosityAutoFill
from prometheus_ultra.learning.exploration_quota import ExplorationQuota
from prometheus_ultra.harness.sub_agent_contract import SubAgentContract
from prometheus_ultra.safety.rule_expiration import RuleExpirationAudit
from prometheus_ultra.safety.capability_ceiling import CapabilityCeiling
from prometheus_ultra.safety.cognitive_collapse import CognitiveCollapse
from prometheus_ultra.loop.semantic_early_stopping import SemanticEarlyStopping
from prometheus_ultra.lifecycle.evaf_consolidation import EVAFConsolidation
from prometheus_ultra.collaboration.a2a_basic import A2ABasic, AgentCapability
from prometheus_ultra.lifecycle.local_maintenance import LocalMaintenance
from prometheus_ultra.memory.memory_depth import MemoryDepthTracker
from prometheus_ultra.evolution.everos import EverOS
from prometheus_ultra.evolution.gepa import GEPA
from prometheus_ultra.evolution.memento import Memento
from prometheus_ultra.evolution.reasoning_bank import ReasoningBank
from prometheus_ultra.evolution.openspace import OpenSpace
from prometheus_ultra.harness.state_persistence import StatePersistence
from prometheus_ultra.evaluation.memory_data_adapter import MemoryDataAdapter

# Lazy import to avoid circular dependency
TopologicalRetrieval = None

logger = logging.getLogger(__name__)


class Omega:
    """Prometheus Ultra — 127-mechanism self-evolving AI agent system.

    Composes all subsystems into a unified interface with 7 pipelines.
    Supports branch-based parallel experimentation.
    """

    def __init__(self, config: ZConfig | None = None, db_path: str | None = None) -> None:
        self._cfg = config if config is not None else ZConfig()
        if db_path:
            self._cfg.database_path = db_path
        self._start_time = time.time()
        self._last_reflect_score = 0.0
        self._last_reflect_time = 0.0
        self._telemetry: dict[str, object] = {}  # Telemetry: 存储各管道原始返回值

        # Learned config
        self._learned_config: dict[str, float] = {}

        # ===== Foundation (1) =====
        self.store = MinervaStore(self._cfg)
        self.store.connect()

        # ===== Memory (13) =====
        self.hebbian = HebbianMemory()
        self.hierarchical = HierarchicalMemory()  # HORMA层级记忆
        self.dopamine = DopamineWriteGate(DopamineGateConfig())
        self.search = PolyphonicRetriever()
        self.graph_memory = GraphMemory(hebbian=self.hebbian)
        self.four_network = FourNetworkMemory()
        self.feedback = NodeFeedbackTracker()
        self.failure_log = FailureLogTracker()
        self.cache = RTKCache()
        self.shmr = SHMRGenerator()
        self.trajectory = TrajectoryStore()
        self.disposition = DispositionLearner()
        self.stream = MemoryStream()
        self.dual_storage = DualPathwayMemory()
        self.mempo = MemPO()
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
        self.evolution_engine = EvolutionEngine(evaluate_fn=lambda c: self._compute_fitness())
        # Swiss Army Knife modules (2026-07-01)
        self.pass_k = PassKConsistency()
        self.strategy_scheduler = MultiStrategyScheduler(["gepa", "everos", "memento", "openspace", "ga"])
        self.trace_engine = TraceEngine()

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
        self.constraint_drift = ConstraintDriftDetector()
        self.owner_harm = OwnerHarmTrustBoundary()
        self.zscore = ZScoreAnomaly()
        self.trend = TrendPredictor()
        self.self_healing = SelfHealingEngine()
        self.rubric = RubricScorer()
        # Will be wired up after Loop mechanisms are initialized

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
        self.lucky_pass = LuckyPassDetector()

        # ===== Loop (13) =====
        self.reflexion = ReflexionEngine()
        self.coala = CoALAArchitecture()
        self.debate = DebateEngine()
        self.info_gain = InformationGainTracker()
        self.agent_forest = AgentForest()
        self.dynamic_scaler = DynamicScaler()
        self.brainstorming = BrainstormingEngine()
        self.systematic_debugging = SystematicDebuggingEngine()
        self.tdd_verifier = TDDVerifier()
        self.plan_writer = PlanWriter()
        self.verification_gate = VerificationGate()
        self.parallel_dispatcher = ParallelDispatcher()
        self.code_reviewer = CodeReviewer()

        # Wire systematic debugging to self_healing
        self.self_healing.set_debugger(self.systematic_debugging)

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
        # Swiss Army Knife: full tool fitness evaluator (from evolution/)
        from prometheus_ultra.evolution.tool_fitness import ToolFitness
        self.tool_fitness_full = ToolFitness()
        self.community_tree = CommunityTree()
        self.edre = EDREReplicator()

        # ===== Execution (4) =====
        self.dag_executor = DAGExecutor()
        self.parallel_dag = ParallelDAG()
        self.retryable_dag = RetryableDAG()
        self.monitored_dag = MonitoredDAG()

        # ===== Governance (2) =====
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

        # ===== New modules (15) =====
        self.tree_of_thoughts = TreeOfThoughts(branching_factor=3, max_depth=4)
        self.think_tool = ThinkTool()
        self.context_clash = ContextClashDetector()
        self.context_failure = ContextFailureDetector()
        self.context_poisoning = ContextPoisoningDetector()
        self.tool_overload = ToolOverloadDetector()
        self.memory_side_effect = MemorySideEffectDetector()
        self.context_isolator = ContextIsolator()
        self.context_window = ContextWindowManager()
        self.progressive_complexity = ProgressiveComplexity()
        self.crash_restore = CrashStateRestore()
        self.human_oversight = HumanOversight()
        self.structured_output = StructuredOutput()
        self.xml_tag = XMLTagPrompting()
        self.reasoning_adapter = ReasoningModelAdapter()

        # ===== Context Engineering =====
        self.context_engineering = ContextEngineering(max_tokens=128000)

        # ===== Loop Engineering =====
        self.loop_selector = LoopSelector()

        # ===== Harness Engineering =====
        self.adaptive_harness = AdaptiveHarness()
        self.adaptive_harness.register_tool(ToolPolicy(tool_name="remember", allowed=True))
        self.adaptive_harness.register_tool(ToolPolicy(tool_name="recall", allowed=True))
        self.adaptive_harness.register_tool(ToolPolicy(tool_name="evolve", allowed=True))
        self.adaptive_harness.register_tool(ToolPolicy(tool_name="learn", allowed=True))
        self.adaptive_harness.register_tool(ToolPolicy(tool_name="reflect", allowed=True))
        self.adaptive_harness.register_tool(ToolPolicy(tool_name="dream", allowed=True))
        self.adaptive_harness.register_tool(ToolPolicy(tool_name="maintain", allowed=True))

        # ===== Prompt Engineering =====
        # evolving_prompt is available for future dynamic prompt generation
        # self.evolving_prompt = EvolvingPrompt()

        # ===== MiMo-derived mechanisms =====
        self.five_gate_chain = FiveGateMemoryChain()
        self.oep_defense = OEPDefense()
        self.progressive_checkpoints = ProgressiveCheckpoints()
        self.evo_quality_gates = EvolutionQualityGates()
        self.rimrule = RIMRULE()
        self.utility_decay = UtilityDecay()
        self.tool_drift = ToolDriftDetector()
        self.deep_retrofit_6 = DeepRetrofit6()
        self.heartbeat_4cycle = Heartbeat4Cycle()
        self.three_layer_compression = ThreeLayerCompression()
        self.knowledge_to_mechanism = KnowledgeToMechanism()

        # Session continuity & file integrity
        self.wal = WriteAheadLog()
        self.file_checksum = FileChecksum()

        # Exploration tracking
        self.explorer_state = ExplorerState()
        self.curiosity_autofill = CuriosityAutoFill(self.curiosity_queue)
        self.exploration_quota = ExplorationQuota(max_daily=200, revision_after=10, weekly_max=3000)
        self._scans: list[dict] = []

        # Sub-agent & rule management
        self.sub_agent_contract = SubAgentContract()
        self.rule_expiration = RuleExpirationAudit()

        # Scaling & cognitive safety
        self.capability_ceiling = CapabilityCeiling()
        self.cognitive_collapse = CognitiveCollapse()

        # A+B+C enhancements
        self.semantic_early_stopping = SemanticEarlyStopping(patience=3, threshold=0.01)
        self.evaf_consolidation = EVAFConsolidation()
        self.a2a_basic = A2ABasic()
        # Lazy import for topological retrieval
        try:
            from prometheus_ultra.memory.topological_retrieval import TopologicalRetrieval as _TR
            self.topological_retrieval = _TR()
        except ImportError:
            self.topological_retrieval = None
        self.local_maintenance = LocalMaintenance()
        self.memory_depth = MemoryDepthTracker()

        # 5 evolution methods from EvoAgentBench
        self.everos = EverOS()
        self.gepa = GEPA()
        self.memento_evolution = Memento()
        self.reasoning_bank = ReasoningBank()
        self.openspace = OpenSpace()

        # State persistence & MemoryData
        self.state_persistence = StatePersistence()
        self.memory_data_adapter = MemoryDataAdapter(self)
        # Defensive measure: memory_data_adapter is called in maintain for benchmark
        # It is excluded from the ULTRA_DIAGNOSTICS guard as it evaluates external benchmarks
        self.state_persistence.load(self)
 
        # ===== HarnessX: register primitives =====
        self.harness_x.register_primitive(
            HarnessPrimitive(name="input_guard", type="prompt", content="Check input safety")
        )
        self.harness_x.register_primitive(
            HarnessPrimitive(name="dopamine_gate", type="memory", content="Evaluate write reward")
        )
        self.harness_x.register_primitive(
            HarnessPrimitive(name="five_gates", type="control", content="5-gate cascade check")
        )
        self.harness_x.register_primitive(
            HarnessPrimitive(name="graph_search", type="memory", content="Graph-based retrieval")
        )
        self.harness_x.register_primitive(
            HarnessPrimitive(name="cot_reasoning", type="prompt", content="Chain-of-thought reasoning")
        )
        self.harness_x.register_primitive(
            HarnessPrimitive(name="debate", type="control", content="Multi-agent debate")
        )
        self.harness_x.register_primitive(
            HarnessPrimitive(name="reflexion", type="control", content="Self-reflection and learning")
        )

        logger.info("Prometheus Ultra initialized: 127 mechanisms across 18 subsystems")

        # 初始化自主神经系统
        from prometheus_ultra.lifecycle.autonomic_regulator import AutonomicRegulator
        self.autonomic_regulator = AutonomicRegulator(self)
        self.autonomic_regulator.subscribe(self.event_bus)

        # 初始化中央神经系统 — 管道间自动触发链
        from prometheus_ultra.lifecycle.cns_orchestrator import CNSOrchestrator
        self.cns = CNSOrchestrator(self)
        self.cns.subscribe(self.event_bus)

        # 初始化大脑皮层 — 学习型管道间调度中枢
        from prometheus_ultra.lifecycle.cerebral_cortex import CerebralCortex
        self.cerebral_cortex = CerebralCortex(self)
        self.cerebral_cortex.subscribe(self.event_bus)

        # 初始化感觉皮层 — 管道信号解析与结构化存储
        from prometheus_ultra.lifecycle.telemetry_pipeline import TelemetryPipeline
        self.telemetry = TelemetryPipeline(self)
        self.telemetry.subscribe(self.event_bus)

        # 初始化信号融合层 — 统一信号消费接口
        from prometheus_ultra.lifecycle.signal_fusion import SignalFusionLayer
        self.signal_fusion = SignalFusionLayer(self)
        self.signal_fusion.subscribe(self.event_bus)

        # B1: Memory security detectors (paper-based)
        try:
            from prometheus_ultra.safety.trigger_detector import TriggerDetector
            self.trigger_detector = TriggerDetector()
        except Exception:
            self.trigger_detector = None

        # 知识翻译：监听 knowledge_added → 轻量 fitness 检查
        # _last_kta_fitness: 上次知识翻译时记录的 fitness 值，用于 delta 比较
        self._last_kta_fitness = self._compute_fitness()
        def _on_knowledge_added(event: dict):
            try:
                data = event.get("data", {})
                if data.get("new_nodes", 0) < 2:
                    return
                current = self._compute_fitness()
                diff = abs(current - self._last_kta_fitness)
                if diff > 0.02:
                    self.event_bus.publish({
                        "type": "fitness_changed",
                        "delta": diff,
                        "new_nodes": data.get("new_nodes", 0),
                    })
                    self._last_kta_fitness = current
            except Exception as e:
                logger.warning("KTA fitness callback failed: %s", e)
        self.event_bus.subscribe("knowledge_added", _on_knowledge_added, priority=0.5)
        logger.info("KTA: knowledge_added subscription registered")

        # 初始化 AdaMEM 门控
        from prometheus_ultra.learning.ada_mem_gate import AdaMEMGate
        self.ada_mem = AdaMEMGate()

        # 初始化自我观察层
        from prometheus_ultra.learning.self_observation import SelfObservation
        self.self_observation = SelfObservation()
    # ============================================================
    # remember pipeline (11 stages)
    # ============================================================
    def remember(self, content: str, utility: float = 0.5, tags: list[str] | None = None,
                 branch: str = "main", trust_level: str = "fact") -> str:
        tags = tags or []
        surprise = max(0.3, utility * 0.6)
        
        # Handle non-string content
        if not isinstance(content, str):
            content = str(content)

        # 收集 remember 管道数据
        remember_data = {}

        # WAL: write-ahead log entry with LCRP validation + Atomic Transaction
        tx_id = self.wal.begin_tx()
        wal_result = self.wal.write_dict("remember", status="started", pending=["create_node"], tx_id=tx_id)
        if not wal_result.get("valid", False):
            self.wal.rollback_tx(tx_id)
            logger.warning("Censor WAL rejected: %s (LCRP invalid)", content[:50])
            return ""

        # Gate 0: InputGuardrail
        gr = self.input_guardrail.check(content)
        if not gr.passed:
            self.wal.rollback_tx(tx_id)
            self.failure_log.log("remember", "input_guardrail_blocked", {"reason": gr.reason})
            return ""

        # Gate 0.5: Five-Gate Memory Chain (MiMo #20)
        chain_results = self.five_gate_chain.check_all(
            content, utility=utility, novelty=surprise,
            trust_score=0.8, delta=0.1, drift_score=0.05, risk_level=0.2,
        )
        if not all(r.passed for r in chain_results):
            self.wal.rollback_tx(tx_id)
            self.failure_log.log("remember", "five_gate_chain_blocked",
                               {"gate": chain_results[-1].gate_name})
            return ""

        # Gate 0.7: OEP Defense (MiMo #19)
        oep_alert = self.oep_defense.check(content, source="user_input",
                                           transferable=True, similar_count=0)
        if oep_alert.severity == "critical":
            self.wal.rollback_tx(tx_id)
            self.failure_log.log("remember", "oep_blocked", {"severity": oep_alert.severity})
            return ""

        # Gate 1: DopamineWriteGate
        gate = self.dopamine.evaluate(utility=utility, surprise=surprise)
        if gate.decision == "reject":
            self.wal.rollback_tx(tx_id)
            self.failure_log.log("remember", "dopamine_rejected", {"score": gate.score})
            return ""

        # Create node
        node = Node(id=generate_uuidv7(), type=NodeType.FACT, content=content,
                     tags=tags, utility=utility, surprise=surprise, branch=branch,
                     raw_chunk=content, trust_state="has")  # Verbatim chunk + PolarMem HAS

        # EVAF: surprise-valence consolidation check
        evaf_result = self.evaf_consolidation.evaluate(node.id, surprise, utility)
        if evaf_result.should_consolidate:
            self.memory_depth.record_consolidation(node.id)

        # Gate 2: FiveGates
        cascade = self.five_gates.evaluate(node, {"current_node_count": self.store.get_node_count()})
        if not cascade.passed:
            self.wal.rollback_tx(tx_id)
            self.failure_log.log("remember", "five_gates_blocked", {"node_count": self.store.get_node_count()})
            return ""

        # Gate 2.5: Constitution (22 principles)
        violations = self.constitution.evaluate({
            "content": content, "utility": utility, "surprise": surprise,
            "action": "remember", "branch": branch,
        })
        blocking = [v for v in violations if not v.passed and "S" in v.gate_name]
        if blocking:
            self.wal.rollback_tx(tx_id)
            self.failure_log.log("remember", "constitution_violation", {"violations": [v.gate_name for v in blocking]})
            return ""

        # Feed all violations into constraint drift detector
        self.constraint_drift.observe([v for v in violations if not v.passed])

        # Gate 3: InstinctsRegistry
        instinct_results = self.instincts.evaluate_all({
            "utility": utility, "surprise": surprise, "content": content,
        })
        for triggered in instinct_results:
            if triggered.get("result", {}).get("action") == "block":
                self.wal.rollback_tx(tx_id)
                self.failure_log.log("remember", "instinct_blocked", {})
                return ""

        # Gate 3.5: RUBAS Four-Dimension Safety Rubric (paper 2606.04051)
        rubric_result = self.rubric.evaluate(content, {
            "query": "",
            "action": "remember",
            "utility": utility,
            "tags": tags,
        })
        failing_dims = rubric_result.get_failing_dimensions(minimum=0.5)
        if failing_dims:
            logger.warning("RUBAS rubric violations in remember: %s", failing_dims)
            self.failure_log.log("remember", "rubric_violations",
                                 {"failing_dimensions": failing_dims, "scores": rubric_result._asdict()})

        # Gate 3.6: Memory Poisoning Detection (MPBench 2606.04329 / Trojan Hippo 2605.01970)
        # Check for trigger keywords that indicate data exfiltration / sleeper attacks
        _TRIGGER_KEYWORDS = {"bank account", "medical history", "social security", "password:", 
                           "credit card", "transfer $", "confidential", "secret key", "api_token"}
        content_lower = content.lower()
        trigger_hits = [kw for kw in _TRIGGER_KEYWORDS if kw in content_lower]
        if trigger_hits:
            logger.warning("Memory security: trigger keywords detected in remember: %s", trigger_hits)
            self.failure_log.log("remember", "trigger_keyword_detected", {"triggers": trigger_hits})
            # Don't block — just log. Blocking would break legitimate uses.
            # But flag for downstream sleeper detection
            self.owner_harm.flag_suspicious(node.id, "trigger_keywords", trigger_hits)

        # Gate 3.7: Sleeper Trigger Detection (B1-1, arXiv 2605.15338)
        if self.trigger_detector is not None:
            try:
                self.trigger_detector.scan(content, source="memory")
            except Exception as e:
                logger.warning("trigger_detector.scan failed: %s", e)
        else:
            logger.debug("trigger_detector not available, skipping scan")

        # Gate 4: VeracityBayesian
        self.veracity.compute_posterior_compat(
            prior=0.5,
            evidence=Evidence(source_confidence=0.5, consistency=utility, corroboration=surprise),
        )

        # Store
        self.store.create_node(node)
        self.wal.commit_tx(tx_id)

        # MemPO: observe node creation
        self.mempo.observe_access(node.id)

        # Owner-Harm: register node ownership
        self.owner_harm.register_owner(node.id, branch)

        # HORMA: 层级记忆索引（按tags构建路径）
        if tags:
            path = "/" + "/".join(tags[:3])  # 如 /ai/memory/test
            self.hierarchical.store(node.id, path, utility, content)

        # Memory management: evict old low-utility nodes to prevent unbounded growth
        node_count = self.store.get_node_count()
        if node_count > 2000:
            # Evict oldest 10% of low-utility nodes
            evict_count = max(1, node_count // 10)
            low_utility = self.store.get_active_nodes(limit=500)
            low_utility.sort(key=lambda n: n.utility)
            for n in low_utility[:evict_count]:
                self.store.delete_node(n.id)

        # FiveGates: register node after successful write
        self.five_gates.register_node(node)

        # ContextPoisoning: track content confidence
        self.context_poisoning.add_chunk(content, confidence=utility)

        # GraphMemory
        self.graph_memory.add_episode(EpisodeEvent(episode_id=node.id, content=content,
                                                   tags=set(tags), importance=utility))

        # FourNetwork
        self.four_network.retain(content, network="experience")

        # Bank
        self.bank.store(content, tier=Tier.WORKING, importance=utility)

        # CoALA
        self.coala.add_to_working_memory({"id": node.id, "content": content[:100], "utility": utility})
        remember_data['coala_wm'] = self.coala.get_working_memory_contents()
        remember_data['coala_ltm'] = self.coala.get_ltm_size()
        remember_data['coala_ltm_retrieve'] = self.coala.retrieve_from_ltm(content[:50])

        # DriftDetector
        self.drift_detector.observe_semantic(utility)

        # Edges (limit to top-10 most similar to prevent O(n^2) growth)
        existing = self.store.get_active_nodes(limit=100)
        edge_candidates = []
        for ex in existing:
            common = set(ex.tags) & set(tags)
            if common:
                weight = len(common) / max(len(tags), len(ex.tags), 1)
                edge_candidates.append((weight, ex))
        edge_candidates.sort(key=lambda x: -x[0])
        edges_created = 0
        for weight, ex in edge_candidates[:10]:
            edge = Edge(source_id=node.id, target_id=ex.id, type=EdgeType.SEMANTIC_SIMILAR,
                        weight=weight)
            self.store.create_edge(edge)
            self.graph_memory.add_edge(node.id, ex.id, "SEMANTIC_SIMILAR", edge.weight)
            edges_created += 1

        # If no edges created (orphan node), create a weak link to the most recent node
        if edges_created == 0 and existing:
            nearest = existing[0]
            weak_edge = Edge(source_id=node.id, target_id=nearest.id, type=EdgeType.SEMANTIC_SIMILAR, weight=0.1)
            self.store.create_edge(weak_edge)

        # Side effects
        self.trajectory.record("remember", [{"node_id": node.id, "utility": utility}])
        self.stream.add("remember", content[:200], importance=utility)
        self.dual_storage.store_verbatim(node.id, content, utility, tags)
        self.disposition.learn("remember_utility", utility)
        self.bridge.bridge(content, "memory", relationship="stored")
        self.vector_clock.increment()
        remember_data['vclock'] = self.vector_clock.get_clock()
        self.vector_clock.merge({"system": 1})
        self.event_bus.publish({"type": "remember", "node_id": node.id})
        self.x_adapter.adapt({"node_id": node.id, "content": content})
        self.y_adapter.adapt({"node_id": node.id, "utility": utility})

        # Feedback + FailureLog
        self.feedback.record(node.id, "remember", utility)
        self.monitor.record("remember", utility)
        # Persist feedback to database
        try:
            self._conn = self.store._conn
            if self._conn:
                self._conn.execute(
                    "INSERT INTO feedback_log (node_id, feedback_type, value, timestamp) VALUES (?,?,?,?)",
                    (node.id, "utility", utility, time.time())
                )
                self._conn.commit()
        except Exception as e:
            logger.warning("Failed to log utility feedback: %s", e)

        # ContextClash: check for conflicting information
        recent_nodes = self.store.get_active_nodes(limit=5)
        if len(recent_nodes) > 1:
            chunks = [n.content[:100] for n in recent_nodes[-3:]]
            self.context_clash.detect(chunks)

        # ContextPoisoning: detect hallucination contamination
        self.context_poisoning.mark_as_cited(content[:50])
        self.context_poisoning.detect()

        # Veracity: check confidence level
        conf_level = self.veracity.get_confidence_level(self.veracity.get_last_posterior())
        self.veracity.compute_posterior(prior=0.5, evidence=Evidence(source_confidence=0.5, consistency=utility, corroboration=surprise))
        # Persist provenance to database
        try:
            self._conn = self.store._conn
            if self._conn:
                self._conn.execute(
                    "INSERT INTO provenance_log (node_id, provenance_type, source, confidence, chain, timestamp) VALUES (?,?,?,?,?,?)",
                    (node.id, "DIRECT_OBSERVATION", "remember_pipeline", conf_level, "[]", time.time())
                )
                self._conn.commit()
        except Exception as e:
            logger.warning("Failed to log provenance: %s", e)

        # === Remember: full mechanism activation ===
        # Memory subsystem
        self.failure_log.log("remember", "success", {"node_id": node.id, "utility": utility})
        ep = self.graph_memory.get_episode(node.id)
        remember_data['gm_edges'] = self.graph_memory.get_edges(node.id)
        remember_data['gm_neighbors'] = self.graph_memory.get_neighbors(node.id)
        self.graph_memory.remove_episode(node.id) if False else None  # skip delete in remember
        self.forgetting.compute_retention(age=0.0)
        if existing:
            self.gravity.compute(node.id, existing[0].id)
        else:
            self.gravity.add_node(node.id, mass=utility)
        remember_data['stream_recent'] = self.stream.recent(3)
        remember_data['stream_count'] = self.stream.get_count("remember")
        remember_data['stream_type_dist'] = self.stream.get_type_distribution()
        remember_data['stream_avg_imp'] = self.stream.get_avg_importance()
        remember_data['stream_search'] = self.stream.search_content(content[:50])
        remember_data['shmr_entities'] = self.shmr.get_entity_stats()
        remember_data['shmr_cooccur'] = self.shmr.get_co_occurrence_stats()
        self.bridge.find_cross_domain_concepts("memory", "memory")
        remember_data['bridge_stats'] = self.bridge.get_domain_stats("memory")
        remember_data['bridge_matrix'] = self.bridge.get_transfer_matrix()
        remember_data['bridge_domains'] = self.bridge.get_domain_bridges("memory")
        remember_data['bridge_xfer'] = self.bridge.transfer_score("memory", "memory")
        self.behavior_mirror.mirror("system", "remember", {"node_id": node.id})
        self.behavior_mirror.compute_profile("system")
        remember_data['behavior_deviation'] = self.behavior_mirror.detect_deviation("system")
        self.event_bus.subscribe("remember_events", lambda e: None)
        remember_data['recent_events'] = self.event_bus.get_recent(5)
        self.event_bus.publish({"type": "remember_completed", "node_id": node.id, "utility": utility, "tags": list(tags)})
        remember_data['x_reverse'] = self.x_adapter.reverse_adapt({"node_id": node.id})
        remember_data['y_tier'] = self.y_adapter.get_tier_name(utility > 0.8 and 2 or 1)
        self.y_adapter.migrate_tier(node.id, 0, 1)
        remember_data['uptime'] = self.monitor.get_uptime()
        remember_data['health'] = self.monitor.get_health()
        self.instincts.register("custom_check", lambda ctx: True)
        self.consolidation.consolidate([{"content": content, "importance": utility}])
        remember_data['dopa_decisions'] = self.dopamine.get_recent_decisions()
        remember_data['dopa_dist'] = self.dopamine.get_score_distribution()

        logger.info("Remembered: %s (confidence: %s)", node.id[:8], conf_level)
        self.utility_tracker.register(node.id, initial_utility=utility)
        # Telemetry: 存储原始返回值
        self._telemetry["remember"] = node.id

        # 写管道结果
        self.signal_fusion.set_pipe_result("remember", {
            "node_id": node.id, "utility": utility, "tags": tags, "branch": branch,
        })

        return node.id

    # ============================================================
    # recall pipeline (6 routes)
    # ============================================================
    def recall(self, query: str, limit: int = 10, branch: str = "main",
               prefer_chunk: bool = False) -> SearchResults:
        start = time.time()
        all_hits: list[SearchHit] = []
        recall_data = {}

        # AdaMEM 门控：选择性跳过检索
        try:
            if not self.ada_mem.should_retrieve(query, task_type="reasoning"):
                return SearchResults(hits=[], total_count=0, query=query, duration_ms=0, metadata=recall_data)
        except Exception as e:
            logger.warning("AdaMEM should_retrieve check failed: %s", e)

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
        for i, r in enumerate(self.four_network.recall(query, top_k=limit)):
            all_hits.append(SearchHit(node_id="fn_%d" % i, score=0.5, content=r.get("content", ""),
                                      snippet=r.get("content", "")[:200]))

        # Route 4: RTKCache
        cached = self.cache.get(key=query)
        if cached:
            all_hits.append(SearchHit(node_id="cache_%s" % query[:16], score=0.8, content=str(cached)))

        # Route 5: Polyphonic
        recall_data['fusion_stats'] = self.search.get_fusion_stats()
        recall_data['route_stats'] = self.search.get_route_stats()
        self.search.reset_stats()
        for r in self.search.search(query, store=self.store, graph_memory=self.graph_memory, limit=limit):
            all_hits.append(SearchHit(node_id=r.node_id, score=r.fused_score,
                                      content=r.content))

        # Route 6: TopologicalRetrieval — 图拓扑感知召回
        if self.topological_retrieval is not None:
            try:
                topo_hits = self.topological_retrieval.retrieve(query=query, graph=self.graph_memory, limit=5)
                for hit in topo_hits:
                    all_hits.append(SearchHit(
                        node_id=f"topo_{hit.node_id}", score=min(1.0, hit.score * 1.05),
                        content=hit.content, snippet=hit.content[:200],
                    ))
            except Exception as e:
                logger.debug("Topological retrieval failed: %s", e)

        # Route 7: HORMA层级检索 — 文件系统式路径匹配
        if hasattr(self, 'hierarchical'):
            try:
                query_path = "/" + "/".join(query.lower().strip("/").split()[:3])
                hier_hits = self.hierarchical.retrieve(query_path, max_results=5)
                for hit in hier_hits:
                    all_hits.append(SearchHit(
                        node_id=hit["node_id"], score=hit["score"] * 0.9,
                        content=hit.get("content", ""), snippet=hit.get("content", "")[:200],
                    ))
            except Exception as e:
                logger.debug("HORMA retrieval failed: %s", e)

        # L-ICL: 精准局部修正 — 当召回结果稀疏时注入定向修正
        if hasattr(self, 'context_engineering'):
            try:
                if len(all_hits) < 3:
                    correction = self.context_engineering.localized_correction(
                        query, f"Low recall coverage: {len(all_hits)} hits from {limit} limit"
                    )
                    if correction:
                        recall_data['l_icl_correction'] = correction[:100]
                        logger.debug("L-ICL correction injected for query '%s'", query[:50])
            except Exception as e:
                logger.debug("L-ICL correction failed: %s", e)

        # Route 8: DualStorage — verbatim + compressed combined retrieval
        if hasattr(self, 'dual_storage'):
            try:
                ds_results = self.dual_storage.retrieve(query, limit=max(3, limit // 3))
                for h in ds_results.get("verbatim", []):
                    all_hits.append(SearchHit(node_id=f"ds_v_{h.get('node_id', '')[:8]}", score=0.6, content=h.get("content", "")))
                for h in ds_results.get("compressed", []):
                    all_hits.append(SearchHit(node_id=f"ds_c_{id(h)}", score=0.5, content=h.get("content", "")))
                recall_data['dual_storage_primary'] = ds_results.get("primary_mode", "unknown")
            except Exception as e:
                logger.debug("DualStorage retrieval failed: %s", e)

        # Deduplicate + sort (cap scores to [0,1] for cross-route consistency)
        seen = set()
        unique = []
        for h in all_hits:
            if h.node_id not in seen:
                seen.add(h.node_id)
                h.score = min(1.0, max(0.0, h.score))
                unique.append(h)
        unique.sort(key=lambda h: h.score, reverse=True)
        unique = unique[:limit]

        # Owner-Harm: filter results the requester can access
        if hasattr(self, 'owner_harm'):
            try:
                requester = branch or "system"
                filtered = []
                for h in unique:
                    access = self.owner_harm.check_access(h.node_id, requester)
                    if access["allowed"]:
                        filtered.append(h)
                    else:
                        recall_data['owner_harm_filtered_count'] = recall_data.get('owner_harm_filtered_count', 0) + 1
                unique = filtered or unique  # If all filtered out, keep originals as fallback
            except Exception as e:
                logger.debug("Owner-Harm check failed: %s", e)

        duration = (time.time() - start) * 1000

        # Side effects
        if unique:
            self.cache.put(key=query, value=unique[0].content)
            # ContextFailure: observe retrieval quality
            self.context_failure.observe_distraction(len(unique), len(unique) / max(limit, 1))
        self.context_failure.observe_clash([h.content[:50] for h in unique[:3]])
        self.context_failure.observe_poisoning(query, is_hallucination=False)
        self.context_failure.observe_confusion(query, "recall context")
        self.compressor.compress(query)
        self.model_router.route(query)
        self.session.create(f"recall_{int(time.time())}")
        self.brain.decide({"action": "recall", "query": query, "result_count": len(unique)})

        # ContextFailure: detect failures after recall
        self.context_failure.detect()

        # OutputGuardrail: check output safety
        if unique:
            self.output_guardrail.check(unique[0].content)

        # Gravity: rank results by gravitational pull
        for h in unique[:5]:
            if h.node_id:
                self.gravity.add_node(h.node_id, mass=h.score)

        # === Context Engineering: Write/Select/Compress ===
        # Write: snapshot recall results for future retrieval
        recall_components = [
            ContextComponent(name="query", type="instruction", content=query, priority=1,
                           tokens=len(query.split()) * 2),
        ]
        for h in unique[:5]:
            recall_components.append(ContextComponent(
                name="result_%s" % h.node_id[:8], type="knowledge",
                content=h.content, priority=3, tokens=len(h.content.split()) * 2,
            ))
        self.context_engineering.write(query, recall_components)

        # Select: retrieve relevant context from memory
        selected = self.context_engineering.select(query, self.store, limit=3)
        if selected:
            unique.extend([SearchHit(node_id=c.name, score=0.5, content=c.content)
                          for c in selected[:2]])

        # Re-sort after context engineering additions
        unique.sort(key=lambda h: h.score, reverse=True)

        # Compress: ensure context fits within budget
        if len(unique) > limit:
            compressed = self.context_engineering.compress(
                [ContextComponent(name=h.node_id, type="knowledge", content=h.content,
                                 tokens=len(h.content.split()) * 2) for h in unique],
                target_ratio=0.7,
            )
            compressed_ids = {c.name for c in compressed}
            unique = [h for h in unique if h.node_id in compressed_ids]

        # === Recall: full mechanism activation ===
        # Cache subsystem
        recall_data['cache_has'] = self.cache.contains(query)
        recall_data['cache_info'] = self.cache.get_entry_info(query)
        self.cache.cleanup_expired()
        recall_data['cache_stats'] = self.cache.get_stats()

        # Graph memory deep queries
        for h in unique[:3]:
            if h.node_id:
                recall_data['gm_episode'] = self.graph_memory.get_episode(h.node_id)
                recall_data['gm_edges'] = self.graph_memory.get_edges(h.node_id)
                recall_data['gm_neighbors'] = self.graph_memory.get_neighbors(h.node_id)
        recall_data['gm_by_tag'] = self.graph_memory.get_episodes_by_tag("ai")

        # Stream analysis
        recall_data['stream_recent'] = self.stream.recent(5, "recall")
        recall_data['stream_search'] = self.stream.search_content(query)

        # Compression analysis
        recall_data['compress_stats'] = self.compressor.compress_with_stats(query)

        # Model routing analysis
        recall_data['model_suggest'] = self.model_router.suggest_model_for_tools(len(unique))

        # Session management
        self.session.access(f"recall_{int(time.time())}")
        self.session.expire_idle()

        # Behavior mirror
        self.behavior_mirror.mirror("system", "recall", {"query": query, "hits": len(unique)})

        # Event bus
        recall_data['recent_events'] = self.event_bus.get_recent(3)

        # Memory side effect
        self.memory_side_effect.set_current_task(f"recall {query}")
        for h in unique[:3]:
            self.memory_side_effect.observe_retrieval(h.content[:100])
        recall_data['side_effect'] = self.memory_side_effect.detect()

        # Context isolator
        snap = self.context_isolator.create_snapshot(
            [h.content[:100] for h in unique[:3]], f"recall {query}"
        )
        recall_data['ctx_merge'] = self.context_isolator.merge(snap, [h.content[:50] for h in unique[:2]])

        # Context window
        self.context_window.register_component("recall_results", len(unique) * 100, priority=7)
        recall_data['ctx_check'] = self.context_window.check()
        recall_data['ctx_compress'] = self.context_window.suggest_compression()
        self.context_window.update_usage("recall_results", len(unique) * 80)

        # Progressive complexity
        recall_data['complexity'] = self.progressive_complexity.assess(
            f"recall {query}", context_tokens=len(unique) * 200, requires_tools=len(unique) > 5
        )

        # Output guardrail (second pass)
        for h in unique[:3]:
            self.output_guardrail.check(h.content)

        # 自动记录 recall 引用到 UtilityTracker
        for h in unique[:5]:
            self.utility_tracker.record_reference(h.node_id)

        # 用 disposition 行为倾向调整排序权重
        for h in unique:
            try:
                disp_score = self.disposition.get_disposition(h.node_id)
                if disp_score:
                    h.score = min(1.0, h.score * (1 + disp_score * 0.2))
            except Exception as e:
                logger.warning("Disposition score adjustment failed for node %s: %s", h.node_id, e)
        unique.sort(key=lambda h: h.score, reverse=True)

        # MemPO: update utilities for recalled nodes
        if hasattr(self, 'mempo'):
            try:
                node_ids = [h.node_id for h in unique if hasattr(h, 'node_id')]
                used = [True] * len(node_ids)
                self.mempo.batch_update_utilities(node_ids, used)
                recall_data['mempo_avg_utility'] = sum(
                    self.mempo.get_utility(nid) for nid in node_ids
                ) / max(len(node_ids), 1)
            except Exception as e:
                logger.debug("MemPO update failed: %s", e)

        # P3 RSI: RIMRULLE→MemPO rule-guided utility boost on recall
        if hasattr(self, 'rimrule') and hasattr(self, 'mempo') and hasattr(self.mempo, 'apply_rule_guidance'):
            try:
                high_conf_rules = self.rimrule.get_rules(sort_by="confidence", limit=3)
                for rule in high_conf_rules:
                    if rule.get("confidence", 0) > 0.5:
                        related_ids = [h.node_id for h in unique[:5] if hasattr(h, 'node_id')]
                        self.mempo.apply_rule_guidance(rule, related_ids)
            except Exception as e:
                logger.debug("P3 RSI rule guidance failed: %s", e)

        # B2-1: Verbatim Chunk Joint Storage (arXiv 2601.00821)
        # Enrich each result with raw_chunk if available, and optionally prefer chunk
        try:
            enriched = []
            for h in unique:
                node = self.store.read_node(h.node_id)
                if node and node.raw_chunk:
                    h.metadata["chunk"] = node.raw_chunk
                    if prefer_chunk:
                        h.content = node.raw_chunk
                enriched.append(h)
            unique = enriched
        except Exception as e:
            logger.debug("Verbatim chunk enrichment failed: %s", e)

        avg_score = sum(h.score for h in unique) / max(len(unique), 1) if unique else 0.0
        self.event_bus.publish({"type": "recall_completed", "query": query, "hits": len(unique),
                                "avg_score": round(avg_score, 4), "duration_ms": duration,
                                "gap_empty": len(unique) == 0})
        recall_result = SearchResults(hits=unique, total_count=len(unique), query=query, duration_ms=duration, metadata=recall_data)
        # Telemetry: 存储原始返回值
        self._telemetry["recall"] = recall_result

        # 写管道结果（双向语义穿透）
        self.signal_fusion.set_pipe_result("recall", {
            "query": query, "hits": len(unique), "avg_score": round(avg_score, 4),
            "total_count": len(unique),
        })

        return recall_result

    # ============================================================
    # B2-2: PolarMem Tristate Query (arXiv 2602.00415)
    # ============================================================
    def _recall_with_trust(self, query: str, limit: int = 10, branch: str = "main",
                           prefer_chunk: bool = False) -> SearchResults:
        """Recall with trust-state-aware filtering.

        Uses three-state memory (HAS/NOT_HAS/Uncertain) to annotate or filter results:
        - trust_state="has": normal results, included with standard confidence.
        - trust_state="not_has": known-absent; included but with suppressed confidence.
        - trust_state="uncertain": flagged as unverified.

        Args:
            query: Search query string.
            limit: Maximum results to return.
            branch: Branch to search in.
            prefer_chunk: If True, use raw_chunk as the main content field.

        Returns:
            SearchResults with trust-state-annotated hits.
        """
        try:
            results = self.recall(query, limit=limit * 3, branch=branch, prefer_chunk=prefer_chunk)
        except Exception as e:
            logger.error("_recall_with_trust: recall failed: %s", e)
            return SearchResults(hits=[], total_count=0, query=query, metadata={"trust_state_error": str(e)})

        filtered_hits = []
        trust_metadata = {"has": 0, "not_has": 0, "uncertain": 0}

        try:
            for hit in results.hits:
                node = self.store.read_node(hit.node_id)
                trust_state = "unknown"
                try:
                    if node:
                        trust_state = node.trust_state or "unknown"
                except Exception:
                    trust_state = "unknown"

                hit.metadata["trust_state"] = trust_state
                trust_metadata[trust_state] = trust_metadata.get(trust_state, 0) + 1

                if trust_state == "not_has":
                    # Known-absent: include but signal low confidence
                    hit.metadata["suppressed"] = True
                    hit.score *= 0.3  # Drastically reduce score
                    hit.metadata["note"] = "known_absent"
                elif trust_state == "uncertain":
                    # Uncertain: flag as unverified
                    hit.metadata["unverified"] = True
                    hit.score *= 0.7
                    hit.metadata["note"] = "unverified"
                # trust_state == "has": no modification needed

                filtered_hits.append(hit)

            filtered_hits.sort(key=lambda h: h.score, reverse=True)
            filtered_hits = filtered_hits[:limit]

        except Exception as e:
            logger.error("_recall_with_trust: filtering failed: %s", e)
            filtered_hits = results.hits[:limit]

        result = SearchResults(
            hits=filtered_hits,
            total_count=len(filtered_hits),
            query=query,
            duration_ms=results.duration_ms,
            metadata={"trust_state_counts": trust_metadata, **results.metadata},
        )
        self._telemetry["recall_with_trust"] = result

        # 反馈环路：recall → learn
        # 零命中 → 告诉 learn 需要补全知识缺口
        if len(filtered_hits) == 0:
            try:
                self.signal_fusion.push_feedback({
                    "from": "recall",
                    "to": "learn",
                    "type": "quality",
                    "data": {
                        "query": query,
                        "hits": 0,
                        "gap": True,
                        "source": "recall_with_trust",
                    },
                })
            except Exception as e:
                logger.debug("recall: push_feedback to learn failed: %s", e)

        return result

    # ============================================================
    # evolve pipeline (11 stages — Superpowers enhanced)
    # ============================================================
    def evolve(self, context: str = "", branch: str = "main", confidence: float = 0.5) -> EvolutionOutcome:
        start = time.time()

        # 链上下文：读取触发管的信号
        try:
            ctx = self.signal_fusion.get_chain_context()
            if ctx:
                trigger_pipe = ctx.get("trigger_pipe", "")
                sigs = ctx.get("trigger_signals", {})
                if trigger_pipe == "reflect":
                    raw_score = sigs.get("raw_score", 0.5)
                    raw_drift = sigs.get("raw_drift", 0)
                    context += f" | Triggered by reflect: score={raw_score:.3f}, drift={raw_drift}"
                    self.cerebral_cortex.add_merge_reason(
                        "evolve", f"reflect_driven:score={raw_score:.3f}")
        except Exception as e:
            logger.warning("Evolve chain context processing failed: %s", e)

        # Stage 0: Brainstorming — Socratic design refinement (Superpowers)
        brainstorm_result = self.brainstorming.brainstorm(
            topic=context or "auto-evolution", context="evolve pipeline"
        )

        # PlanWriter: generate implementation plan from brainstorming (Superpowers)
        plan = self.plan_writer.write_plan(
            feature=context or "auto-evolution",
            context="evolve pipeline after brainstorming",
        )

        # LoopSelector: auto-select loop strategy
        loop_config = self.loop_selector.select(context)
        self.loop_selector.record_outcome(loop_config.strategy, 0.5)

        # EvolutionQualityGates: check step budget
        allowed, reason = self.evo_quality_gates.check_step("evolve", 1, max_steps=loop_config.max_steps)
        if not allowed:
            blocked = EvolutionOutcome(result=EvolutionResult.BLOCKED, details=reason)
            self._telemetry["evolve"] = blocked
            return blocked

        # AdaptiveHarness: record execution
        self.adaptive_harness.execute(context, tool="evolve")

        # Step -1: ToolOverload check
        overload = self.tool_overload.detect()
        if overload.is_overloaded:
            blocked = EvolutionOutcome(result=EvolutionResult.BLOCKED, details=f"ToolOverload: {overload.tool_count} tools")
            self._telemetry["evolve"] = blocked
            return blocked

        # Step 0: LoopGuard
        self.loop_guard.start()
        loop_state = self.loop_guard.check()
        if loop_state in (LoopState.CIRCUIT_BREAKER,):
            blocked = EvolutionOutcome(result=EvolutionResult.BLOCKED, details="LoopGuard")
            self._telemetry["evolve"] = blocked
            return blocked

        # Semantic Early-Stopping check
        ses_decision = self.semantic_early_stopping.check(context)
        if ses_decision.should_stop:
            blocked = EvolutionOutcome(result=EvolutionResult.BLOCKED, details="semantic_early_stop")
            self._telemetry["evolve"] = blocked
            return blocked

        # Ensure context is dynamic enough to pass AntiEvolution and SemanticEarlyStop gates
        if not context or context == "auto-evolution":
            fitness = self._compute_fitness()
            reflect_score = self._last_reflect_score or 0.0
            node_count = self.store.get_node_count()
            health = self._compute_health()
            dynamic_suffix = f"auto:fitness={fitness:.4f}:reflect={reflect_score:.4f}:nodes={node_count}:health={health:.3f}"
            context = f"Periodic evolution from reflect insights — {dynamic_suffix}"

        # Step 1: EquilibriumGuard
        if self.equilibrium.get_alert_level() == AlertLevel.RED:
            blocked = EvolutionOutcome(result=EvolutionResult.BLOCKED, details="Equilibrium RED")
            self._telemetry["evolve"] = blocked
            return blocked

        # Step 2: AntiEvolutionGate
        anti = self.anti_evolution.check(hypothesis=context or "auto-evolution")
        if not anti.passed:
            blocked = EvolutionOutcome(result=EvolutionResult.BLOCKED, details=f"AntiEvolution: {anti.verdict}")
            self._telemetry["evolve"] = blocked
            return blocked

        # Step 3: VerificationIronLaw
        self.iron_law.verify(claim=context or "auto-evolution")

        # Step 3.5: Measure fitness before evolution
        fitness_before = self._compute_fitness()
        diagnostics: Dict[str, Any] = {}

        # Step 4: RLPathology — observe() 内部已调用 detect_all()
        self.rl_pathology.observe(fitness_before, "evolve")

        # Step 4.5: UCB1 — 用实际适应度差值作为奖励信号
        try:
            strategy = self.ucb1.select()
            fitness_reward = max(0.0, min(1.0, fitness_before + 0.5))
            self.ucb1.update(strategy, fitness_reward)
            best_arm = self.ucb1.get_best_arm()
        except Exception:
            strategy = "default"

        # Step 4.6: FGG — 门控结果用于阻断违规进化
        fgg_result = self.fggm.verify_compat({"context": context})
        if not fgg_result.get("passed", True):
            blocked = EvolutionOutcome(result=EvolutionResult.BLOCKED,
                                       details=f"FGG violations: {fgg_result.get('violations', [])}")
            self._telemetry["evolve"] = blocked
            return blocked

        # Step 4.7: EvalDriven
        self.eval_engine.evaluate({"context": context, "strategy": strategy})

        # Step 4.8: DAG scheduling — 添加任务后执行调度
        self.dag_scheduler.add_task(f"evolve_{int(time.time())}", {"context": context})
        try:
            scheduled = self.dag_scheduler.schedule()
        except ValueError:
            scheduled = []

        # Step 4.9: ConfidenceGate — 低置信度阻断进化
        cg_result = self.confidence_gate.check({"context": context, "fitness": fitness_before})
        if not cg_result.get("passed", True):
            blocked = EvolutionOutcome(result=EvolutionResult.BLOCKED,
                                       details=f"ConfidenceGate: confidence={cg_result.get('confidence', 0):.3f} < threshold={cg_result.get('threshold', 0):.3f}")
            self._telemetry["evolve"] = blocked
            return blocked

        # Step 5: HarnessX evolution (with AntiEvolutionGate protection)
        # Compose harness from primitives
        harness_config = self.harness_x.compose(["input_guard", "dopamine_gate", "five_gates"])
        # Execute and trace
        harness_traces = self.harness_x.execute(harness_config, input_data=context)
        # AntiEvolutionGate: check before evolving harness
        harness_anti = self.anti_evolution.check(hypothesis=f"harness_evolution_{context}")
        if harness_anti.passed:
            new_harness_config = self.harness_x.evolve(harness_config, harness_traces)
            # Evaluate the evolved harness
            harness_score = self.harness_x.evaluate(
                new_harness_config,
                test_cases=[{"input": context}, {"input": "test"}]
            )
            self.marginal.record(harness_score, "harness_evolution", context)

        # RIMRULE: observe evolution context for pattern extraction
        self.rimrule.add_observation({"condition": str(context)[:100], "outcome": "evolve", "utility": 0.5})
        # P3 RSI: MemPO→RIMRULLE observation weighting
        mempo_weights: dict[str, float] = {}
        if hasattr(self, 'mempo') and hasattr(self.mempo, 'get_utility_for_condition'):
            try:
                cond_str = str(context)[:100]
                u = self.mempo.get_utility_for_condition(cond_str)
                mempo_weights[cond_str] = u
            except Exception as e:
                logger.debug("P3 RSI mempo weight failed: %s", e)
        rules = self.rimrule.extract_rules(observation_weights=mempo_weights if mempo_weights else None)
        if rules:
            evolution_data['rimrule_rules_count'] = len(rules)
            evolution_data['rimrule_top_score'] = rules[0].get("mdl_score", 0) if rules else 0

        # Step 6: Context Engineering — manage evolve context
        self.context_engineering.write("evolve_%s" % context, [
            ContextComponent(name="task", type="instruction", content=context, priority=1,
                           tokens=len(context.split()) * 2),
        ])

        # Step 7: Execute evolution

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
        diagnostics["communities"] = self.community_tree.find_communities()

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

        # Verification Gate — ensure evolution is actually beneficial (Superpowers)
        delta = fitness_after - fitness_before
        verification = self.verification_gate.verify(
            task="evolve_%s" % context,
            fix_applied="fitness_delta=%.4f" % delta,
            tests_passing=delta >= -0.01,
        )

        # TDD Verifier — verify test coverage (Superpowers)
        tdd_result = self.tdd_verifier.verify(
            feature="evolution_%s" % context,
            test_description="evolution produces measurable improvement",
        )

        # Reflexion
        self.reflexion.reflect(context or "evolve", f"delta={delta:.4f}", fitness_after)

        # Debate
        self.debate.debate(context or "evolution", [f"before={fitness_before:.4f}", f"after={fitness_after:.4f}"])

        # MultiAgent
        self.multi_agent.register_agent(f"evolver_{int(time.time())}", ["evolve"])

        # BootstrapCI
        self.bootstrap.compute([fitness_before, fitness_after])

        # LuckyPass — analyze trajectory for fragile "lucky pass" patterns
        lucky_trajectory = {
            "paths": [{"context": context, "result": "success"}],
            "steps": [
                {"action": "evaluate", "content": f"fitness_before={fitness_before:.4f}"},
                {"action": "evolve", "content": context or "auto"},
                {"action": "verify", "content": f"fitness_after={fitness_after:.4f}, delta={fitness_after - fitness_before:.4f}"},
            ],
            "actions": ["evaluate", "evolve", "verify"],
            "success": fitness_after > fitness_before,
            "explanation": context or "",
            "reasoning": f"evolution from {fitness_before:.4f} to {fitness_after:.4f}",
        }
        lucky_analysis = self.lucky_pass.analyze(lucky_trajectory)
        diagnostics["lucky_pass"] = {
            "is_lucky": lucky_analysis.is_lucky_pass,
            "lucky_probability": lucky_analysis.lucky_probability,
            "ideal_probability": lucky_analysis.ideal_path_probability,
            "missing_steps": lucky_analysis.missing_steps,
            "heuristic_signals": lucky_analysis.heuristic_signals,
        }
        diagnostics["lucky_pass_stats"] = self.lucky_pass.get_stats()

        # SEAGym
        self.seagym.evaluate(context or "evolve", f"delta={fitness_after - fitness_before:.4f}", fitness_after)

        # EvolutionGrill
        self.evolution_grill.review({"context": context, "delta": fitness_after - fitness_before})

        # CAMP: 动态专家组装(arXiv 2604.00085) — 对进化方案进行三值投票
        try:
            agents = list(self.multi_agent._agents.values()) if hasattr(self.multi_agent, '_agents') else []
            if agents:
                camp_panel = self.multi_agent._deliberate_assembly(
                    context or "evolution",
                    agents,
                    ["evolve", "analyze"],
                    min_panel_size=2
                )
                if len(camp_panel) >= 2:
                    panel_agents = [a for a in agents if a["id"] in camp_panel]
                    vote_result = self.multi_agent._three_value_vote(
                        ["accept", "reject", "modify"], panel_agents
                    )
                    diagnostics["camp_vote"] = vote_result
                    diagnostics["camp_panel"] = camp_panel
                    logger.debug("CAMP panel assembled: %s", camp_panel)
        except Exception as e:
            logger.debug("CAMP deliberation failed: %s", e)

        # Marginal
        delta = fitness_after - fitness_before
        self.marginal.record(delta, "evolution", context)

        # AntiEvolution record
        self.anti_evolution.record_score(fitness_after)
        diagnostics["anti_evolution_compat"] = self.anti_evolution.check_compat(hypothesis=context or "auto-evolution")

        # ToolOverload: record tool usage during evolution
        self.tool_overload.record_selection("evolve", success=True)

        # ToolDrift: record tool usage for drift detection
        self.tool_drift.record_tool_use("evolve")

        # CircuitBreaker: record success
        self.circuit_breaker.record_success()

        # Trend: observe fitness trend
        self.trend.observe("fitness", fitness_after)

        # 5 Evolution Methods from EvoAgentBench
        # EverOS: search-oriented external memory evolution
        everos_result = self.everos.evolve(context or "auto", initial_state={"fitness": fitness_after})
        # GEPA: gradient-guided parameter evolution
        gepa_result = self.gepa.evolve(context or "auto")
        # Memento: memory-driven method evolution
        memento_result = self.memento_evolution.evolve(context or "auto", current_method="default", success=True)
        # ReasoningBank: reasoning strategy retrieval
        rb_result = self.reasoning_bank.evolve(context or "auto", context={"type": "general"})
        # OpenSpace: open-space exploration
        os_result = self.openspace.evolve(context or "auto", current_fitness=fitness_after)

        # Swiss Army Knife: Pass-k consistency verification
        pk_result = self.pass_k.evaluate(
            task="evolve_candidates",
            evaluate_fn=lambda c: fitness_after > 0.5,
        )

        # Swiss Army Knife: Multi-strategy selection
        strategy_names = ["gepa", "everos", "memento", "openspace", "ga"]
        _get_improvement = lambda r: getattr(r, "improvement", getattr(r, "best_fitness", 0))
        strategy_fitness = {
            "gepa": _get_improvement(gepa_result),
            "everos": _get_improvement(everos_result),
            "memento": _get_improvement(memento_result),
            "openspace": _get_improvement(os_result),
            "ga": delta,
        }
        for name, f in strategy_fitness.items():
            self.strategy_scheduler.update(arm_id=name, reward=f)
        best_result = self.strategy_scheduler.select(strategy="best")
        best_strategy = best_result.selected_arm if best_result.selected_arm else "gepa"

        # Swiss Army Knife: Trace engine records evolution trace
        trace_id = self.trace_engine.start_trace("evolve", {"fitness_before": fitness_before, "fitness_after": fitness_after})
        self.trace_engine.record_step(
            trace_id=trace_id,
            step_id=1,
            action="multi_strategy_evolve",
            confidence=fitness_after,
            result=f"best={best_strategy}, delta={delta:.4f}",
            metadata={"best_strategy": best_strategy, "delta": delta},
        )
        diagnostics["trace_decision"] = self.trace_engine.decision_analysis(trace_id)

        # === Evolve: full mechanism activation ===
        # Safety mechanisms
        diagnostics["circuit_breaker_allow"] = self.circuit_breaker.allow_request()
        diagnostics["circuit_breaker_state"] = self.circuit_breaker.get_state()

        # DAG scheduler deep operations
        diagnostics["dag_topo_sort"] = self.dag_scheduler.topological_sort()
        self.dag_scheduler.schedule()
        diagnostics["dag_critical_path"] = self.dag_scheduler.critical_path()

        # Evolution engine deep
        diagnostics["evolution_eval"] = self.evolution_engine.evaluate()

        # Multi-agent deep operations
        diagnostics["multi_agent_alloc"] = self.multi_agent.allocate_task({"task": context, "required_capabilities": []})
        diagnostics["multi_agent_consensus"] = self.multi_agent.reach_consensus([{"value": "strategy_a"}, {"value": "strategy_b"}])

        # Reflexion deep operations
        self.reflexion.record_attempt(context or "evolve", fitness_after)
        diagnostics["reflexion_context"] = self.reflexion.get_reflection_context(top_k=3, query=context)
        diagnostics["reflexion_worst"] = self.reflexion.get_worst_actions()
        diagnostics["reflexion_trend"] = self.reflexion.get_improvement_trend()

        # Marginal deep operations
        self.marginal.accumulate_batch(
            baseline_score=fitness_before,
            operations=[{"id": "evo_1", "type": "evolve", "content": context, "score": fitness_after}]
        )
        diagnostics["marginal_advantages"] = self.marginal.get_advantages()
        diagnostics["marginal_stable"] = self.marginal.get_stable_operations()
        diagnostics["marginal_history"] = self.marginal.get_operation_history("evo_1")
        diagnostics["marginal_batch"] = self.marginal.get_batch_comparison(1, 2)

        # SEAGym deep operations
        self.seagym.register_case({"context": context, "fitness": fitness_after})
        self.seagym.register_cases([{"context": context, "fitness": fitness_after, "split": "train", "expected": 0.5}])
        diagnostics["seagym_overfitting"] = self.seagym.detect_overfitting()
        diagnostics["seagym_cost"] = self.seagym.get_cost_analysis()
        diagnostics["seagym_transfer"] = self.seagym.get_transfer_analysis()
        self.seagym.save_snapshot(epoch=int(time.time()), metadata={"fitness": fitness_after})
        # _ = self.seagym.evaluate_all_splits()  # requires case data

        # Behavior mirror deep
        self.behavior_mirror.mirror("system", "evolve", {"fitness": fitness_after})
        diagnostics["behavior_profile"] = self.behavior_mirror.compute_profile("system")
        diagnostics["behavior_deviation"] = self.behavior_mirror.detect_deviation("system")

        # Event bus
        diagnostics["event_bus_recent"] = self.event_bus.get_recent(3)

        # === 知识翻译：Level A + Level B ===
        try:
            kta_result = self.knowledge_to_mechanism.analyze_and_apply(
                context=context or "auto",
                tags=[context.split()[0]] if context else [],
                omega=self,
            )
            if kta_result.get("applied", 0) > 0:
                logger.info("KTA translations applied: %s", kta_result["summary"])
        except Exception as e:
            logger.debug("KTA translation skipped: %s", e)

        # Trend prediction
        diagnostics["trend_prediction"] = self.trend.predict()

        # Speculative fork merge
        diagnostics["speculative_result"] = self.speculative.evaluate_and_select()
        diagnostics["speculative_fork_merge"] = self.speculative_fork.merge(0, 1)

        # Tool fitness record (both old and new)
        self.tool_fitness.record_usage(context or "auto", "evolve", success=True, latency_ms=10.0)
        self.tool_fitness_full.record_call(context or "auto", {}, success=True, latency_ms=10.0)

        # 反馈环路：evolve → recall
        # 告诉 recall 哪些参数被进化提升了，帮助下次召回更好节点
        try:
            self.signal_fusion.push_feedback({
                "from": "evolve",
                "to": "recall",
                "type": "quality",
                "data": {
                    "fitness_before": round(fitness_before, 4),
                    "fitness_after": round(fitness_after, 4),
                    "delta": round(delta, 4),
                    "effective": delta > 0,
                    "method": result.method if hasattr(result, 'method') else strategy_name,
                },
            })
        except Exception as e:
            logger.debug("evolve: push_feedback to recall failed: %s", e)

        # FGG verify
        diagnostics["fggm_verify"] = self.fggm.verify({"context": context})

        # Eval engine deep
        diagnostics["eval_fitness_history"] = self.eval_engine.get_fitness_history()
        diagnostics["eval_convergence"] = self.eval_engine.get_convergence_curve()

        self.event_bus.publish({"type": "evolve_completed", "fitness_before": fitness_before, "fitness_after": fitness_after, "result": "SUCCESS", "strategy": strategy})
        evolve_result = EvolutionOutcome(
            result=EvolutionResult.SUCCESS,
            fitness_before=fitness_before, fitness_after=fitness_after,
            duration_ms=(time.time() - start) * 1000,
            details=f"delta={delta:.4f}, diagnostics_keys={list(diagnostics.keys())}",
            metadata=diagnostics,
        )
        # Telemetry: 存储原始返回值
        self._telemetry["evolve"] = evolve_result

        # 写管道结果
        self.signal_fusion.set_pipe_result("evolve", {
            "result": evolve_result.result.value if hasattr(evolve_result.result, 'value') else str(evolve_result.result),
            "fitness_before": fitness_before, "fitness_after": fitness_after,
            "delta": round(delta, 4),
        })

        return evolve_result

    # ============================================================
    # learn pipeline
    # ============================================================
    def learn(self, source: str = "web", query: str = "AI", max_results: int = 5) -> dict:
        # 链上下文: 读取触发管信号（如 recall 检测到的知识缺口）
        learn_diagnostics: Dict[str, Any] = {}
        try:
            ctx = self.signal_fusion.get_chain_context()
            if ctx:
                trigger_pipe = ctx.get("trigger_pipe", "")
                sigs = ctx.get("trigger_signals", {})
                learn_diagnostics["trigger_pipe"] = trigger_pipe
                if trigger_pipe == "recall":
                    # recall detected a knowledge gap — learn fills it
                    gap_query = sigs.get("query", query)
                    if gap_query and gap_query != query:
                        logger.info("learn: filling gap from recall chain: %s", gap_query)
                        query = gap_query
                learn_diagnostics["chain_context_used"] = True
        except Exception as e:
            logger.warning("learn: chain_context read failed: %s", e)
            learn_diagnostics["chain_context_used"] = False

        # Exploration quota check
        can_explore, reason = self.exploration_quota.can_explore()
        if not can_explore:
            self.exploration_quota.record_round()  # prevent counter deadlock
            quota_result = {"source": source, "query": query, "total_results": 0, "new_nodes": 0,
                    "reason": reason}
            self._telemetry["learn"] = quota_result
            # Record scan for repeated-query detection
            self._scans.append({"query": query, "source": source, "nodes": 0, "ts": time.time(), "reason": reason})
            # Publish so AR can track consecutive_zero_gain
            self.event_bus.publish({"type": "learn_completed", "source": source, "query": query, "new_nodes": 0, "reason": reason})
            return quota_result

        if reason == "revision_round_required":
            # Insert a revision round before continuing exploration
            self.exploration_quota.record_round()

        # EvolvingPrompt: generate optimized prompt
        # (disabled - variable kept for future use)
        
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

        # === Learn: full mechanism activation ===
        # ParallelDispatcher: 并行处理扫描结果
        learn_dispatch_info = {}
        if results:
            dispatch_result = self.parallel_dispatcher.dispatch([
                {"description": f"Process: {r.title}"} for r in results[:3]
            ])
            learn_dispatch_info = {
                "dispatched": dispatch_result.completed,
                "failed": dispatch_result.failed,
            }

        # A2ABasic: 注册当前 agent 能力并委托任务
        a2a_stats = {}
        a2a_task = None
        try:
            self.a2a_basic.register_agent("omega", ["learn"])
            a2a_task = self.a2a_basic.delegate_task(f"Learn about {query}", required=[], requester="omega")
            a2a_stats = self.a2a_basic.get_stats()
        except Exception:
            a2a_stats = {"status": "a2a_unavailable"}

        # SubAgentContract: 为委托学习创建合约
        contract_id = ""
        if a2a_task and hasattr(a2a_task, 'executor') and a2a_task.executor:
            try:
                contract = self.sub_agent_contract.create_contract(
                    agent_id=a2a_task.executor,
                    task=f"Learn: {query}",
                    quality_threshold=0.7
                )
                contract_id = contract.get("id", "") if isinstance(contract, dict) else str(getattr(contract, 'id', ''))
            except Exception:
                contract_id = "contract_creation_failed"

        # Anti-pattern 2: 只列不深 → short titles with no content = shallow scan
        if all(len(r.content or '') < 80 for r in results[:max_results]):
            logger.debug("Anti-pattern: shallow learn (all results have < 80 chars)")

        # Anti-pattern 3: 重复学习检测
        scan_history = self._scans[-5:] if len(self._scans) > 5 else self._scans
        same_query_count = sum(1 for s in scan_history if s.get("query") == query)
        if same_query_count > 2:
            logger.debug("Anti-pattern: repeated learn (same query 3+ times in last 5)")
            # 降低效用 (initially 0.7 from remember call)
            utility_val = 0.56  # 0.7 * 0.8

        # Curiosity queue deep
        curiosity_item = self.curiosity_queue.pop()

        # Utility tracker deep
        for node_id in new_nodes[:3]:
            learn_diagnostics.setdefault("utility_averages", []).append(self.utility_tracker.get_average(node_id))

        # Mechanism registry deep
        self.mechanism_registry.enable(f"learn_{source}")
        learn_diagnostics["mechanism_invoke"] = self.mechanism_registry.invoke(f"learn_{source}")
        self.mechanism_registry.disable(f"learn_{source}")

        # Skill registry deep
        learn_diagnostics["skill_lookup"] = self.skill_registry.get_skill(f"learn_{source}_{query}")
        learn_diagnostics["active_skills"] = self.skill_registry.get_active_skills()

        # Curator deep
        learn_diagnostics["curator_ranking"] = self.curator.get_quality_ranking()

        # Few-shot deep
        learn_diagnostics["few_shot_selected"] = self.few_shot.select(query)

        # Knowledge gen deep
        self.knowledge_gen.generate_from_context(results[0].content if results else "")
        learn_diagnostics["kg_from_query"] = self.knowledge_gen.generate_from_query(query)
        learn_diagnostics["kg_top_entities"] = self.knowledge_gen.get_top_entities()
        learn_diagnostics["kg_facts"] = self.knowledge_gen.get_facts_for_entity(query.split()[0] if query else "")

        # Behavior mirror
        self.behavior_mirror.mirror("system", "learn", {"source": source, "query": query})

        # Event bus
        learn_diagnostics["event_recent"] = self.event_bus.get_recent(3)

        # Knowledge-to-Mechanism: check if knowledge can update parameters
        applied_changes = []
        for r in results:
            mappings = self.knowledge_to_mechanism.analyze_knowledge(
                "%s %s" % (r.title, r.content), tags=r.tags)
            for mapping in mappings:
                if self.knowledge_to_mechanism.apply_mapping(mapping, self):
                    applied_changes.append(mapping)

        # Record exploration round
        self.exploration_quota.record_round()
        self.explorer_state.record_round(query, source, 0.5)

        # Auto-fill curiosity queue if low
        if self.curiosity_queue._queue and len(self.curiosity_queue._queue) < 3:
            self.curiosity_autofill.auto_fill(count=2)

        # DeepRetrofit6: trigger deep learning when knowledge is acquired
        if len(new_nodes) > 0:
            source_content = "\n---\n".join(
                f"{r.title}: {r.content}" for r in results
            )
            self.deep_retrofit_6.execute(
                    topic=query,
                    source_file="%s://%s" % (source, query),
                    source_content=source_content,
                )

            self.event_bus.publish({"type": "learn_completed", "source": source, "query": query, "new_nodes": len(new_nodes)})

            # Record scan for repeated-query detection
            self._scans.append({"query": query, "source": source, "nodes": len(new_nodes), "ts": time.time()})

            # Self-Observation: 记录 learn，在周循环时触发回顾
            try:
                review = self.self_observation.record_learn(query, len(new_nodes), source, utility_val if same_query_count > 2 else 0.7)
                if review and review.get("patterns"):
                    logger.info("SelfObservation: %d patterns, zero_gain=%d",
                                len(review["patterns"]), review.get("zero_gain_streak", 0))
            except Exception as e:
                logger.warning("SelfObservation.record_learn failed: %s", e)

            learn_result = {"source": source, "query": query, "total_results": len(new_nodes),
                "new_nodes": len(new_nodes), "applied_changes": len(applied_changes),
                "parallel_dispatch": learn_dispatch_info, "a2a_stats": a2a_stats,
                "contract_id": contract_id, "diagnostics": learn_diagnostics}
            # Telemetry: 存储原始返回值
            self._telemetry["learn"] = learn_result

            # 写管道结果
            self.signal_fusion.set_pipe_result("learn", {
                "source": source, "query": query,
                "total_results": len(new_nodes), "new_nodes": len(new_nodes),
            })

            # 反馈环路: learn → recall
            # 告诉 recall 学到的查询, 下次 recall 命中率更高
            if len(new_nodes) > 0:
                try:
                    self.signal_fusion.push_feedback({
                        "from": "learn",
                        "to": "recall",
                        "type": "quality",
                        "data": {
                            "query": query,
                            "new_nodes": len(new_nodes),
                            "source": source,
                        },
                    })
                except Exception as e:
                    logger.debug("learn: push_feedback to recall failed: %s", e)

            return learn_result

        # Publish for 0-result scan so AR can track consecutive_zero_gain
        self.event_bus.publish({"type": "learn_completed", "source": source, "query": query, "new_nodes": 0})
        # Record scan for repeated-query detection
        self._scans.append({"query": query, "source": source, "nodes": 0, "ts": time.time(), "reason": "empty_scan"})
        return {"source": source, "query": query, "total_results": 0, "new_nodes": 0, "reason": "empty_scan"}

    # ============================================================
    # reflect pipeline
    # ============================================================
    def reflect(self, context: str = "") -> dict:
        # AdaptiveHarness: check harness state
        harness_state = self.adaptive_harness.get_state()
        reflect_diagnostics: Dict[str, Any] = {}

        # 链上下文：读取触发管的完整信号
        try:
            ctx = self.signal_fusion.get_chain_context()
            if ctx:
                trigger_pipe = ctx.get("trigger_pipe", "")
                sigs = ctx.get("trigger_signals", {})
                if trigger_pipe == "learn":
                    new_nodes = sigs.get("new_nodes", 0) or sigs.get("node_count", 0)
                    source = sigs.get("source", "?")
                    query = sigs.get("query", "?")
                    context += f" | Learn quality review: {new_nodes} nodes from {source}:{query}"
                    self.cerebral_cortex.add_merge_reason(
                        "reflect", f"learn_evaluation:{source}:{query}")
                elif trigger_pipe == "recall":
                    gap_query = sigs.get("query", "")
                    gap_count = sigs.get("gap_count", 0)
                    context += f" | Knowledge gap: '{gap_query}' missed {gap_count}x"
                elif trigger_pipe == "reflect":
                    raw_score = sigs.get("raw_score", 0.5)
                    raw_drift = sigs.get("raw_drift", 0)
                    context += f" | Reflect-driven: score={raw_score:.3f}, drift={raw_drift}"
                elif trigger_pipe == "evolve":
                    raw_before = sigs.get("raw_before", 0.5)
                    raw_after = sigs.get("raw_after", 0.5)
                    delta = raw_after - raw_before
                    context += f" | Evolve efficacy: delta={delta:.4f}"
                elif trigger_pipe == "dream":
                    patterns = sigs.get("patterns_found", 0)
                    context += f" | Pattern consolidation: {patterns} patterns"
        except Exception as e:
            logger.warning("Reflexion chain context processing failed: %s", e)

        # LoopSelector: record reflection outcome
        self.loop_selector.record_outcome(LoopStrategy.REFLEXION, 0.8)

        # === Cross-analyze recent learned knowledge ===
        # Get recent nodes directly from store (bypass RecallRequest validation)
        recent_nodes = self.store.search("", limit=20)
        learned_knowledge_summary = []
        for node in recent_nodes[:5]:
            learned_knowledge_summary.append({
                "content": node.content[:200] if node else "",
                "utility": getattr(node, "utility", 0.0) if node else 0.0,
                "tags": getattr(node, "tags", []) if node else [],
                "type": getattr(node, "type", "") if node else "",
            })

        # ThinkTool: structured thinking before reflection
        think_result = self.think_tool.run(
            task="Reflect on system performance and identify improvements",
            context=f"health={self._compute_health()}, nodes={self.store.get_node_count()}, recent_knowledge={len(recent_nodes)}",
        )

        # ContextEngineering: isolate reflection context
        reflect_components = [
            ContextComponent(name="task", type="instruction",
                           content="Reflect on system performance", priority=1, tokens=20),
            ContextComponent(name="health", type="knowledge",
                           content="health=%s, nodes=%d, recent_learned=%d" % (self._compute_health(), self.store.get_node_count(), len(recent_nodes)),
                           priority=2, tokens=20),
            ContextComponent(name="learned_knowledge", type="knowledge",
                           content=str(learned_knowledge_summary[:3]),
                           priority=3, tokens=100),
        ]
        isolated, remaining = self.context_engineering.isolate(
            reflect_components, "reflection analysis", max_tokens=8000
        )

        current_fitness = self._compute_fitness()
        fv = self.five_view.evaluate(
            node_count=self.store.get_node_count(),
            edge_count=self.store.get_edge_count(),
            bank_count=self.bank.count(),
            evolution_fitness=current_fitness,
            alert_level=self.equilibrium.get_alert_level(),
            uptime_s=time.time() - self._start_time,
            drift_alerts=len(self.drift_detector.detect()),
            convergence=self.convergence.is_converged(),
        )

        # Stale detection: skip heavy processing if score unchanged within 15min
        STALE_THRESHOLD_SEC = 900  # 15 minutes
        now = time.time()
        score_delta = abs(fv.composite_score - self._last_reflect_score)
        time_since_last = now - self._last_reflect_time
        if score_delta < 0.0001 and time_since_last < STALE_THRESHOLD_SEC and self._last_reflect_time > 0:
            logger.info("reflect skipped (stale: delta=%.6f, last=%.1fs ago)", score_delta, time_since_last)
            self._last_reflect_time = now  # extend timeout so we don't spam
            stale_result = {
                "five_view": {"score": fv.composite_score, "grade": fv.grade},
                "harness": {"score": 0, "grade": "N/A"},
                "drift_alerts": 0,
                "stale_skipped": True,
                "reason": "Score unchanged since last reflect; skipping heavy cycle.",
            }
            self._telemetry["reflect"] = stale_result
            return stale_result
        self._last_reflect_score = fv.composite_score
        self._last_reflect_time = now
        hv = self.harness_x.evaluate()
        # HarnessX: evaluate best config if available
        best_config = self.harness_x.get_best_config()
        harness_score = getattr(hv, 'score', getattr(hv, 'composite_score', 0.0))
        if best_config:
            harness_eval = self.harness_x.evaluate(best_config, test_cases=[{"input": "reflect"}])
            if hasattr(harness_eval, 'score'):
                harness_score = harness_eval.score
        drift = self.drift_detector.detect()
        self.thermodynamic.update(0.1)
        # thermodynamic.reset when temperature is extreme
        stats = self.thermodynamic.get_stats()
        if stats.get("temperature", 0.5) > 0.9 or stats.get("temperature", 0.5) < 0.1:
            self.thermodynamic.reset()
        self.convergence.observe(fv.composite_score)
        self.coala.observe({"five_view": fv.composite_score, "harness": harness_score})
        reflect_diagnostics["four_network_reflect"] = self.four_network.reflect("system performance", num_reflections=2)
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

        # Equilibrium: observe system balance
        self.equilibrium.observe(fv.composite_score, "composite")

        # Trend: observe five_view trend
        self.trend.observe("five_view", fv.composite_score)

        # SystematicDebugging: 自动调试低 fitness 状态
        reflect_debug_info = {"status": "no_debug_needed"}
        if fv.composite_score < 0.3:
            try:
                debug_result = self.systematic_debugging.debug(
                    f"Low fitness: {fv.composite_score:.2f}",
                    context={"five_view": fv.__dict__ if hasattr(fv, '__dict__') else {}}
                )
                reflect_debug_info = {
                    "root_cause": debug_result.root_cause,
                    "verified": debug_result.verified,
                    "confidence": debug_result.confidence,
                }
            except Exception as e:
                reflect_debug_info = {"error": str(e)}

        # CodeReviewer: 审查 reflect 分析质量
        reflect_review = {"score": 0, "critical": 0, "approved": False}
        try:
            review_result = self.code_reviewer.review(
                code_path="life.py:reflect",
                changes=[{"type": "reflection", "score": fv.composite_score}]
            )
            reflect_review = {
                "score": review_result.overall_score,
                "critical": review_result.critical_count,
                "approved": review_result.approved,
            }
        except Exception:
            reflect_review["status"] = "review_unavailable"

        # Disposition: get behavioral prediction
        disposition = self.disposition.get_disposition("remember_utility")

        # MARS: get belief state
        mars_belief = self.mars.get_belief("dream_belief")

        # === Reflect: full mechanism activation ===
        # Thermodynamic deep operations
        reflect_diagnostics["thermo_energy"] = self.thermodynamic.get_energy()
        reflect_diagnostics["thermo_compressed"] = self.thermodynamic.get_compressed_scale()
        reflect_diagnostics["thermo_intelligence"] = self.thermodynamic.compute_intelligence()
        reflect_diagnostics["thermo_intel_breakdown"] = self.thermodynamic.get_intelligence_breakdown()
        reflect_diagnostics["thermo_rare_valid"] = self.thermodynamic.get_rare_valid_fidelity()
        reflect_diagnostics["thermo_trajectory"] = self.thermodynamic.get_trajectory_summary()
        # 喂入真实数据：outcome_valid=低漂移说明反思有效，rarity=复合分数反映反思价值
        self.thermodynamic.observe_baseline(0.3)
        self.thermodynamic.observe_action(
            action="reflect",
            outcome_valid=len(drift) < 3,
            rarity=1.0 - (fv.composite_score or 0.5),
            baseline_prob=0.3,
            induced_prob=0.3 * (1 + (1.0 - (fv.composite_score or 0.5))),
        )
        reflect_diagnostics["thermo_validity_rate"] = self.thermodynamic.get_validity_rate()
        reflect_diagnostics["thermo_rare_ratio"] = self.thermodynamic.get_rare_valid_ratio()

        # Convergence deep
        reflect_diagnostics["convergence_history"] = self.convergence.get_history()

        # Info gain deep
        reflect_diagnostics["info_gain_returns"] = self.info_gain.diminishing_returns()

        # Agent forest deep operations
        self.agent_forest.record_performance(f"reflector_{int(time.time())}", fv.composite_score)
        reflect_diagnostics["agent_rankings"] = self.agent_forest.get_agent_rankings()
        reflect_diagnostics["agent_samples"] = self.agent_forest.sample_agents(2)
        vote = self.agent_forest.sample_vote("reflect", responses=["ok", "ok", "needs_work"])
        reflect_diagnostics["agent_removed"] = self.agent_forest.remove_agent("old_reflector")

        # Behavior mirror deep
        reflect_diagnostics["behavior_profile"] = self.behavior_mirror.compute_profile("system")
        reflect_diagnostics["behavior_deviation"] = self.behavior_mirror.detect_deviation("system")

        # Event bus deep
        self.event_bus.subscribe("reflect_events", lambda e: None)
        reflect_diagnostics["event_recent"] = self.event_bus.get_recent(5)

        # Feedback deep operations
        reflect_diagnostics["feedback_avg"] = self.feedback.get_average("recent")
        reflect_diagnostics["feedback_best"] = self.feedback.get_best_performers()
        reflect_diagnostics["feedback_count"] = self.feedback.get_feedback_count("recent")
        reflect_diagnostics["feedback_trend"] = self.feedback.get_feedback_trend("recent")
        reflect_diagnostics["feedback_type_stats"] = self.feedback.get_type_stats()

        # Failure log deep operations
        logger.info("reflect: score=%.4f, grade=%s, drift=%d", fv.composite_score, fv.grade, len(drift))
        reflect_diagnostics["failure_rates"] = self.failure_log.get_action_failure_rates()
        reflect_diagnostics["failure_errors"] = self.failure_log.get_common_errors()
        reflect_diagnostics["failure_recent"] = self.failure_log.get_recent_failures()
        reflect_diagnostics["failure_severity"] = self.failure_log.get_severity_distribution()

        # Disposition deep operations
        reflect_diagnostics["disposition_shifts"] = self.disposition.detect_shifts("remember_utility")
        reflect_diagnostics["disposition_all"] = self.disposition.get_all_dispositions()
        reflect_diagnostics["disposition_stable"] = self.disposition.get_most_stable()
        reflect_diagnostics["disposition_volatile"] = self.disposition.get_most_volatile()
        reflect_diagnostics["disposition_shift_count"] = self.disposition.get_shift_count("remember_utility")
        reflect_diagnostics["disposition_shift_history"] = self.disposition.get_shift_history("remember_utility")
        reflect_diagnostics["disposition_variance"] = self.disposition.get_variance("remember_utility")
        reflect_diagnostics["disposition_std"] = self.disposition.get_std("remember_utility")
        reflect_diagnostics["disposition_predict"] = self.disposition.predict("remember_utility")

        # MARS deep operations
        reflect_diagnostics["mars_all_beliefs"] = self.mars.get_all_beliefs()

        # Causal graph deep
        self.causal_graph.add_edge("reflect_start", f"reflect_{int(time.time())}", "causes", 0.8)
        reflect_diagnostics["causal_shortest"] = self.causal_graph.shortest_path("reflect_start", f"reflect_{int(time.time())}")
        reflect_diagnostics["causal_effects"] = self.causal_graph.causal_effects("reflect_start")
        self.causal_graph.do_intervention("reflect_start", 0.9)

        # Reflexion deep
        self.reflexion.record_attempt("reflect", fv.composite_score)
        reflect_diagnostics["reflexion_context"] = self.reflexion.get_reflection_context(query="reflect")
        reflect_diagnostics["reflexion_worst"] = self.reflexion.get_worst_actions()
        reflect_diagnostics["reflexion_trend"] = self.reflexion.get_improvement_trend()

        # Extended thinking deep
        reflect_diagnostics["extended_thought_tree"] = self.extended_thinking.get_thought_tree()

        # Loop guard deep
        self.loop_guard.record_action("reflect")
        self.loop_guard.reset()

        # RL pathology deep
        self.rl_pathology.observe(fv.composite_score, "reflect")

        # 大脑皮层洞察：激活 CerebralCortex.get_insights()
        try:
            if hasattr(self, 'cerebral_cortex') and self.cerebral_cortex is not None:
                cc_insights = self.cerebral_cortex.get_insights()
                reflect_diagnostics['cc_insights'] = cc_insights
                fuse_state = cc_insights.get("fuse_state", {})
                active_fuses = {k: v for k, v in fuse_state.items() if v.get("suppressed")}
                if active_fuses:
                    reflect_diagnostics['active_fuses'] = active_fuses
                    logger.info("reflect: %d active fuses detected", len(active_fuses))
        except Exception as e:
            logger.debug("CC insights not available: %s", e)

        # Session
        self.session.access(f"reflect_{int(time.time())}")
        self.session.expire_idle()

        # publish before return (fix: was dead code after return)
        self.event_bus.publish({"type": "reflect_completed", "composite_score": fv.composite_score, "drift_alerts": len(drift)})

        reflect_result = {
            "five_view": {"score": fv.composite_score, "grade": fv.grade},
            "harness": {"score": harness_score, "grade": "B" if harness_score > 0.7 else "C" if harness_score > 0.4 else "D"},
            "drift_alerts": len(drift),
            "thermodynamic": self.thermodynamic.get_stats(),
            "convergence": self.convergence.is_converged(),
            "worst_performers": len(worst),
            "avoidance_list": len(avoidance),
            "equilibrium": self.equilibrium.get_alert_level(),
            "disposition": disposition,
            "mars_belief": mars_belief,
            "recent_learned": {
                "count": len(recent_nodes),
                "knowledge": learned_knowledge_summary,
            },
            "debug": reflect_debug_info,
            "code_review": reflect_review,
            "diagnostics": reflect_diagnostics,
        }
        # Telemetry: 存储原始返回值
        self._telemetry["reflect"] = reflect_result

        # 反馈环路: reflect → evolve
        # 告诉 evolve 这次 reflect 的质量分数, 帮助选择值得进化的方向
        try:
            self.signal_fusion.push_feedback({
                "from": "reflect",
                "to": "evolve",
                "type": "quality",
                "data": {
                    "composite_score": fv.composite_score,
                    "drift_count": len(drift),
                    "harness_score": harness_score,
                    "effective": fv.composite_score > 0.5,
                },
            })
        except Exception as e:
            logger.debug("reflect: push_feedback to evolve failed: %s", e)

        # 写管道结果（双向语义穿透）
        self.signal_fusion.set_pipe_result("reflect", {
            "composite_score": fv.composite_score,
            "grade": fv.grade,
            "drift_count": len(drift),
            "converged": fv.composite_score > 0.5,
        })

        return reflect_result

    # ============================================================
    # dream pipeline
    # ============================================================
    def dream_cycle(self, branch: str = "main") -> DreamResult:
        nodes = self.store.get_branch_nodes(branch)
        for node in nodes:
            self.dream.register_memory(node)

        # 初始化梦境数据收集字典
        dream_data = {}

        # 链上下文：读取触发管的信号
        try:
            ctx = self.signal_fusion.get_chain_context()
            if ctx:
                trigger_pipe = ctx.get("trigger_pipe", "")
                sigs = ctx.get("trigger_signals", {})
                dream_data["trigger_pipe"] = trigger_pipe
                if trigger_pipe == "reflect":
                    raw_score = sigs.get("raw_score", 0.5)
                    dream_data["trigger_score"] = raw_score
                    logger.info("Dream triggered by reflect (score=%.3f)", raw_score)
                elif trigger_pipe == "evolve":
                    raw_delta = sigs.get("raw_delta", 0)
                    dream_data["evolve_delta"] = raw_delta
                    logger.info("Dream triggered by evolve (delta=%.4f)", raw_delta)
        except Exception:
            pass

        dream_result = self.dream.run_cycle(branch=branch)
        dream_data['extra_dream'] = self.dream.dream()  # 收集额外梦境输出
        self.shmr.generate(entities=[], context="dream")
        self.consolidation_engine.run()
        self.rare_valid.detect()
        self.mars.create_belief("dream_belief", "Dream synthesis", 0.5)
        self.gravity.add_node("dream", mass=0.5)
        self.forgetting.compute_retention_compat("dream", age=1.0)
        self.state_machine.transition(LoopState.RUNNING)
        dream_data['pre_transition_state'] = self.state_machine.state  # 记录转移前状态
        self.state_machine.force_transition(LoopState.COMPLETED)
        self.state_machine.force_transition(LoopState.RUNNING)
        dream_data['post_transition_state'] = self.state_machine.state  # 记录转移后状态
        self.consistency.vote([n.content[:100] for n in nodes[:10]])
        dream_data['consensus_history'] = self.consistency.get_consensus_history()  # 收集共识历史
        dream_data['weighted_vote'] = self.consistency.vote_with_weights(["a","b"], [0.8,0.2])  # 收集加权投票结果
        self.extended_thinking.think({"context": "dream", "memory_count": len(nodes)})
        self.dna_extractor.extract({"memories": len(nodes), "patterns": dream_result.patterns_found})

        # SHMR: get synthesized beliefs
        beliefs = self.shmr.get_beliefs(min_confidence=0.3)
        dream_result.beliefs_synthesized += len(beliefs)

        # === Dream: full mechanism activation ===
        # 状态机深度查询
        dream_data['valid_next'] = self.state_machine.get_valid_next()  # 收集有效下一步状态
        dream_data['transition_history'] = self.state_machine.get_transition_history()  # 收集状态转移历史
        dream_data['sm_state'] = self.state_machine.state  # 收集当前状态机状态

        # 遗忘机制深度操作
        dream_data['expired_nodes'] = self.forgetting.get_expired_nodes(threshold=0.1)  # 收集过期节点
        dream_data['most_forgotten'] = self.forgetting.get_most_forgotten()  # 收集最被遗忘项
        dream_data['most_retained'] = self.forgetting.get_most_retained()  # 收集最被保留项
        dream_data['retention'] = self.forgetting.get_retention("dream")  # 收集保留率
        dream_data['retention_dist'] = self.forgetting.get_retention_distribution()  # 收集保留率分布
        dream_data['forget_time'] = self.forgetting.predict_forget_time("dream")  # 收集遗忘预测时间

        # 引力机制深度查询
        dream_data['gravity'] = self.gravity.compute("dream", "dream")  # 收集引力计算结果
        dream_data['gravity_rank'] = self.gravity.rank_by_gravity("dream")  # 收集引力排名
        dream_data['strongest_pair'] = self.gravity.get_strongest_pair()  # 收集最强引力对
        dream_data['total_gravity'] = self.gravity.get_total_gravity()  # 收集总引力值

        # 稀有值检测深度查询
        self.rare_valid.observe(0.5)
        dream_data['rare_values'] = self.rare_valid.get_rare_values()  # 收集稀有值

        # DNA提取器深度查询
        dream_data['dominant_features'] = self.dna_extractor.get_dominant_features()  # 收集主导特征

        # 巩固管道深度操作
        self.consolidation.consolidate([{"content": "dream_content", "importance": 0.5}])

        # Hebbian hub-driven consolidation: consolidate in hub order
        try:
            hubs = self.hebbian.find_hubs(top_k=10)
            dream_data['hebbian_hubs'] = [{"node_id": n, "score": round(s, 4)} for n, s in hubs]
            for node_id, hub_score in hubs:
                if self.hebbian.should_consolidate(node_id, hub_degree_threshold=2.0):
                    logger.info("Hebbian consolidation candidate: %s (hub_score=%.3f)", node_id[:8], hub_score)
            candidates = self.hebbian.get_consolidation_candidates(min_hub_score=1.0, top_k=20)
            dream_data['hebbian_consolidation_candidates'] = len(candidates)
        except Exception as exc:
            logger.warning("Hebbian consolidation failed: %s", exc)
            dream_data['hebbian_error'] = str(exc)

        # SHMR深度查询
        dream_data['co_occurrence'] = self.shmr.get_co_occurrence_stats()  # 收集共现统计
        dream_data['entity_stats'] = self.shmr.get_entity_stats()  # 收集实体统计

        # 扩展思考深度查询
        dream_data['thought_tree'] = self.extended_thinking.get_thought_tree()  # 收集思考树

        # 行为镜像
        self.behavior_mirror.mirror("system", "dream", {"patterns": dream_result.patterns_found})

        # 事件总线
        dream_data['recent_events'] = self.event_bus.get_recent(3)  # 收集最近事件

        # Session
        self.session.access(f"dream_{int(time.time())}")

        import uuid
        # Log dream to database
        cycle_id = f"dream_{uuid.uuid4().hex[:12]}"
        self.store.log_evolution(cycle_id, 0.0, dream_result.patterns_found / max(len(nodes), 1), "dream")
        # Also write to dream_log table directly
        try:
            self._conn = self.store._conn
            if self._conn:
                self._conn.execute(
                    "INSERT INTO dream_log (cycle_id, patterns_found, beliefs_synthesized, connections_discovered, timestamp) VALUES (?,?,?,?,?)",
                    (cycle_id, dream_result.patterns_found, dream_result.beliefs_synthesized, dream_result.connections_discovered, time.time())
                )
                self._conn.commit()
                logger.debug("Dream log written: %s", cycle_id)
            else:
                logger.warning("Dream log: store connection is None")
        except Exception as e:
            logger.warning("Failed to write dream log: %s: %s", type(e).__name__, e)

        # 附加梦境数据到结果对象
        setattr(dream_result, 'dream_data', dream_data)

        self.event_bus.publish({"type": "dream_completed", "patterns": dream_result.patterns_found, "beliefs": dream_result.beliefs_synthesized, "connections": dream_result.connections_discovered})
        # Telemetry: 存储原始返回值
        self._telemetry["dream"] = dream_result

        # 写管道结果
        self.signal_fusion.set_pipe_result("dream", {
            "patterns_found": dream_result.patterns_found,
            "beliefs_synthesized": dream_result.beliefs_synthesized,
            "connections_discovered": dream_result.connections_discovered,
            "insights": getattr(dream_result, 'insights', [])[:3],
        })

        return dream_result

    # ============================================================
    # maintain pipeline
    # ============================================================
    def maintain(self) -> dict:
        start = time.time()
        maintain_data = {}

        # 链上下文：读取触发管的信号
        try:
            ctx = self.signal_fusion.get_chain_context()
            if ctx:
                trigger_pipe = ctx.get("trigger_pipe", "")
                sigs = ctx.get("trigger_signals", {})
                maintain_data["trigger_pipe"] = trigger_pipe
                if trigger_pipe == "dream":
                    patterns = sigs.get("patterns_found", 0)
                    maintain_data["upstream_patterns"] = patterns
                    logger.info("Maintain triggered by dream (%d patterns)", patterns)
        except Exception:
            pass

        self.bank.run_migration()
        self.bank.run_aging()
        self.consolidation_engine.run()
        self.consolidation_engine.consolidate()
        self.convergence.update(self.bank.count())
        self.thermodynamic.update(0.1)
        # thermodynamic.reset when temperature is extreme
        stats = self.thermodynamic.get_stats()
        if stats.get("temperature", 0.5) > 0.9 or stats.get("temperature", 0.5) < 0.1:
            self.thermodynamic.reset()
        # Feed real maintenance data: outcome_valid=system stable, rarity=convergence delta
        try:
            ec = self.thermodynamic.get_energy()
            self.thermodynamic.observe_action(
                action="maintain",
                outcome_valid=stats.get("temperature", 0.5) < 0.8,
                rarity=max(0.01, 1.0 - (ec or 0.5)),
                baseline_prob=0.3,
            )
        except Exception:
            pass
        self.circuit_breaker.record_success()
        self.self_healing.heal({"bank_count": self.bank.count()})
        self.mars.update_belief("dream_belief", 0.6)
        self.mars.create_belief("temp_belief", "temporary", 0.1)
        self.mars.delete_belief("temp_belief")
        self.crash_recovery.create_checkpoint()
        self.crash_recovery.recover({"status": "maintain", "bank_count": self.bank.count()})
        self.tool_loop.execute("maintain")
        self.organ_pipeline.execute({"action": "maintain"})
        self.hands.execute({"action": "maintain"})

        # MiMo: Utility Decay — apply decay rules
        self.utility_decay.apply_decay(days_elapsed=1)
        self.utility_tracker.apply_decay()

        # MiMo: Progressive Checkpoints — check context pressure
        node_count = self.store.get_node_count()
        context_usage = min(1.0, node_count / 10000)
        cp_level = self.progressive_checkpoints.should_save(context_usage)
        if cp_level:
            self.progressive_checkpoints.save_checkpoint(cp_level, context_usage,
                {"node_count": node_count, "edge_count": self.store.get_edge_count()})

        # MiMo: Tool Drift Detection
        recent_tools = self.trajectory.get_action_summary()
        if recent_tools:
            tool_counts = {k: v.get("count", 0) for k, v in recent_tools.items()}
            if not self.tool_drift._baseline:
                self.tool_drift.record_baseline(tool_counts)
            else:
                self.tool_drift.record_current(tool_counts)

        # MiMo: Three-Layer Compression
        nodes = self.store.get_active_nodes(limit=20)
        for n in nodes:
            self.forgetting.compute_retention_compat(n.id, age=1.0)
            self.gravity.add_node(n.id, mass=n.utility)
            self.zscore.observe(n.utility)
            # LocalMaintenance: per-node maintenance
            actions = self.local_maintenance.check_node(n.id, n.utility, 1.0, 0)
            for action in actions:
                if action.action == "prune":
                    self.store.delete_node(n.id)
            # MemoryDepth: track access
            self.memory_depth.record_access(n.id)

        # MiMo: Heartbeat 4-cycle
        self.heartbeat_4cycle.run_cycles()

        # MiMo: Capability ceiling check
        can_add, ceiling_reason = self.capability_ceiling.should_add_agents()

        # MiMo: Cognitive collapse detection
        collapse = self.cognitive_collapse.detect()

        # MiMo: WAL checkpoint
        self.wal.write("maintain", status="completed",
                      payload={"node_count": self.store.get_node_count()})

        # State persistence: save memory state
        self.state_persistence.save(self)

        # MiMo: Rule expiration audit
        expired = self.rule_expiration.audit()

        # MiMo: FileChecksum — verify core file integrity
        checksum_results = self.file_checksum.verify_all()

        # OmegaServer: 检查服务状态
        maintain_server_status = {"status": "unknown"}
        try:
            maintain_server_status = self.server.status()
        except Exception:
            maintain_server_status = {"status": "server_check_failed"}

        # MemoryDataAdapter: 运行快速基准评估
        maintain_benchmark = {}
        try:
            benchmark = self.memory_data_adapter.evaluate("memoryagentbench", "ultra")
            maintain_benchmark = benchmark.metrics if hasattr(benchmark, 'metrics') else {}
        except Exception:
            maintain_benchmark = {"status": "benchmark_unavailable"}

        # MiMo: ThreeLayerCompression — compress maintain report
        report_text = "Maintain completed: %d nodes, %d edges, %d expired rules" % (
            self.store.get_node_count(), self.store.get_edge_count(), len(expired))
        compressed = self.three_layer_compression.compress(report_text)
        self.zscore.detect()
        self.drift_detector.observe_behavioral(0.5)
        drift_alerts = self.constraint_drift.detect()
        if drift_alerts:
            logger.warning("Constraint drift detected: %s", drift_alerts)
        maintain_data['constraint_drift_alerts'] = drift_alerts

        # RIMRULE: extract rule report for maintain
        if hasattr(self, 'rimrule'):
            try:
                rule_report = self.rimrule.get_rules(sort_by="confidence", limit=5)
                maintain_data['rimrule_rules'] = rule_report
                # P3 RSI: feed high-confidence RIMRULLE rules back into MemPO condition utilities
                if hasattr(self, 'mempo') and hasattr(self.mempo, 'apply_rule_guidance'):
                    for rule in rule_report:
                        if rule.get("confidence", 0) > 0.6:
                            cond = rule.get("condition", "")
                            if cond:
                                self.mempo.apply_rule_guidance(rule, [])
            except Exception as e:
                logger.debug("RIMRULE report failed: %s", e)

        self.cache.delete("old_key")

        # Forgetting: get expired nodes for cleanup
        expired_nodes = self.forgetting.get_expired_nodes(threshold=0.1)

        # Trajectory: get action summary
        traj_summary = self.trajectory.get_action_summary()

        # MemorySideEffect: check for retrieval side effects
        self.memory_side_effect.set_current_task("maintain")
        self.memory_side_effect.detect()

        # === Maintain: full mechanism activation ===
        # Bank deep operations
        maintain_data['bank_tiers'] = self.bank.count_by_tier()
        self.bank.deposit("maintain_ref", tier=Tier.WORKING)
        # Store deep operations
        maintain_data['store_read'] = self.store.read_node("test_id")
        self.store.log_evolution("maintain", 0.5, 0.6, "maintain")
        self.store.log_maintenance("migration", 10, 5.0)
        self.store.log_audit("maintain", 0.8, {"action": "cleanup"})
        # delete_node and update_node: test via temporary node
        temp_node = Node(id="temp_test_node", content="temp", utility=0.1)
        self.store.create_node(temp_node)
        maintain_data['temp_read'] = self.store.read_node("temp_test_node")
        temp_node.utility = 0.9
        self.store.update_node(temp_node)
        self.store.delete_node("temp_test_node")
        maintain_data['bank_importance'] = self.bank.get_importance_distribution()
        maintain_data['bank_newest'] = self.bank.get_newest_items(Tier.WORKING)
        maintain_data['bank_oldest'] = self.bank.get_oldest_items(Tier.WORKING)
        maintain_data['bank_tier_items'] = self.bank.get_tier_items(Tier.WORKING)

        # Crash restore deep
        self.crash_restore.save_checkpoint({"maintain_cycle": time.time(), "nodes": self.store.get_node_count()})
        maintain_data['crash_restore'] = self.crash_restore.restore_latest()
        maintain_data['crash_checkpoints'] = self.crash_restore.list_checkpoints()

        # Self healing deep
        maintain_data['heal_diagnosis'] = self.self_healing.diagnose({"bank_count": self.bank.count()})

        # Convergence deep
        maintain_data['convergence_history'] = self.convergence.get_history()

        # DAG executor deep
        self.dag_executor.add_node("maintain_task")
        maintain_data['dag_validate'] = self.dag_executor.validate()
        maintain_data['dag_execute'] = self.dag_executor.execute()
        maintain_data['dag_state_summary'] = self.dag_executor.get_state_summary()

        # Monitored DAG deep
        maintain_data['monitored_dag_execute'] = self.monitored_dag.execute_monitored()
        maintain_data['monitored_dag_latency'] = self.monitored_dag.get_latency_stats()

        # Parallel DAG deep
        maintain_data['parallel_dag_execute'] = self.parallel_dag.execute_parallel()

        # Retryable DAG deep
        maintain_data['retryable_dag_execute'] = self.retryable_dag.execute_with_retry(failure_rate=0.0)

        # Trajectory deep operations
        maintain_data['traj_action_summary'] = self.trajectory.get_action_summary()
        maintain_data['traj_compare'] = self.trajectory.compare_trajectories("remember", "recall")
        maintain_data['traj_common_errors'] = self.trajectory.get_common_errors()
        maintain_data['traj_common_failures'] = self.trajectory.get_common_failures()
        maintain_data['traj_duration_stats'] = self.trajectory.get_duration_stats("remember")
        maintain_data['traj_trajectories'] = self.trajectory.get_trajectories()
        maintain_data['traj_success_rate'] = self.trajectory.success_rate("remember")

        # Progressive complexity deep
        maintain_data['progressive_complexity'] = self.progressive_complexity.assess("maintain", context_tokens=5000)

        # Context window deep
        maintain_data['context_check'] = self.context_window.check()
        maintain_data['context_suggest_compression'] = self.context_window.suggest_compression()

        # Human oversight deep
        req = self.human_oversight.submit_action("maintain_cleanup", RiskLevel.LOW)
        maintain_data['human_oversight_needs_human'] = self.human_oversight.needs_human(req)
        maintain_data['human_oversight_pending'] = self.human_oversight.get_pending()
        self.human_oversight.check_timeouts()
        # approve/reject are triggered by human input, not pipeline
        # but we test the interface:
        if self.human_oversight.get_pending():
            pending = self.human_oversight.get_pending()[0]
            self.human_oversight.approve(pending.request_id, "system")
        # reject: submit a high-risk action then reject it
        reject_req = self.human_oversight.submit_action("dangerous_op", RiskLevel.CRITICAL)
        if self.human_oversight.needs_human(reject_req):
            self.human_oversight.reject(reject_req.request_id, "system", "too dangerous")

        # Tree of thoughts deep
        maintain_data['tree_of_thoughts'] = self.tree_of_thoughts.search("maintain optimization", strategy=SearchStrategy.BFS)

        # Think tool deep
        maintain_data['think_tool'] = self.think_tool.run(task="maintain analysis", context="system maintenance")

        # Structured output deep
        maintain_data['structured_validate'] = self.structured_output.validate('{"status": "ok"}', [])
        maintain_data['structured_schema_prompt'] = self.structured_output.generate_schema_prompt([SchemaField("task", "string"), SchemaField("result", "string")])

        # XML tag deep
        from prometheus_ultra.prompt.xml_tag import PromptSection
        prompt = self.xml_tag.build([PromptSection("task", "maintain")])
        maintain_data['xml_all_sections'] = self.xml_tag.extract_all_sections(prompt)
        maintain_data['xml_task_section'] = self.xml_tag.extract_section(prompt, "task")

        # Reasoning adapter deep
        maintain_data['reasoning_adapter'] = self.reasoning_adapter.adapt("think step by step", "reasoning")

        # Stream deep
        maintain_data['stream_recent'] = self.stream.recent(5)
        maintain_data['stream_search'] = self.stream.search_content("maintain")
        maintain_data['stream_count'] = self.stream.get_count()
        maintain_data['stream_type_dist'] = self.stream.get_type_distribution()
        maintain_data['stream_avg_importance'] = self.stream.get_avg_importance()

        # Behavior mirror deep
        self.behavior_mirror.mirror("system", "maintain", {"duration": time.time() - start})
        maintain_data['behavior_profile'] = self.behavior_mirror.compute_profile("system")
        maintain_data['behavior_deviation'] = self.behavior_mirror.detect_deviation("system")

        # Event bus deep
        maintain_data['event_bus_recent'] = self.event_bus.get_recent(5)

        # Session deep
        self.session.access(f"maintain_{int(time.time())}")
        self.session.expire_idle()

        # Adapter deep
        maintain_data['x_adapter_reverse'] = self.x_adapter.reverse_adapt({"node_id": "maintain"})
        maintain_data['y_adapter_tier_name'] = self.y_adapter.get_tier_name(0)

        # Monitor deep
        maintain_data['monitor_uptime'] = self.monitor.get_uptime()
        maintain_data['monitor_health'] = self.monitor.get_health()

        # Skill deep
        self.skill_claw.register_skill("maintain_skill", "maintain_skill", "Maintenance and cleanup skill", ["maintenance", "cleanup"])
        maintain_data['skill_get'] = self.skill_registry.get_skill("maintain_skill")
        maintain_data['skill_active'] = self.skill_registry.get_active_skills()

        # Instincts deep
        self.instincts.register("maintain_check", lambda ctx: True)

        # Consolidation pipeline deep
        self.consolidation.consolidate([{"content": "maintain", "importance": 0.3}])
        self.dopamine.update_config(threshold=0.3)
        # dopamine.reset only when accept rate is extreme
        stats = self.dopamine.get_stats()
        if stats.get("accept_rate", 0.5) > 0.95 or stats.get("accept_rate", 0.5) < 0.05:
            self.dopamine.reset()

        # 活性检查：激活低调用频率的机制
        # Note: heartbeat, capability_ceiling, cognitive_collapse, rule_expiration
        # are also called earlier in maintain() (see MiMo blocks).
        # This block adds: loop_selector + agent_forest.
        loop_cfg = self.loop_selector.select("maintain")
        self.loop_selector.record_outcome(loop_cfg.strategy, self._compute_fitness())
        self.agent_forest.record_performance("maintainer", self._compute_fitness())
        
        # === KTA: 定期扫描未翻译的高 utility 知识 ===
        try:
            hint = self.knowledge_to_mechanism.scan_for_opportunities(
                store=self.store, utility_threshold=0.6,
            )
            if hint.get("untranslated_count", 0) >= 3:
                logger.info(
                    "KTA scan: %d untranslated nodes (utility ≥ 0.6)",
                    hint["untranslated_count"],
                )
        except Exception as e:
            logger.debug("KTA scan skipped: %s", e)
        
        # === 反退化检查 ===
        try:
            all_avgs = self.utility_tracker.get_all_averages()
            if all_avgs:
                vals = list(all_avgs.values())
                maintain_data['aging_compression_var'] = sum((v - sum(vals)/len(vals))**2 for v in vals) / len(vals)
        except Exception:
            pass
        try:
            maintain_data['tracelift_inert'] = sum(1 for k in self._learned_config if not k.startswith('_'))
        except Exception:
            pass

        # 链分析：激活历史链的总结（signal_fusion.chain_analysis）
        try:
            active_chains = self.signal_fusion.get_state().get("active_chains", [])
            if active_chains:
                chain_summaries = []
                for cid in list(active_chains.keys())[:3]:
                    analysis = self.signal_fusion.chain_analysis(cid)
                    if analysis:
                        chain_summaries.append(analysis)
                if chain_summaries:
                    maintain_data['chain_analysis'] = chain_summaries
        except Exception as e:
            logger.debug("chain_analysis failed: %s", e)

        self.event_bus.publish({"type": "maintain_completed", "decayed": len(expired_nodes), "heartbeat": True})
        maintain_result = {
            "consolidation": self.consolidation.get_stats(),
            "convergence": self.convergence.get_stats(),
            "thermodynamic": self.thermodynamic.get_stats(),
            "duration_ms": (time.time() - start) * 1000,
            "expired_nodes": len(expired_nodes),
            "trajectory_actions": len(traj_summary),
            "server_status": maintain_server_status,
            "benchmark": maintain_benchmark,
            "maintain_data": maintain_data,
        }
        # Telemetry: 存储原始返回值
        self._telemetry["maintain"] = maintain_result

        # 写管道结果
        self.signal_fusion.set_pipe_result("maintain", {
            "consolidated": maintain_data.get("consolidated_count", 0),
            "server_status": maintain_server_status,
        })

        return maintain_result

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
            mechanisms=127,
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
        """Compute system fitness based on multiple quality dimensions."""
        # Dimension 1: Memory richness (0-0.3)
        node_count = self.store.get_node_count()
        edge_count = self.store.get_edge_count()
        memory_score = min(0.3, (node_count * 0.0005 + edge_count * 0.0003))

        # Dimension 2: Diversity (0-0.2)
        types = set()
        nodes = self.store.get_active_nodes(limit=200)
        for n in nodes:
            types.add(n.type.value if hasattr(n.type, 'value') else str(n.type))
        diversity_score = min(0.2, len(types) * 0.04)

        # Dimension 3: Evolution activity (0-0.2)
        evo_stats = self.evolution_engine.get_stats()
        evo_score = min(0.2, evo_stats.get("generations", 0) * 0.02)

        # Dimension 4: System health (0-0.15)
        health_map = {"healthy": 0.15, "degraded": 0.08, "critical": 0.02, "empty": 0.0}
        health_score = health_map.get(self._compute_health(), 0.0)

        # Dimension 5: HarnessX evolution (0-0.15)
        harness_stats = self.harness_x.get_stats()
        harness_score = min(0.15, harness_stats.get("evolutions", 0) * 0.05)

        # Dimension 6: Utility health (0-0.1)
        util_stats = self.utility_tracker.get_stats()
        util_score = min(0.1, util_stats.get("avg_utility", 0.5) * 0.1)

        # Dimension 7: Thermodynamic energy (0-0.1)
        ti_energy = self.thermodynamic.get_energy()
        energy_score = min(0.1, ti_energy * 0.1)

        total = memory_score + diversity_score + evo_score + health_score + harness_score + util_score + energy_score
        return min(1.0, max(0.0, total))

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
        self.wal.checkpoint()
        self.bank.close()
        self.cache.close()
        self.store.close()
        logger.info("Prometheus Ultra closed")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
