"""MechanismRegistry — 机制注册表.

基于:
- "Plugin Architecture with Dependency Resolution"
  - 注册机制: 名称+元数据+依赖声明
  - 依赖解析: DAG拓扑排序
  - 生命周期: register/enable/disable/invoke
  - 健康检查: 调用统计+依赖验证

算法:
    register(name, dependencies):
        1. 创建机制条目
        2. 验证依赖(DAG无环)
        3. 设置初始状态
    
    resolve_dependencies():
        1. 构建依赖图
        2. 拓扑排序
        3. 返回执行顺序

复杂度:
    register(): O(D) 其中D=依赖数
    resolve_dependencies(): O(V+E)
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

from collections import defaultdict


class MechanismRegistry:
    """机制注册表.
    
    支持依赖解析和健康检查.
    """
    
    def __init__(self):
        """初始化."""
        self._mechanisms: dict[str, dict] = {}
        self._enabled: set[str] = set()
        self._history: list[dict] = []
        self._health_checks: list[dict] = []
    
    def register(self, name: str, data: dict | None = None,
                 dependencies: list[str] | None = None,
                 category: str = "general") -> dict:
        """注册机制.
        
        Args:
            name: 机制名称
            data: 元数据
            dependencies: 依赖列表
            category: 分类
        
        Returns:
            dict: 注册结果
        """
        deps = dependencies or []
        
        # 验证依赖是否存在
        missing_deps = [d for d in deps if d not in self._mechanisms]
        if missing_deps:
            return {
                "registered": False,
                "error": "missing_dependencies",
                "missing": missing_deps,
            }
        
        entry = {
            "name": name,
            "data": data or {},
            "dependencies": deps,
            "category": category,
            "status": "registered",
            "invoke_count": 0,
            "error_count": 0,
            "last_invoked": None,
        }
        
        self._mechanisms[name] = entry
        self._enabled.add(name)
        self._history.append({"action": "register", "name": name, "deps": deps})
        
        return {
            "registered": True,
            "name": name,
            "dependencies": deps,
            "category": category,
        }
    
    def enable(self, name: str) -> bool:
        """启用机制.
        
        Args:
            name: 机制名称
        
        Returns:
            bool: 是否成功
        """
        if name not in self._mechanisms:
            return False
        
        self._mechanisms[name]["status"] = "enabled"
        self._enabled.add(name)
        self._history.append({"action": "enable", "name": name})
        return True
    
    def disable(self, name: str) -> bool:
        """禁用机制.
        
        Args:
            name: 机制名称
        
        Returns:
            bool: 是否成功
        """
        if name not in self._mechanisms:
            return False
        
        self._mechanisms[name]["status"] = "disabled"
        self._enabled.discard(name)
        self._history.append({"action": "disable", "name": name})
        return True
    
    def invoke(self, name: str, context: dict | None = None) -> bool:
        """调用机制.
        
        Args:
            name: 机制名称
            context: 上下文
        
        Returns:
            bool: 是否成功
        """
        if name not in self._enabled:
            return False
        
        self._mechanisms[name]["invoke_count"] += 1
        import time
        self._mechanisms[name]["last_invoked"] = time.time()
        
        return True
    
    def resolve_dependencies(self) -> list[str]:
        """解析依赖顺序(拓扑排序).
        
        Returns:
            list: 执行顺序(字符串列表)
        """
        # 构建邻接表
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        for name, mech in self._mechanisms.items():
            if name not in in_degree:
                in_degree[name] = 0
            for dep in mech["dependencies"]:
                graph[dep].append(name)
                in_degree[name] += 1
        
        # Kahn算法
        queue = [n for n in self._mechanisms if in_degree[n] == 0]
        order = []
        
        while queue:
            node = queue.pop(0)
            order.append(node)
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 检测环
        if len(order) != len(self._mechanisms):
            return []  # 有环,返回空
        
        return order
    
    def health_check(self) -> dict:
        """健康检查.
        
        Returns:
            dict: 健康报告
        """
        issues = []
        
        # 检查孤立机制(未被依赖且从未调用)
        depended_on = set()
        for name, mech in self._mechanisms.items():
            for dep in mech["dependencies"]:
                depended_on.add(dep)
        
        for name in self._enabled:
            if self._mechanisms[name]["invoke_count"] == 0 and name not in depended_on:
                issues.append({"type": "unused", "mechanism": name})
        
        # 检查环依赖
        order = self.resolve_dependencies()
        if len(order) < len(self._mechanisms):
            issues.append({"type": "circular_dependency", "total": len(self._mechanisms), "resolved": len(order)})
        
        report = {
            "healthy": len(issues) == 0,
            "issues": issues,
            "total_mechanisms": len(self._mechanisms),
            "enabled": len(self._enabled),
            "total_invocations": sum(m["invoke_count"] for m in self._mechanisms.values()),
        }
        
        self._health_checks.append(report)
        return report
    
    def get_stats(self) -> dict:
        """获取统计."""
        categories = {}
        for mech in self._mechanisms.values():
            cat = mech["category"]
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "registered": len(self._mechanisms),
            "enabled": len(self._enabled),
            "categories": categories,
            "history_size": len(self._history),
            "total_invocations": sum(m["invoke_count"] for m in self._mechanisms.values()),
        }
