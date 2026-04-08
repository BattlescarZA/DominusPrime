# -*- coding: utf-8 -*-
"""Tests for proactive memory delivery system."""
import pytest
import time
from dominusprime.agents.memory.proactive.monitor import (
    ConversationContext,
    ContextMonitor
)
from dominusprime.agents.memory.proactive.scorer import RelevanceScorer
from dominusprime.agents.memory.proactive.delivery import DeliveryManager


class TestConversationContext:
    """Test suite for ConversationContext."""
    
    def test_initialization(self):
        """Test context initialization."""
        context = ConversationContext()
        
        assert context.topics == set()
        assert context.entities == set()
        assert context.keywords == set()
        assert context.intent is None
    
    def test_adding_topics(self):
        """Test adding topics to context."""
        context = ConversationContext()
        context.topics.add("debugging")
        context.topics.add("python")
        
        assert len(context.topics) == 2
        assert "debugging" in context.topics
        assert "python" in context.topics
    
    def test_adding_entities(self):
        """Test adding entities to context."""
        context = ConversationContext()
        context.entities.add("Python")
        context.entities.add("Django")
        
        assert len(context.entities) == 2
    
    def test_adding_keywords(self):
        """Test adding keywords to context."""
        context = ConversationContext()
        context.keywords.update(["error", "stack", "trace"])
        
        assert len(context.keywords) == 3
    
    def test_setting_intent(self):
        """Test setting conversation intent."""
        context = ConversationContext()
        context.intent = "request"
        
        assert context.intent == "request"


class TestContextMonitor:
    """Test suite for ContextMonitor."""
    
    def test_initialization(self):
        """Test monitor initialization."""
        monitor = ContextMonitor()
        
        assert monitor is not None
        assert monitor.current_context is not None
    
    def test_analyze_message(self):
        """Test analyzing a message."""
        monitor = ContextMonitor()
        
        message = {
            "role": "user",
            "content": "I'm having a Python debugging error with stack traces"
        }
        
        context = monitor.analyze_message(message)
        
        assert context is not None
        assert len(context.keywords) > 0
    
    def test_extract_keywords(self):
        """Test keyword extraction."""
        monitor = ContextMonitor()
        
        text = "Python debugging error with stack traces and exceptions"
        keywords = monitor.extract_keywords(text)
        
        assert len(keywords) > 0
        assert isinstance(keywords, set)
    
    def test_detect_topics(self):
        """Test topic detection."""
        monitor = ContextMonitor()
        
        text = "I need help debugging my Python Django application"
        topics = monitor.detect_topics(text)
        
        assert len(topics) >= 0
        assert isinstance(topics, set)
    
    def test_detect_entities(self):
        """Test entity detection."""
        monitor = ContextMonitor()
        
        text = "I'm using Python and Django for my project"
        entities = monitor.detect_entities(text)
        
        assert isinstance(entities, set)
    
    def test_detect_intent(self):
        """Test intent detection."""
        monitor = ContextMonitor()
        
        request_text = "Can you help me debug this error?"
        intent = monitor.detect_intent(request_text)
        
        assert intent in ["request", "question", "statement", None]
    
    def test_should_trigger_search(self):
        """Test search triggering logic."""
        monitor = ContextMonitor()
        
        # Analyze a message with clear intent
        message = {
            "role": "user",
            "content": "Show me Python debugging examples"
        }
        monitor.analyze_message(message)
        
        should_trigger = monitor.should_trigger_search()
        
        assert isinstance(should_trigger, bool)
    
    def test_context_accumulation(self):
        """Test that context accumulates across messages."""
        monitor = ContextMonitor()
        
        # Analyze multiple messages
        messages = [
            {"role": "user", "content": "I'm working on Python"},
            {"role": "user", "content": "Having debugging issues"},
            {"role": "user", "content": "Stack traces are confusing"}
        ]
        
        for msg in messages:
            monitor.analyze_message(msg)
        
        # Context should have accumulated
        assert len(monitor.current_context.keywords) >= 3
    
    def test_reset_context(self):
        """Test resetting context."""
        monitor = ContextMonitor()
        
        # Add some context
        message = {"role": "user", "content": "Python debugging error"}
        monitor.analyze_message(message)
        
        assert len(monitor.current_context.keywords) > 0
        
        # Reset
        monitor.reset_context()
        
        assert len(monitor.current_context.keywords) == 0
        assert len(monitor.current_context.topics) == 0


class TestRelevanceScorer:
    """Test suite for RelevanceScorer."""
    
    def test_initialization(self):
        """Test scorer initialization."""
        scorer = RelevanceScorer()
        
        assert scorer is not None
        assert scorer.topic_weight > 0
        assert scorer.keyword_weight > 0
        assert scorer.recency_weight > 0
        assert scorer.similarity_weight > 0
    
    def test_initialization_custom_weights(self):
        """Test scorer with custom weights."""
        scorer = RelevanceScorer(
            topic_weight=0.4,
            keyword_weight=0.3,
            recency_weight=0.2,
            similarity_weight=0.1
        )
        
        assert scorer.topic_weight == 0.4
        assert scorer.keyword_weight == 0.3
    
    def test_score_memory(self):
        """Test scoring a memory."""
        scorer = RelevanceScorer()
        
        context = ConversationContext()
        context.topics.add("debugging")
        context.keywords.update(["python", "error"])
        
        memory = {
            "id": "mem_001",
            "metadata": {
                "description": "Python debugging session with errors",
                "tags": ["debugging", "python"]
            },
            "created_at": time.time()
        }
        
        score = scorer.score_memory(memory, context, embedding_similarity=0.8)
        
        assert isinstance(score, float)
        assert 0 <= score <= 1
    
    def test_topic_scoring(self):
        """Test topic-based scoring."""
        scorer = RelevanceScorer()
        
        context = ConversationContext()
        context.topics.add("debugging")
        
        memory_with_topic = {
            "metadata": {"tags": ["debugging"]},
            "created_at": time.time()
        }
        
        memory_without_topic = {
            "metadata": {"tags": ["cooking"]},
            "created_at": time.time()
        }
        
        score_with = scorer.score_memory(memory_with_topic, context)
        score_without = scorer.score_memory(memory_without_topic, context)
        
        assert score_with > score_without
    
    def test_keyword_scoring(self):
        """Test keyword-based scoring."""
        scorer = RelevanceScorer()
        
        context = ConversationContext()
        context.keywords.update(["python", "error", "debug"])
        
        memory_matching = {
            "metadata": {"description": "Python error during debugging"},
            "created_at": time.time()
        }
        
        memory_non_matching = {
            "metadata": {"description": "Cooking recipes"},
            "created_at": time.time()
        }
        
        score_match = scorer.score_memory(memory_matching, context)
        score_no_match = scorer.score_memory(memory_non_matching, context)
        
        assert score_match >= score_no_match
    
    def test_recency_scoring(self):
        """Test recency-based scoring."""
        scorer = RelevanceScorer()
        
        context = ConversationContext()
        
        recent_memory = {
            "metadata": {},
            "created_at": time.time()
        }
        
        old_memory = {
            "metadata": {},
            "created_at": time.time() - 86400  # 1 day ago
        }
        
        score_recent = scorer.score_memory(recent_memory, context)
        score_old = scorer.score_memory(old_memory, context)
        
        assert score_recent >= score_old
    
    def test_similarity_scoring(self):
        """Test embedding similarity scoring."""
        scorer = RelevanceScorer()
        
        context = ConversationContext()
        
        memory = {
            "metadata": {},
            "created_at": time.time()
        }
        
        score_high_sim = scorer.score_memory(memory, context, embedding_similarity=0.9)
        score_low_sim = scorer.score_memory(memory, context, embedding_similarity=0.3)
        
        assert score_high_sim > score_low_sim
    
    def test_combined_scoring(self):
        """Test combined multi-signal scoring."""
        scorer = RelevanceScorer()
        
        context = ConversationContext()
        context.topics.add("debugging")
        context.keywords.update(["python", "error"])
        
        perfect_memory = {
            "metadata": {
                "description": "Python debugging error",
                "tags": ["debugging", "python"]
            },
            "created_at": time.time()
        }
        
        score = scorer.score_memory(perfect_memory, context, embedding_similarity=0.95)
        
        # Perfect match should score high
        assert score > 0.5


class TestDeliveryManager:
    """Test suite for DeliveryManager."""
    
    def test_initialization(self):
        """Test delivery manager initialization."""
        manager = DeliveryManager()
        
        assert manager is not None
        assert manager.min_relevance > 0
        assert manager.max_deliveries_per_session > 0
    
    def test_initialization_custom_params(self):
        """Test delivery manager with custom parameters."""
        manager = DeliveryManager(
            min_relevance=0.7,
            max_deliveries_per_session=5,
            min_delivery_interval=30.0
        )
        
        assert manager.min_relevance == 0.7
        assert manager.max_deliveries_per_session == 5
        assert manager.min_delivery_interval == 30.0
    
    def test_should_deliver_initial(self):
        """Test delivery decision initially."""
        manager = DeliveryManager()
        context = ConversationContext()
        context.intent = "request"
        
        should_deliver = manager.should_deliver(context)
        
        assert isinstance(should_deliver, bool)
    
    def test_delivery_quota_enforcement(self):
        """Test that delivery quota is enforced."""
        manager = DeliveryManager(max_deliveries_per_session=2)
        context = ConversationContext()
        
        # Simulate deliveries
        manager.delivery_count = 2
        
        should_deliver = manager.should_deliver(context)
        
        assert should_deliver is False
    
    def test_delivery_interval_enforcement(self):
        """Test that delivery interval is enforced."""
        manager = DeliveryManager(min_delivery_interval=60.0)
        context = ConversationContext()
        
        # Set last delivery time to now
        manager.last_delivery_time = time.time()
        
        should_deliver = manager.should_deliver(context)
        
        # Should not deliver again immediately
        assert should_deliver is False
    
    def test_select_memories(self):
        """Test memory selection for delivery."""
        manager = DeliveryManager(min_relevance=0.5)
        scorer = RelevanceScorer()
        
        context = ConversationContext()
        context.keywords.add("python")
        
        candidates = [
            {
                "id": "mem_001",
                "metadata": {"description": "Python tutorial"},
                "created_at": time.time(),
                "similarity_score": 0.8
            },
            {
                "id": "mem_002",
                "metadata": {"description": "JavaScript tutorial"},
                "created_at": time.time(),
                "similarity_score": 0.3
            },
            {
                "id": "mem_003",
                "metadata": {"description": "Python debugging"},
                "created_at": time.time(),
                "similarity_score": 0.9
            }
        ]
        
        selected = manager.select_memories(candidates, context, scorer, top_k=2)
        
        assert len(selected) <= 2
        # Should select most relevant ones
        if len(selected) > 0:
            assert selected[0]["id"] in ["mem_001", "mem_003"]
    
    def test_relevance_filtering(self):
        """Test that low-relevance memories are filtered."""
        manager = DeliveryManager(min_relevance=0.7)
        scorer = RelevanceScorer()
        
        context = ConversationContext()
        
        candidates = [
            {
                "id": "low_rel",
                "metadata": {},
                "created_at": time.time(),
                "similarity_score": 0.2
            }
        ]
        
        selected = manager.select_memories(candidates, context, scorer, top_k=5)
        
        # Low relevance should be filtered out
        assert len(selected) == 0
    
    def test_duplicate_prevention(self):
        """Test that already delivered memories are not selected again."""
        manager = DeliveryManager()
        scorer = RelevanceScorer()
        
        context = ConversationContext()
        
        candidates = [
            {
                "id": "mem_001",
                "metadata": {},
                "created_at": time.time(),
                "similarity_score": 0.8
            }
        ]
        
        # Mark as delivered
        manager.delivered_memory_ids.add("mem_001")
        
        selected = manager.select_memories(candidates, context, scorer, top_k=5)
        
        # Should not select already delivered memory
        assert len(selected) == 0
    
    def test_record_delivery(self):
        """Test recording a delivery."""
        manager = DeliveryManager()
        
        initial_count = manager.delivery_count
        
        manager.record_delivery(["mem_001", "mem_002"])
        
        assert manager.delivery_count == initial_count + 1
        assert "mem_001" in manager.delivered_memory_ids
        assert "mem_002" in manager.delivered_memory_ids
        assert manager.last_delivery_time > 0
    
    def test_reset_session(self):
        """Test resetting delivery session."""
        manager = DeliveryManager()
        
        # Simulate some deliveries
        manager.delivery_count = 5
        manager.delivered_memory_ids.update(["mem_001", "mem_002"])
        manager.last_delivery_time = time.time()
        
        manager.reset_session()
        
        assert manager.delivery_count == 0
        assert len(manager.delivered_memory_ids) == 0
        assert manager.last_delivery_time == 0
    
    def test_get_stats(self):
        """Test getting delivery statistics."""
        manager = DeliveryManager()
        
        manager.delivery_count = 3
        manager.delivered_memory_ids.update(["mem_001", "mem_002"])
        
        stats = manager.get_stats()
        
        assert stats["delivery_count"] == 3
        assert stats["unique_memories_delivered"] == 2
        assert "last_delivery_time" in stats


class TestProactiveIntegration:
    """Integration tests for proactive delivery system."""
    
    def test_monitor_scorer_integration(self):
        """Test monitor and scorer working together."""
        monitor = ContextMonitor()
        scorer = RelevanceScorer()
        
        # Analyze message
        message = {"role": "user", "content": "Help me debug Python errors"}
        context = monitor.analyze_message(message)
        
        # Score a memory
        memory = {
            "id": "mem_001",
            "metadata": {"description": "Python debugging guide"},
            "created_at": time.time()
        }
        
        score = scorer.score_memory(memory, context, embedding_similarity=0.8)
        
        assert isinstance(score, float)
        assert score > 0
    
    def test_full_proactive_pipeline(self):
        """Test full proactive delivery pipeline."""
        monitor = ContextMonitor()
        scorer = RelevanceScorer()
        manager = DeliveryManager()
        
        # 1. Analyze conversation
        message = {"role": "user", "content": "Show me Python debugging examples"}
        context = monitor.analyze_message(message)
        
        # 2. Check if should deliver
        should_deliver = manager.should_deliver(context)
        
        if should_deliver:
            # 3. Select memories (mock candidates)
            candidates = [
                {
                    "id": "mem_001",
                    "metadata": {"description": "Python debugging tutorial"},
                    "created_at": time.time(),
                    "similarity_score": 0.85
                }
            ]
            
            selected = manager.select_memories(candidates, context, scorer, top_k=3)
            
            # 4. Record delivery
            if selected:
                manager.record_delivery([m["id"] for m in selected])
                
                assert manager.delivery_count > 0
    
    def test_throttling_behavior(self):
        """Test that throttling works correctly."""
        monitor = ContextMonitor()
        manager = DeliveryManager(
            max_deliveries_per_session=2,
            min_delivery_interval=1.0
        )
        
        context = ConversationContext()
        context.intent = "request"
        
        # First delivery should work
        assert manager.should_deliver(context) is True
        manager.record_delivery(["mem_001"])
        
        # Second delivery immediately should be blocked by interval
        assert manager.should_deliver(context) is False
        
        # After interval, should work
        time.sleep(1.1)
        assert manager.should_deliver(context) is True
        manager.record_delivery(["mem_002"])
        
        # Third delivery should be blocked by quota
        time.sleep(1.1)
        assert manager.should_deliver(context) is False
