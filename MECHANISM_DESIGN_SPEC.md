# Prometheus Ultra — 机制算法设计规范 v1.0

> 本文档为每个机制提供：算法选择理由、输入/输出规格、边界条件、复杂度分析、配置参数、错误处理策略。

---

## 设计原则

1. **每个机制独立可测试** — 不依赖 Omega 主类
2. **所有公共方法有完整 docstring** — 参数、返回值、异常
3. **所有 public API 有类型注解** — mypy 可检查
4. **错误不吞没** — 抛出有意义的异常或返回错误结果
5. **配置通过构造函数** — 不依赖全局状态
6. **线程安全** — 共享状态用锁保护

---

## L0: Foundation

### MinervaStore
- **算法**: SQLite3 + FTS5 全文搜索 + WAL 模式
- **复杂度**: CRUD O(1), Search O(n·log n), Merge O(n)
- **边界**: 空数据库、并发写入、超大结果集、特殊字符搜索
- **配置**: database_path, max_nodes, max_edges, fts_tokenizer
- **错误**: IronLawViolation (写入违反约束时抛出)

### Schema
- **42 NodeType** + **40 EdgeType** 枚举
- **Node**: 15 维数据模型 (id, type, content, utility, surprise, tags, branch, source, confidence, tier, access_count, created_at, updated_at, tx_from, tx_to, version)
- **边权**: 0.0-1.0 浮点数

---

## L1: Memory

### DopamineWriteGate
- **算法**: 加权评分 score = utility × α + surprise × β, 阈值比较
- **复杂度**: O(1)
- **边界**: utility/surprise 超出 [0,1] 范围时 clamp
- **配置**: threshold, decay, α, β
- **状态**: 滑动窗口历史 (最近 1000 条)

### GraphMemory
- **算法**: 邻接表 + BFS 图遍历 + 标签倒排索引
- **复杂度**: Add O(1), Search O(V+E), BFS O(V+E)
- **边界**: 孤立节点、环形边、超大图截断
- **配置**: max_episodes, bfs_depth_limit
- **状态**: episodes dict, adjacency dict, tag index

### FourNetworkMemory
- **算法**: 4 网络独立存储 + 网络特化评分策略
- **复杂度**: Retain O(1), Recall O(N×M) N=网络数 M=条目数
- **边界**: 空网络、查询无匹配、网络名无效
- **配置**: network_names, max_entries_per_network
- **状态**: 4 个独立列表 + tag index

### RTKCache
- **算法**: OrderedDict LRU + TTL 过期
- **复杂度**: Get/Put O(1)
- **边界**: TTL=0 (禁用缓存), max_size=0 (禁用), 并发访问
- **配置**: max_size, ttl_seconds
- **状态**: OrderedDict, hit/miss 计数

### SHMRGenerator
- **算法**: 实体共现分析 + PMI (点互信息) 信念合成
- **复杂度**: Generate O(E²) E=实体数, 通常 E<20
- **边界**: 空实体列表、单一实体、超高频实体
- **配置**: min_pmi_threshold, max_beliefs
- **状态**: entity_freq Counter, co_occurrence Counter

### TrajectoryStore
- **算法**: 轨迹记录 + Counter 模式统计
- **复杂度**: Record O(1), Analysis O(N)
- **边界**: 超大轨迹截断、空动作
- **配置**: max_size
- **状态**: trajectories list, action/success/failure Counter

### KnowledgeBridge
- **算法**: 概念提取 (停用词过滤) + 领域概念 Counter + 跨域 Jaccard 相似度
- **复杂度**: Bridge O(C) C=概念数, TransferScore O(D₁∩D₂)
- **边界**: 空内容、单领域、无共有概念
- **配置**: stopwords, min_concept_length
- **状态**: domain_concepts dict[domain, Counter]

### DispositionLearner
- **算法**: 按 pattern_key 存储值列表 + 均值计算
- **复杂度**: Learn O(1), GetDisposition O(1)
- **边界**: 超长值列表截断
- **配置**: max_values_per_pattern
- **状态**: patterns dict[key, list[float]]

### MemoryStream
- **算法**: 追加日志 + 窗口截断
- **复杂度**: Add O(1), Recent O(1)
- **边界**: 超大流截断
- **配置**: max_size
- **状态**: stream list[dict]

### NodeFeedbackTracker
- **算法**: 反馈记录 + 按 node_id 聚合 + 排序
- **复杂度**: Record O(1), GetWorst O(N·log N)
- **边界**: 空反馈
- **状态**: feedbacks list[NodeFeedback]

### FailureLogTracker
- **算法**: 失败记录 + action 去重
- **复杂度**: Log O(1), GetAvoidance O(N)
- **边界**: 空日志
- **状态**: failures list[FailureLog]

---

## L2: Lifecycle

### MemoryBank
- **算法**: 7 层存储 + 重要性迁移 + 时间老化 (168h)
- **复杂度**: Store O(1), Migration O(N), Aging O(N)
- **边界**: 空 bank, 所有层满, tier 值越界
- **配置**: tier_count, aging_hours
- **状态**: tiers dict[int, list], migrations list

### WeibullForgetting
- **算法**: Weibull CDF: R(t) = exp(-(t/λ)^k) + LRU 淘汰
- **复杂度**: Compute O(1), Evict O(N·log N)
- **边界**: age=0 (R=1), age=∞ (R→0), shape=0 (除零)
- **配置**: shape(k), scale(λ), max_tracked
- **状态**: retentions dict[id, float]

### ConsolidationPipeline
- **算法**: 4 阶段管道: 编码→强化→整合→裁剪
- **复杂度**: O(N) per stage
- **边界**: 空输入、全重复、全弱项
- **配置**: strength_threshold, dedup_window
- **状态**: stage_stats Counter

### MemoryGravity
- **算法**: 引力模型 g = m₁·m₂/|m₁-m₂| (正则化避免除零)
- **复杂度**: AddNode O(1), Compute O(1)
- **边界**: m₁=m₂ (正则化到 0.01), 空节点
- **状态**: nodes dict[id, mass]

### VeracityBayesian
- **算法**: 贝叶斯后验: P(H|E) = P(E|H)·P(H) / [P(E|H)·P(H) + P(E|¬H)·P(¬H)]
- **复杂度**: O(1)
- **边界**: prior=0 or 1 (边界), likelihood=0
- **状态**: posteriors list[float]

### DreamCycle
- **算法**: 共现分析 (PMI) + 信念合成 (utility 聚合) + 连接发现 (共享标签)
- **复杂度**: Patterns O(N²), Beliefs O(N·T), Connections O(N²)
- **边界**: <3 记忆 (无模式), 空标签
- **状态**: memories list, dreams list, beliefs list

### ConsolidationEngine
- **算法**: 重要性强化 + 弱项裁剪
- **复杂度**: O(N)
- **边界**: 空记忆集
- **状态**: runs, consolidated, pruned 计数器

### ConvergenceDetector
- **算法**: 滑动窗口内所有值在阈值内 → 收敛; 新值不收敛 → 重置
- **复杂度**: O(W) W=window
- **边界**: window<2, 所有值相同
- **配置**: window, threshold
- **状态**: history deque, converged bool

### LoopStateMachine
- **算法**: 有效转移矩阵 + 守卫条件
- **复杂度**: O(1)
- **边界**: 无效转移 (拒绝 + 记录)
- **状态**: state LoopState, transitions list

### ThermodynamicIntelligence
- **算法**: 熵 H = -p·ln(p) - (1-p)·ln(1-p), 能量 E = 1 - H/ln(2)
- **复杂度**: O(1)
- **边界**: p=0 or 1 (H=0)
- **状态**: temperature, entropy, energy

### RareValidDetector
- **算法**: 频率直方图 + 稀有性阈值
- **复杂度**: Observe O(1), Detect O(N)
- **边界**: <10 观察 (无法检测)
- **配置**: rarity_threshold
- **状态**: histogram Counter, total_observations

### MARS
- **算法**: 信念字典 + 置信度更新 + 更新计数
- **复杂度**: O(1)
- **边界**: 不存在的信念名
- **状态**: beliefs dict[name, dict]

---

## L3: Evolution

### EvalDrivenEngine
- **算法**: 迭代收敛 fitness = min(1.0, f + 0.05·(1-f))
- **复杂度**: O(max_iterations)
- **边界**: max_iterations=0, threshold>1
- **配置**: max_iterations, convergence_threshold
- **状态**: history list[EvolutionEvalResult]

### AntiEvolutionGate
- **算法**: 已解检测 (set) + 回归检测 (窗口对比) + 停滞检测 + 质量评估
- **复杂度**: O(1) amortized
- **边界**: 空历史, 超长假设
- **配置**: history_window
- **状态**: history deque, seen_hypotheses set

### VerificationIronLaw
- **算法**: 重复惩罚 (Counter) + 模糊度检测 (正则) + 特异性评分
- **复杂度**: O(1) amortized
- **边界**: 空声明, 超短声明
- **配置**: strict_fuzzy_rejection
- **状态**: claims_seen dict, verifications list

### UCB1Bandit
- **算法**: UCB1: aᵢ = x̄ᵢ + √(2·ln(n)/nᵢ)
- **复杂度**: Select O(K), Update O(1) K=臂数
- **边界**: 未访问臂优先, n=0 (除零保护)
- **配置**: arm_names
- **状态**: counts dict, values dict, total int

### FGGVerifier
- **算法**: 上下文质量 + 空进化检测 + 速率限制
- **复杂度**: O(1)
- **边界**: 空数据, 超过速率限制
- **状态**: verifications int, history list

### DAGScheduler
- **算法**: Kahn 拓扑排序 + 关键路径 (最长路径)
- **复杂度**: Sort O(V+E), CriticalPath O(V+E)
- **边界**: 循环依赖 (抛异常), 孤立节点
- **状态**: tasks dict, dependencies dict, dependents dict

### CoEvolution
- **算法**: Red Queen 动态 (适应度耦合) + 锦标赛选择 + 交叉变异
- **复杂度**: O(P·G) P=种群大小 G=代数
- **边界**: 单一种群, 空种群
- **配置**: niche_radius
- **状态**: populations dict, generation int

### SpeculativeEvolution
- **算法**: 分支推测 + 适应度评估 + 回滚/晋升
- **复杂度**: O(F) F=max_forks
- **边界**: 满活跃分支 (替换最弱), 空分支
- **配置**: max_forks
- **状态**: forks list, active_forks list

### EvolutionEngine
- **算法**: 种群初始化 + 锦标赛选择 + 单点交叉 + 高斯变异 + 精英保留
- **复杂度**: O(P·G) P=population_size G=generations
- **边界**: population_size<2, mutation_rate=0
- **配置**: population_size, mutation_rate, crossover_rate, elitism
- **状态**: population list, generation int

---

## L4: Safety

### Constitution
- **算法**: 22 条规则 (5×S + 5×A + 5×B + 5×C + 2×D) + 正则语义检查
- **复杂度**: O(R·L) R=规则数 L=内容长度
- **边界**: 空内容 (A3 拦截), 超长内容 (C3 拦截)
- **状态**: evaluations 计数器

### InstinctsRegistry
- **算法**: 可插拔检查函数列表 + 优先级执行
- **复杂ity**: O(N) N=本能数
- **边界**: 空注册表, 检查函数抛异常
- **状态**: instincts list

### FiveGates
- **算法**: 5 道级联门控 (效用→惊奇→内容→容量→标签)
- **复杂度**: O(1)
- **边界**: 任一门控失败即终止
- **配置**: max_nodes, min_utility, max_surprise
- **状态**: evaluated, passed 计数器

### LoopGuard
- **算法**: 迭代计数 + 超时检测 + 重复检测 (滑动窗口) + 振荡检测 (ABABAB)
- **复杂度**: O(1) amortized
- **边界**: max_iterations=0 (立即触发), timeout=0
- **配置**: max_iterations, timeout, repetition_window
- **状态**: iterations, state, history deque

### EquilibriumGuard
- **算法**: 多指标复合应力 + 迟滞防抖 (连续 N 次才切换)
- **复杂度**: O(W) W=window
- **边界**: 单指标, 无数据
- **配置**: window, hysteresis_threshold
- **状态**: metrics dict, level, hysteresis_counter

### RLPathologyDetector
- **算法**: 5 种病理检测 (崩溃/黑客/停滞/规范博弈/不稳定)
- **复杂度**: O(W) W=window
- **边界**: <5 观察 (无法检测)
- **配置**: window
- **状态**: rewards deque, actions deque

### CircuitBreaker
- **算法**: 三态 (CLOSED→OPEN→HALF_OPEN→CLOSED) + 冷却期
- **复杂度**: O(1)
- **边界**: cooldown=0 (立即半开), threshold=1
- **配置**: failure_threshold, cooldown, half_open_max
- **状态**: failures, state, last_failure_time

### DriftDetector
- **算法**: PSI (Population Stability Index) + KL 散度 + 方差检测
- **复杂度**: O(W) W=window
- **边界**: <W 观察, 空分布 (KL 除零保护)
- **配置**: window, psi_threshold
- **状态**: semantic/behavioral deques, reference/current Counter

### ZScoreAnomaly
- **算法**: Welford 在线方差 + Z-score 异常检测
- **复杂度**: O(1) amortized
- **边界**: <10 观察 (无法检测), std=0
- **配置**: threshold, window
- **状态**: n, mean, m2 (Welford), values deque

### TrendPredictor
- **算法**: 指数平滑 Sₜ = α·Yₜ + (1-α)·Sₜ₋₁ + 线性回归斜率 + 置信区间
- **复杂度**: O(1) amortized
- **边界**: <3 点 (无法回归), 空序列
- **配置**: alpha, window
- **状态**: series dict, smoothed dict, slopes dict

### SelfHealingEngine
- **算法**: 症状分类 (5 种) + 策略映射 + 诊断输出
- **复杂度**: O(1)
- **边界**: 无症状 (返回 unknown)
- **状态**: healings list, fault_history list

---

## L5: Evaluation

### FiveViewEvaluator
- **算法**: 5 维加权评分 (记忆/进化/安全/效率/一致性)
- **复杂度**: O(1)
- **边界**: 无数据 (返回默认值)
- **状态**: reports list

### MarginalAdvantageAccumulator
- **算法**: 边际收益记录 + 均值/总和统计
- **复杂度**: O(1) amortized
- **边界**: 空记录
- **状态**: records list

### SEAGym
- **算法**: 自进化评估记录
- **复杂度**: O(1)
- **状态**: evaluations list

### HarnessX
- **算法**: 系统评估 (延迟/吞吐/可靠性/效率)
- **复杂度**: O(1)
- **状态**: reports list

### BootstrapCI
- **算法**: Bootstrap 重采样: n_bootstrap 次有放回抽样 + 百分位置信区间
- **复杂度**: O(n_bootstrap · n_samples)
- **边界**: <2 样本 (无法计算), n_bootstrap=0
- **配置**: n_bootstrap, confidence
- **状态**: results list

---

## L6: Loop

### ReflexionEngine
- **算法**: 反思积累 + Counter 模式统计 + 最差动作排名
- **复杂度**: O(1) amortized
- **边界**: 空反思, 超长历史截断
- **配置**: max_reflections
- **状态**: reflections list, failure/success Counter

### CoALAArchitecture
- **算法**: 工作记忆 (固定大小) + LTM 溢出 + 注意力权重
- **复杂度**: Add O(W), Retrieve O(L) W=WM大小 L=LTM大小
- **边界**: WM 满时挤出最低注意力项
- **配置**: working_memory_size
- **状态**: working_memory list, long_term_memory list

### DebateEngine
- **算法**: 论点质量评分 (长度×0.3 + 证据×0.4 + 特异性×0.3) + 胜者选择 + 综合
- **复杂度**: O(N) N=论点数
- **边界**: 0 个论点
- **状态**: debates list

### InformationGainTracker
- **算法**: Shannon 熵计算 (离散化分箱) + 递减收益检测
- **复杂度**: O(N) N=总记录数
- **边界**: <10 记录 (无法计算熵)
- **配置**: window
- **状态**: gains list, entropy_history list

### AgentForest
- **算法**: 代理注册 + 能力画像 + 性能排名
- **复杂度**: O(N·log N) for ranking
- **边界**: 空森林, 无匹配能力
- **状态**: agents dict, performance dict

### DynamicScaler
- **算法**: 指数移动平均负载 + 阈值触发缩放
- **复杂度**: O(1) amortized
- **边界**: 空负载历史
- **配置**: scale_up_threshold, scale_down_threshold
- **状态**: current_scale dict, load_history list

---

## L7: Prompt

### CoTPrompter
- **算法**: 关键词分类 (how/why/compare/solve/debug/design) + 步骤模板
- **复杂度**: O(S) S=步骤数
- **边界**: 无匹配模式 (通用分解)
- **状态**: prompts list

### DynamicFewShot
- **算法**: TF-IDF 相关性 + 时效性加分 + 多样性去重
- **复杂度**: O(N·Q) N=示例数 Q=查询词数
- **边界**: 无示例, 无匹配
- **配置**: max_examples
- **状态**: examples list, word_doc_freq Counter

### ExtendedThinking
- **算法**: 递归分解 (最大深度限制) + 子思维树
- **复杂度**: O(D^B) D=分支 B=深度
- **边界**: max_depth=0 (立即返回), 空上下文
- **配置**: max_depth
- **状态**: thoughts list

### KnowledgeGenerator
- **算法**: SVO (主谓宾) 事实提取 + 关系推断
- **复杂度**: O(W) W=词数
- **边界**: 无匹配模式
- **状态**: facts list, relations list

### SelfConsistencyVoter
- **算法**: 归一化 + Counter 多数投票 + 加权投票
- **复杂度**: O(N) N=候选数
- **边界**: 空候选列表
- **状态**: votes list

### SelfRefiner
- **算法**: 问题识别 (冗余/过长/模糊) + 定向修正 + 迭代收敛
- **复杂度**: O(I·N) I=迭代数 N=文本长度
- **边界**: 无问题 (0 迭代), max_iterations=0
- **配置**: max_iterations
- **状态**: refinements list

---

## L8: Harness

### ContextCompressor
- **算法**: 句子分割 + 多维评分 (位置×0.3 + 长度×0.3 + 关键词×0.4) + 选择
- **复杂度**: O(S²) S=句子数
- **边界**: ≤500 字符 (不压缩), ≤3 句
- **配置**: target_ratio
- **状态**: compressions, total_saved 计数器

### InputGuardrail
- **算法**: 空值检查 + 大小限制
- **复杂度**: O(1)
- **状态**: checks, blocked 计数器

### OutputGuardrail
- **算法**: 毒性正则 + 编码安全 + 格式检测 + 长度限制
- **复杂度**: O(L) L=内容长度
- **边界**: 空内容, 超长内容
- **配置**: max_length
- **状态**: checks, blocked, violations

### ModelRouter
- **算法**: 复杂度估算 (长度×0.4 + 技术词×0.4 + 问号×0.2) + 多标准评分
- **复杂度**: O(M) M=模型数
- **边界**: 无匹配模型 (fallback default)
- **配置**: models dict
- **状态**: routes list, model_usage Counter

### Session
- **算法**: 创建/访问/过期管理
- **复杂度**: O(1)
- **边界**: 空闲超时=0 (立即过期)
- **配置**: idle_timeout
- **状态**: sessions list, active dict

### Brain
- **算法**: 效用估算 (历史×0.3 + 上下文×0.7) + 动作排名
- **复杂度**: O(K) K=候选数
- **边界**: 空候选
- **状态**: action_values dict, action_counts dict

### Hands
- **算法**: 重试循环 + 超时检测 + 结果聚合
- **复杂度**: O(R) R=max_retries
- **边界**: max_retries=0 (不重试), timeout=0
- **配置**: max_retries, timeout
- **状态**: executions list, success/failure 计数器

### CrashRecovery
- **算法**: 检查点快照 (MD5 hash) + 状态重建 + 完整性校验
- **复杂度**: O(1)
- **边界**: 无检查点 (fresh start)
- **配置**: max_checkpoints
- **状态**: checkpoints list, recoveries list

---

## L9: Collaboration

### MultiAgentSystem
- **算法**: 能力匹配 + 最小负载/最大能力选择 + 共识投票
- **复杂度**: Allocate O(A) A=代理数, Consensus O(P) P=提案数
- **边界**: 无代理, 无匹配能力
- **状态**: agents dict, allocations list

### CIPEventBus
- **算法**: 主题匹配发布订阅 + 扇出 + 死信队列
- **复杂度**: Publish O(S) S=订阅者数
- **边界**: 无订阅者, 回调异常
- **状态**: subscribers dict, events list, dead_letters list

### VectorClock
- **算法**: 向量时钟 increment + merge (逐元素 max)
- **复杂度**: O(1) amortized
- **状态**: clock dict[node, counter]

### CausalKnowledgeGraph
- **算法**: BFS 最短路径 + 中介中心性 + 因果效应 (路径权重乘积) + 干预追踪
- **复杂度**: Path O(V+E), Centrality O(V³)
- **边界**: 不存在的节点, 无路径
- **状态**: nodes dict, edges list, adjacency dict

### BehaviorMirror
- **算法**: 行为画像 (Counter + Shannon 熵) + JS 散度偏差检测
- **复杂度**: O(N) N=历史长度
- **边界**: <10 历史 (无法检测偏差)
- **配置**: window
- **状态**: action_history dict, profiles dict

---

## L10: Ecosystem

### LotkaVolterra
- **算法**: 真实 ODE: dx/dt = αx - βxy (猎物), dy/dt = δxy - γy (捕食者)
- **复杂度**: O(S·T) S=物种数 T=步数
- **边界**: 种群<0.1 (下限保护), 无捕食者关系
- **状态**: species dict, history dict

### SpeculativeFork
- **算法**: 分叉创建 + 偏差累积 + 合并策略 (best_fitness/most_mutations)
- **复杂度**: O(F) F=分叉数
- **边界**: 无效分叉 ID
- **状态**: forks list, merges list

### ToolFitnessPredictor
- **算法**: 成功率×0.5 + 延迟得分×0.3 + 熟悉度×0.2
- **复杂度**: O(1)
- **边界**: 无使用记录 (返回 0.5)
- **状态**: tool_stats dict

### CommunityTree
- **算法**: DFS 遍历 + 社区检测 + 路径追踪 + 修剪
- **复杂度**: Traversal O(V+E), Communities O(V+E)
- **边界**: 空树, 孤立节点
- **状态**: tree dict, node_data dict

### EDREReplicator
- **算法**: 复制子动力学: dx/dt = x·(f - f̄) + Shannon 多样性
- **复杂度**: O(P) P=种群数
- **边界**: 单一种群, 空种群
- **状态**: populations dict, diversity_history list

---

## L11: Execution

### DAGExecutor
- **算法**: Kahn 拓扑排序
- **复杂度**: O(V+E)
- **边界**: 循环依赖
- **状态**: nodes dict, execution_order list

### ParallelDAG
- **算法**: 并发执行 (逻辑模拟)
- **复杂度**: O(1)
- **配置**: max_workers

### RetryableDAG
- **算法**: 指数退避重试 delay = base × factor^attempt
- **复杂度**: O(R) R=重试次数
- **配置**: max_retries, backoff_factor

### MonitoredDAG
- **算法**: 执行追踪 + 延迟百分位 (p50/p99)
- **复杂度**: O(1)
- **状态**: traces list

---

## L12: Governance

### ConfidenceGate
- **算法**: 自适应阈值 = base×0.8 + avg(history)×0.2
- **复杂度**: O(1)
- **配置**: base_threshold, adaptive
- **状态**: history list, current_threshold

### EvolutionGrill
- **算法**: 安全检查 (|delta|<0.5) + 上下文检查
- **复杂度**: O(1)
- **状态**: reviews list, approved/rejected 计数器

---

## L13: Organs

### FiveOrganPipeline
- **算法**: 5 阶段顺序处理 (感知→处理→记忆→决策→行动)
- **复杂度**: O(1) (模拟)
- **状态**: organ_states dict, executions list

### DNAExtractor
- **算法**: 4 维特征提取 (词多样性/模式密度/标签覆盖/效用分布)
- **复杂度**: O(N) N=记忆数
- **边界**: 空记忆集
- **状态**: extractions list, feature_memory list

### ToolLoop
- **算法**: ReAct 循环 (观察→思考→行动) + 最大迭代限制
- **复杂度**: O(I) I=max_iterations
- **配置**: max_iterations
- **状态**: loops list

---

## L14: Skills

### SkillRegistry
- **算法**: 注册 + 版本递增 + 依赖追踪 + 冲突检测 (标签交集)
- **复杂度**: Register O(1), Conflicts O(N²)
- **状态**: skills list, skill_map dict, versions dict

### Curator
- **算法**: 4 维质量评分 (新颖性×0.3 + 效用×0.3 + 正确性×0.25 + 可组合性×0.15)
- **复杂度**: O(1)
- **边界**: 无注册技能 (novelty=0.8)
- **状态**: evaluations list, quality_scores dict

### SkillClaw
- **算法**: 关键词匹配×0.6 + 类别匹配×0.3 + 使用频率×0.1
- **复杂度**: O(S) S=技能数
- **边界**: 无注册技能
- **状态**: routes list, route_stats Counter

---

## L15: Mechanisms

### MechanismRegistry
- **算法**: 注册 + 启用/禁用 + 依赖检查
- **复杂度**: O(1)
- **状态**: mechanisms dict, enabled set

### XMemoryAdapter
- **算法**: Schema 映射 (固定字段映射表) + 双向适配
- **复杂度**: O(F) F=字段数
- **状态**: adaptations list, schema_map dict

### YBankAdapter
- **算法**: utility→tier 映射 (阈值分级) + 迁移编排
- **复杂度**: O(1)
- **状态**: adaptations list, tier_map dict

---

## L16: Learning

### KnowledgeScanner
- **算法**: 源选择 + 结果生成 (简化版, 生产版需接入真实 API)
- **复杂度**: O(R) R=max_results
- **边界**: 无效源
- **状态**: scans list

### CuriosityQueue
- **算法**: heapq 优先队列 + seen-set 去重
- **复杂度**: Add O(log N), Pop O(log N)
- **状态**: queue list, seen set

### UtilityTracker
- **算法**: 按 node_id 存储值列表 + 均值
- **复杂度**: O(1)
- **状态**: tracked dict

### FiveStepEvolution
- **算法**: 5 步管道 (扫描→评估→变异→验证→整合)
- **复杂度**: O(1) per step
- **状态**: steps_log list

### DeepRetrofit
- **算法**: 依赖分析 + 影响评估 + 迁移计划生成
- **复杂度**: O(W) W=词数
- **状态**: retrofits list, dependency_map dict

---

## L17: Monitor + Services

### SystemMonitor
- **算法**: 指标记录 (deque) + 异常告警 (2×均值) + 健康评分
- **复杂度**: O(1) amortized
- **配置**: alert_threshold
- **状态**: metrics dict[metric, deque], alerts list

### OmegaServer
- **算法**: 端点注册 + 请求路由 + 健康检查
- **复杂度**: O(1)
- **状态**: endpoints dict, requests list
