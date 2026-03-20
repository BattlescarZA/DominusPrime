# -*- coding: utf-8 -*-
"""Conversation analyzer for experience distillation."""

import logging
from typing import List, Optional
from datetime import datetime
import uuid

from agentscope.message import Msg
from agentscope.model import ChatModelBase

from .base import (
    ConversationAnalysis,
    LearningMoment,
    ExperienceType,
)

logger = logging.getLogger(__name__)


class ConversationAnalyzer:
    """Analyzes conversations to identify learning opportunities."""

    def __init__(self, chat_model: ChatModelBase):
        """Initialize conversation analyzer.

        Args:
            chat_model: Language model for analysis
        """
        self.chat_model = chat_model

    async def analyze_conversation(
        self,
        messages: List[Msg],
        session_id: str
    ) -> ConversationAnalysis:
        """Analyze a conversation for learning potential.

        Args:
            messages: List of conversation messages
            session_id: Session identifier

        Returns:
            ConversationAnalysis with extracted insights
        """
        logger.info(f"Analyzing conversation {session_id} with {len(messages)} messages")

        # Extract task outcomes
        successful_tasks = await self._identify_successful_tasks(messages)
        failed_tasks = await self._identify_failed_tasks(messages)

        # Extract user preferences
        preferences = await self._extract_preferences(messages)

        # Identify technical topics
        topics = await self._identify_topics(messages)

        # Track tool usage
        tools_used = self._extract_tools_used(messages)

        # Extract command patterns
        command_patterns = self._extract_command_patterns(messages)

        analysis = ConversationAnalysis(
            session_id=session_id,
            total_messages=len(messages),
            successful_tasks=successful_tasks,
            failed_tasks=failed_tasks,
            user_preferences=preferences,
            technical_topics=topics,
            tools_used=tools_used,
            command_patterns=command_patterns,
            analysis_timestamp=datetime.utcnow()
        )

        logger.info(
            f"Analysis complete: {len(successful_tasks)} successful tasks, "
            f"{len(topics)} topics, {len(tools_used)} tools"
        )

        return analysis

    async def identify_learning_moments(
        self,
        analysis: ConversationAnalysis
    ) -> List[LearningMoment]:
        """Identify specific moments worth extracting as experiences.

        Args:
            analysis: Conversation analysis result

        Returns:
            List of learning moments
        """
        moments = []

        # Successful task completions are high-value learning moments
        for task in analysis.successful_tasks:
            moment = LearningMoment(
                id=f"lm_{uuid.uuid4().hex[:12]}",
                timestamp=analysis.analysis_timestamp,
                messages=[],  # Will be populated with relevant message subset
                category="task_completion",
                importance_score=0.8,
                context_keywords=analysis.technical_topics[:5]
            )
            moments.append(moment)

        # Repeated patterns are worth capturing
        if len(analysis.command_patterns) > 2:
            moment = LearningMoment(
                id=f"lm_{uuid.uuid4().hex[:12]}",
                timestamp=analysis.analysis_timestamp,
                messages=[],
                category="workflow_pattern",
                importance_score=0.7,
                context_keywords=["automation", "workflow"]
            )
            moments.append(moment)

        # User preferences are important
        if analysis.user_preferences:
            moment = LearningMoment(
                id=f"lm_{uuid.uuid4().hex[:12]}",
                timestamp=analysis.analysis_timestamp,
                messages=[],
                category="user_preference",
                importance_score=0.6,
                context_keywords=list(analysis.user_preferences.keys())
            )
            moments.append(moment)

        logger.info(f"Identified {len(moments)} learning moments")
        return moments

    async def _identify_successful_tasks(
        self,
        messages: List[Msg]
    ) -> List[str]:
        """Identify successfully completed tasks."""
        # Use LLM to identify task completions
        # For now, simple heuristic: look for positive outcomes
        tasks = []
        
        for i, msg in enumerate(messages):
            if msg.role == "user" and i + 1 < len(messages):
                response = messages[i + 1]
                if response.role == "assistant":
                    # Check for success indicators
                    content = str(response.content).lower()
                    if any(indicator in content for indicator in [
                        "successfully",
                        "completed",
                        "done",
                        "✓",
                        "✅"
                    ]):
                        task_desc = str(msg.content)[:100]
                        tasks.append(task_desc)

        return tasks

    async def _identify_failed_tasks(
        self,
        messages: List[Msg]
    ) -> List[str]:
        """Identify failed or problematic tasks."""
        tasks = []
        
        for i, msg in enumerate(messages):
            if msg.role == "assistant":
                content = str(msg.content).lower()
                if any(indicator in content for indicator in [
                    "error",
                    "failed",
                    "couldn't",
                    "unable to",
                    "❌"
                ]):
                    if i > 0:
                        task_desc = str(messages[i - 1].content)[:100]
                        tasks.append(task_desc)

        return tasks

    async def _extract_preferences(
        self,
        messages: List[Msg]
    ) -> dict:
        """Extract user preferences from conversation."""
        preferences = {}
        
        # Look for explicit preferences
        for msg in messages:
            if msg.role == "user":
                content = str(msg.content).lower()
                
                # Preference indicators
                if "i prefer" in content or "i like" in content:
                    preferences["stated_preference"] = content[:200]
                
                # Tool choices
                if "use" in content and ("python" in content or "node" in content):
                    preferences["preferred_language"] = "extracted from usage"

        return preferences

    async def _identify_topics(
        self,
        messages: List[Msg]
    ) -> List[str]:
        """Identify technical topics discussed."""
        topics = set()
        
        # Common technical keywords
        tech_keywords = {
            "python", "javascript", "docker", "git", "api",
            "database", "sql", "web", "server", "client",
            "frontend", "backend", "deployment", "testing"
        }
        
        for msg in messages:
            content = str(msg.content).lower()
            for keyword in tech_keywords:
                if keyword in content:
                    topics.add(keyword)

        return list(topics)

    def _extract_tools_used(self, messages: List[Msg]) -> List[str]:
        """Extract tools that were used in conversation."""
        tools = set()
        
        for msg in messages:
            # Check if message has tool calls
            if hasattr(msg, 'content') and isinstance(msg.content, list):
                for block in msg.content:
                    if hasattr(block, 'type') and block.type == "tool_use":
                        tools.add(block.name if hasattr(block, 'name') else "unknown")

        return list(tools)

    def _extract_command_patterns(self, messages: List[Msg]) -> List[str]:
        """Extract shell command patterns."""
        commands = []
        
        for msg in messages:
            content = str(msg.content)
            # Look for common command indicators
            if "execute_shell_command" in content or "```bash" in content:
                # Extract command (simplified)
                commands.append(content[:100])

        return commands
