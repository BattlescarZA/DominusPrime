# -*- coding: utf-8 -*-
"""Data models for multi-agent system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional


class TaskComplexity(Enum):
    """Task complexity levels."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class ExecutionMode(Enum):
    """Task execution modes."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    CANCELLED = "cancelled"


class MessageType(Enum):
    """Agent message types."""

    TASK_ASSIGNMENT = "task_assignment"
    PROGRESS_UPDATE = "progress_update"
    RESULT = "result"
    ERROR = "error"
    QUERY = "query"
    RESPONSE = "response"
    CANCELLATION = "cancellation"


@dataclass
class SubTask:
    """Represents a decomposed subtask for execution by a sub-agent.

    Attributes:
        id: Unique identifier for the subtask
        description: What needs to be done
        dependencies: IDs of required preceding tasks
        required_tools: Tools needed for execution
        required_skills: Skills needed for execution
        estimated_complexity: Complexity level
        execution_mode: Sequential or parallel execution
        timeout: Maximum execution time in seconds
        context: Relevant context for the subtask
        metadata: Additional metadata
    """

    id: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)
    estimated_complexity: TaskComplexity = TaskComplexity.MODERATE
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    timeout: int = 300  # 5 minutes default
    context: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class TaskResult:
    """Result from a subtask execution.

    Attributes:
        subtask_id: ID of the completed subtask
        status: Execution status
        output: Main result/output from the task
        artifacts: Files created, URLs visited, etc.
        execution_time: Time taken in seconds
        errors: List of errors encountered
        logs: Execution logs
        metadata: Additional result metadata
    """

    subtask_id: str
    status: TaskStatus
    output: Any = None
    artifacts: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    logs: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class AggregatedResult:
    """Aggregated result from multiple subtask executions.

    Attributes:
        overall_status: Combined status of all subtasks
        summary: High-level overview of results
        detailed_results: Individual subtask results
        combined_artifacts: All artifacts from all subtasks
        total_execution_time: Total time taken
        recommendations: Next steps, issues found, etc.
        metadata: Additional aggregated metadata
    """

    overall_status: TaskStatus
    summary: str
    detailed_results: List[TaskResult]
    combined_artifacts: List[str] = field(default_factory=list)
    total_execution_time: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class AgentMessage:
    """Message passed between agents.

    Attributes:
        type: Type of message
        sender_id: ID of sending agent
        receiver_id: ID of receiving agent
        content: Message content/payload
        timestamp: When message was created
        metadata: Additional message metadata
    """

    type: MessageType
    sender_id: str
    receiver_id: str
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


@dataclass
class AgentSpec:
    """Specification for creating a sub-agent.

    Attributes:
        agent_id: Unique identifier
        tools: List of tool names to register
        skills: List of skill names to load
        max_iters: Maximum reasoning iterations
        timeout: Agent timeout in seconds
        context: Initial context/prompt
        metadata: Additional spec metadata
    """

    agent_id: str
    tools: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    max_iters: int = 20
    timeout: int = 300
    context: Optional[str] = None
    metadata: dict = field(default_factory=dict)
