# -*- coding: utf-8 -*-
"""Data models for proactive memory delivery."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List


class DeliveryTiming(str, Enum):
    """When to deliver proactive memories."""
    
    IMMEDIATE = "immediate"  # Deliver right away
    NEXT_TURN = "next_turn"  # Deliver at next user message
    OPPORTUNE = "opportune"  # Wait for opportune moment
    NEVER = "never"  # Don't deliver


class DeliveryMethod(str, Enum):
    """How to deliver the memory."""
    
    INLINE = "inline"  # Include in agent response
    NOTIFICATION = "notification"  # Separate notification
    CONTEXT = "context"  # Add to context window
    SUGGESTION = "suggestion"  # Show as suggestion


@dataclass
class ProactiveMemory:
    """A memory candidate for proactive delivery."""
    
    # Memory identifiers
    memory_id: str
    memory_type: str  # "experience", "skill", "multimodal"
    
    # Content
    title: str
    content: str
    summary: Optional[str] = None
    
    # Relevance
    relevance_score: float = 0.0
    confidence: float = 0.0
    
    # Context matching
    matched_keywords: List[str] = field(default_factory=list)
    matched_topics: List[str] = field(default_factory=list)
    matched_patterns: List[str] = field(default_factory=list)
    
    # Delivery settings
    timing: DeliveryTiming = DeliveryTiming.OPPORTUNE
    method: DeliveryMethod = DeliveryMethod.CONTEXT
    priority: int = 0  # Higher = more important
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    suggested_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    user_feedback: Optional[str] = None  # "helpful", "not_helpful", "ignored"
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "relevance_score": self.relevance_score,
            "confidence": self.confidence,
            "matched_keywords": self.matched_keywords,
            "matched_topics": self.matched_topics,
            "matched_patterns": self.matched_patterns,
            "timing": self.timing.value,
            "method": self.method.value,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "suggested_at": self.suggested_at.isoformat() if self.suggested_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "user_feedback": self.user_feedback,
            "metadata": self.metadata,
        }


@dataclass
class ContextSignal:
    """Signal indicating context that might trigger proactive delivery."""
    
    signal_type: str  # "task_start", "error", "topic_change", "tool_use", etc.
    strength: float  # 0.0 to 1.0
    
    # Context details
    keywords: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RelevanceScore:
    """Detailed relevance scoring for a memory."""
    
    memory_id: str
    total_score: float  # 0.0 to 1.0
    
    # Component scores
    keyword_score: float = 0.0
    topic_score: float = 0.0
    temporal_score: float = 0.0
    pattern_score: float = 0.0
    context_score: float = 0.0
    
    # Confidence
    confidence: float = 0.0
    
    # Explanation
    explanation: str = ""
    reasons: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "memory_id": self.memory_id,
            "total_score": self.total_score,
            "keyword_score": self.keyword_score,
            "topic_score": self.topic_score,
            "temporal_score": self.temporal_score,
            "pattern_score": self.pattern_score,
            "context_score": self.context_score,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "reasons": self.reasons,
        }
