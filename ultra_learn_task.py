import json, sys, os
sys.path.insert(0, '/e/Prometheus-Ultra')
os.environ['PYTHONWARNINGS'] = 'ignore'
from prometheus_ultra.life import Omega
o = Omega()
results = []
sources = [
    ('arxiv', 'agent memory systems', 3),
    ('hackernews', 'AI agent LLM', 3),
    ('github', 'agent framework', 3),
    ('wiki', 'self-evolving systems', 3),
    ('web', 'AI agent architecture memory', 5),
]
for src, qry, maxr in sources:
    try:
        r = o.learn(source=src, query=qry, max_results=maxr)
        if r and isinstance(r, dict):
            results.append({'source': src, 'total': r.get('total_results',0), 'changes': r.get('applied_changes',0)})
            print(f'OK  {src}: {r.get("total_results",0)} nodes, {r.get("applied_changes",0)} changes')
        else:
            results.append({'source': src, 'total': 0, 'changes': 0})
            print(f'FAIL {src}: empty result')
    except Exception as e:
        results.append({'source': src, 'total': 0, 'changes': 0})
        print(f'FAIL {src}: {e}')

with open('/tmp/ultra_learn_result.json', 'w') as f:
    json.dump(results, f)
ok = [r for r in results if r['total'] > 0]
print(f'DONE: {len(ok)}/{len(results)} sources successful')
