"""Fixed runner — single process with thread pool to avoid DB lock issues."""
import sys; sys.path.insert(0, 'src')
import time, json, os, traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
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
log("FIXED RUNNER STARTED (single process + thread pool)")
log("=" * 60)

m = {"start": time.time(), "cycles": 0, "errors": 0, "ops": {}, "learnings": 0}

# Single Omega instance shared across threads
with Omega(db_path=DB) as o:
    cycle = 0
    learning_cycle = 0
    
    # Thread pool for parallel operations
    with ThreadPoolExecutor(max_workers=4) as executor:
        while True:
            cycle += 1
            m["cycles"] = cycle
            
            futures = []
            
            # === REMEMBER (parallel) ===
            for i in range(3):
                content = "C%d fact %d: %s networks evolve through %s" % (
                    cycle, i, ['neural', 'quantum', 'cognitive'][i%3],
                    ['gradient', 'attention', 'memory', 'consolidation'][i%4])
                future = executor.submit(
                    o.remember, content, 
                    utility=0.4 + (cycle*0.02) % 0.6,
                    tags=[f"c{cycle}", f"t{i%3}", "ai"]
                )
                futures.append(future)
                m["ops"]["remember"] = m["ops"].get("remember", 0) + 1
            
            # === RECALL (parallel) ===
            for q in ["neural", "quantum", f"c{cycle}", "memory"]:
                future = executor.submit(o.recall, q, limit=3)
                futures.append(future)
                m["ops"]["recall"] = m["ops"].get("recall", 0) + 1
            
            # Wait for all operations to complete
            for f in as_completed(futures):
                try:
                    result = f.result()
                except Exception as e:
                    log("ERR operation: %s" % e)
                    m["errors"] += 1
            
            # === SEQUENTIAL OPERATIONS ===
            try:
                outcome = o.evolve(f"improve {cycle}")
                m["ops"]["evolve"] = m["ops"].get("evolve", 0) + 1
            except Exception as e:
                log("ERR evolve: %s" % e)
                m["errors"] += 1
            
            # === LEARN (every 5 cycles) ===
            if cycle % 5 == 0:
                learning_cycle += 1
                try:
                    sources = [
                        (ScanSource.ARXIV, f"agent memory {learning_cycle}"),
                        (ScanSource.HACKERNEWS, f"LLM agent {learning_cycle}"),
                        (ScanSource.GITHUB, f"agent framework {learning_cycle}"),
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
                    cycle, m["errors"], m["status"]["nodes"], 
                    m["status"]["edges"], m["status"]["health"]))
            
            time.sleep(0.05)
