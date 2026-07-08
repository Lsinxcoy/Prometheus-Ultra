"""MultiAgentSystem — 多代理协调与任务分配.

基于:
- "Contract Net Protocol for Multi-Agent Task Allocation" (Davis, 1980)
  - 合同网协议: 任务招标+投标+分配
  - 能力匹配: 根据代理能力分配任务
  - 负载均衡: 避免过载
  - 共识机制: 投票/多数决策

算法:
    allocate_task(task, agents):
        1. 广播任务请求
        2. 收集投标(能力评分)
        3. 选择最佳投标者
        4. 确认分配
    
    consensus_vote(agents, options):
        1. 收集投票
        2. 加权计票
        3. 返回共识结果

复杂度:
    allocate_task(): O(N) N=代理数
    consensus_vote(): O(N×M) M=选项数
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

import time
import random
from collections import defaultdict


class MultiAgentSystem:
    """多代理协调系统 — 合同网协议+共识决策.
    
    管理代理注册、任务分配和集体决策.
    """
    
    def __init__(self, load_threshold: float = 0.8):
        """初始化.
        
        Args:
            load_threshold: 负载阈值,超过则不接受新任务
        """
        self._load_threshold = load_threshold
        self._agents: dict[str, dict] = {}
        self._allocations: list[dict] = []
        self._votes: list[dict] = []
    
    def register_agent(self, agent_id: str, capabilities: list[str],
                       capacity: int = 10) -> dict:
        """注册代理.
        
        Args:
            agent_id: 代理ID
            capabilities: 能力列表
            capacity: 最大并发任务数
        
        Returns:
            dict: 代理信息
        """
        agent = {
            "id": agent_id,
            "capabilities": set(capabilities),
            "capacity": capacity,
            "current_load": 0,
            "success_count": 0,
            "total_tasks": 0,
            "reputation": 1.0,
            "registered_at": time.time(),
        }
        self._agents[agent_id] = agent
        return {
            "id": agent_id,
            "capabilities": capabilities,
            "capacity": capacity,
            "reputation": 1.0,
        }
    
    def allocate_task(self, task: str | dict, required_cap: str | list[str] | None = None) -> dict:
        """分配任务(合同网协议).
        
        Args:
            task: 任务描述 (str 或 dict 含 'required_capabilities')
            required_cap: 所需能力 (str 或 list)
        
        Returns:
            dict: 分配结果
        """
        # 兼容 dict 输入
        if isinstance(task, dict):
            required_caps = task.get("required_capabilities", [])
            task_str = str(task.get("task", str(task)))
        else:
            required_caps = [required_cap] if required_cap else []
            task_str = task
        
        if not required_caps:
            required_caps = ["general"]
        candidates = []
        
        for agent_id, agent in self._agents.items():
            # 能力匹配
            if not any(rc in agent["capabilities"] for rc in required_caps):
                continue
            
            # 负载检查
            load_ratio = agent["current_load"] / max(agent["capacity"], 1)
            if load_ratio >= self._load_threshold:
                continue
            
            # 计算投标得分
            score = (
                agent["reputation"] * 0.4 +
                (1 - load_ratio) * 0.3 +
                min(agent["success_count"] / 10, 1.0) * 0.3
            )
            
            candidates.append({
                "agent_id": agent_id,
                "score": round(score, 4),
                "load_ratio": round(load_ratio, 4),
                "reputation": agent["reputation"],
            })
        
        if not candidates:
            return {
                "allocated": False,
                "reason": "no suitable agent available",
                "required_caps": required_caps,
            }
        
        # 选择最高分
        candidates.sort(key=lambda x: x["score"], reverse=True)
        winner = candidates[0]
        winner_id = winner["agent_id"]
        
        # 更新代理状态
        self._agents[winner_id]["current_load"] += 1
        self._agents[winner_id]["total_tasks"] += 1
        
        allocation = {
            "allocated": True,
            "agent_id": winner_id,
            "task": task_str[:100],
            "score": winner["score"],
            "candidates": len(candidates),
            "ts": time.time(),
        }
        
        self._allocations.append(allocation)
        if len(self._allocations) > 500:
            self._allocations = self._allocations[-250:]
        
        return allocation
    
    def complete_task(self, agent_id: str, success: bool = True) -> dict:
        """完成任务.
        
        Args:
            agent_id: 代理ID
            success: 是否成功
        
        Returns:
            dict: 更新结果
        """
        agent = self._agents.get(agent_id)
        if not agent:
            return {"error": "agent not found"}
        
        agent["current_load"] = max(0, agent["current_load"] - 1)
        
        if success:
            agent["success_count"] += 1
            agent["reputation"] = min(1.0, agent["reputation"] * 0.99 + 0.01)
        else:
            agent["reputation"] = max(0.0, agent["reputation"] * 0.95 - 0.03)
        
        return {
            "agent_id": agent_id,
            "current_load": agent["current_load"],
            "reputation": round(agent["reputation"], 4),
            "success_rate": round(
                agent["success_count"] / max(agent["total_tasks"], 1), 4
            ),
        }
    
    def consensus_vote(self, agent_ids: list[str], options: list[str],
                       weights: dict[str, float] | None = None) -> dict:
        """共识投票.
        
        Args:
            agent_ids: 投票代理ID列表
            options: 选项列表
            weights: 代理权重
        
        Returns:
            dict: 投票结果
        """
        scores: dict[str, float] = {opt: 0.0 for opt in options}
        votes = []
        
        for agent_id in agent_ids:
            agent = self._agents.get(agent_id)
            if not agent:
                continue
            
            # 模拟投票(基于声誉加权随机)
            weight = (weights or {}).get(agent_id, agent["reputation"])
            chosen = random.choices(options, weights=[1.0] * len(options), k=1)[0]
            scores[chosen] += weight
            
            votes.append({
                "agent_id": agent_id,
                "vote": chosen,
                "weight": round(weight, 4),
            })
        
        # 找出获胜者
        winner = max(scores, key=scores.get) if scores else None
        total_weight = sum(scores.values())
        
        result = {
            "winner": winner,
            "scores": {k: round(v, 4) for k, v in scores.items()},
            "total_participants": len(votes),
            "total_weight": round(total_weight, 4),
            "margin": round(
                (scores[winner] / max(total_weight, 1)) if winner and total_weight > 0 else 0, 4
            ),
            "ts": time.time(),
        }
        
        self._votes.append(result)
        if len(self._votes) > 200:
            self._votes = self._votes[-100:]
        
        return result
    
    def _deliberate_assembly(self, task_description: str,
                             available_agents: list[dict],
                             required_caps: list[str],
                             min_panel_size: int = 3) -> list[str]:
        """CAMP: 案例自适应动态专家组装 (arXiv 2604.00085).

        按案例需求动态组装专家团，不做静态角色划分。

        Args:
            task_description: 任务描述
            available_agents: 可用代理列表
            required_caps: 所需能力列表
            min_panel_size: 最小专家团大小

        Returns:
            选中的agent_id列表
        """
        if not available_agents:
            return []

        scored = []
        for agent in available_agents:
            caps = agent.get("capabilities", set())
            if isinstance(caps, list):
                caps = set(caps)

            # 能力匹��分数
            cap_score = sum(1 for rc in required_caps if rc in caps) / max(len(required_caps), 1)
            # 声誉分数
            rep_score = agent.get("reputation", 0.5)
            # 负载分数
            load = agent.get("current_load", 0)
            capacity = agent.get("capacity", 10)
            load_score = 1.0 - (load / max(capacity, 1))

            total = cap_score * 0.5 + rep_score * 0.3 + load_score * 0.2
            scored.append((total, agent["id"]))

        scored.sort(key=lambda x: -x[0])
        selected = [sid for _, sid in scored[:max(min_panel_size, len(required_caps))]]
        return selected

    def _three_value_vote(self, options: list[str],
                           agents: list[dict]) -> dict:
        """CAMP: 三值投票（支持/反对/弃权），弃权比强制投票更有信息量。

        Args:
            options: 选项列表
            agents: 代理列表（含id, reputation）

        Returns:
            投票结果 dict
        """
        scores = {opt: {"for": 0.0, "against": 0.0, "abstain": 0.0}
                  for opt in options}

        for agent in agents:
            aid = agent["id"]
            rep = agent.get("reputation", 0.5)
            for opt in options:
                # 有rep一定概率弃权（低rep更可能弃权）
                abstain_prob = 1.0 - rep
                if random.random() < abstain_prob:
                    scores[opt]["abstain"] += rep
                elif random.random() < 0.7:  # 70%支持（匹配的）
                    scores[opt]["for"] += rep
                else:
                    scores[opt]["against"] += rep

        # 计算净得分
        net_scores = {}
        for opt, s in scores.items():
            net_scores[opt] = round(s["for"] - s["against"], 4)

        winner = max(net_scores, key=net_scores.get) if net_scores else None

        return {
            "winner": winner,
            "scores": scores,
            "net_scores": net_scores,
            "total_participants": len(agents),
        }

    def reach_consensus(self, options: list[dict], agent_ids: list[str] | None = None) -> dict:
        """达成共识 (兼容别名)."""
        if not options:
            return {"winner": None, "scores": {}, "total_participants": 0}
        if agent_ids is None:
            agent_ids = list(self._agents.keys())
        if not agent_ids:
            return {"winner": None, "scores": {}, "total_participants": 0}
        opt_values = [o.get("value", str(o)) for o in options]
        return self.consensus_vote(agent_ids, opt_values)
    
    def get_stats(self) -> dict:
        """获取统计."""
        return {
            "agents": len(self._agents),
            "total_allocations": len(self._allocations),
            "total_votes": len(self._votes),
            "avg_reputation": round(
                sum(a["reputation"] for a in self._agents.values()) / max(len(self._agents), 1), 4
            ),
            "total_load": sum(a["current_load"] for a in self._agents.values()),
        }
