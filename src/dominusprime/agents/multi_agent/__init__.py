# -*- coding: utf-8 -*-
"""Multi-Agent System for DominusPrime.

This module provides task decomposition, sub-agent spawning, and result
aggregation capabilities for handling complex multi-step tasks.

Public API:
- AgentOrchestrator: Main orchestration class
- TaskComplexityAnalyzer: Analyze task complexity
- TaskDecomposer: Decompose complex tasks
- ExecutionMonitor: Track execution progress
- SubTask, TaskResult: Data models
- TaskComplexity: Complexity levels
"""

from .agent_pool import AgentPool
from .communication import AgentCommunicationBus
from .complexity_analyzer import TaskComplexityAnalyzer
from .execution_monitor import ExecutionMonitor, ExecutionState, SubtaskProgress
from .models import (
    AgentMessage,
    AggregatedResult,
    ExecutionMode,
    MessageType,
    SubTask,
    TaskComplexity,
    TaskResult,
    TaskStatus,
)
from .orchestrator import AgentOrchestrator
from .sub_agent import SubAgent
from .task_decomposer import TaskDecomposer

__all__ = [
    # Core orchestration
    "AgentOrchestrator",
    "SubAgent",
    "AgentPool",
    "AgentCommunicationBus",
    # Task analysis
    "TaskComplexityAnalyzer",
    "TaskDecomposer",
    # Monitoring
    "ExecutionMonitor",
    "ExecutionState",
    "SubtaskProgress",
    # Data models
    "AgentMessage",
    "AggregatedResult",
    "SubTask",
    "TaskResult",
    # Enums
    "TaskComplexity",
    "TaskStatus",
    "MessageType",
    "ExecutionMode",
]
