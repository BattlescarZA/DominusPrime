# -*- coding: utf-8 -*-
"""
Skill Auto-Generation Manager - Complete workflow for skill auto-generation.

Integrates trajectory tracking, template generation, and approval workflow.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Any

from .trajectory_tracker import TrajectoryTracker, ToolCall
from .skill_template_generator import SkillTemplateGenerator
from .skill_approval import SkillApprovalWorkflow

logger = logging.getLogger(__name__)


class SkillAutoGenManager:
    """
    Complete auto-generation manager integrating all components.
    
    Usage:
        manager = SkillAutoGenManager()
        
        # Start task
        manager.start_task("Debug Python application")
        
        # Record tool calls
        manager.record_tool("execute_shell", {"command": "pytest"})
        
        # Complete task
        skill = await manager.complete_task(success=True)
        if skill:
            # Skill proposed for creation
            pass
    """
    
    def __init__(
        self,
        storage_dir: Optional[Path] = None,
        auto_approve: bool = False,
        min_tools: int = 3,
    ):
        """
        Initialize auto-generation manager.
        
        Args:
            storage_dir: Directory for persistent storage
            auto_approve: Auto-approve generated skills
            min_tools: Minimum tools for skill worthiness
        """
        # Initialize components
        trajectory_path = None
        if storage_dir:
            storage_dir.mkdir(parents=True, exist_ok=True)
            trajectory_path = storage_dir / "trajectories.json"
        
        self.tracker = TrajectoryTracker(
            min_tools_for_skill=min_tools,
            storage_path=trajectory_path,
        )
        
        self.generator = SkillTemplateGenerator()
        self.workflow = SkillApprovalWorkflow(
            template_generator=self.generator,
            auto_approve=auto_approve,
            storage_dir=storage_dir,
        )
        
        logger.info("Skill auto-generation manager initialized")
    
    def start_task(self, task_description: str, metadata: Optional[Dict] = None) -> None:
        """Start tracking a new task."""
        self.tracker.start_trajectory(task_description, metadata)
        logger.debug(f"Started tracking: {task_description}")
    
    def record_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Optional[Any] = None,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """Record a tool call in current trajectory."""
        self.tracker.record_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            success=success,
            error=error,
        )
    
    async def complete_task(
        self,
        success: bool,
        outcome: Optional[str] = None,
    ) -> Optional[Dict[str, str]]:
        """
        Complete task and propose skill if worthy.
        
        Returns:
            Skill data if proposed, None otherwise
        """
        trajectory = self.tracker.complete_trajectory(success, outcome)
        
        if not trajectory:
            return None
        
        # Propose skill for approval
        skill_data = await self.workflow.propose_skill(trajectory)
        
        if skill_data:
            logger.info(f"Skill proposed: {skill_data['name']}")
        
        return skill_data
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        return {
            "tracker": self.tracker.get_stats(),
            "approval": self.workflow.get_stats(),
        }


__all__ = ["SkillAutoGenManager"]
