# -*- coding: utf-8 -*-
"""
Relevance scorer for proactive memory delivery.

Scores how relevant a memory is to the current conversation context.
"""
import logging
from typing import Dict, List

from .monitor import ConversationContext

logger = logging.getLogger(__name__)


class RelevanceScorer:
    """
    Scores memory relevance based on context matching.
    
    Uses multiple signals:
    - Topic overlap
    - Keyword matching
    - Temporal recency
    - Embedding similarity
    """
    
    def __init__(
        self,
        topic_weight: float = 0.3,
        keyword_weight: float = 0.3,
        recency_weight: float = 0.2,
        similarity_weight: float = 0.2,
    ):
        """
        Initialize relevance scorer.
        
        Args:
            topic_weight: Weight for topic matching
            keyword_weight: Weight for keyword matching
            recency_weight: Weight for recency
            similarity_weight: Weight for embedding similarity
        """
        self.topic_weight = topic_weight
        self.keyword_weight = keyword_weight
        self.recency_weight = recency_weight
        self.similarity_weight = similarity_weight
        
        logger.info("RelevanceScorer initialized")
    
    def score_memory(
        self,
        memory: Dict,
        context: ConversationContext,
        embedding_similarity: float = 0.0,
    ) -> float:
        """
        Score a memory's relevance to current context.
        
        Args:
            memory: Memory item to score
            context: Current conversation context
            embedding_similarity: Precomputed similarity score (0-1)
            
        Returns:
            Relevance score (0-1, higher is more relevant)
        """
        scores = []
        
        # Topic matching
        topic_score = self._score_topics(memory, context)
        scores.append(self.topic_weight * topic_score)
        
        # Keyword matching
        keyword_score = self._score_keywords(memory, context)
        scores.append(self.keyword_weight * keyword_score)
        
        # Recency (more recent = more relevant)
        recency_score = self._score_recency(memory)
        scores.append(self.recency_weight * recency_score)
        
        # Embedding similarity
        scores.append(self.similarity_weight * embedding_similarity)
        
        # Combined score
        total_score = sum(scores)
        
        logger.debug(f"Scored memory: {total_score:.3f} (topic={topic_score:.2f}, keyword={keyword_score:.2f}, recency={recency_score:.2f})")
        
        return total_score
    
    def _score_topics(self, memory: Dict, context: ConversationContext) -> float:
        """Score topic overlap."""
        # Extract topics from memory metadata
        memory_topics = set()
        
        # Check context text
        context_text = memory.get('context_text', '').lower()
        if context_text:
            # Simple topic extraction
            if 'python' in context_text or 'code' in context_text:
                memory_topics.add('programming')
            if 'image' in context_text or 'photo' in context_text:
                memory_topics.add('visual')
        
        # Calculate overlap
        if not context.topics or not memory_topics:
            return 0.0
        
        overlap = len(context.topics & memory_topics)
        return overlap / len(context.topics)
    
    def _score_keywords(self, memory: Dict, context: ConversationContext) -> float:
        """Score keyword matching."""
        # Extract text from memory
        memory_text = " ".join([
            memory.get('context_text', ''),
            memory.get('auto_description', ''),
            memory.get('ocr_text', ''),
        ]).lower()
        
        if not memory_text or not context.keywords:
            return 0.0
        
        # Count keyword matches
        matches = sum(1 for kw in context.keywords if kw in memory_text)
        
        return matches / len(context.keywords)
    
    def _score_recency(self, memory: Dict) -> float:
        """Score based on recency."""
        import time
        
        created_at = memory.get('created_at', 0)
        if not created_at:
            return 0.0
        
        # Age in seconds
        age = time.time() - created_at
        
        # Decay function: more recent = higher score
        # Score 1.0 for items < 1 hour old
        # Score 0.5 for items ~ 1 day old
        # Score 0.1 for items > 1 week old
        
        hour = 3600
        day = 24 * hour
        week = 7 * day
        
        if age < hour:
            return 1.0
        elif age < day:
            return 0.5 + 0.5 * (1 - age / day)
        elif age < week:
            return 0.1 + 0.4 * (1 - age / week)
        else:
            return 0.1


__all__ = ["RelevanceScorer"]
