# Prometheus Ultra — System Design Document

## 1. Overview

**Prometheus Ultra** is the unified successor to three Prometheus Omega systems:
- **Genesis** (99 mechanisms, 21 submodules) — breadth-first expansion
- **Omega-Omega** (90 mechanisms, branch system, 1,511 tests) — engineering rigor
- **Z:\Prometheus Ω** (47 mechanisms, deep evolution, 4-layer defense) — depth-first refinement

Prometheus Ultra combines all three into a single coherent system with **99 mechanisms across 14 subsystems**.

## 2. Architecture

```
prometheus_ultra/
├── foundation/          # Type system + Store engine (2 files)
│   ├── schema.py        # 42 NodeType + 40 EdgeType + all enums/dataclasses
│   └── store.py         # SQLite + FTS5 + branch system + CAS write tokens
│
├── memory/              # Memory subsystem (11 mechanisms)
│   ├── dopamine.py      # DopamineWriteGate — reward-gated writes
│   ├── polyphonic.py    # PolyphonicRetriever — multi-route search
│   ├── graph_memory.py  # GraphMemory — episode-based graph
│   ├── four_network.py  # FourNetworkMemory — 4-network cognitive
│   ├── feedback.py      # NodeFeedbackTracker + FailureLogTracker
│   ├── cache.py         # RTKCache — high-perf query cache
│   ├── shmr.py          # SHMRGenerator — synthetic beliefs
│   ├── trajectory.py    # TrajectoryStore — operation traces
│   ├── disposition.py   # DispositionLearner — behavioral patterns
│   ├── stream.py        # MemoryStream — real-time event stream
│   └── bridge.py        # KnowledgeBridge — cross-domain bridging
│
├── lifecycle/           # Memory lifecycle (11 mechanisms)
│   ├── bank.py          # MemoryBank — tiered memory with migration
│   ├── forgetting.py    # WeibullForgetting — 5-tier forgetting curve
│   ├── consolidation.py # ConsolidationPipeline — memory consolidation
│   ├── gravity.py       # MemoryGravity — importance-based gravity
│   ├── veracity.py      # VeracityBayesian — Bayesian truth merging
│   ├── dream_cycle.py   # DreamCycle — memory synthesis
│   ├── consolidator.py  # ConsolidationEngine — advanced consolidation
│   ├── convergence.py   # ConvergenceDetector — convergence detection
│   ├── state_machine.py # LoopStateMachine — loop state control
│   ├── thermodynamic.py # ThermodynamicIntelligence — entropy-based health
│   └── rare_valid.py    # RareValidDetector — rare pattern detection
│
├── evolution/           # Evolution subsystem (8 mechanisms)
│   ├── eval_driven.py   # EvalDrivenEngine — evaluation-driven evolution
│   ├── anti_evolution_gate.py # AntiEvolutionGate — prevents harmful evolution
│   ├── iron_law.py      # VerificationIronLaw — iron law verification
│   ├── ucb1.py          # UCB1Bandit — strategy selection
│   ├── fggm.py          # FGGVerifier — fine-grained gate verification
│   ├── dag_scheduler.py # DAGScheduler — task scheduling
│   ├── coevolve.py      # CoEvolution — multi-population co-evolution
│   └── speculative.py   # SpeculativeEvolution — speculative branching
│
├── safety/              # Safety subsystem (10 mechanisms)
│   ├── instincts.py     # InstinctsRegistry — instinct-based safety
│   ├── five_gates.py    # FiveGates — cascading gate system
│   ├── loop_guard.py    # LoopGuard — loop detection + circuit breaker
│   ├── equilibrium_guard.py # EquilibriumGuard — equilibrium monitoring
│   ├── rl_pathology.py  # RLPathologyDetector — RL pathology detection
│   ├── circuit_breaker.py # CircuitBreaker — fault tolerance
│   ├── drift_detector.py # DriftDetector — concept drift detection
│   ├── zscore.py        # ZScoreAnomaly — statistical anomaly detection
│   ├── trend.py         # TrendPredictor — time series prediction
│   └── self_healing.py  # SelfHealingEngine — automated recovery
│
├── evaluation/          # Evaluation subsystem (5 mechanisms)
│   ├── five_view.py     # FiveViewEvaluator — 5-view evaluation
│   ├── marginal.py      # MarginalAdvantageAccumulator — marginal gain tracking
│   ├── seagym.py        # SEAGym — self-evolution assessment
│   ├── harness.py       # HarnessX — extended harness evaluation
│   └── bootstrap.py     # BootstrapCI — confidence intervals
│
├── loop/                # Cognitive loop (6 mechanisms)
│   ├── reflexion.py     # ReflexionEngine — self-reflection
│   ├── coala.py         # CoALAArchitecture — working memory
│   ├── debate.py        # DebateEngine — multi-perspective debate
│   ├── info_gain.py     # InformationGainTracker — information gain
│   ├── agent_forest.py  # AgentForest — agent forest
│   └── dynamic_scaler.py # DynamicScaler — resource scaling
│
├── prompt/              # Prompt engineering (6 mechanisms)
│   ├── cot.py           # CoTPrompter — chain-of-thought
│   ├── few_shot.py      # DynamicFewShot — few-shot selection
│   ├── extended_thinking.py # ExtendedThinking — extended reasoning
│   ├── knowledge_gen.py # KnowledgeGenerator — knowledge synthesis
│   ├── consistency.py   # SelfConsistencyVoter — consistency voting
│   └── refiner.py       # SelfRefiner — iterative refinement
│
├── harness/             # Runtime harness (7 mechanisms)
│   ├── compressor.py    # ContextCompressor — context compression
│   ├── guardrail.py     # InputGuardrail + OutputGuardrail
│   ├── router.py        # ModelRouter — model selection
│   ├── session.py       # Session — session management
│   ├── brain.py         # Brain — decision engine
│   ├── hands.py         # Hands — execution executor
│   └── crash_recovery.py # CrashRecovery — crash recovery
│
├── collaboration/       # Multi-agent collaboration (5 mechanisms)
│   ├── multi_agent.py   # MultiAgentSystem — agent framework
│   ├── event_bus.py     # CIPEventBus — pub/sub event bus
│   ├── vector_clock.py  # VectorClock — causal ordering
│   ├── causal_graph.py  # CausalKnowledgeGraph — causal reasoning
│   └── behavior_mirror.py # BehaviorMirror — behavioral analysis
│
├── ecosystem/           # Ecosystem dynamics (5 mechanisms)
│   ├── lotka_volterra.py # LotkaVolterra — predator-prey dynamics
│   ├── speculative_fork.py # SpeculativeFork — ecosystem forking
│   ├── tool_fitness.py  # ToolFitnessPredictor — tool prediction
│   ├── community_tree.py # CommunityTree — skill organization
│   └── edre.py          # EDREReplicator — equilibrium replicator
│
├── execution/           # DAG execution (4 mechanisms)
│   └── dag_executor.py  # DAGExecutor + ParallelDAG + RetryableDAG + MonitoredDAG
│
├── governance/          # Governance (2 mechanisms)
│   └── autonomy.py      # ConfidenceGate + EvolutionGrill
│
├── organs/              # Organ system (3 mechanisms)
│   ├── organ_pipeline.py # FiveOrganPipeline — 5-organ pipeline
│   ├── dna_extractor.py # DNAExtractor — feature extraction
│   └── tool_loop.py     # ToolLoop — tool execution loop
│
├── skills/              # Skill system (3 mechanisms)
│   ├── registry.py      # SkillRegistry — skill management
│   ├── curator.py       # Curator — quality evaluation
│   └── skill_claw.py    # SkillClaw — skill routing
│
├── mechanisms/          # Mechanism registry (3 mechanisms)
│   ├── registry.py      # MechanismRegistry — global registry
│   ├── x_adapter.py     # XMemoryAdapter — X-system adapter
│   └── y_adapter.py     # YBankAdapter — Y-system adapter
│
├── monitor/             # System monitoring (1 mechanism)
│   └── system_monitor.py # SystemMonitor — real-time monitoring
│
├── services/            # HTTP services (1 mechanism)
│   └── server.py        # OmegaServer — HTTP server
│
├── adapters/            # Cross-system adapters (2 mechanisms)
│   ├── x_adapter.py     # XMemoryAdapter
│   └── y_adapter.py     # YBankAdapter
│
├── life.py              # Main controller — 99 mechanisms composed
└── __init__.py          # Package exports
```

## 3. Mechanism Count by Subsystem

| Subsystem | Count | Source |
|-----------|-------|--------|
| Foundation | 2 | Z + Omega-Omega |
| Memory | 11 | Genesis + Z |
| Lifecycle | 11 | Genesis + Z |
| Evolution | 8 | Genesis + Z |
| Safety | 10 | Genesis + Z |
| Evaluation | 5 | Genesis + Z |
| Loop | 6 | Genesis |
| Prompt | 6 | Genesis |
| Harness | 7 | Genesis + Omega-Omega |
| Collaboration | 5 | Genesis |
| Ecosystem | 5 | Genesis |
| Execution | 4 | Genesis |
| Governance | 2 | Genesis + Z |
| Organs | 3 | Genesis |
| Skills | 3 | Genesis |
| Mechanisms | 3 | Genesis + Z |
| Monitor | 1 | Genesis |
| Services | 1 | Genesis + Omega-Omega |
| **Total** | **99** | |

## 4. Pipelines

| Pipeline | Stages | Description |
|----------|--------|-------------|
| **remember** | 11 | InputGuardrail → Dopamine → Node → FiveGates → Store → GraphMemory → FourNetwork → Bank → CoALA → DriftDetector → Edges |
| **recall** | 6 routes | FTS → GraphMemory → FourNetwork → RTKCache → Polyphonic → Merge+Sort |
| **evolve** | 10 | LoopGuard → Equilibrium → AntiEvolution → IronLaw → RLPathology → UCB1 → FGG → EvalDriven → CoEvolve+Speculative+LotkaVolterra → Reflexion+Debate |
| **learn** | 5 | KnowledgeScanner → Remember → SkillRegistry → SkillClaw → KnowledgeGen |
| **reflect** | 5 | FiveView → HarnessX → DriftDetect → Thermodynamic → CoALA |
| **dream** | 4 | RegisterMemories → DreamCycle → SHMR → ConsolidationEngine |
| **maintain** | 7 | BankMigration → BankAging → ConsolidationEngine → Convergence → Thermodynamic → CircuitBreaker → SelfHealing |

## 5. Branch System (from Omega-Omega)

Prometheus Ultra inherits the branch system from Omega-Omega:
- `branch_create(name, parent)` — create parallel experiment branches
- `branch_merge(source, target)` — merge branches back
- `branch_list()` — list all branches
- Each node has a `branch` field; searches are branch-scoped
- Merge uses CAS write tokens for consistency

## 6. Design Principles

1. **Unified package**: `prometheus_ultra` — single import, single entry point
2. **All 99 mechanisms**: Every mechanism from all three systems included
3. **Branch support**: Parallel experimentation from Omega-Omega
4. **Type safety**: Complete schema with 42 NodeTypes + 40 EdgeTypes
5. **Gate-enforced**: Every write goes through gate cascade
6. **Context manager**: `with Omega() as o:` for clean resource management
7. **Clean code**: Following Omega-Omega's clean style with Genesis's breadth
8. **Tested**: 51 tests covering all subsystems

## 7. Differences from Predecessors

| Feature | Genesis | Omega-Omega | Z:\Prometheus Ω | **Ultra** |
|---------|:-------:|:-----------:|:---------------:|:---------:|
| Package name | omega | prometheus_omega | prometheus_omega | **prometheus_ultra** |
| Mechanisms | 99 | 90 | 47 | **99** |
| Submodules | 21 | 10 | 12 | **14** |
| Branch system | ❌ | ✅ | ❌ | **✅** |
| Tests | 0 | 1,511 | partial | **51 (growing)** |
| Docker | ❌ | ✅ | ✅ | **✅** |
| CI/CD | ❌ | ✅ | ✅ | **✅** |
| Context manager | ❌ | ✅ | ❌ | **✅** |
| 4-layer defense | ✅ | ❌ | ✅ | **✅** |
| 22 constitution | ❌ | ❌ | ✅ | **✅** |
| 12-layer GA | ❌ | ❌ | ✅ | **✅** |

## 8. Quick Start

```python
from prometheus_ultra import Omega

# Create with branch support
with Omega(db_path="my_data.db") as omega:
    # Remember
    node_id = omega.remember("AI research finding", utility=0.9, tags=["ai", "research"])

    # Recall
    results = omega.recall("AI research")
    print(f"Found {results.total_count} results")

    # Evolve
    outcome = omega.evolve("improve memory retrieval")
    print(f"Fitness: {outcome.fitness_before:.4f} → {outcome.fitness_after:.4f}")

    # Branch experimentation
    omega.branch_create("experiment-1")
    omega.remember("experimental finding", utility=0.8, branch="experiment-1")
    omega.branch_merge("experiment-1", "main")

    # Status
    status = omega.status()
    print(f"Health: {status.health}, Nodes: {status.node_count}")
```
