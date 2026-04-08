# -*- coding: utf-8 -*-
"""
Delivery manager for proactive memory surfacing.

Decides when and how to deliver relevant memories during conversation.
"""
import logging
import time
from typing import Dict, List, Optional

from .monitor import ContextMonitor, ConversationContext
from .scorer import RelevanceScorer

logger = logging.getLogger(__name__)


class DeliveryManager:
    """
    Manages proactive memory delivery.
    
    Decides:
    - When to search for memories
    - Which memories to surface
    - How to present them
    - Delivery timing/throttling
    """
    
    def __init__(
        self,
        min_relevance: float = 0.5,
        max_deliveries_per_session: int = 10,
        min_delivery_interval: float = 60.0,  # seconds
    ):
        """
        Initialize delivery manager.
        
        Args:
            min_relevance: Minimum relevance score to deliver
            max_deliveries_per_session: Max memories to surface per session
            min_delivery_interval: Minimum time between deliveries
        """
        self.min_relevance = min_relevance
        self.max_deliveries_per_session = max_deliveries_per_session
        self.min_delivery_interval = min_delivery_interval
        
        # State tracking
        self.delivery_count = 0
        self.last_delivery_time = 0.0
        self.delivered_memory_ids = set()
        
        logger.info("DeliveryManager initialized")
    
    def should_deliver(self, context: ConversationContext) -> bool:
        """
        Decide if we should attempt memory delivery.
        
        Args:
            context: Current conversation context
            
        Returns:
            True if should search and deliver memories
        """
        # Check delivery quota
        if self.delivery_count >= self.max_deliveries_per_session:
            logger.debug("Delivery quota reached")
            return False
        
        # Check delivery interval
        time_since_last = time.time() - self.last_delivery_time
        if time_since_last < self.min_delivery_interval:
            logger.debug(f"Too soon since last delivery ({time_since_last:.1f}s)")
            return False
        
        # Context should indicate need for memory
        if context.intent in ['request', 'question']:
            return True
        
        if len(context.topics) > 0 and len(context.keywords) >= 2:
            return True
        
        return False
    
    def select_memories(
        self,
        candidates: List[Dict],
        context: ConversationContext,
        scorer: RelevanceScorer,
        top_k: int = 3,
    ) -> List[Dict]:
        """
        Select which memories to deliver.
        
        Args:
            candidates: Candidate memories from search
            context: Current conversation context
            scorer: Relevance scorer
            top_k: Maximum number to deliver
            
        Returns:
            List of memories to deliver
        """
        # Score all candidates
        scored = []
        for memory in candidates:
            # Skip already delivered
            if memory.get('id') in self.delivered_memory_ids:
                continue
            
            # Get embedding similarity if available
            similarity = memory.get('similarity_score', 0.0)
            
            # Compute relevance
            score = scorer.score_memory(memory, context, similarity)
            
            if score >= self.min_relevance:
                scored.append((score, memory))
        
        # Sort by score
        scored.sort(reverse=True, key=lambda x: x[0])
        
        # Take top k
        selected = [memory for score, memory in scored[:top_k]]
        
        logger.info(f"Selected {len(selected)} memories for delivery (from {len(candidates)} candidates)")
        
        return selected
    
    def deliver(self, memories: List[Dict]) -> Optional[str]:
        """
        Format memories for delivery.
        
        Args:
            memories: Memories to deliver
            
        Returns:
            Formatted message for delivery
        """
        if not memories:
            return None
        
        # Update state
        self.delivery_count += len(memories)
        self.last_delivery_time = time.time()
        self.delivered_memory_ids.update(m.get('id') for m in memories)
        
        # Format message
        lines = ["📸 **Relevant Memories:**", ""]
        
        for i, memory in enumerate(memories, 1):
            media_type = memory.get('media_type', 'unknown')
            context_text = memory.get('context_text', 'No context')
            created_at = memory.get('created_at', 0)
            
            # Format timestamp
            import datetime
            timestamp = datetime.datetime.fromtimestamp(created_at).strftime('%Y-%m-%d %H:%M')
            
            lines.append(f"{i}. **{media_type.upper()}** ({timestamp})")
            lines.append(f"   {context_text[:100]}...")
            lines.append("")
        
        message = "\n".join(lines)
        
        logger.info(f"Delivered {len(memories)} memories")
        
        return message
    
    def reset_session(self) -> None:
        """Reset delivery state for new session."""
        self.delivery_count = 0
        self.delivered_memory_ids.clear()
        logger.debug("Delivery state reset")


__all__ = ["DeliveryManager"]
