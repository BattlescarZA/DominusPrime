# -*- coding: utf-8 -*-
"""
Skill Template Generator - Create skill templates from successful trajectories.

Generates YAML frontmatter + Markdown skill content from execution patterns.
"""

import logging
from typing import Dict, List, Optional
from .trajectory_tracker import Trajectory, ToolCall

logger = logging.getLogger(__name__)


class SkillTemplateGenerator:
    """Generates skill content from trajectories."""
    
    def generate_skill_from_trajectory(
        self,
        trajectory: Trajectory,
        skill_name: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Generate a skill template from a trajectory.
        
        Args:
            trajectory: Successful trajectory to convert
            skill_name: Optional skill name (auto-generated if not provided)
            category: Optional category
            
        Returns:
            Dict with 'name', 'category', and 'content' keys
        """
        # Generate skill name from task description
        if not skill_name:
            skill_name = self._generate_skill_name(trajectory.task_description)
        
        # Infer category from tools used
        if not category:
            category = self._infer_category(trajectory)
        
        # Build frontmatter
        frontmatter = self._build_frontmatter(
            skill_name=skill_name,
            category=category,
            trajectory=trajectory,
        )
        
        # Build content
        content = self._build_content(trajectory)
        
        # Combine
        full_content = f"{frontmatter}\n{content}"
        
        return {
            "name": skill_name,
            "category": category,
            "content": full_content,
        }
    
    def _generate_skill_name(self, task_description: str) -> str:
        """Generate skill name from task description."""
        # Simple approach: take first few words, lowercase, hyphenate
        words = task_description.lower().split()[:4]
        # Remove common words
        stopwords = {"the", "a", "an", "to", "for", "with", "using", "how", "and"}
        words = [w for w in words if w not in stopwords]
        name = "-".join(words[:3])
        
        # Clean up
        name = "".join(c if c.isalnum() or c == "-" else "-" for c in name)
        name = name.strip("-")
        
        return name or "generated-skill"
    
    def _infer_category(self, trajectory: Trajectory) -> str:
        """Infer skill category from tools used."""
        tools = trajectory.get_tool_names()
        
        # Simple heuristics
        if any("file" in t.lower() or "read" in t.lower() or "write" in t.lower() for t in tools):
            return "development"
        elif any("search" in t.lower() or "web" in t.lower() for t in tools):
            return "research"
        elif any("shell" in t.lower() or "execute" in t.lower() for t in tools):
            return "system"
        else:
            return "general"
    
    def _build_frontmatter(
        self,
        skill_name: str,
        category: str,
        trajectory: Trajectory,
    ) -> str:
        """Build YAML frontmatter."""
        description = trajectory.task_description[:200]  # Truncate
        tools = list(set(trajectory.get_tool_names()))
        
        frontmatter = f"""---
name: {skill_name}
description: {description}
category: {category}
platforms:
  - linux
  - darwin
  - windows
required_tools: {tools}
tags:
  - auto-generated
  - trajectory-based
created_from: task execution pattern
---"""
        
        return frontmatter
    
    def _build_content(self, trajectory: Trajectory) -> str:
        """Build markdown content."""
        lines = [
            f"# {trajectory.task_description}",
            "",
            "**Auto-generated skill from successful task execution.**",
            "",
            "## Overview",
            "",
            f"This skill captures the procedure for: {trajectory.task_description}",
            f"",
            f"- **Tools used**: {len(trajectory.tool_calls)}",
            f"- **Duration**: {trajectory.duration():.2f} seconds",
            f"- **Success rate**: Based on {self._get_repetition_note(trajectory)}",
            "",
            "## Procedure",
            "",
        ]
        
        # Add steps from tool calls
        for i, call in enumerate(trajectory.tool_calls, 1):
            lines.append(f"### Step {i}: {call.tool_name}")
            lines.append("")
            
            # Add arguments (sanitized)
            if call.arguments:
                lines.append("**Parameters:**")
                lines.append("```json")
                lines.append(self._sanitize_arguments(call.arguments))
                lines.append("```")
                lines.append("")
            
            if call.success:
                lines.append("✅ Step completed successfully")
            else:
                lines.append(f"❌ Step failed: {call.error}")
            
            lines.append("")
        
        # Add outcome
        if trajectory.outcome:
            lines.extend([
                "## Outcome",
                "",
                trajectory.outcome,
                "",
            ])
        
        # Add usage notes
        lines.extend([
            "## Usage",
            "",
            "This skill was automatically generated from a successful task execution.",
            "You may need to adapt the parameters and steps for your specific use case.",
            "",
            "**To use this skill:**",
            f"1. Load it: `await skills(action=\"view\", name=\"{trajectory.metadata.get('skill_name', 'this-skill')}\")`",
            "2. Follow the procedure steps above",
            "3. Adapt parameters as needed for your context",
            "",
            "## Notes",
            "",
            "- Review and verify each step before execution",
            "- This skill may need refinement based on your specific requirements",
            "- Consider adding error handling and edge cases",
        ])
        
        return "\n".join(lines)
    
    def _sanitize_arguments(self, args: Dict) -> str:
        """Sanitize arguments for display (remove sensitive data)."""
        import json
        
        # Create sanitized copy
        sanitized = {}
        for key, value in args.items():
            # Hide potential sensitive keys
            if any(word in key.lower() for word in ["password", "token", "secret", "key", "api"]):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, str) and len(value) > 100:
                sanitized[key] = value[:100] + "..."
            else:
                sanitized[key] = value
        
        return json.dumps(sanitized, indent=2)
    
    def _get_repetition_note(self, trajectory: Trajectory) -> str:
        """Get note about how often this pattern was seen."""
        # This would need access to tracker's pattern_counts
        # For now, just return generic note
        return "observed successful execution"


__all__ = [
    "SkillTemplateGenerator",
]
