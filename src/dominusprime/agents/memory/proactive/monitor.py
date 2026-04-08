# -*- coding: utf-8 -*-
"""
Context monitor for proactive memory delivery.

Analyzes conversation flow to detect opportunities for memory surfacing.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """
    Current conversation context.
    
    Attributes:
        topics: Detected topics/themes
        entities: Named entities mentioned
        keywords: Important keywords
        intent: Detected user intent
        sentiment: Conversation sentiment
        recent_turns: Number of recent turns analyzed
    """
    topics: Set[str] = field(default_factory=set)
    entities: Set[str] = field(default_factory=set)
    keywords: Set[str] = field(default_factory=set)
    intent: Optional[str] = None
    sentiment: str = "neutral"
    recent_turns: int = 0
    
    def add_keywords(self, words: List[str]) -> None:
        """Add keywords to context."""
        self.keywords.update(w.lower() for w in words)
    
    def add_topics(self, new_topics: List[str]) -> None:
        """Add topics to context."""
        self.topics.update(t.lower() for t in new_topics)
    
    def has_topic(self, topic: str) -> bool:
        """Check if topic is present."""
        return topic.lower() in self.topics
    
    def has_keyword(self, keyword: str) -> bool:
        """Check if keyword is present."""
        return keyword.lower() in self.keywords


class ContextMonitor:
    """
    Monitors conversation context for memory triggers.
    
    Analyzes recent messages to detect:
    - Topic changes
    - Repeated themes
    - Named entities
    - Questions that might benefit from past context
    """
    
    def __init__(
        self,
        window_size: int = 5,
        keyword_threshold: int = 2,
    ):
        """
        Initialize context monitor.
        
        Args:
            window_size: Number of recent messages to analyze
            keyword_threshold: Min keyword frequency to trigger
        """
        self.window_size = window_size
        self.keyword_threshold = keyword_threshold
        
        # State tracking
        self.message_history: List[Dict] = []
        self.current_context = ConversationContext()
        
        logger.info("ContextMonitor initialized")
    
    def analyze_message(self, message: Dict) -> ConversationContext:
        """
        Analyze new message and update context.
        
        Args:
            message: Message dict with 'role' and 'content'
            
        Returns:
            Updated conversation context
        """
        # Add to history
        self.message_history.append(message)
        
        # Keep only recent messages
        if len(self.message_history) > self.window_size:
            self.message_history = self.message_history[-self.window_size:]
        
        # Extract features from recent messages
        self._extract_keywords()
        self._detect_topics()
        self._detect_intent()
        
        self.current_context.recent_turns = len(self.message_history)
        
        logger.debug(f"Context updated: {len(self.current_context.keywords)} keywords, {len(self.current_context.topics)} topics")
        
        return self.current_context
    
    def _extract_keywords(self) -> None:
        """Extract important keywords from recent messages."""
        # Simple keyword extraction (word frequency)
        word_freq: Dict[str, int] = {}
        
        for msg in self.message_history:
            content = msg.get('content', '')
            if isinstance(content, str):
                words = content.lower().split()
                for word in words:
                    # Filter out common words
                    if len(word) > 3 and word.isalnum():
                        word_freq[word] = word_freq.get(word, 0) + 1
        
        # Add frequent words as keywords
        keywords = [
            word for word, freq in word_freq.items()
            if freq >= self.keyword_threshold
        ]
        
        self.current_context.add_keywords(keywords)
    
    def _detect_topics(self) -> None:
        """Detect topics from keywords and patterns."""
        # Simple topic detection based on keyword clusters
        topics = set()
        
        # Technical topics
        if any(kw in self.current_context.keywords for kw in ['python', 'code', 'function', 'error']):
            topics.add('programming')
        
        if any(kw in self.current_context.keywords for kw in ['image', 'photo', 'picture', 'screenshot']):
            topics.add('visual')
        
        if any(kw in self.current_context.keywords for kw in ['data', 'analysis', 'chart', 'graph']):
            topics.add('data-analysis')
        
        if any(kw in self.current_context.keywords for kw in ['deploy', 'server', 'docker', 'kubernetes']):
            topics.add('deployment')
        
        self.current_context.add_topics(list(topics))
    
    def _detect_intent(self) -> None:
        """Detect user intent from recent messages."""
        # Look at most recent user message
        for msg in reversed(self.message_history):
            if msg.get('role') == 'user':
                content = msg.get('content', '').lower()
                
                # Question patterns
                if any(content.startswith(q) for q in ['what', 'how', 'why', 'when', 'where', 'who']):
                    self.current_context.intent = 'question'
                
                # Request patterns
                elif any(word in content for word in ['show', 'find', 'get', 'search', 'recall']):
                    self.current_context.intent = 'request'
                
                # Task patterns
                elif any(word in content for word in ['create', 'build', 'make', 'develop']):
                    self.current_context.intent = 'task'
                
                break
    
    def should_trigger_search(self) -> bool:
        """
        Determine if context warrants memory search.
        
        Returns:
            True if should search memories
        """
        # Trigger on questions about past
        if self.current_context.intent == 'request':
            return True
        
        # Trigger when discussing familiar topics
        if len(self.current_context.topics) > 0:
            return True
        
        # Trigger on sufficient keyword density
        if len(self.current_context.keywords) >= 3:
            return True
        
        return False
    
    def get_search_query(self) -> Optional[str]:
        """
        Generate search query from context.
        
        Returns:
            Search query string or None
        """
        if not self.should_trigger_search():
            return None
        
        # Combine topics and keywords
        query_parts = list(self.current_context.topics) + list(self.current_context.keywords)[:5]
        
        if query_parts:
            return " ".join(query_parts)
        
        return None
    
    def reset(self) -> None:
        """Reset context state."""
        self.message_history.clear()
        self.current_context = ConversationContext()


__all__ = ["ContextMonitor", "ConversationContext"]
