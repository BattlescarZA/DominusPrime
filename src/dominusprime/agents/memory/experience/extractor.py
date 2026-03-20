# -*- coding: utf-8 -*-
"""Experience extractor - converts patterns into structured experiences."""

import logging
import json
import uuid
from typing import List, Dict, Any
from datetime import datetime

from agentscope.model import ChatModelBase
from agentscope.formatter import FormatterBase
from agentscope.message import Msg

from .base import (
    ExperienceType,
    LearningMoment,
    Pattern,
    ConversationAnalysis,
)
from ....database.models import Experience

logger = logging.getLogger(__name__)


class ExperienceExtractor:
    """Extracts structured experiences from patterns and learning moments."""

    def __init__(
        self,
        chat_model: ChatModelBase,
        formatter: FormatterBase
    ):
        """Initialize experience extractor.

        Args:
            chat_model: Language model for extraction
            formatter: Formatter for model inputs
        """
        self.chat_model = chat_model
        self.formatter = formatter

    async def extract_patterns(
        self,
        moments: List[LearningMoment],
        analysis: ConversationAnalysis
    ) -> List[Pattern]:
        """Extract patterns from learning moments.

        Args:
            moments: List of learning moments
            analysis: Conversation analysis

        Returns:
            List of identified patterns
        """
        patterns = []

        for moment in moments:
            if moment.category == "task_completion":
                pattern = await self._extract_task_pattern(moment, analysis)
                if pattern:
                    patterns.append(pattern)

            elif moment.category == "workflow_pattern":
                pattern = await self._extract_workflow_pattern(moment, analysis)
                if pattern:
                    patterns.append(pattern)

            elif moment.category == "user_preference":
                pattern = await self._extract_preference_pattern(moment, analysis)
                if pattern:
                    patterns.append(pattern)

        logger.info(f"Extracted {len(patterns)} patterns from {len(moments)} moments")
        return patterns

    async def create_experience(
        self,
        pattern: Pattern,
        analysis: ConversationAnalysis
    ) -> Experience:
        """Create a structured experience from a pattern.

        Args:
            pattern: Identified pattern
            analysis: Conversation analysis

        Returns:
            Structured Experience object
        """
        exp_id = f"exp_{datetime.utcnow().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"

        # Build experience content
        content = {
            "pattern_id": pattern.id,
            "description": pattern.description,
            "steps": pattern.steps,
            "context_requirements": pattern.context_requirements,
            "success_indicators": pattern.success_indicators,
            "source_session": analysis.session_id,
        }

        experience = Experience(
            id=exp_id,
            type=pattern.type.value,
            title=self._generate_title(pattern),
            description=pattern.description,
            context=pattern.context_requirements,
            content=content,
            confidence=pattern.confidence,
            frequency=pattern.frequency,
            success_rate=1.0,  # Initial success rate
            created_at=datetime.utcnow(),
            last_used=None,
            updated_at=datetime.utcnow()
        )

        logger.info(f"Created experience: {exp_id} ({experience.title})")
        return experience

    async def _extract_task_pattern(
        self,
        moment: LearningMoment,
        analysis: ConversationAnalysis
    ) -> Pattern:
        """Extract a task workflow pattern."""
        # Build steps from command patterns
        steps = []
        for i, cmd in enumerate(analysis.command_patterns, 1):
            steps.append({
                "step": i,
                "action": "execute_command",
                "details": cmd[:100]
            })

        pattern = Pattern(
            id=f"pat_{uuid.uuid4().hex[:12]}",
            type=ExperienceType.TASK_WORKFLOW,
            description=f"Task workflow using {', '.join(analysis.tools_used[:3])}",
            frequency=1,
            success_indicators=["task_completed", "no_errors"],
            steps=steps,
            context_requirements=moment.context_keywords,
            confidence=moment.importance_score
        )

        return pattern

    async def _extract_workflow_pattern(
        self,
        moment: LearningMoment,
        analysis: ConversationAnalysis
    ) -> Pattern:
        """Extract a repeated workflow pattern."""
        # Identify command sequence
        steps = []
        for i, cmd in enumerate(analysis.command_patterns, 1):
            steps.append({
                "step": i,
                "command": cmd[:50],
                "purpose": "automated_step"
            })

        pattern = Pattern(
            id=f"pat_{uuid.uuid4().hex[:12]}",
            type=ExperienceType.TASK_WORKFLOW,
            description="Repeated command sequence",
            frequency=len(analysis.command_patterns),
            success_indicators=["sequence_completed"],
            steps=steps,
            context_requirements=["automation", "workflow"],
            confidence=0.7
        )

        return pattern

    async def _extract_preference_pattern(
        self,
        moment: LearningMoment,
        analysis: ConversationAnalysis
    ) -> Pattern:
        """Extract a user preference pattern."""
        pattern = Pattern(
            id=f"pat_{uuid.uuid4().hex[:12]}",
            type=ExperienceType.PREFERENCE,
            description="User preferences",
            frequency=1,
            success_indicators=["user_satisfied"],
            steps=[{
                "preference_type": key,
                "value": value
            } for key, value in analysis.user_preferences.items()],
            context_requirements=list(analysis.user_preferences.keys()),
            confidence=0.6
        )

        return pattern

    def _generate_title(self, pattern: Pattern) -> str:
        """Generate a descriptive title for an experience."""
        if pattern.type == ExperienceType.TASK_WORKFLOW:
            return f"Workflow: {pattern.description[:50]}"
        elif pattern.type == ExperienceType.PROBLEM_SOLUTION:
            return f"Solution: {pattern.description[:50]}"
        elif pattern.type == ExperienceType.PREFERENCE:
            return "User Preferences"
        else:
            return pattern.description[:60]
