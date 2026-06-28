"""DAGScheduler — DAG task scheduler with topological sort."""
from __future__ import annotations
from collections import defaultdict, deque


class DAGScheduler:
    """DAG task scheduler.

    Usage:
        scheduler = DAGScheduler()
        scheduler.add_task("deploy", dependencies=["build", "test"])
        scheduler.add_task("build")
        scheduler.add_task("test")
        order = scheduler.topological_sort()
    """

    def __init__(self):
        self._tasks: dict[str, dict] = {}
        self._dependencies: dict[str, set[str]] = defaultdict(set)
        self._dependents: dict[str, set[str]] = defaultdict(set)
        self._task_counter = 0

    def add_task(self, task_id: str, data: dict | None = None, dependencies: list[str] | None = None):
        self._tasks[task_id] = data or {}
        self._task_counter += 1
        for dep in (dependencies or []):
            self._dependencies[task_id].add(dep)
            self._dependents[dep].add(task_id)

    def topological_sort(self) -> list[str]:
        in_degree = {t: len(self._dependencies[t]) for t in self._tasks}
        queue = deque([t for t, d in in_degree.items() if d == 0])
        result = []
        while queue:
            task = queue.popleft()
            result.append(task)
            for dependent in self._dependents[task]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        if len(result) != len(self._tasks):
            raise ValueError("Cycle detected in DAG")
        return result

    def schedule(self) -> list[dict]:
        order = self.topological_sort()
        return [{"id": t, "data": self._tasks[t], "deps": list(self._dependencies[t])}
                for t in order]

    def critical_path(self) -> list[str]:
        order = self.topological_sort()
        dist = {t: 0 for t in self._tasks}
        parent = {t: None for t in self._tasks}
        for task in order:
            for dep in self._dependencies[task]:
                if dist[dep] + 1 > dist[task]:
                    dist[task] = dist[dep] + 1
                    parent[task] = dep
        end = max(dist, key=lambda t: dist[t])
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = parent[current]
        return list(reversed(path))

    def get_stats(self) -> dict:
        return {"tasks": len(self._tasks),
                "total_dependencies": sum(len(v) for v in self._dependencies.values())}
