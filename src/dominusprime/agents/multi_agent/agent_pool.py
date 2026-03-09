# -*- coding: utf-8 -*-
"""Agent pool for managing sub-agent instances."""

import asyncio
import logging
from typing import Dict, List, Optional

from .communication import AgentCommunicationBus
from .models import AgentSpec
from .sub_agent import SubAgent

logger = logging.getLogger(__name__)


class AgentPool:
    """Manages a pool of reusable sub-agent instances.

    Provides:
    - Agent creation and destruction
    - Concurrent agent limits
    - Agent reuse when possible
    - Resource cleanup
    """

    def __init__(
        self,
        communication_bus: AgentCommunicationBus,
        max_concurrent: int = 5,
        agent_timeout: int = 300,
        cleanup_interval: int = 60,
    ):
        """Initialize agent pool.

        Args:
            communication_bus: Communication bus for agents
            max_concurrent: Maximum concurrent agents
            agent_timeout: Default timeout per agent (seconds)
            cleanup_interval: How often to cleanup idle agents (seconds)
        """
        self.comm_bus = communication_bus
        self.max_concurrent = max_concurrent
        self.default_timeout = agent_timeout
        self.cleanup_interval = cleanup_interval

        self._active_agents: Dict[str, SubAgent] = {}
        self._idle_agents: List[SubAgent] = []
        self._agent_counter = 0
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the agent pool and cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(
            f"AgentPool started (max_concurrent={self.max_concurrent})"
        )

    async def get_agent(
        self,
        spec: Optional[AgentSpec] = None,
        main_agent_id: str = "main",
    ) -> SubAgent:
        """Get or create an agent matching specification.

        Args:
            spec: Agent specification (None for default)
            main_agent_id: ID of main agent

        Returns:
            SubAgent instance

        Raises:
            RuntimeError: If max concurrent agents reached
        """
        async with self._lock:
            # Check if we're at capacity
            if len(self._active_agents) >= self.max_concurrent:
                raise RuntimeError(
                    f"Maximum concurrent agents ({self.max_concurrent}) "
                    "reached. Cannot spawn more agents."
                )

            # Try to reuse idle agent if specs match
            agent = await self._find_reusable_agent(spec)

            if agent is None:
                # Create new agent
                agent = await self._create_agent(spec, main_agent_id)

            self._active_agents[agent.agent_id] = agent
            logger.debug(
                f"Agent {agent.agent_id} acquired "
                f"({len(self._active_agents)} active)"
            )

            return agent

    async def _find_reusable_agent(
        self,
        spec: Optional[AgentSpec],
    ) -> Optional[SubAgent]:
        """Find an idle agent that matches the spec.

        Args:
            spec: Desired agent specification

        Returns:
            Reusable agent or None
        """
        # For now, simple implementation: no reuse
        # In full version, would match spec.tools, spec.skills, etc.
        return None

    async def _create_agent(
        self,
        spec: Optional[AgentSpec],
        main_agent_id: str,
    ) -> SubAgent:
        """Create a new sub-agent.

        Args:
            spec: Agent specification
            main_agent_id: ID of main agent

        Returns:
            Initialized SubAgent
        """
        # Generate unique ID
        self._agent_counter += 1
        agent_id = f"sub_agent_{self._agent_counter}"

        # Create default spec if not provided
        if spec is None:
            spec = AgentSpec(
                agent_id=agent_id,
                timeout=self.default_timeout,
            )
        else:
            # Use provided spec but override ID
            spec.agent_id = agent_id

        # Create and initialize agent
        agent = SubAgent(
            spec=spec,
            communication_bus=self.comm_bus,
            main_agent_id=main_agent_id,
        )

        await agent.initialize()

        logger.info(f"Created new agent {agent_id}")
        return agent

    async def release_agent(self, agent: SubAgent) -> None:
        """Release an agent back to the pool.

        Args:
            agent: Agent to release
        """
        async with self._lock:
            agent_id = agent.agent_id

            if agent_id not in self._active_agents:
                logger.warning(
                    f"Agent {agent_id} not in active pool, cannot release"
                )
                return

            # Remove from active
            del self._active_agents[agent_id]

            # Decide whether to keep for reuse or destroy
            if len(self._idle_agents) < self.max_concurrent // 2:
                # Keep for potential reuse
                self._idle_agents.append(agent)
                logger.debug(
                    f"Agent {agent_id} moved to idle pool "
                    f"({len(self._idle_agents)} idle)"
                )
            else:
                # Cleanup immediately
                await agent.cleanup()
                logger.debug(f"Agent {agent_id} cleaned up immediately")

            logger.debug(
                f"Agent {agent_id} released "
                f"({len(self._active_agents)} active)"
            )

    async def cancel_agent(self, agent_id: str) -> bool:
        """Cancel a running agent.

        Args:
            agent_id: ID of agent to cancel

        Returns:
            True if agent was cancelled, False if not found
        """
        async with self._lock:
            if agent_id not in self._active_agents:
                return False

            agent = self._active_agents[agent_id]
            await agent.cancel()
            return True

    async def cancel_all(self) -> None:
        """Cancel all running agents."""
        async with self._lock:
            agent_ids = list(self._active_agents.keys())

        for agent_id in agent_ids:
            await self.cancel_agent(agent_id)

        logger.info("All agents cancelled")

    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of idle agents."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)

                async with self._lock:
                    # Clean up all idle agents
                    while self._idle_agents:
                        agent = self._idle_agents.pop()
                        await agent.cleanup()

                    logger.debug("Idle agent cleanup completed")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in cleanup loop: {e}")

    async def shutdown(self) -> None:
        """Shutdown the agent pool."""
        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Cancel all active agents
        await self.cancel_all()

        # Cleanup all agents
        async with self._lock:
            # Active agents
            for agent in self._active_agents.values():
                await agent.cleanup()
            self._active_agents.clear()

            # Idle agents
            for agent in self._idle_agents:
                await agent.cleanup()
            self._idle_agents.clear()

        logger.info("AgentPool shut down")

    @property
    def active_count(self) -> int:
        """Get number of active agents."""
        return len(self._active_agents)

    @property
    def idle_count(self) -> int:
        """Get number of idle agents."""
        return len(self._idle_agents)

    @property
    def total_count(self) -> int:
        """Get total number of agents."""
        return len(self._active_agents) + len(self._idle_agents)

    def get_stats(self) -> dict:
        """Get pool statistics.

        Returns:
            Dictionary with pool stats
        """
        return {
            "active_agents": self.active_count,
            "idle_agents": self.idle_count,
            "total_agents": self.total_count,
            "max_concurrent": self.max_concurrent,
            "at_capacity": self.active_count >= self.max_concurrent,
        }
