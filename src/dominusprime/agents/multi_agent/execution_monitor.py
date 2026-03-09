# -*- coding: utf-8 -*-
"""Execution Monitor for tracking multi-agent system execution."""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Callable

from agentscope.message import Msg


class ExecutionState(Enum):
    """Execution state for monitoring."""

    IDLE = "idle"
    ANALYZING = "analyzing"
    DECOMPOSING = "decomposing"
    SPAWNING = "spawning"
    EXECUTING = "executing"
    AGGREGATING = "aggregating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SubtaskProgress:
    """Progress tracking for a single subtask."""

    subtask_id: str
    description: str
    state: str = "pending"  # pending, running, completed, failed
    progress_percentage: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    agent_id: Optional[str] = None
    current_iteration: int = 0
    max_iterations: int = 20
    last_update: str = ""
    error: Optional[str] = None

    @property
    def duration(self) -> Optional[float]:
        """Calculate duration in seconds."""
        if self.start_time is None:
            return None
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def is_running(self) -> bool:
        """Check if subtask is currently running."""
        return self.state == "running"

    @property
    def is_completed(self) -> bool:
        """Check if subtask completed successfully."""
        return self.state == "completed"

    @property
    def is_failed(self) -> bool:
        """Check if subtask failed."""
        return self.state == "failed"


@dataclass
class ExecutionMetrics:
    """Metrics for execution monitoring."""

    total_subtasks: int = 0
    completed_subtasks: int = 0
    failed_subtasks: int = 0
    running_subtasks: int = 0
    pending_subtasks: int = 0
    total_time: float = 0.0
    avg_subtask_time: float = 0.0
    active_agents: int = 0
    messages_sent: int = 0
    errors_encountered: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_subtasks == 0:
            return 0.0
        return (self.completed_subtasks / self.total_subtasks) * 100

    @property
    def completion_percentage(self) -> float:
        """Calculate overall completion percentage."""
        if self.total_subtasks == 0:
            return 0.0
        finished = self.completed_subtasks + self.failed_subtasks
        return (finished / self.total_subtasks) * 100


@dataclass
class ExecutionSnapshot:
    """Snapshot of execution state at a point in time."""

    timestamp: float
    state: ExecutionState
    metrics: ExecutionMetrics
    subtask_progress: Dict[str, SubtaskProgress]
    logs: List[str] = field(default_factory=list)


class ExecutionMonitor:
    """Monitors and tracks multi-agent execution progress.
    
    Provides real-time tracking of:
    - Overall execution state
    - Individual subtask progress
    - Resource usage and metrics
    - Error tracking
    - Execution logs
    """

    def __init__(self, enable_streaming: bool = True):
        """Initialize execution monitor.
        
        Args:
            enable_streaming: Enable real-time progress streaming
        """
        self.enable_streaming = enable_streaming
        self.state = ExecutionState.IDLE
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
        # Tracking data
        self.subtask_progress: Dict[str, SubtaskProgress] = {}
        self.execution_logs: List[str] = []
        self.error_logs: List[str] = []
        
        # Metrics
        self.metrics = ExecutionMetrics()
        
        # Streaming callbacks
        self.progress_callbacks: List[Callable] = []
        self.state_change_callbacks: List[Callable] = []
        
        # Snapshot history
        self.snapshots: List[ExecutionSnapshot] = []
        self.max_snapshots = 100

    def register_progress_callback(self, callback: Callable):
        """Register callback for progress updates.
        
        Args:
            callback: Async function to call with progress updates
        """
        self.progress_callbacks.append(callback)

    def register_state_change_callback(self, callback: Callable):
        """Register callback for state changes.
        
        Args:
            callback: Async function to call on state changes
        """
        self.state_change_callbacks.append(callback)

    async def set_state(self, new_state: ExecutionState):
        """Update execution state.
        
        Args:
            new_state: New execution state
        """
        old_state = self.state
        self.state = new_state
        
        self._log(f"State change: {old_state.value} → {new_state.value}")
        
        # Handle state transitions
        if new_state == ExecutionState.EXECUTING and self.start_time is None:
            self.start_time = time.time()
        elif new_state in [ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.CANCELLED]:
            self.end_time = time.time()
            if self.start_time:
                self.metrics.total_time = self.end_time - self.start_time
        
        # Notify callbacks
        for callback in self.state_change_callbacks:
            try:
                await callback(old_state, new_state)
            except Exception as e:
                self._log_error(f"State change callback error: {e}")
        
        # Create snapshot
        self._create_snapshot()

    def initialize_subtasks(self, subtasks: List[any]):
        """Initialize tracking for subtasks.
        
        Args:
            subtasks: List of SubTask objects
        """
        self.metrics.total_subtasks = len(subtasks)
        self.metrics.pending_subtasks = len(subtasks)
        
        for subtask in subtasks:
            self.subtask_progress[subtask.id] = SubtaskProgress(
                subtask_id=subtask.id,
                description=subtask.description,
                state="pending",
            )
        
        self._log(f"Initialized tracking for {len(subtasks)} subtasks")
        self._create_snapshot()

    async def start_subtask(self, subtask_id: str, agent_id: str):
        """Mark subtask as started.
        
        Args:
            subtask_id: ID of the subtask
            agent_id: ID of the agent executing the subtask
        """
        if subtask_id in self.subtask_progress:
            progress = self.subtask_progress[subtask_id]
            progress.state = "running"
            progress.start_time = time.time()
            progress.agent_id = agent_id
            progress.progress_percentage = 0
            
            self.metrics.running_subtasks += 1
            self.metrics.pending_subtasks -= 1
            
            self._log(f"Subtask {subtask_id} started by agent {agent_id}")
            await self._notify_progress_update(subtask_id)

    async def update_subtask_progress(
        self,
        subtask_id: str,
        percentage: int,
        status: str,
        iteration: Optional[int] = None,
    ):
        """Update subtask progress.
        
        Args:
            subtask_id: ID of the subtask
            percentage: Progress percentage (0-100)
            status: Status message
            iteration: Current iteration number
        """
        if subtask_id in self.subtask_progress:
            progress = self.subtask_progress[subtask_id]
            progress.progress_percentage = min(100, max(0, percentage))
            progress.last_update = status
            
            if iteration is not None:
                progress.current_iteration = iteration
            
            await self._notify_progress_update(subtask_id)

    async def complete_subtask(self, subtask_id: str, success: bool, error: Optional[str] = None):
        """Mark subtask as completed.
        
        Args:
            subtask_id: ID of the subtask
            success: Whether subtask completed successfully
            error: Error message if failed
        """
        if subtask_id in self.subtask_progress:
            progress = self.subtask_progress[subtask_id]
            progress.state = "completed" if success else "failed"
            progress.end_time = time.time()
            progress.progress_percentage = 100 if success else progress.progress_percentage
            
            if error:
                progress.error = error
                self._log_error(f"Subtask {subtask_id} failed: {error}")
            
            self.metrics.running_subtasks -= 1
            
            if success:
                self.metrics.completed_subtasks += 1
                self._log(f"Subtask {subtask_id} completed in {progress.duration:.2f}s")
            else:
                self.metrics.failed_subtasks += 1
                self.metrics.errors_encountered += 1
            
            # Update average time
            if self.metrics.completed_subtasks > 0:
                total_time = sum(
                    p.duration for p in self.subtask_progress.values()
                    if p.is_completed and p.duration
                )
                self.metrics.avg_subtask_time = total_time / self.metrics.completed_subtasks
            
            await self._notify_progress_update(subtask_id)
            self._create_snapshot()

    def update_active_agents(self, count: int):
        """Update count of active agents.
        
        Args:
            count: Number of currently active agents
        """
        self.metrics.active_agents = count

    def increment_messages_sent(self):
        """Increment message counter."""
        self.metrics.messages_sent += 1

    def get_current_status(self) -> str:
        """Get formatted current status.
        
        Returns:
            Human-readable status string
        """
        if self.state == ExecutionState.IDLE:
            return "⏸️ Idle"
        
        if self.state == ExecutionState.ANALYZING:
            return "🔍 Analyzing task complexity..."
        
        if self.state == ExecutionState.DECOMPOSING:
            return "🧩 Breaking down task into subtasks..."
        
        if self.state == ExecutionState.SPAWNING:
            return f"🤖 Spawning {self.metrics.pending_subtasks} sub-agents..."
        
        if self.state == ExecutionState.EXECUTING:
            progress_pct = self.metrics.completion_percentage
            return (
                f"⚡ Executing: {self.metrics.completed_subtasks}/{self.metrics.total_subtasks} "
                f"complete ({progress_pct:.1f}%)"
            )
        
        if self.state == ExecutionState.AGGREGATING:
            return "📊 Aggregating results..."
        
        if self.state == ExecutionState.COMPLETED:
            return f"✅ Completed successfully in {self.metrics.total_time:.2f}s"
        
        if self.state == ExecutionState.FAILED:
            return f"❌ Failed with {self.metrics.errors_encountered} error(s)"
        
        if self.state == ExecutionState.CANCELLED:
            return "🛑 Cancelled by user"
        
        return f"State: {self.state.value}"

    def get_detailed_progress(self) -> str:
        """Get detailed progress report.
        
        Returns:
            Formatted progress report
        """
        lines = [
            f"\n**Execution Status**: {self.get_current_status()}",
            f"**Total Subtasks**: {self.metrics.total_subtasks}",
            f"**Completed**: {self.metrics.completed_subtasks} ✅",
            f"**Failed**: {self.metrics.failed_subtasks} ❌",
            f"**Running**: {self.metrics.running_subtasks} ⚡",
            f"**Pending**: {self.metrics.pending_subtasks} ⏳",
            f"**Success Rate**: {self.metrics.success_rate:.1f}%",
        ]
        
        if self.metrics.active_agents > 0:
            lines.append(f"**Active Agents**: {self.metrics.active_agents}")
        
        if self.start_time:
            elapsed = (self.end_time or time.time()) - self.start_time
            lines.append(f"**Elapsed Time**: {elapsed:.2f}s")
        
        if self.metrics.avg_subtask_time > 0:
            lines.append(f"**Avg Subtask Time**: {self.metrics.avg_subtask_time:.2f}s")
        
        # Show running subtasks
        running = [p for p in self.subtask_progress.values() if p.is_running]
        if running:
            lines.append("\n**Currently Running**:")
            for progress in running:
                lines.append(
                    f"- {progress.description} "
                    f"({progress.progress_percentage}%, "
                    f"iter {progress.current_iteration}/{progress.max_iterations})"
                )
        
        return "\n".join(lines)

    def _log(self, message: str):
        """Add log entry.
        
        Args:
            message: Log message
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.execution_logs.append(log_entry)
        
        # Keep last 1000 logs
        if len(self.execution_logs) > 1000:
            self.execution_logs = self.execution_logs[-1000:]

    def _log_error(self, message: str):
        """Add error log entry.
        
        Args:
            message: Error message
        """
        self._log(f"ERROR: {message}")
        self.error_logs.append(message)

    async def _notify_progress_update(self, subtask_id: str):
        """Notify callbacks of progress update.
        
        Args:
            subtask_id: ID of updated subtask
        """
        if not self.enable_streaming:
            return
        
        progress = self.subtask_progress.get(subtask_id)
        if not progress:
            return
        
        for callback in self.progress_callbacks:
            try:
                await callback(subtask_id, progress)
            except Exception as e:
                self._log_error(f"Progress callback error: {e}")

    def _create_snapshot(self):
        """Create execution snapshot."""
        snapshot = ExecutionSnapshot(
            timestamp=time.time(),
            state=self.state,
            metrics=ExecutionMetrics(**self.metrics.__dict__),
            subtask_progress={
                k: SubtaskProgress(**v.__dict__)
                for k, v in self.subtask_progress.items()
            },
            logs=self.execution_logs[-10:],  # Last 10 logs
        )
        
        self.snapshots.append(snapshot)
        
        # Keep max snapshots
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots = self.snapshots[-self.max_snapshots:]

    def get_snapshot_history(self) -> List[ExecutionSnapshot]:
        """Get historical snapshots.
        
        Returns:
            List of execution snapshots
        """
        return self.snapshots.copy()

    def reset(self):
        """Reset monitor to idle state."""
        self.state = ExecutionState.IDLE
        self.start_time = None
        self.end_time = None
        self.subtask_progress.clear()
        self.execution_logs.clear()
        self.error_logs.clear()
        self.metrics = ExecutionMetrics()
        self.snapshots.clear()
