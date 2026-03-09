# -*- coding: utf-8 -*-
"""Agent-to-agent communication system."""

import asyncio
import logging
from collections import defaultdict
from typing import Dict, List, Optional

from .models import AgentMessage, MessageType

logger = logging.getLogger(__name__)


class AgentCommunicationBus:
    """Message passing system between main agent and sub-agents.

    Provides asynchronous message queues for each agent to send/receive
    messages without blocking.
    """

    def __init__(self, queue_size: int = 1000):
        """Initialize communication bus.

        Args:
            queue_size: Maximum messages per agent queue
        """
        self._queues: Dict[str, asyncio.Queue] = {}
        self._queue_size = queue_size
        self._message_history: List[AgentMessage] = []
        self._lock = asyncio.Lock()

    async def register_agent(self, agent_id: str) -> None:
        """Register an agent to receive messages.

        Args:
            agent_id: Unique agent identifier
        """
        async with self._lock:
            if agent_id not in self._queues:
                self._queues[agent_id] = asyncio.Queue(maxsize=self._queue_size)
                logger.debug(f"Registered agent {agent_id} on communication bus")

    async def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the bus.

        Args:
            agent_id: Agent identifier to remove
        """
        async with self._lock:
            if agent_id in self._queues:
                # Clear any remaining messages
                while not self._queues[agent_id].empty():
                    try:
                        self._queues[agent_id].get_nowait()
                    except asyncio.QueueEmpty:
                        break
                del self._queues[agent_id]
                logger.debug(f"Unregistered agent {agent_id} from communication bus")

    async def send_message(self, message: AgentMessage) -> bool:
        """Send a message to a specific agent.

        Args:
            message: Message to send

        Returns:
            True if message was queued successfully, False otherwise
        """
        receiver_id = message.receiver_id

        # Store in history
        self._message_history.append(message)

        # Check if receiver is registered
        if receiver_id not in self._queues:
            logger.warning(
                f"Cannot send message: receiver {receiver_id} not registered"
            )
            return False

        # Try to queue the message
        try:
            await self._queues[receiver_id].put(message)
            logger.debug(
                f"Message sent: {message.sender_id} → {receiver_id} "
                f"(type: {message.type.value})"
            )
            return True
        except asyncio.QueueFull:
            logger.error(
                f"Message queue full for agent {receiver_id}, "
                "message dropped"
            )
            return False

    async def receive_message(
        self,
        agent_id: str,
        timeout: Optional[float] = None,
    ) -> Optional[AgentMessage]:
        """Receive a message for an agent.

        Args:
            agent_id: Agent identifier
            timeout: Max time to wait for message (None = wait forever)

        Returns:
            Message if available, None if timeout
        """
        if agent_id not in self._queues:
            logger.warning(f"Agent {agent_id} not registered on bus")
            return None

        try:
            if timeout is not None:
                message = await asyncio.wait_for(
                    self._queues[agent_id].get(),
                    timeout=timeout,
                )
            else:
                message = await self._queues[agent_id].get()

            logger.debug(
                f"Message received: {message.sender_id} → {agent_id} "
                f"(type: {message.type.value})"
            )
            return message

        except asyncio.TimeoutError:
            return None

    async def broadcast(
        self,
        message: AgentMessage,
        exclude: Optional[List[str]] = None,
    ) -> int:
        """Broadcast message to all registered agents.

        Args:
            message: Message to broadcast
            exclude: List of agent IDs to exclude from broadcast

        Returns:
            Number of agents that received the message
        """
        exclude = exclude or []
        sent_count = 0

        async with self._lock:
            agent_ids = list(self._queues.keys())

        for agent_id in agent_ids:
            if agent_id not in exclude:
                # Create a copy with the correct receiver
                broadcast_msg = AgentMessage(
                    type=message.type,
                    sender_id=message.sender_id,
                    receiver_id=agent_id,
                    content=message.content,
                    timestamp=message.timestamp,
                    metadata=message.metadata,
                )
                if await self.send_message(broadcast_msg):
                    sent_count += 1

        logger.debug(f"Broadcast sent to {sent_count} agents")
        return sent_count

    async def has_messages(self, agent_id: str) -> bool:
        """Check if agent has pending messages.

        Args:
            agent_id: Agent identifier

        Returns:
            True if messages are waiting
        """
        if agent_id not in self._queues:
            return False
        return not self._queues[agent_id].empty()

    async def get_pending_count(self, agent_id: str) -> int:
        """Get number of pending messages for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Number of messages in queue
        """
        if agent_id not in self._queues:
            return 0
        return self._queues[agent_id].qsize()

    def get_message_history(
        self,
        agent_id: Optional[str] = None,
        message_type: Optional[MessageType] = None,
        limit: int = 100,
    ) -> List[AgentMessage]:
        """Get message history with optional filtering.

        Args:
            agent_id: Filter by sender or receiver ID
            message_type: Filter by message type
            limit: Maximum messages to return

        Returns:
            List of messages matching filters
        """
        filtered = self._message_history

        if agent_id:
            filtered = [
                m
                for m in filtered
                if m.sender_id == agent_id or m.receiver_id == agent_id
            ]

        if message_type:
            filtered = [m for m in filtered if m.type == message_type]

        return filtered[-limit:]

    async def clear_history(self) -> None:
        """Clear message history."""
        async with self._lock:
            self._message_history.clear()
            logger.debug("Message history cleared")

    async def shutdown(self) -> None:
        """Shutdown the communication bus."""
        async with self._lock:
            agent_ids = list(self._queues.keys())

        for agent_id in agent_ids:
            await self.unregister_agent(agent_id)

        await self.clear_history()
        logger.info("Communication bus shut down")
