# -*- coding: utf-8 -*-
"""Skill generator - creates executable skills from experiences."""

import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import uuid

from agentscope.model import ChatModelBase

from .base import GeneratedSkill, ExperienceType
from ....database.models import Experience

logger = logging.getLogger(__name__)


class SkillGenerator:
    """Generates executable skills from high-confidence experiences."""

    def __init__(
        self,
        chat_model: ChatModelBase,
        skills_dir: Path
    ):
        """Initialize skill generator.

        Args:
            chat_model: Language model for skill generation
            skills_dir: Directory for generated skills
        """
        self.chat_model = chat_model
        self.skills_dir = skills_dir / "learned"
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    async def should_generate_skill(
        self,
        experience: Experience,
        min_confidence: float = 0.7,
        min_frequency: int = 3
    ) -> bool:
        """Determine if experience warrants skill generation.

        Args:
            experience: Experience to evaluate
            min_confidence: Minimum confidence threshold
            min_frequency: Minimum frequency threshold

        Returns:
            True if skill should be generated
        """
        # Check confidence
        if experience.confidence < min_confidence:
            logger.debug(
                f"Experience {experience.id} confidence too low: "
                f"{experience.confidence} < {min_confidence}"
            )
            return False

        # Check frequency
        if experience.frequency < min_frequency:
            logger.debug(
                f"Experience {experience.id} frequency too low: "
                f"{experience.frequency} < {min_frequency}"
            )
            return False

        # Only certain types should become skills
        if experience.type not in [
            ExperienceType.TASK_WORKFLOW.value,
            ExperienceType.PROBLEM_SOLUTION.value
        ]:
            logger.debug(
                f"Experience {experience.id} type not suitable: {experience.type}"
            )
            return False

        return True

    async def generate_skill(
        self,
        experience: Experience
    ) -> GeneratedSkill:
        """Generate a skill from an experience.

        Args:
            experience: Experience to convert to skill

        Returns:
            GeneratedSkill object
        """
        logger.info(f"Generating skill from experience: {experience.id}")

        # Generate skill name
        skill_name = self._generate_skill_name(experience)
        skill_id = f"skill_{uuid.uuid4().hex[:12]}"

        # Create skill content
        content = experience.content
        steps = content.get("steps", [])
        
        # Generate when-to-use guidance
        when_to_use = self._generate_when_to_use(experience)

        # Generate examples
        examples = self._generate_examples(experience)

        # Write skill file
        skill_file = await self._write_skill_file(
            skill_name,
            experience,
            steps,
            when_to_use,
            examples
        )

        skill = GeneratedSkill(
            id=skill_id,
            name=skill_name,
            file_path=str(skill_file),
            source_experiences=[experience.id],
            description=experience.description,
            when_to_use=when_to_use,
            steps=[self._format_step(s) for s in steps],
            examples=examples,
            confidence=experience.confidence,
            created_at=datetime.utcnow()
        )

        logger.info(f"Generated skill: {skill_name} at {skill_file}")
        return skill

    def _generate_skill_name(self, experience: Experience) -> str:
        """Generate a unique skill name."""
        # Clean title for filename
        base_name = experience.title.lower()
        base_name = "".join(c if c.isalnum() or c == " " else "" for c in base_name)
        base_name = base_name.replace(" ", "_")
        return base_name[:50]

    def _generate_when_to_use(self, experience: Experience) -> str:
        """Generate when-to-use guidance."""
        context_keywords = ", ".join(experience.context)
        return f"Use this skill when working with: {context_keywords}"

    def _generate_examples(self, experience: Experience) -> List[str]:
        """Generate example usage."""
        content = experience.content
        steps = content.get("steps", [])
        
        if not steps:
            return ["No examples available yet"]

        examples = []
        for step in steps[:2]:  # Show first 2 steps as examples
            if "command" in step:
                examples.append(f"$ {step['command']}")
            elif "action" in step:
                examples.append(f"Action: {step['action']}")

        return examples

    def _format_step(self, step: dict) -> str:
        """Format a step for display."""
        if "command" in step:
            return step["command"]
        elif "action" in step:
            return f"{step['action']}: {step.get('details', '')}"
        else:
            return str(step)

    async def _write_skill_file(
        self,
        skill_name: str,
        experience: Experience,
        steps: List[dict],
        when_to_use: str,
        examples: List[str]
    ) -> Path:
        """Write skill markdown file."""
        skill_file = self.skills_dir / f"{skill_name}.md"

        content = self._generate_skill_markdown(
            skill_name,
            experience,
            steps,
            when_to_use,
            examples
        )

        skill_file.write_text(content, encoding="utf-8")
        return skill_file

    def _generate_skill_markdown(
        self,
        skill_name: str,
        experience: Experience,
        steps: List[dict],
        when_to_use: str,
        examples: List[str]
    ) -> str:
        """Generate skill markdown content."""
        created_date = datetime.utcnow().strftime("%Y-%m-%d")
        
        md = f"""# {experience.title}

**Source:** Experience Distillation  
**Created:** {created_date}  
**Confidence:** {experience.confidence:.2f}  
**Usage Count:** {experience.frequency}  
**Experience ID:** {experience.id}

## Description

{experience.description}

## When to Use

{when_to_use}

## Steps

"""
        
        # Add steps
        for i, step in enumerate(steps, 1):
            step_text = self._format_step(step)
            md += f"{i}. {step_text}\n"

        md += "\n## Examples\n\n"
        
        # Add examples
        for example in examples:
            md += f"```\n{example}\n```\n\n"

        md += f"""## Related Experiences

- {experience.id}

## Notes

This skill was automatically generated from conversation patterns.  
Review and edit as needed before using in production.

---
*Generated by DominusPrime Experience Distillation*
"""
        
        return md
