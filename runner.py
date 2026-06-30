"""Enhanced runner — exercises all mechanisms continuously."""
import sys; sys.path.insert(0, 'src')
import time, json, os, traceback
from prometheus_ultra import Omega
from prometheus_ultra.loop.loop_selector import LoopStrategy
from prometheus_ultra.loop.tree_of_thoughts import SearchStrategy
from prometheus_ultra.governance.human_oversight import RiskLevel
from prometheus_ultra.prompt.structured_output import SchemaField
from prometheus_ultra.prompt.xml_tag import PromptSection
from prometheus_ultra.prompt.reasoning_adapter import ModelType
from prometheus_ultra.learning.scanner import ScanSource

BASE = os.path.dirname(os.path.abspath(__file__))
METRICS = os.path.join(BASE, "metrics.json")
LOG = os.path.join(BASE, "runtime.log")
DB = os.path.join(BASE, "runner.db")

def log(msg):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write("[%s] %s\n" % (time.strftime('%H:%M:%S'), msg))

def save(m):
    with open(METRICS, 'w', encoding='utf-8') as f:
        json.dump(m, f, indent=2)

log("=" * 60)
log("ENHANCED RUNNER STARTED")
log("=" * 60)

m = {"start": time.time(), "cycles": 0, "errors": 0, "ops": {}, "learnings": 0}

with Omega(db_path=DB) as o:
    cycle = 0
    learning_cycle = 0

    while True:
        cycle += 1
        m["cycles"] = cycle

        # === REMEMBER ===
        for i in range(3):
            try:
                content = "C%d fact %d: %s networks evolve through %s" % (
                    cycle, i, ['neural', 'quantum', 'cognitive'][i%3],
                    ['gradient', 'attention', 'memory', 'consolidation'][i%4])
                nid = o.remember(content, utility=0.4 + (cycle*0.02) % 0.6,
                                tags=["c%d" % cycle, "t%d" % (i%3), "ai"])
                m["ops"]["remember"] = m["ops"].get("remember", 0) + 1
            except Exception as e:
                log("ERR remember: %s" % e)
                m["errors"] += 1

        # === RECALL ===
        for q in ["neural", "quantum", "c%d" % cycle, "memory"]:
            try:
                results = o.recall(q, limit=3)
                m["ops"]["recall"] = m["ops"].get("recall", 0) + 1
            except Exception as e:
                log("ERR recall: %s" % e)
                m["errors"] += 1

        # === EVOLVE ===
        try:
            outcome = o.evolve("improve %d" % cycle)
            m["ops"]["evolve"] = m["ops"].get("evolve", 0) + 1
        except Exception as e:
            log("ERR evolve: %s" % e)
            m["errors"] += 1

        # === LEARN (every 5 cycles) ===
        if cycle % 5 == 0:
            learning_cycle += 1
            try:
                sources = [
                    (ScanSource.ARXIV, "agent memory %d" % learning_cycle),
                    (ScanSource.HACKERNEWS, "LLM agent %d" % learning_cycle),
                    (ScanSource.GITHUB, "agent framework %d" % learning_cycle),
                ]
                for source, query in sources:
                    result = o.learn(source.value, query, max_results=2)
                    m["ops"]["learn"] = m["ops"].get("learn", 0) + 1
                    m["learnings"] += result.get("new_nodes", 0)
            except Exception as e:
                log("ERR learn: %s" % e)
                m["errors"] += 1

        # === REFLECT ===
        try:
            report = o.reflect()
            m["ops"]["reflect"] = m["ops"].get("reflect", 0) + 1
        except Exception as e:
            log("ERR reflect: %s" % e)
            m["errors"] += 1

        # === DREAM ===
        try:
            dream = o.dream_cycle()
            m["ops"]["dream"] = m["ops"].get("dream", 0) + 1
        except Exception as e:
            log("ERR dream: %s" % e)
            m["errors"] += 1

        # === MAINTAIN ===
        try:
            maintain = o.maintain()
            m["ops"]["maintain"] = m["ops"].get("maintain", 0) + 1
        except Exception as e:
            log("ERR maintain: %s" % e)
            m["errors"] += 1

        # === NEW MODULES (15) ===
        try:
            o.tree_of_thoughts.search("p%d" % cycle, strategy=SearchStrategy.BFS)
            o.think_tool.run(task="t%d" % cycle, context="ctx")
            o.context_clash.detect(["x%d" % i for i in range(3)])
            o.context_poisoning.add_chunk("ch%d" % cycle, confidence=0.5)
            o.context_poisoning.mark_as_cited("ch%d" % cycle)
            o.context_poisoning.detect()
            o.tool_overload.register_tool("tool_%d" % cycle)
            o.tool_overload.detect()
            o.tool_overload.unregister_tool("tool_%d" % cycle)
            o.context_window.register_component("w%d" % cycle, cycle*100, priority=5)
            o.context_window.check()
            req = o.human_oversight.submit_action("a%d" % cycle, RiskLevel.LOW)
            _ = o.human_oversight.needs_human(req)
            r = o.structured_output.validate('{"k":"v"}', [SchemaField("k","string")])
            _ = o.structured_output.generate_schema_prompt([SchemaField("t","string")])
            p = o.xml_tag.build([PromptSection("task", "t%d" % cycle)])
            _ = o.xml_tag.extract_all_sections(p)
            _ = o.reasoning_adapter.adapt("think step by step %d" % cycle, ModelType.REASONING)
            _ = o.progressive_complexity.assess("t%d" % cycle, context_tokens=cycle*1000)
            o.crash_restore.save_checkpoint({"c": cycle})
            _ = o.crash_restore.restore_latest()
            snap = o.context_isolator.create_snapshot(["c%d" % i for i in range(3)], "t%d" % cycle)
            _ = o.context_isolator.merge(snap, ["f%d" % i for i in range(2)])
            o.memory_side_effect.set_current_task("t%d" % cycle)
            o.memory_side_effect.observe_retrieval("info%d" % cycle)
            _ = o.memory_side_effect.detect()
            m["ops"]["new_modules"] = m["ops"].get("new_modules", 0) + 1
        except Exception as e:
            log("ERR new_modules: %s" % e)
            m["errors"] += 1

        # === MiMo MECHANISMS ===
        try:
            chain_results = o.five_gate_chain.check_all(
                "content %d" % cycle, utility=0.7, novelty=0.6,
                trust_score=0.8, delta=0.1, drift_score=0.05, risk_level=0.2)
            oep = o.oep_defense.check("finding %d" % cycle, source="arxiv", transferable=True)
            o.utility_decay.apply_decay(days_elapsed=1)
            usage = min(1.0, o.store.get_node_count() / 5000)
            level = o.progressive_checkpoints.should_save(usage)
            if level:
                o.progressive_checkpoints.save_checkpoint(level, usage, {"nodes": o.store.get_node_count()})
            o.tool_drift.record_tool_use("learn")
            o.evo_quality_gates.record_step("cycle", "output %d" % cycle, information_gain=0.5)
            hb_results = o.heartbeat_4cycle.run_cycles()
            m["ops"]["mimo"] = m["ops"].get("mimo", 0) + 1
        except Exception as e:
            log("ERR mimo: %s" % e)
            m["errors"] += 1

        # === STATUS ===
        try:
            s = o.status()
            m["status"] = {"health": s.health, "nodes": s.node_count,
                          "edges": s.edge_count, "uptime": s.uptime_seconds}
        except Exception as e:
            log("ERR status: %s" % e)
            m["errors"] += 1

        save(m)

        if cycle % 10 == 0:
            log("STATUS c=%d err=%d nodes=%d edges=%d health=%s" % (
                cycle, m["errors"], m["status"]["nodes"], m["status"]["edges"], m["status"]["health"]))

        time.sleep(0.05)
