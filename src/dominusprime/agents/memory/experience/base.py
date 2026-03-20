# -*- coding: utf-8 -*-
"""Base classes for experience distillation."""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List


class ExperienceType(Enum):
    """Types of extractable experiences."""
    
    TASK_WORKFLOW = "task_workflow"
    PROBLEM_SOLUTION = "problem_solution"
    PREFERENCE = "preference"
    DOMAIN_KNOWLEDGE = "domain_knowledge"


@dataclass
class LearningMoment:
    """A moment in conversation that contains learning potential."""
    
    id: str
    timestamp: datetime
    messages: List[Any]  # List[Msg]
    category: str
    importance_score: float
    context_keywords: List[str]


@dataclass
class Pattern:
    """An identified pattern in user behavior or workflows."""
    
    id: str
    type: ExperienceType
    description: str
    frequency: int
    success_indicators: List[str]
    steps: List[Dict[str, Any]]
    context_requirements: List[str]
    confidence: float


@dataclass
class ConversationAnalysis:
    """Result of analyzing a conversation."""
    
    session_id: str
    total_messages: int
    successful_tasks: List[str]
    failed_tasks: List[str]
    user_preferences: Dict[str, Any]
    technical_topics: List[str]
    tools_used: List[str]
    command_patterns: List[str]
    analysis_timestamp: datetime


@dataclass
class GeneratedSkill:
    """A skill generated from experiences."""
    
    id: str
    name: str
    file_path: str
    source_experiences: List[str]
    description: str
    when_to_use: str
    steps: List[str]
    examples: List[str]
    confidence: float
    created_at: datetime
