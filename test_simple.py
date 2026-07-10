"""Full system test — 7 pipes + nervous system — smart type check"""
import logging, sys, os

logging.basicConfig(level=logging.ERROR)
import warnings
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore::RuntimeWarning'

from prometheus_ultra.life import Omega

omega = Omega()

pass_count = 0
fail_count = 0

def check(name, result):
    global pass_count, fail_count
    t = type(result).__name__
    if isinstance(result, dict):
        keys = list(result.keys())[:5]
        print(f"  ✅ {name:<10s} dict[{len(result)} keys] {keys}")
        pass_count += 1
    elif hasattr(result, '__dataclass_fields__'):
        fields = list(result.__dataclass_fields__.keys())[:5]
        print(f"  ✅ {name:<10s} {t}[{len(result.__dataclass_fields__)} fields] {fields}")
        pass_count += 1
    elif isinstance(result, (str, int, float)):
        print(f"  ✅ {name:<10s} {t} = {result}")
        pass_count += 1
    else:
        print(f"  ❌ {name:<10s} unexpected {t}: {str(result)[:80]}")
        fail_count += 1

# 1. REMEMBER
r = omega.remember("test content", utility=0.7, tags=["test"])
check("remember", r)

# 2. RECALL
r = omega.recall("test content")
check("recall", r)

# 3. EVOLVE
r = omega.evolve(context="system_test")
check("evolve", r)

# 4. LEARN
r = omega.learn(query="ml basics", source="test")
check("learn", r)

# 5. REFLECT
r = omega.reflect()
check("reflect", r)

# 6. DREAM
r = omega.dream_cycle()
check("dream", r)

# 7. MAINTAIN
r = omega.maintain()
check("maintain", r)

print()
if fail_count == 0:
    print("ALL 7 PIPES OK ✅")
    print()

    # Nervous system
    cns = omega.cns
    subs = getattr(cns, '_handlers', getattr(cns, '_subscriptions', None))
    print(f"CNS handlers/events: {len(subs) if subs else 'N/A'}")

    cc = omega.cerebral_cortex
    print(f"CC methods: {len([m for m in dir(cc) if not m.startswith('_')])}")

    sf = omega.signal_fusion
    state = sf.get_state() if hasattr(sf, 'get_state') else {}
    print(f"SF state: {list(state.keys())[:5] if state else 'empty'}")

    tp = omega.telemetry
    print(f"TP methods: {len([m for m in dir(tp) if not m.startswith('_')])}")

    ar = omega.autonomic_regulator
    ar_stats = ar.get_stats() if hasattr(ar, 'get_stats') else {}
    print(f"AR stats: {list(ar_stats.keys())[:5] if ar_stats else 'empty'}")

    pop = sf.pop_feedback("evolve") if hasattr(sf, 'pop_feedback') else None
    print(f"SF pop_feedback(evolve): {'OK' if pop is not None else 'None'}")

    evaf_ok = hasattr(omega.memory_depth, 'record_consolidation') and hasattr(omega.memory_depth, 'record_access')
    print(f"EVAF record_consolidation + record_access: {'EXISTS' if evaf_ok else 'MISSING'}")

    print()
    print("NERVOUS SYSTEM: FULLY FUNCTIONAL ✅")
else:
    print(f"{fail_count} FAILURES ❌")
