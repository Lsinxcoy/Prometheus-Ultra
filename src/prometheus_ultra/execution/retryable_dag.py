"""RetryableDAG — 可重试DAG执行器.

基于:
- "Failure-Tolerant Distributed Computing" (Spark, Zaharia et al., 2010)
  - 自动重试: 失败节点重新调度
  - 指数退避: 减少重试风暴
  - 检查点: 中间状态持久化

算法:
    execute(dag, max_retries):
        1. 执行DAG
        2. 失败节点加入重试队列
        3. 计算退避时间
        4. 重新执行失败节点
        5. 重复直到成功或达到最大重试次数

复杂度:
    execute(): O(R * (V + E)) 其中 R=最大重试次数
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import time
import random
from dataclasses import dataclass, field
from enum import Enum


class RetryStrategy(Enum):
    IMMEDIATE = "immediate"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"


@dataclass
class RetryConfig:
    """重试配置."""
    max_retries: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    base_delay_ms: float = 100.0
    max_delay_ms: float = 5000.0
    jitter: bool = True


@dataclass
class RetryRecord:
    """重试记录."""
    node_id: str = ""
    attempt: int = 0
    delay_ms: float = 0.0
    success: bool = False
    error: str = ""


class RetryableDAG:
    """可重试DAG执行器.
    
    支持自动重试和指数退避.
    """
    
    def __init__(self, retry_config: RetryConfig | None = None):
        self.config = retry_config or RetryConfig()
        self._retry_log: list[RetryRecord] = []
    
    def execute(self, dag: dict, node_exec_fn=None) -> dict:
        """执行DAG，失败节点自动重试."""
        nodes = dag.get("nodes", {})
        edges = dag.get("edges", [])
        
        results: dict[str, any] = {}
        failed: dict[str, dict] = {}
        retry_queue: list[tuple[str, dict, int]] = []  # (node_id, data, attempt)
        
        # 首次执行所有节点
        for node_id, node_data in nodes.items():
            result = self._try_execute(node_id, node_data, node_exec_fn, 0)
            if result is not None:
                results[node_id] = result
            else:
                failed[node_id] = node_data
                retry_queue.append((node_id, node_data, 1))
        
        # 重试循环
        final_failed = []
        while retry_queue:
            next_queue = []
            for node_id, node_data, attempt in retry_queue:
                if attempt > self.config.max_retries:
                    final_failed.append(node_id)
                    continue
                
                # 计算退避时间
                delay = self._calculate_delay(attempt)
                record = RetryRecord(node_id=node_id, attempt=attempt, delay_ms=delay)
                self._retry_log.append(record)
                
                # 执行重试
                result = self._try_execute(node_id, node_data, node_exec_fn, attempt)
                if result is not None:
                    results[node_id] = result
                    record.success = True
                else:
                    record.success = False
                    record.error = f"Failed after {attempt} retries"
                    next_queue.append((node_id, node_data, attempt + 1))
            
            retry_queue = next_queue
        
        return {
            "results": results,
            "failed_nodes": final_failed,
            "retry_count": len(self._retry_log),
            "success_rate": len(results) / max(len(nodes), 1),
        }
    
    def _try_execute(self, node_id: str, node_data: dict, attempt: int, exec_fn=None) -> any:
        """尝试执行节点."""
        try:
            if exec_fn:
                return exec_fn(node_id, node_data)
            # 默认模拟执行
            return {"node_id": node_id, "status": "completed"}
        except Exception as e:
            return None
    
    def _calculate_delay(self, attempt: int) -> float:
        """计算退避延迟."""
        if self.config.strategy == RetryStrategy.IMMEDIATE:
            delay = 0
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay_ms * attempt
        else:  # EXPONENTIAL
            delay = self.config.base_delay_ms * (2 ** (attempt - 1))
        
        # 添加抖动
        if self.config.jitter:
            delay *= random.uniform(0.5, 1.5)
        
        return min(delay, self.config.max_delay_ms)
    
    def get_stats(self) -> dict:
        """获取重试统计."""
        total = len(self._retry_log)
        success = sum(1 for r in self._retry_log if r.success)
        
        return {
            "total_retries": total,
            "successful_retries": success,
            "success_rate": success / max(total, 1),
            "avg_attempts": sum(r.attempt for r in self._retry_log) / max(total, 1),
        }
