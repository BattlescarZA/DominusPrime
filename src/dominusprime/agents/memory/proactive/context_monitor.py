# -*- coding: utf-8 -*-
"""Context monitoring for proactive memory delivery."""

import re
from collections import Counter
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set

from agentscope.message import Msg

from .models import ContextSignal


class ContextMonitor:
    """Monitors conversation context to identify memory trigger opportunities."""
    
    # Keywords that indicate task starts
    TASK_START_KEYWORDS = [
        "help", "show", "create", "build", "make", "implement",
        "fix", "debug", "solve", "explain", "how to", "need to",
    ]
    
    # Keywords that indicate errors or problems
    ERROR_KEYWORDS = [
        "error", "fail", "failed", "wrong", "broken", "issue",
        "problem", "bug", "not working", "doesn't work",
    ]
    
    # Tool usage patterns
    TOOL_PATTERN = re.compile(r'\b(execute|run|use)\s+(\w+)', re.IGNORECASE)
    
    def __init__(
        self,
        window_size: int = 10,
        signal_threshold: float = 0.3,
    ):
        """Initialize context monitor.
        
        Args:
            window_size: Number of recent messages to analyze
            signal_threshold: Minimum signal strength to trigger
        """
        self.window_size = window_size
        self.signal_threshold = signal_threshold
        
        self._message_history: List[Msg] = []
        self._recent_topics: List[str] = []
        self._recent_tools: List[str] = []
        self._last_signal_time: Optional[datetime] = None
    
    async def add_message(self, message: Msg) -> List[ContextSignal]:
        """Add message to context and detect signals.
        
        Args:
            message: New message to analyze
            
        Returns:
            List of detected context signals
        """
        self._message_history.append(message)
        
        # Keep only recent messages
        if len(self._message_history) > self.window_size:
            self._message_history = self._message_history[-self.window_size:]
        
        # Detect signals
        signals = []
        
        # Task start signal
        task_signal = await self._detect_task_start(message)
        if task_signal and task_signal.strength >= self.signal_threshold:
            signals.append(task_signal)
        
        # Error signal
        error_signal = await self._detect_error(message)
        if error_signal and error_signal.strength >= self.signal_threshold:
            signals.append(error_signal)
        
        # Topic change signal
        topic_signal = await self._detect_topic_change(message)
        if topic_signal and topic_signal.strength >= self.signal_threshold:
            signals.append(topic_signal)
        
        # Tool usage signal
        tool_signal = await self._detect_tool_usage(message)
        if tool_signal and tool_signal.strength >= self.signal_threshold:
            signals.append(tool_signal)
        
        # Update state
        if signals:
            self._last_signal_time = datetime.utcnow()
        
        return signals
    
    async def _detect_task_start(self, message: Msg) -> Optional[ContextSignal]:
        """Detect if message indicates a new task starting."""
        content = str(message.content).lower()
        
        # Count task start keywords
        keyword_matches = [kw for kw in self.TASK_START_KEYWORDS if kw in content]
        
        if not keyword_matches:
            return None
        
        # Calculate strength based on keyword matches
        strength = min(1.0, len(keyword_matches) * 0.3)
        
        # Extract keywords and topics
        keywords = self._extract_keywords(content)
        topics = self._extract_topics(content)
        
        return ContextSignal(
            signal_type="task_start",
            strength=strength,
            keywords=keywords,
            topics=topics,
            metadata={
                "matched_keywords": keyword_matches,
                "message_role": message.role,
            },
        )
    
    async def _detect_error(self, message: Msg) -> Optional[ContextSignal]:
        """Detect if message indicates an error or problem."""
        content = str(message.content).lower()
        
        # Count error keywords
        error_matches = [kw for kw in self.ERROR_KEYWORDS if kw in content]
        
        if not error_matches:
            return None
        
        # Higher strength for errors (more urgent)
        strength = min(1.0, len(error_matches) * 0.4)
        
        keywords = self._extract_keywords(content)
        topics = self._extract_topics(content)
        
        return ContextSignal(
            signal_type="error",
            strength=strength,
            keywords=keywords,
            topics=topics,
            metadata={
                "error_keywords": error_matches,
                "message_role": message.role,
            },
        )
    
    async def _detect_topic_change(self, message: Msg) -> Optional[ContextSignal]:
        """Detect if conversation topic has changed."""
        content = str(message.content).lower()
        current_topics = self._extract_topics(content)
        
        if not current_topics:
            return None
        
        # Compare with recent topics
        if not self._recent_topics:
            self._recent_topics = current_topics
            return None
        
        # Calculate topic overlap
        overlap = len(set(current_topics) & set(self._recent_topics))
        total = len(set(current_topics) | set(self._recent_topics))
        
        if total == 0:
            return None
        
        similarity = overlap / total
        
        # Topic changed if similarity is low
        if similarity < 0.3:
            strength = 1.0 - similarity
            
            self._recent_topics = current_topics
            
            return ContextSignal(
                signal_type="topic_change",
                strength=strength,
                keywords=self._extract_keywords(content),
                topics=current_topics,
                metadata={
                    "previous_topics": self._recent_topics,
                    "new_topics": current_topics,
                    "similarity": similarity,
                },
            )
        
        # Update recent topics gradually
        self._recent_topics = current_topics
        return None
    
    async def _detect_tool_usage(self, message: Msg) -> Optional[ContextSignal]:
        """Detect tool usage in messages."""
        content = str(message.content)
        
        # Check for tool calls in message metadata
        tools_used = []
        
        if hasattr(message, 'metadata') and message.metadata:
            if 'tool_calls' in message.metadata:
                tools_used = [tc.get('name') for tc in message.metadata['tool_calls'] if 'name' in tc]
        
        # Also check content for tool mentions
        tool_matches = self.TOOL_PATTERN.findall(content)
        if tool_matches:
            tools_used.extend([match[1] for match in tool_matches])
        
        if not tools_used:
            return None
        
        # Calculate strength based on number of tools
        strength = min(1.0, len(tools_used) * 0.4)
        
        self._recent_tools.extend(tools_used)
        if len(self._recent_tools) > 20:
            self._recent_tools = self._recent_tools[-20:]
        
        return ContextSignal(
            signal_type="tool_use",
            strength=strength,
            keywords=self._extract_keywords(content.lower()),
            tools_used=tools_used,
            metadata={
                "tools": tools_used,
                "message_role": message.role,
            },
        )
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract important keywords from content."""
        # Simple keyword extraction: words 4+ chars, alphanumeric
        words = re.findall(r'\b[a-z]{4,}\b', content.lower())
        
        # Remove common words
        stopwords = {
            "that", "this", "with", "from", "have", "been", "were",
            "will", "would", "could", "should", "them", "their", "there",
        }
        
        keywords = [w for w in words if w not in stopwords]
        
        # Return top keywords by frequency
        counter = Counter(keywords)
        return [word for word, _ in counter.most_common(10)]
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract topics from content."""
        # Topics are typically nouns or noun phrases
        # For now, use keyword extraction
        # In production, would use NLP for better topic extraction
        
        content_lower = content.lower()
        
        # Common topic categories
        topics = []
        
        # Programming topics
        if any(word in content_lower for word in ["python", "javascript", "code", "function", "class"]):
            topics.append("programming")
        
        # Data topics
        if any(word in content_lower for word in ["data", "database", "sql", "query"]):
            topics.append("data")
        
        # Web topics
        if any(word in content_lower for word in ["web", "http", "api", "server"]):
            topics.append("web")
        
        # System topics
        if any(word in content_lower for word in ["file", "directory", "system", "process"]):
            topics.append("system")
        
        # Security topics
        if any(word in content_lower for word in ["security", "auth", "permission", "access"]):
            topics.append("security")
        
        return topics
    
    def get_recent_context(self) -> Dict[str, Any]:
        """Get current context summary.
        
        Returns:
            Dictionary with context information
        """
        return {
            "message_count": len(self._message_history),
            "recent_topics": self._recent_topics,
            "recent_tools": list(set(self._recent_tools[-10:])),
            "last_signal_time": self._last_signal_time.isoformat() if self._last_signal_time else None,
        }
    
    def should_deliver_now(self) -> bool:
        """Check if it's a good time to deliver proactive memories.
        
        Returns:
            True if opportune moment for delivery
        """
        # Don't deliver if we just sent a signal recently
        if self._last_signal_time:
            time_since_signal = datetime.utcnow() - self._last_signal_time
            if time_since_signal < timedelta(seconds=30):
                return False
        
        # Check if there's a natural pause
        if len(self._message_history) >= 2:
            last_msg = self._message_history[-1]
            second_last = self._message_history[-2]
            
            # Good time if user just asked a question
            if last_msg.role == "user" and "?" in str(last_msg.content):
                return True
            
            # Good time after completing a task
            if last_msg.role == "assistant" and any(
                word in str(last_msg.content).lower()
                for word in ["completed", "done", "finished", "success"]
            ):
                return True
        
        return False
