# -*- coding: utf-8 -*-
"""SubAgent wrapper for isolated task execution."""

import asyncio
import logging
from typing import TYPE_CHECKING, Any, List, Optional

from agentscope.message import Msg

from .communication import AgentCommunicationBus
from .models import (
    AgentMessage,
    AgentSpec,
    MessageType,
    SubTask,
    TaskResult,
    TaskStatus,
)

if TYPE_CHECKING:
    from ..react_agent import DominusPrimeAgent

logger = logging.getLogger(__name__)


class SubAgent:
    """Wrapper around DominusPrimeAgent for isolated subtask execution.

    Provides:
    - Limited scope (only sees subtask context)
    - Resource limits (timeout, max iterations)
    - Progress reporting to main agent
    - Cancellation support
    """

    def __init__(
        self,
        spec: AgentSpec,
        communication_bus: AgentCommunicationBus,
        main_agent_id: str = "main",
    ):
        """Initialize SubAgent.

        Args:
            spec: Agent specification
            communication_bus: Communication bus for messaging
            main_agent_id: ID of the main coordinating agent
        """
        self.agent_id = spec.agent_id
        self.spec = spec
        self.comm_bus = communication_bus
        self.main_agent_id = main_agent_id

        self._agent: Optional["DominusPrimeAgent"] = None
        self._task: Optional[asyncio.Task] = None
        self._cancelled = False
        self._start_time: Optional[float] = None
        self._result: Optional[TaskResult] = None

    async def initialize(self) -> None:
        """Initialize the underlying agent."""
        # Lazy import to avoid circular dependency
        from ..react_agent import DominusPrimeAgent
        
        # Create agent with limited resources
        self._agent = DominusPrimeAgent(
            env_context=self.spec.context,
            enable_memory_manager=False,  # No memory manager for sub-agents
            max_iters=self.spec.max_iters,
        )

        # Register specific tools only
        # (In full implementation, would filter toolkit based on spec.tools)

        # Register on communication bus
        await self.comm_bus.register_agent(self.agent_id)

        logger.info(f"SubAgent {self.agent_id} initialized")

    async def execute_subtask(self, subtask: SubTask) -> TaskResult:
        """Execute a subtask.

        Args:
            subtask: Subtask to execute

        Returns:
            TaskResult with output and metadata
        """
        if self._agent is None:
            raise RuntimeError("SubAgent not initialized. Call initialize() first.")

        self._start_time = asyncio.get_event_loop().time()

        # Create initial message for the subtask
        initial_msg = Msg(
            name="user",
            content=subtask.description,
            role="user",
        )

        try:
            # Execute with timeout
            self._task = asyncio.create_task(
                self._execute_with_progress(initial_msg, subtask)
            )

            result = await asyncio.wait_for(
                self._task,
                timeout=subtask.timeout,
            )

            self._result = result
            return result

        except asyncio.TimeoutError:
            logger.warning(
                f"SubAgent {self.agent_id} timed out after {subtask.timeout}s"
            )
            await self.cancel()
            return self._create_timeout_result(subtask)

        except asyncio.CancelledError:
            logger.info(f"SubAgent {self.agent_id} was cancelled")
            return self._create_cancelled_result(subtask)

        except Exception as e:
            logger.exception(f"SubAgent {self.agent_id} execution failed: {e}")
            return self._create_error_result(subtask, str(e))

    async def _execute_with_progress(
        self,
        initial_msg: Msg,
        subtask: SubTask,
    ) -> TaskResult:
        """Execute subtask with progress reporting.

        Args:
            initial_msg: Initial message for the agent
            subtask: Subtask being executed

        Returns:
            TaskResult from execution
        """
        output_text = ""
        artifacts = []
        logs = []

        # Send progress update: started
        await self._send_progress_update("started", 0)

        try:
            # Execute agent reasoning
            response = await self._agent([initial_msg])

            # Extract output
            if response and hasattr(response, "content"):
                output_text = str(response.content)

            # Send progress update: completed
            await self._send_progress_update("completed", 100)

            execution_time = asyncio.get_event_loop().time() - self._start_time

            return TaskResult(
                subtask_id=subtask.id,
                status=TaskStatus.SUCCESS,
                output=output_text,
                artifacts=artifacts,
                execution_time=execution_time,
                errors=[],
                logs="\n".join(logs),
            )

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - self._start_time

            return TaskResult(
                subtask_id=subtask.id,
                status=TaskStatus.FAILURE,
                output=output_text,
                artifacts=artifacts,
                execution_time=execution_time,
                errors=[str(e)],
                logs="\n".join(logs),
            )

    async def _send_progress_update(
        self,
        status: str,
        percentage: int,
    ) -> None:
        """Send progress update to main agent.

        Args:
            status: Current status description
            percentage: Completion percentage (0-100)
        """
        message = AgentMessage(
            type=MessageType.PROGRESS_UPDATE,
            sender_id=self.agent_id,
            receiver_id=self.main_agent_id,
            content={
                "status": status,
                "percentage": percentage,
            },
        )
        await self.comm_bus.send_message(message)

    def _create_timeout_result(self, subtask: SubTask) -> TaskResult:
        """Create result for timeout case."""
        execution_time = asyncio.get_event_loop().time() - self._start_time

        return TaskResult(
            subtask_id=subtask.id,
            status=TaskStatus.FAILURE,
            output=None,
            execution_time=execution_time,
            errors=[f"Task timed out after {subtask.timeout} seconds"],
        )

    def _create_cancelled_result(self, subtask: SubTask) -> TaskResult:
        """Create result for cancellation case."""
        execution_time = (
            asyncio.get_event_loop().time() - self._start_time
            if self._start_time
            else 0
        )

        return TaskResult(
            subtask_id=subtask.id,
            status=TaskStatus.CANCELLED,
            output=None,
            execution_time=execution_time,
            errors=["Task was cancelled"],
        )

    def _create_error_result(self, subtask: SubTask, error: str) -> TaskResult:
        """Create result for error case."""
        execution_time = (
            asyncio.get_event_loop().time() - self._start_time
            if self._start_time
            else 0
        )

        return TaskResult(
            subtask_id=subtask.id,
            status=TaskStatus.FAILURE,
            output=None,
            execution_time=execution_time,
            errors=[error],
        )

    async def cancel(self) -> None:
        """Cancel the running task."""
        if self._task and not self._task.done():
            self._cancelled = True
            self._task.cancel()

            # Send cancellation message
            message = AgentMessage(
                type=MessageType.CANCELLATION,
                sender_id=self.agent_id,
                receiver_id=self.main_agent_id,
                content="Task cancelled",
            )
            await self.comm_bus.send_message(message)

            logger.info(f"SubAgent {self.agent_id} cancelled")

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._agent is not None:
            # Cleanup agent resources if needed
            pass

        await self.comm_bus.unregister_agent(self.agent_id)
        logger.debug(f"SubAgent {self.agent_id} cleaned up")

    @property
    def is_running(self) -> bool:
        """Check if agent is currently executing."""
        return self._task is not None and not self._task.done()

    @property
    def result(self) -> Optional[TaskResult]:
        """Get the execution result if available."""
        return self._result
