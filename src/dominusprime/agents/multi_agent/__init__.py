# -*- coding: utf-8 -*-
"""Multi-Agent System for DominusPrime.

This module provides task decomposition, sub-agent spawning, and result
aggregation capabilities for handling complex multi-step tasks.

Public API:
- AgentOrchestrator: Main orchestration class
- SubTask, TaskResult: Data models
- TaskComplexity: Complexity levels
"""

from .models import (
    AgentMessage,
    AggregatedResult,
    SubTask,
    TaskComplexity,
    TaskResult,
)
from .orchestrator import AgentOrchestrator

__all__ = [
    "AgentOrchestrator",
    "AgentMessage",
    "AggregatedResult",
    "SubTask",
    "TaskComplexity",
    "TaskResult",
]
