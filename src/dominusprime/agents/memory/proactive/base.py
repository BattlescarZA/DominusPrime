# -*- coding: utf-8 -*-
"""Base classes for proactive memory delivery."""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any


class TriggerType(Enum):
    """Types of proactive triggers."""
    
    TOPIC_MATCH = "topic_match"
    TASK_PATTERN = "task_pattern"
    PROBLEM_RECOGNITION = "problem_recognition"
    TIME_BASED = "time_based"
    LOCATION_BASED = "location_based"


class DeliveryStrategy(Enum):
    """Strategies for delivering proactive memories."""
    
    INLINE_SUGGESTION = "inline_suggestion"      # Mention in response
    GENTLE_REMINDER = "gentle_reminder"          # "By the way..."
    PROACTIVE_CARD = "proactive_card"            # Rich card (console UI)
    SILENT_BACKGROUND = "silent_background"      # Add to context silently


class UserFeedback(Enum):
    """User feedback on delivered memories."""
    
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    IGNORE = "ignore"


@dataclass
class ProactiveTrigger:
    """A trigger for proactive memory delivery."""
    
    trigger_type: TriggerType
    confidence: float
    matched_keywords: List[str]
    context_similarity: float
    timestamp: datetime


@dataclass
class ConversationContext:
    """Current conversation context."""
    
    recent_messages: List[Any]  # List[Msg]
    current_topic: str
    active_tasks: List[str]
    keywords: List[str]
    entities: List[str]
    session_id: str
    user_id: str
    channel: str
    timestamp: datetime


@dataclass
class RankedMemory:
    """Memory ranked by relevance."""
    
    memory_id: str
    memory_type: str  # 'experience', 'multimodal', 'conversation'
    title: str
    content: str
    relevance_score: float
    confidence: float
    last_used: Optional[datetime]
    frequency: int


@dataclass
class DeliveryResult:
    """Result of memory delivery."""
    
    delivery_id: str
    memory_id: str
    strategy: DeliveryStrategy
    delivered_at: datetime
    user_acknowledged: bool
    feedback: Optional[UserFeedback]
