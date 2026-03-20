# -*- coding: utf-8 -*-
"""Experience system - main coordinator for experience distillation."""

import logging
from typing import List, Optional
from pathlib import Path

from agentscope.model import ChatModelBase
from agentscope.formatter import FormatterBase
from agentscope.message import Msg

from .analyzer import ConversationAnalyzer
from .extractor import ExperienceExtractor
from .skill_generator import SkillGenerator
from .knowledge_base import ExperienceKnowledgeBase
from .base import GeneratedSkill
from ....database.connection import DatabaseManager
from ....database.models import Experience

logger = logging.getLogger(__name__)


class ExperienceSystem:
    """Main coordinator for experience distillation and skill extraction."""

    def __init__(
        self,
        working_dir: Path,
        chat_model: ChatModelBase,
        formatter: FormatterBase,
        db_manager: DatabaseManager
    ):
        """Initialize experience system.

        Args:
            working_dir: Working directory path
            chat_model: Language model for analysis
            formatter: Formatter for model inputs
            db_manager: Database manager
        """
        self.working_dir = Path(working_dir)
        self.chat_model = chat_model
        self.formatter = formatter
        
        # Initialize components
        self.analyzer = ConversationAnalyzer(chat_model)
        self.extractor = ExperienceExtractor(chat_model, formatter)
        self.skill_generator = SkillGenerator(
            chat_model,
            self.working_dir / "skills"
        )
        self.knowledge_base = ExperienceKnowledgeBase(db_manager)
        
        logger.info("ExperienceSystem initialized")

    async def distill_experiences(
        self,
        messages: List[Msg],
        session_id: str
    ) -> List[Experience]:
        """Distill experiences from conversation history.

        This is the main entry point for experience distillation.

        Args:
            messages: List of conversation messages
            session_id: Session identifier

        Returns:
            List of extracted experiences
        """
        logger.info(
            f"Starting experience distillation for session {session_id} "
            f"({len(messages)} messages)"
        )

        # Step 1: Analyze conversation
        analysis = await self.analyzer.analyze_conversation(messages, session_id)

        # Step 2: Identify learning moments
        moments = await self.analyzer.identify_learning_moments(analysis)

        if not moments:
            logger.info("No learning moments identified")
            return []

        # Step 3: Extract patterns from moments
        patterns = await self.extractor.extract_patterns(moments, analysis)

        if not patterns:
            logger.info("No patterns extracted")
            return []

        # Step 4: Create experiences from patterns
        experiences = []
        for pattern in patterns:
            experience = await self.extractor.create_experience(pattern, analysis)
            
            # Store in knowledge base
            stored = await self.knowledge_base.store_experience(experience)
            if stored:
                experiences.append(experience)

        logger.info(f"Distilled {len(experiences)} experiences")
        return experiences

    async def generate_skills(
        self,
        min_confidence: float = 0.7,
        min_frequency: int = 3
    ) -> List[GeneratedSkill]:
        """Generate skills from high-confidence experiences.

        Args:
            min_confidence: Minimum confidence threshold
            min_frequency: Minimum frequency threshold

        Returns:
            List of generated skills
        """
        logger.info(
            f"Generating skills (confidence >= {min_confidence}, "
            f"frequency >= {min_frequency})"
        )

        # Get high-confidence experiences
        experiences = await self.knowledge_base.list_experiences(
            min_confidence=min_confidence,
            limit=100
        )

        skills = []
        for experience in experiences:
            # Check if should generate skill
            should_generate = await self.skill_generator.should_generate_skill(
                experience,
                min_confidence,
                min_frequency
            )

            if should_generate:
                skill = await self.skill_generator.generate_skill(experience)
                skills.append(skill)

        logger.info(f"Generated {len(skills)} skills")
        return skills

    async def suggest_skills(
        self,
        context: str,
        max_results: int = 5
    ) -> List[GeneratedSkill]:
        """Suggest relevant skills for current context.

        Args:
            context: Current context description
            max_results: Maximum results to return

        Returns:
            List of relevant generated skills
        """
        # Extract keywords from context
        keywords = context.lower().split()

        # Search experiences
        experiences = await self.knowledge_base.search_experiences(
            keywords,
            limit=max_results
        )

        # Convert to skills (if they exist)
        skills = []
        for exp in experiences:
            # Check if skill was already generated
            # (This would be tracked in generated_skills table)
            # For now, return experience info
            pass

        return skills

    async def get_statistics(self) -> dict:
        """Get experience system statistics.

        Returns:
            Dictionary with statistics
        """
        kb_stats = await self.knowledge_base.get_statistics()
        
        return {
            "knowledge_base": kb_stats,
            "skills_directory": str(self.skill_generator.skills_dir),
        }
