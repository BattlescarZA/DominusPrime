# -*- coding: utf-8 -*-
"""
Skill Approval Workflow - Interactive confirmation for auto-generated skills.

Provides user interface for reviewing and approving auto-generated skills.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Callable, Any
from .trajectory_tracker import Trajectory
from .skill_template_generator import SkillTemplateGenerator

logger = logging.getLogger(__name__)


class SkillApprovalWorkflow:
    """
    Manages user approval for auto-generated skills.
    
    Presents skill previews and handles user decisions.
    """
    
    def __init__(
        self,
        template_generator: Optional[SkillTemplateGenerator] = None,
        auto_approve: bool = False,
        storage_dir: Optional[Path] = None,
    ):
        """
        Initialize approval workflow.
        
        Args:
            template_generator: Template generator instance
            auto_approve: Skip approval and auto-create skills
            storage_dir: Directory to save approved skills
        """
        self.template_generator = template_generator or SkillTemplateGenerator()
        self.auto_approve = auto_approve
        self.storage_dir = storage_dir
        
        # Statistics
        self.proposed_count = 0
        self.approved_count = 0
        self.rejected_count = 0
    
    async def propose_skill(
        self,
        trajectory: Trajectory,
        callback: Optional[Callable[[Dict[str, Any]], Any]] = None,
    ) -> Optional[Dict[str, str]]:
        """
        Propose a skill to the user for approval.
        
        Args:
            trajectory: Successful trajectory to create skill from
            callback: Optional callback for user interaction
            
        Returns:
            Skill dict if approved, None if rejected
        """
        self.proposed_count += 1
        
        # Generate skill template
        skill_data = self.template_generator.generate_skill_from_trajectory(trajectory)
        
        # Auto-approve mode
        if self.auto_approve:
            logger.info(f"Auto-approved skill: {skill_data['name']}")
            self.approved_count += 1
            
            # Save if storage_dir provided
            if self.storage_dir:
                self._save_skill(skill_data)
            
            return skill_data
        
        # Build proposal message
        proposal = self._build_proposal_message(skill_data, trajectory)
        
        # If callback provided, use it for interactive approval
        if callback:
            decision = await callback(proposal)
            
            if decision.get("approved"):
                self.approved_count += 1
                
                # Apply user edits if provided
                if decision.get("edits"):
                    skill_data = self._apply_edits(skill_data, decision["edits"])
                
                logger.info(f"User approved skill: {skill_data['name']}")
                
                # Save if storage_dir provided
                if self.storage_dir:
                    self._save_skill(skill_data)
                
                return skill_data
            else:
                self.rejected_count += 1
                logger.info(f"User rejected skill: {skill_data['name']}")
                return None
        
        # No callback - return for agent to handle
        return {
            **skill_data,
            "proposal_message": proposal,
            "requires_approval": True,
        }
    
    def _build_proposal_message(
        self,
        skill_data: Dict[str, str],
        trajectory: Trajectory,
    ) -> str:
        """Build approval proposal message."""
        lines = [
            "## 🎯 Skill Creation Opportunity Detected",
            "",
            f"I've identified a reusable procedure based on your recent task:",
            f"**{trajectory.task_description}**",
            "",
            "### Proposed Skill",
            "",
            f"- **Name**: `{skill_data['name']}`",
            f"- **Category**: {skill_data['category']}",
            f"- **Steps**: {len(trajectory.tool_calls)}",
            f"- **Pattern frequency**: Seen {self._get_pattern_note(trajectory)}",
            "",
            "### Preview",
            "",
            "```markdown",
            skill_data['content'][:500] + "...",  # Preview first 500 chars
            "```",
            "",
            "### Would you like me to create this skill?",
            "",
            "**Options:**",
            "1. ✅ **Approve** - Create the skill as-is",
            "2. ✏️ **Edit** - Modify the skill before creating",
            "3. ❌ **Reject** - Skip this skill",
            "",
            f"Use: `await skill_manage(action=\"create\", name=\"{skill_data['name']}\", content=\"...\")` to approve",
        ]
        
        return "\n".join(lines)
    
    def _get_pattern_note(self, trajectory: Trajectory) -> str:
        """Get note about pattern frequency."""
        # Would need tracker access for accurate count
        return "in successful execution"
    
    def _apply_edits(
        self,
        skill_data: Dict[str, str],
        edits: Dict[str, Any],
    ) -> Dict[str, str]:
        """Apply user edits to skill data."""
        if "name" in edits:
            skill_data["name"] = edits["name"]
        if "category" in edits:
            skill_data["category"] = edits["category"]
        if "content" in edits:
            skill_data["content"] = edits["content"]
        
        return skill_data
    
    def get_stats(self) -> Dict[str, int]:
        """Get approval statistics."""
        return {
            "proposed": self.proposed_count,
            "approved": self.approved_count,
            "rejected": self.rejected_count,
            "approval_rate": (
                self.approved_count / self.proposed_count
                if self.proposed_count > 0
                else 0.0
            ),
        }
    
    def reset_stats(self) -> None:
        """Reset approval statistics."""
        self.proposed_count = 0
        self.approved_count = 0
        self.rejected_count = 0
    
    def _save_skill(self, skill_data: Dict[str, str]) -> None:
        """Save approved skill to disk."""
        if not self.storage_dir:
            return
        
        try:
            # Create skill directory
            category = skill_data["category"]
            name = skill_data["name"]
            skill_dir = self.storage_dir / category / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            
            # Save skill file
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(skill_data["content"], encoding="utf-8")
            
            logger.info(f"Saved skill to {skill_file}")
        except Exception as e:
            logger.error(f"Failed to save skill: {e}", exc_info=True)


# Convenience function for quick skill proposal
def propose_skill_from_trajectory(
    trajectory: Trajectory,
    auto_approve: bool = False,
) -> Dict[str, str]:
    """
    Quick function to propose skill from trajectory.
    
    Args:
        trajectory: Successful trajectory
        auto_approve: Skip approval
        
    Returns:
        Skill data dictionary
    """
    workflow = SkillApprovalWorkflow(auto_approve=auto_approve)
    generator = SkillTemplateGenerator()
    
    skill_data = generator.generate_skill_from_trajectory(trajectory)
    
    if not auto_approve:
        proposal = workflow._build_proposal_message(skill_data, trajectory)
        skill_data["proposal_message"] = proposal
        skill_data["requires_approval"] = True
    
    return skill_data


__all__ = [
    "SkillApprovalWorkflow",
    "propose_skill_from_trajectory",
]
