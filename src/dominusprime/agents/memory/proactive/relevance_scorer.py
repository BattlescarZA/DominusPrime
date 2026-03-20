# -*- coding: utf-8 -*-
"""Relevance scoring for proactive memory delivery."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from .models import ContextSignal, RelevanceScore


class RelevanceScorer:
    """Scores memory relevance based on current context."""
    
    def __init__(
        self,
        keyword_weight: float = 0.3,
        topic_weight: float = 0.25,
        temporal_weight: float = 0.15,
        pattern_weight: float = 0.2,
        context_weight: float = 0.1,
    ):
        """Initialize relevance scorer.
        
        Args:
            keyword_weight: Weight for keyword matching
            topic_weight: Weight for topic matching
            temporal_weight: Weight for temporal relevance
            pattern_weight: Weight for pattern matching
            context_weight: Weight for context similarity
        """
        self.keyword_weight = keyword_weight
        self.topic_weight = topic_weight
        self.temporal_weight = temporal_weight
        self.pattern_weight = pattern_weight
        self.context_weight = context_weight
        
        # Normalize weights
        total = sum([
            keyword_weight, topic_weight, temporal_weight,
            pattern_weight, context_weight
        ])
        self.keyword_weight /= total
        self.topic_weight /= total
        self.temporal_weight /= total
        self.pattern_weight /= total
        self.context_weight /= total
    
    async def score_memory(
        self,
        memory: Dict[str, Any],
        signals: List[ContextSignal],
        current_context: Dict[str, Any],
    ) -> RelevanceScore:
        """Score a memory's relevance to current context.
        
        Args:
            memory: Memory to score (dict with id, content, metadata)
            signals: Active context signals
            current_context: Current conversation context
            
        Returns:
            RelevanceScore with detailed scoring
        """
        memory_id = memory.get("id", "unknown")
        
        # Calculate component scores
        keyword_score = await self._score_keywords(memory, signals)
        topic_score = await self._score_topics(memory, signals)
        temporal_score = await self._score_temporal(memory)
        pattern_score = await self._score_patterns(memory, current_context)
        context_score = await self._score_context(memory, current_context)
        
        # Calculate total weighted score
        total_score = (
            keyword_score * self.keyword_weight +
            topic_score * self.topic_weight +
            temporal_score * self.temporal_weight +
            pattern_score * self.pattern_weight +
            context_score * self.context_weight
        )
        
        # Calculate confidence based on signal strength and score consistency
        confidence = self._calculate_confidence(
            [keyword_score, topic_score, temporal_score, pattern_score, context_score],
            signals
        )
        
        # Generate explanation
        explanation, reasons = self._generate_explanation(
            keyword_score, topic_score, temporal_score,
            pattern_score, context_score, confidence
        )
        
        return RelevanceScore(
            memory_id=memory_id,
            total_score=total_score,
            keyword_score=keyword_score,
            topic_score=topic_score,
            temporal_score=temporal_score,
            pattern_score=pattern_score,
            context_score=context_score,
            confidence=confidence,
            explanation=explanation,
            reasons=reasons,
        )
    
    async def _score_keywords(
        self,
        memory: Dict[str, Any],
        signals: List[ContextSignal],
    ) -> float:
        """Score keyword overlap between memory and context."""
        # Extract memory keywords
        memory_content = str(memory.get("content", "")).lower()
        memory_keywords = set(memory.get("keywords", []))
        
        if not memory_keywords and memory_content:
            # Extract keywords from content
            import re
            words = re.findall(r'\b[a-z]{4,}\b', memory_content)
            memory_keywords = set(words[:20])  # Top 20 words
        
        if not memory_keywords:
            return 0.0
        
        # Get signal keywords
        signal_keywords = set()
        for signal in signals:
            signal_keywords.update(signal.keywords)
        
        if not signal_keywords:
            return 0.0
        
        # Calculate overlap
        overlap = len(memory_keywords & signal_keywords)
        total = len(memory_keywords | signal_keywords)
        
        return overlap / total if total > 0 else 0.0
    
    async def _score_topics(
        self,
        memory: Dict[str, Any],
        signals: List[ContextSignal],
    ) -> float:
        """Score topic overlap between memory and context."""
        memory_topics = set(memory.get("topics", []))
        
        if not memory_topics:
            return 0.0
        
        # Get signal topics
        signal_topics = set()
        for signal in signals:
            signal_topics.update(signal.topics)
        
        if not signal_topics:
            return 0.0
        
        # Calculate overlap
        overlap = len(memory_topics & signal_topics)
        
        # Higher weight for exact matches
        return min(1.0, overlap * 0.5)
    
    async def _score_temporal(self, memory: Dict[str, Any]) -> float:
        """Score temporal relevance (recent is more relevant)."""
        created_at = memory.get("created_at")
        
        if not created_at:
            return 0.5  # Neutral score if no timestamp
        
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        # Calculate age
        age = datetime.utcnow() - created_at
        
        # Decay function: 1.0 for today, 0.5 for 30 days ago, 0.1 for 6 months
        if age < timedelta(days=1):
            return 1.0
        elif age < timedelta(days=7):
            return 0.9
        elif age < timedelta(days=30):
            return 0.7
        elif age < timedelta(days=90):
            return 0.5
        elif age < timedelta(days=180):
            return 0.3
        else:
            return 0.1
    
    async def _score_patterns(
        self,
        memory: Dict[str, Any],
        current_context: Dict[str, Any],
    ) -> float:
        """Score pattern similarity."""
        memory_patterns = memory.get("patterns", [])
        
        if not memory_patterns:
            return 0.0
        
        # Check for pattern matches in recent tools
        recent_tools = current_context.get("recent_tools", [])
        
        if not recent_tools:
            return 0.0
        
        # Simple pattern matching
        matches = 0
        for pattern in memory_patterns:
            pattern_lower = pattern.lower()
            for tool in recent_tools:
                if pattern_lower in tool.lower() or tool.lower() in pattern_lower:
                    matches += 1
                    break
        
        return min(1.0, matches * 0.4)
    
    async def _score_context(
        self,
        memory: Dict[str, Any],
        current_context: Dict[str, Any],
    ) -> float:
        """Score overall context similarity."""
        # Check session similarity
        memory_session = memory.get("session_id")
        current_session = current_context.get("session_id")
        
        if memory_session and current_session and memory_session == current_session:
            return 1.0
        
        # Check usage frequency
        usage_count = memory.get("usage_count", 0)
        
        if usage_count > 10:
            return 0.8
        elif usage_count > 5:
            return 0.6
        elif usage_count > 0:
            return 0.4
        
        return 0.2
    
    def _calculate_confidence(
        self,
        scores: List[float],
        signals: List[ContextSignal],
    ) -> float:
        """Calculate confidence in the relevance score."""
        # Confidence based on:
        # 1. Score consistency (low variance = high confidence)
        # 2. Signal strength
        # 3. Number of non-zero scores
        
        non_zero_scores = [s for s in scores if s > 0.1]
        
        if not non_zero_scores:
            return 0.0
        
        # Variance of non-zero scores
        mean_score = sum(non_zero_scores) / len(non_zero_scores)
        variance = sum((s - mean_score) ** 2 for s in non_zero_scores) / len(non_zero_scores)
        
        consistency = 1.0 - min(1.0, variance)
        
        # Signal strength
        signal_strength = max([s.strength for s in signals]) if signals else 0.5
        
        # Coverage (how many score components are active)
        coverage = len(non_zero_scores) / len(scores)
        
        # Combined confidence
        confidence = (consistency * 0.4 + signal_strength * 0.3 + coverage * 0.3)
        
        return min(1.0, max(0.0, confidence))
    
    def _generate_explanation(
        self,
        keyword_score: float,
        topic_score: float,
        temporal_score: float,
        pattern_score: float,
        context_score: float,
        confidence: float,
    ) -> tuple[str, List[str]]:
        """Generate human-readable explanation of relevance."""
        reasons = []
        
        if keyword_score > 0.5:
            reasons.append(f"Strong keyword match ({keyword_score:.1%})")
        
        if topic_score > 0.5:
            reasons.append(f"Related topics ({topic_score:.1%})")
        
        if temporal_score > 0.7:
            reasons.append("Recent memory")
        
        if pattern_score > 0.5:
            reasons.append(f"Similar patterns ({pattern_score:.1%})")
        
        if context_score > 0.7:
            reasons.append("Relevant to current context")
        
        if not reasons:
            reasons.append("Low overall relevance")
        
        # Generate explanation
        if confidence > 0.7:
            explanation = f"High confidence: {', '.join(reasons)}"
        elif confidence > 0.4:
            explanation = f"Moderate confidence: {', '.join(reasons)}"
        else:
            explanation = f"Low confidence: {', '.join(reasons)}"
        
        return explanation, reasons
