# -*- coding: utf-8 -*-
"""Proactive memory delivery manager."""

import asyncio
from collections import deque
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Any, Optional, Callable

from agentscope.message import Msg

from .models import (
    ProactiveMemory,
    ContextSignal,
    DeliveryTiming,
    DeliveryMethod,
)
from .context_monitor import ContextMonitor
from .relevance_scorer import RelevanceScorer


class DeliveryStrategy(str, Enum):
    """Strategy for delivering proactive memories."""
    
    AGGRESSIVE = "aggressive"  # Deliver frequently
    BALANCED = "balanced"  # Moderate delivery
    CONSERVATIVE = "conservative"  # Deliver rarely, only high confidence
    PASSIVE = "passive"  # Never deliver proactively


class DeliveryManager:
    """Manages proactive delivery of memories."""
    
    def __init__(
        self,
        context_monitor: ContextMonitor,
        relevance_scorer: RelevanceScorer,
        strategy: DeliveryStrategy = DeliveryStrategy.BALANCED,
        max_deliveries_per_session: int = 10,
        min_confidence: float = 0.6,
    ):
        """Initialize delivery manager.
        
        Args:
            context_monitor: ContextMonitor instance
            relevance_scorer: RelevanceScorer instance
            strategy: Delivery strategy
            max_deliveries_per_session: Maximum proactive deliveries per session
            min_confidence: Minimum confidence to deliver
        """
        self.context_monitor = context_monitor
        self.relevance_scorer = relevance_scorer
        self.strategy = strategy
        self.max_deliveries_per_session = max_deliveries_per_session
        self.min_confidence = min_confidence
        
        # Adjust thresholds based on strategy
        if strategy == DeliveryStrategy.AGGRESSIVE:
            self.min_confidence = 0.4
            self.max_deliveries_per_session = 20
        elif strategy == DeliveryStrategy.CONSERVATIVE:
            self.min_confidence = 0.75
            self.max_deliveries_per_session = 5
        elif strategy == DeliveryStrategy.PASSIVE:
            self.min_confidence = 1.0  # Effectively disable proactive delivery
        
        # State tracking
        self._pending_deliveries: deque = deque(maxlen=50)
        self._delivered_count = 0
        self._last_delivery_time: Optional[datetime] = None
        self._delivery_cooldown = timedelta(seconds=60)
        
        # Callbacks
        self._delivery_callback: Optional[Callable] = None
    
    def set_delivery_callback(self, callback: Callable[[ProactiveMemory], None]):
        """Set callback for when memories are delivered."""
        self._delivery_callback = callback
    
    async def evaluate_memories(
        self,
        memories: List[Dict[str, Any]],
        signals: List[ContextSignal],
        current_context: Dict[str, Any],
    ) -> List[ProactiveMemory]:
        """Evaluate memories for proactive delivery.
        
        Args:
            memories: List of candidate memories
            signals: Active context signals
            current_context: Current conversation context
            
        Returns:
            List of ProactiveMemory objects ready for delivery
        """
        if self.strategy == DeliveryStrategy.PASSIVE:
            return []
        
        candidates = []
        
        for memory in memories:
            # Score relevance
            score = await self.relevance_scorer.score_memory(
                memory, signals, current_context
            )
            
            # Check if meets threshold
            if score.total_score < 0.3 or score.confidence < self.min_confidence:
                continue
            
            # Create ProactiveMemory
            proactive = ProactiveMemory(
                memory_id=memory.get("id", "unknown"),
                memory_type=memory.get("type", "unknown"),
                title=memory.get("title", "Relevant memory"),
                content=memory.get("content", ""),
                summary=memory.get("summary"),
                relevance_score=score.total_score,
                confidence=score.confidence,
                matched_keywords=list(set(
                    kw for signal in signals for kw in signal.keywords
                )),
                matched_topics=list(set(
                    topic for signal in signals for topic in signal.topics
                )),
            )
            
            # Determine delivery timing
            proactive.timing = self._determine_timing(proactive, signals)
            
            # Determine delivery method
            proactive.method = self._determine_method(proactive, signals)
            
            # Set priority
            proactive.priority = self._calculate_priority(proactive, signals)
            
            candidates.append(proactive)
        
        # Sort by priority and score
        candidates.sort(
            key=lambda m: (m.priority, m.relevance_score, m.confidence),
            reverse=True
        )
        
        return candidates
    
    async def should_deliver(
        self,
        memory: ProactiveMemory,
        force: bool = False,
    ) -> bool:
        """Check if memory should be delivered now.
        
        Args:
            memory: ProactiveMemory to check
            force: Force delivery regardless of conditions
            
        Returns:
            True if should deliver now
        """
        if force:
            return True
        
        # Check delivery count limit
        if self._delivered_count >= self.max_deliveries_per_session:
            return False
        
        # Check cooldown
        if self._last_delivery_time:
            time_since = datetime.utcnow() - self._last_delivery_time
            if time_since < self._delivery_cooldown:
                return False
        
        # Check timing
        if memory.timing == DeliveryTiming.NEVER:
            return False
        
        if memory.timing == DeliveryTiming.IMMEDIATE:
            return True
        
        if memory.timing == DeliveryTiming.OPPORTUNE:
            return self.context_monitor.should_deliver_now()
        
        # NEXT_TURN - queue for next message
        return False
    
    async def deliver_memory(
        self,
        memory: ProactiveMemory,
        current_message: Optional[Msg] = None,
    ) -> Dict[str, Any]:
        """Deliver proactive memory.
        
        Args:
            memory: ProactiveMemory to deliver
            current_message: Current message context
            
        Returns:
            Delivery result with formatted content
        """
        # Mark as delivered
        memory.delivered_at = datetime.utcnow()
        self._delivered_count += 1
        self._last_delivery_time = datetime.utcnow()
        
        # Format based on delivery method
        if memory.method == DeliveryMethod.INLINE:
            formatted = self._format_inline(memory)
        elif memory.method == DeliveryMethod.NOTIFICATION:
            formatted = self._format_notification(memory)
        elif memory.method == DeliveryMethod.CONTEXT:
            formatted = self._format_context(memory)
        else:  # SUGGESTION
            formatted = self._format_suggestion(memory)
        
        # Call callback if set
        if self._delivery_callback:
            await asyncio.to_thread(self._delivery_callback, memory)
        
        return {
            "memory_id": memory.memory_id,
            "formatted": formatted,
            "method": memory.method.value,
            "delivered_at": memory.delivered_at.isoformat(),
        }
    
    def _determine_timing(
        self,
        memory: ProactiveMemory,
        signals: List[ContextSignal],
    ) -> DeliveryTiming:
        """Determine when to deliver memory."""
        # High urgency for error signals
        if any(s.signal_type == "error" for s in signals):
            if memory.confidence > 0.8:
                return DeliveryTiming.IMMEDIATE
        
        # High confidence = immediate delivery
        if memory.confidence > 0.85 and memory.relevance_score > 0.8:
            return DeliveryTiming.IMMEDIATE
        
        # Moderate confidence = opportune moment
        if memory.confidence > 0.6:
            return DeliveryTiming.OPPORTUNE
        
        # Low confidence = next turn
        return DeliveryTiming.NEXT_TURN
    
    def _determine_method(
        self,
        memory: ProactiveMemory,
        signals: List[ContextSignal],
    ) -> DeliveryMethod:
        """Determine how to deliver memory."""
        # Errors should be notifications
        if any(s.signal_type == "error" for s in signals):
            return DeliveryMethod.NOTIFICATION
        
        # High priority = inline
        if memory.priority >= 3:
            return DeliveryMethod.INLINE
        
        # Default = context
        return DeliveryMethod.CONTEXT
    
    def _calculate_priority(
        self,
        memory: ProactiveMemory,
        signals: List[ContextSignal],
    ) -> int:
        """Calculate delivery priority (0-5)."""
        priority = 0
        
        # High score = higher priority
        if memory.relevance_score > 0.8:
            priority += 2
        elif memory.relevance_score > 0.6:
            priority += 1
        
        # High confidence = higher priority
        if memory.confidence > 0.8:
            priority += 2
        elif memory.confidence > 0.6:
            priority += 1
        
        # Error signals = highest priority
        if any(s.signal_type == "error" for s in signals):
            priority += 1
        
        return min(5, priority)
    
    def _format_inline(self, memory: ProactiveMemory) -> str:
        """Format memory for inline delivery."""
        return (
            f"\n\n💡 **Relevant Memory**: {memory.title}\n"
            f"{memory.summary or memory.content[:200]}\n"
            f"_(Confidence: {memory.confidence:.0%})_\n"
        )
    
    def _format_notification(self, memory: ProactiveMemory) -> str:
        """Format memory as notification."""
        return (
            f"🔔 **{memory.title}**\n\n"
            f"{memory.summary or memory.content[:300]}\n\n"
            f"Relevance: {memory.relevance_score:.0%} | "
            f"Confidence: {memory.confidence:.0%}"
        )
    
    def _format_context(self, memory: ProactiveMemory) -> str:
        """Format memory for context window."""
        return (
            f"[MEMORY: {memory.title}]\n"
            f"{memory.summary or memory.content[:150]}\n"
        )
    
    def _format_suggestion(self, memory: ProactiveMemory) -> str:
        """Format memory as suggestion."""
        return (
            f"💭 Suggestion: {memory.title}\n"
            f"{memory.summary or memory.content[:100]}"
        )
    
    def get_delivery_stats(self) -> Dict[str, Any]:
        """Get delivery statistics.
        
        Returns:
            Dictionary with delivery stats
        """
        return {
            "delivered_count": self._delivered_count,
            "max_deliveries": self.max_deliveries_per_session,
            "pending_count": len(self._pending_deliveries),
            "last_delivery": self._last_delivery_time.isoformat() if self._last_delivery_time else None,
            "strategy": self.strategy.value,
            "min_confidence": self.min_confidence,
        }
    
    def reset_session(self):
        """Reset delivery counters for new session."""
        self._delivered_count = 0
        self._last_delivery_time = None
        self._pending_deliveries.clear()
