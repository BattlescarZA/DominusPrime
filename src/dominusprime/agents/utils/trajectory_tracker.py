# -*- coding: utf-8 -*-
"""
Trajectory Tracker - Monitor agent execution patterns for skill generation.

Tracks:
- Tool usage sequences
- Successful task patterns
- Repeated procedures
- Context and outcomes
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Record of a single tool invocation."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    timestamp: float = field(default_factory=time.time)
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result": self.result,
            "timestamp": self.timestamp,
            "success": self.success,
            "error": self.error,
        }


@dataclass
class Trajectory:
    """A sequence of tool calls forming a task execution pattern."""
    task_description: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    success: bool = False
    outcome: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_tool_call(self, call: ToolCall) -> None:
        """Add a tool call to the trajectory."""
        self.tool_calls.append(call)
    
    def complete(self, success: bool, outcome: Optional[str] = None) -> None:
        """Mark trajectory as complete."""
        self.end_time = time.time()
        self.success = success
        self.outcome = outcome
    
    def duration(self) -> float:
        """Get trajectory duration in seconds."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def get_signature(self) -> str:
        """
        Get signature of tool sequence for pattern matching.
        
        Returns:
            Hash of tool names sequence
        """
        tool_sequence = [call.tool_name for call in self.tool_calls]
        signature_str = "|".join(tool_sequence)
        return hashlib.md5(signature_str.encode()).hexdigest()
    
    def get_tool_names(self) -> List[str]:
        """Get list of tool names used."""
        return [call.tool_name for call in self.tool_calls]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_description": self.task_description,
            "tool_calls": [call.to_dict() for call in self.tool_calls],
            "start_time": self.start_time,
            "end_time": self.end_time,
            "success": self.success,
            "outcome": self.outcome,
            "duration": self.duration(),
            "signature": self.get_signature(),
            "metadata": self.metadata,
        }


class TrajectoryTracker:
    """
    Tracks agent execution trajectories to identify skill creation opportunities.
    
    Features:
    - Records tool usage sequences
    - Detects repeated patterns
    - Identifies successful procedures
    - Suggests skill creation
    """
    
    def __init__(
        self,
        min_tools_for_skill: int = 3,
        similarity_threshold: float = 0.7,
        storage_path: Optional[Path] = None,
    ):
        """
        Initialize trajectory tracker.
        
        Args:
            min_tools_for_skill: Minimum tool calls to consider for skill
            similarity_threshold: Pattern similarity threshold (0-1)
            storage_path: Path to persist trajectories
        """
        self.min_tools_for_skill = min_tools_for_skill
        self.similarity_threshold = similarity_threshold
        self.storage_path = storage_path
        
        # Active trajectory being built
        self.current_trajectory: Optional[Trajectory] = None
        
        # Historical trajectories
        self.trajectories: List[Trajectory] = []
        
        # Pattern tracking
        self.pattern_counts: Dict[str, int] = {}
        
        # Load persisted trajectories
        if self.storage_path and self.storage_path.exists():
            self._load_trajectories()
    
    def start_trajectory(self, task_description: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Start tracking a new trajectory.
        
        Args:
            task_description: Description of the task being performed
            metadata: Optional metadata about the task
        """
        self.current_trajectory = Trajectory(
            task_description=task_description,
            metadata=metadata or {},
        )
        logger.debug(f"Started trajectory: {task_description}")
    
    def record_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Optional[Any] = None,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """
        Record a tool call in the current trajectory.
        
        Args:
            tool_name: Name of the tool called
            arguments: Tool arguments
            result: Tool result
            success: Whether call succeeded
            error: Error message if failed
        """
        if not self.current_trajectory:
            logger.warning("Tool call recorded without active trajectory")
            return
        
        call = ToolCall(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            success=success,
            error=error,
        )
        
        self.current_trajectory.add_tool_call(call)
        logger.debug(f"Recorded tool call: {tool_name}")
    
    def complete_trajectory(self, success: bool, outcome: Optional[str] = None) -> Optional[Trajectory]:
        """
        Complete the current trajectory.
        
        Args:
            success: Whether trajectory succeeded
            outcome: Description of the outcome
            
        Returns:
            Completed trajectory if skill-worthy, None otherwise
        """
        if not self.current_trajectory:
            return None
        
        self.current_trajectory.complete(success, outcome)
        
        # Add to history
        self.trajectories.append(self.current_trajectory)
        
        # Update pattern tracking
        if success:
            signature = self.current_trajectory.get_signature()
            self.pattern_counts[signature] = self.pattern_counts.get(signature, 0) + 1
        
        # Check if skill-worthy
        completed = self.current_trajectory
        self.current_trajectory = None
        
        if self._is_skill_worthy(completed):
            logger.info(f"Skill-worthy trajectory detected: {completed.task_description}")
            
            # Persist
            if self.storage_path:
                self._save_trajectories()
            
            return completed
        
        return None
    
    def _is_skill_worthy(self, trajectory: Trajectory) -> bool:
        """
        Check if trajectory is worth creating a skill for.
        
        Args:
            trajectory: Trajectory to evaluate
            
        Returns:
            True if skill-worthy
        """
        # Must be successful
        if not trajectory.success:
            return False
        
        # Must have minimum tool calls
        if len(trajectory.tool_calls) < self.min_tools_for_skill:
            return False
        
        # Check if pattern is repeated
        signature = trajectory.get_signature()
        if self.pattern_counts.get(signature, 0) >= 2:
            # Seen this pattern before - definitely skill-worthy
            return True
        
        # Single occurrence but complex enough
        if len(trajectory.tool_calls) >= 5:
            return True
        
        return False
    
    def get_similar_trajectories(
        self,
        trajectory: Trajectory,
        limit: int = 5,
    ) -> List[Trajectory]:
        """
        Find similar trajectories.
        
        Args:
            trajectory: Trajectory to find similar ones for
            limit: Maximum number to return
            
        Returns:
            List of similar trajectories
        """
        target_tools = set(trajectory.get_tool_names())
        similar = []
        
        for t in self.trajectories:
            if t == trajectory:
                continue
            
            t_tools = set(t.get_tool_names())
            
            # Calculate Jaccard similarity
            intersection = len(target_tools & t_tools)
            union = len(target_tools | t_tools)
            
            if union > 0:
                similarity = intersection / union
                
                if similarity >= self.similarity_threshold:
                    similar.append((t, similarity))
        
        # Sort by similarity
        similar.sort(key=lambda x: x[1], reverse=True)
        
        return [t for t, _ in similar[:limit]]
    
    def get_pattern_frequency(self, trajectory: Trajectory) -> int:
        """
        Get how many times this pattern has been seen.
        
        Args:
            trajectory: Trajectory to check
            
        Returns:
            Number of times pattern occurred
        """
        signature = trajectory.get_signature()
        return self.pattern_counts.get(signature, 0)
    
    def clear_history(self) -> None:
        """Clear trajectory history."""
        self.trajectories.clear()
        self.pattern_counts.clear()
        
        if self.storage_path and self.storage_path.exists():
            self.storage_path.unlink()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get tracker statistics.
        
        Returns:
            Statistics dictionary
        """
        successful = [t for t in self.trajectories if t.success]
        
        return {
            "total_trajectories": len(self.trajectories),
            "successful_trajectories": len(successful),
            "unique_patterns": len(self.pattern_counts),
            "repeated_patterns": sum(1 for count in self.pattern_counts.values() if count >= 2),
            "current_trajectory_active": self.current_trajectory is not None,
        }
    
    def _save_trajectories(self) -> None:
        """Save trajectories to disk."""
        if not self.storage_path:
            return
        
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "trajectories": [t.to_dict() for t in self.trajectories[-50:]],  # Keep last 50
                "pattern_counts": self.pattern_counts,
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self.trajectories)} trajectories")
        
        except Exception as e:
            logger.error(f"Failed to save trajectories: {e}", exc_info=True)
    
    def _load_trajectories(self) -> None:
        """Load trajectories from disk."""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Note: We don't fully reconstruct trajectories from disk
            # Just load pattern counts for pattern detection
            self.pattern_counts = data.get("pattern_counts", {})
            
            logger.info(f"Loaded {len(self.pattern_counts)} patterns")
        
        except Exception as e:
            logger.error(f"Failed to load trajectories: {e}", exc_info=True)


__all__ = [
    "ToolCall",
    "Trajectory",
    "TrajectoryTracker",
]
