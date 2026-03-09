# -*- coding: utf-8 -*-
"""Agent orchestrator for coordinating multi-agent task execution."""

import asyncio
import logging
from typing import Dict, List, Optional, Set

from .agent_pool import AgentPool
from .communication import AgentCommunicationBus
from .models import (
    AggregatedResult,
    AgentSpec,
    ExecutionMode,
    SubTask,
    TaskResult,
    TaskStatus,
)

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Coordinates multi-agent task execution.

    Manages:
    - Sub-agent spawning and lifecycle
    - Sequential and parallel execution
    - Dependency resolution
    - Result aggregation
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        agent_timeout: int = 300,
        main_agent_id: str = "main",
    ):
        """Initialize orchestrator.

        Args:
            max_concurrent: Maximum concurrent sub-agents
            agent_timeout: Default timeout per agent (seconds)
            main_agent_id: ID of the main coordinating agent
        """
        self.max_concurrent = max_concurrent
        self.agent_timeout = agent_timeout
        self.main_agent_id = main_agent_id

        self.comm_bus = AgentCommunicationBus()
        self.agent_pool = AgentPool(
            communication_bus=self.comm_bus,
            max_concurrent=max_concurrent,
            agent_timeout=agent_timeout,
        )

        self._started = False

    async def start(self) -> None:
        """Start the orchestrator."""
        if self._started:
            return

        await self.comm_bus.register_agent(self.main_agent_id)
        await self.agent_pool.start()

        self._started = True
        logger.info("AgentOrchestrator started")

    async def execute_subtasks(
        self,
        subtasks: List[SubTask],
    ) -> AggregatedResult:
        """Execute a list of subtasks with dependency management.

        Args:
            subtasks: List of subtasks to execute

        Returns:
            Aggregated result from all subtasks
        """
        if not self._started:
            await self.start()

        # Build dependency graph
        dependency_graph = self._build_dependency_graph(subtasks)

        # Execute tasks respecting dependencies
        results = await self._execute_with_dependencies(
            subtasks,
            dependency_graph,
        )

        # Aggregate results
        aggregated = await self._aggregate_results(results, subtasks)

        return aggregated

    def _build_dependency_graph(
        self,
        subtasks: List[SubTask],
    ) -> Dict[str, Set[str]]:
        """Build dependency graph from subtasks.

        Args:
            subtasks: List of subtasks

        Returns:
            Dictionary mapping task ID to set of dependency IDs
        """
        graph = {}

        for task in subtasks:
            graph[task.id] = set(task.dependencies)

        logger.debug(f"Built dependency graph: {graph}")
        return graph

    async def _execute_with_dependencies(
        self,
        subtasks: List[SubTask],
        dependency_graph: Dict[str, Set[str]],
    ) -> Dict[str, TaskResult]:
        """Execute subtasks respecting dependencies.

        Args:
            subtasks: List of subtasks
            dependency_graph: Task dependencies

        Returns:
            Dictionary mapping task ID to result
        """
        task_map = {task.id: task for task in subtasks}
        results: Dict[str, TaskResult] = {}
        completed: Set[str] = set()
        in_progress: Set[str] = set()

        while len(completed) < len(subtasks):
            # Find tasks ready to execute (dependencies met)
            ready_tasks = [
                task_id
                for task_id in task_map.keys()
                if task_id not in completed
                and task_id not in in_progress
                and dependency_graph[task_id].issubset(completed)
            ]

            if not ready_tasks:
                # Check if we're stuck (circular dependencies or all in progress)
                if in_progress:
                    # Wait for in-progress tasks
                    await asyncio.sleep(0.5)
                    continue
                else:
                    # Circular dependency detected
                    logger.error("Circular dependency detected in subtasks")
                    break

            # Determine how many to execute in parallel
            available_slots = self.max_concurrent - len(in_progress)
            tasks_to_execute = ready_tasks[:available_slots]

            # Create coroutines for parallel execution
            execution_coroutines = []
            for task_id in tasks_to_execute:
                in_progress.add(task_id)
                coro = self._execute_single_subtask(task_map[task_id])
                execution_coroutines.append((task_id, coro))

            # Execute in parallel
            if execution_coroutines:
                await self._execute_parallel_batch(
                    execution_coroutines,
                    results,
                    completed,
                    in_progress,
                )

        return results

    async def _execute_parallel_batch(
        self,
        execution_coroutines: List[tuple],
        results: Dict[str, TaskResult],
        completed: Set[str],
        in_progress: Set[str],
    ) -> None:
        """Execute a batch of tasks in parallel.

        Args:
            execution_coroutines: List of (task_id, coroutine) tuples
            results: Dictionary to store results
            completed: Set of completed task IDs
            in_progress: Set of in-progress task IDs
        """
        # Execute all coroutines concurrently
        batch_results = await asyncio.gather(
            *[coro for _, coro in execution_coroutines],
            return_exceptions=True,
        )

        # Process results
        for (task_id, _), result in zip(execution_coroutines, batch_results):
            in_progress.discard(task_id)

            if isinstance(result, Exception):
                logger.error(f"Task {task_id} failed with exception: {result}")
                # Create error result
                results[task_id] = TaskResult(
                    subtask_id=task_id,
                    status=TaskStatus.FAILURE,
                    errors=[str(result)],
                )
            else:
                results[task_id] = result

            completed.add(task_id)
            logger.info(
                f"Task {task_id} completed with status: "
                f"{results[task_id].status.value}"
            )

    async def _execute_single_subtask(
        self,
        subtask: SubTask,
    ) -> TaskResult:
        """Execute a single subtask using a sub-agent.

        Args:
            subtask: Subtask to execute

        Returns:
            TaskResult from execution
        """
        agent = None

        try:
            # Create agent spec
            spec = AgentSpec(
                agent_id=f"agent_{subtask.id}",
                tools=subtask.required_tools,
                skills=subtask.required_skills,
                timeout=subtask.timeout,
                context=subtask.context,
            )

            # Get agent from pool
            agent = await self.agent_pool.get_agent(
                spec=spec,
                main_agent_id=self.main_agent_id,
            )

            # Execute subtask
            result = await agent.execute_subtask(subtask)

            return result

        except Exception as e:
            logger.exception(f"Failed to execute subtask {subtask.id}: {e}")
            return TaskResult(
                subtask_id=subtask.id,
                status=TaskStatus.FAILURE,
                errors=[str(e)],
            )

        finally:
            # Release agent back to pool
            if agent is not None:
                await self.agent_pool.release_agent(agent)

    async def execute_parallel(
        self,
        subtasks: List[SubTask],
    ) -> List[TaskResult]:
        """Execute independent subtasks in parallel.

        Args:
            subtasks: List of independent subtasks

        Returns:
            List of task results
        """
        if not self._started:
            await self.start()

        # Execute all tasks concurrently
        execution_coroutines = [
            self._execute_single_subtask(task) for task in subtasks
        ]

        results = await asyncio.gather(
            *execution_coroutines,
            return_exceptions=True,
        )

        # Convert exceptions to error results
        processed_results = []
        for subtask, result in zip(subtasks, results):
            if isinstance(result, Exception):
                processed_results.append(
                    TaskResult(
                        subtask_id=subtask.id,
                        status=TaskStatus.FAILURE,
                        errors=[str(result)],
                    )
                )
            else:
                processed_results.append(result)

        return processed_results

    async def execute_sequential(
        self,
        subtasks: List[SubTask],
    ) -> List[TaskResult]:
        """Execute subtasks sequentially in order.

        Args:
            subtasks: List of subtasks in execution order

        Returns:
            List of task results
        """
        if not self._started:
            await self.start()

        results = []

        for subtask in subtasks:
            result = await self._execute_single_subtask(subtask)
            results.append(result)

            # Stop if a critical task fails
            if result.status == TaskStatus.FAILURE:
                logger.warning(
                    f"Sequential execution stopped due to failure "
                    f"in task {subtask.id}"
                )
                break

        return results

    async def _aggregate_results(
        self,
        results: Dict[str, TaskResult],
        subtasks: List[SubTask],
    ) -> AggregatedResult:
        """Aggregate results from multiple subtasks.

        Args:
            results: Dictionary of task results
            subtasks: Original subtasks

        Returns:
            Aggregated result
        """
        # Calculate overall status
        statuses = [r.status for r in results.values()]

        if all(s == TaskStatus.SUCCESS for s in statuses):
            overall_status = TaskStatus.SUCCESS
        elif any(s == TaskStatus.SUCCESS for s in statuses):
            overall_status = TaskStatus.PARTIAL_SUCCESS
        else:
            overall_status = TaskStatus.FAILURE

        # Collect all artifacts
        all_artifacts = []
        for result in results.values():
            all_artifacts.extend(result.artifacts)

        # Calculate total execution time
        total_time = sum(r.execution_time for r in results.values())

        # Generate summary
        summary = self._generate_summary(results, subtasks)

        # Generate recommendations
        recommendations = self._generate_recommendations(results)

        return AggregatedResult(
            overall_status=overall_status,
            summary=summary,
            detailed_results=list(results.values()),
            combined_artifacts=all_artifacts,
            total_execution_time=total_time,
            recommendations=recommendations,
        )

    def _generate_summary(
        self,
        results: Dict[str, TaskResult],
        subtasks: List[SubTask],
    ) -> str:
        """Generate human-readable summary of results.

        Args:
            results: Task results
            subtasks: Original subtasks

        Returns:
            Summary string
        """
        task_map = {t.id: t for t in subtasks}

        summary_lines = ["Multi-agent task execution completed:", ""]

        for task_id, result in results.items():
            task_desc = task_map[task_id].description[:50]
            status_symbol = "✓" if result.status == TaskStatus.SUCCESS else "✗"
            summary_lines.append(
                f"{status_symbol} {task_desc}: {result.status.value}"
            )

        return "\n".join(summary_lines)

    def _generate_recommendations(
        self,
        results: Dict[str, TaskResult],
    ) -> List[str]:
        """Generate recommendations based on results.

        Args:
            results: Task results

        Returns:
            List of recommendations
        """
        recommendations = []

        # Check for failures
        failed = [r for r in results.values() if r.status == TaskStatus.FAILURE]
        if failed:
            recommendations.append(
                f"{len(failed)} task(s) failed - review error logs"
            )

        # Check for long execution times
        slow_tasks = [r for r in results.values() if r.execution_time > 120]
        if slow_tasks:
            recommendations.append(
                f"{len(slow_tasks)} task(s) took >2 minutes - "
                "consider optimization"
            )

        return recommendations

    async def shutdown(self) -> None:
        """Shutdown the orchestrator."""
        if not self._started:
            return

        await self.agent_pool.shutdown()
        await self.comm_bus.shutdown()

        self._started = False
        logger.info("AgentOrchestrator shut down")

    def get_stats(self) -> dict:
        """Get orchestrator statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "started": self._started,
            "agent_pool": self.agent_pool.get_stats(),
        }
