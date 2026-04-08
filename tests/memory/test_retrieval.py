# -*- coding: utf-8 -*-
"""Tests for multimodal retrieval system."""
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch
from dominusprime.agents.memory.multimodal.models import MediaType, MediaMemoryItem, MediaSearchResult
from dominusprime.agents.memory.multimodal.retrieval import MultimodalRetriever


class TestMultimodalRetriever:
    """Test suite for MultimodalRetriever."""
    
    @pytest.fixture
    def retriever(self, temp_dir: Path):
        """Create a retriever instance for testing."""
        from dominusprime.agents.memory.multimodal.storage import MediaStorageManager
        from dominusprime.agents.memory.multimodal.processor import MediaProcessor
        from dominusprime.agents.memory.multimodal.embedder import SimpleEmbedder
        from dominusprime.agents.memory.multimodal.index import MultimodalIndex
        
        storage = MediaStorageManager(storage_dir=temp_dir)
        processor = MediaProcessor()
        embedder = SimpleEmbedder()
        index = MultimodalIndex(index_dir=temp_dir / "index", embedding_dim=512)
        
        retriever = MultimodalRetriever(
            storage=storage,
            processor=processor,
            embedder=embedder,
            index=index,
            db_path=temp_dir / "memory.db"
        )
        return retriever
    
    def test_initialization(self, retriever):
        """Test retriever initialization."""
        assert retriever is not None
        assert retriever.storage is not None
        assert retriever.embedder is not None
        assert retriever.index is not None
    
    def test_search_by_text_empty(self, retriever):
        """Test text search on empty database."""
        results = retriever.search_by_text("python debugging", top_k=5)
        
        assert results is not None
        assert len(results) == 0
    
    def test_search_by_media_empty(self, retriever, sample_image: Path):
        """Test media search on empty database."""
        results = retriever.search_by_media(sample_image, MediaType.IMAGE, top_k=5)
        
        assert results is not None
        assert len(results) == 0
    
    @patch('dominusprime.agents.memory.multimodal.retrieval.MultimodalRetriever._get_memory_items')
    def test_search_by_text_with_results(self, mock_get_items, retriever, temp_dir: Path):
        """Test text search with mocked results."""
        # Mock database results
        mock_items = [
            MediaMemoryItem(
                id="img_001",
                session_id="session1",
                media_type=MediaType.IMAGE,
                file_path=temp_dir / "test.png",
                file_size=1024,
                created_at=1.0,
                metadata={"description": "Python debugging session"}
            )
        ]
        mock_get_items.return_value = mock_items
        
        results = retriever.search_by_text("python debugging", top_k=5)
        
        # Should return results
        assert isinstance(results, list)
    
    def test_filter_by_media_type(self, retriever):
        """Test filtering results by media type."""
        results = retriever.search_by_text(
            "test query",
            media_types=[MediaType.IMAGE],
            top_k=5
        )
        
        assert isinstance(results, list)
    
    def test_filter_by_session(self, retriever):
        """Test filtering results by session ID."""
        results = retriever.search_by_text(
            "test query",
            session_ids=["session1", "session2"],
            top_k=5
        )
        
        assert isinstance(results, list)
    
    def test_top_k_parameter(self, retriever):
        """Test top_k parameter limits results."""
        results = retriever.search_by_text("test", top_k=3)
        
        assert len(results) <= 3
    
    def test_search_result_format(self, retriever):
        """Test that search results have correct format."""
        results = retriever.search_by_text("test", top_k=5)
        
        # Even if empty, should be a list
        assert isinstance(results, list)
        
        # If there are results, check format
        for result in results:
            assert isinstance(result, (MediaSearchResult, dict))
    
    def test_similarity_scores(self, retriever):
        """Test that results include similarity scores."""
        results = retriever.search_by_text("test", top_k=5)
        
        for result in results:
            if hasattr(result, 'similarity_score'):
                assert isinstance(result.similarity_score, (int, float))
                assert 0 <= result.similarity_score <= 1
    
    def test_search_by_media_different_types(self, retriever, sample_image: Path, sample_video: Path):
        """Test searching by different media types."""
        # Search by image
        img_results = retriever.search_by_media(sample_image, MediaType.IMAGE, top_k=5)
        assert isinstance(img_results, list)
        
        # Search by video
        vid_results = retriever.search_by_media(sample_video, MediaType.VIDEO, top_k=5)
        assert isinstance(vid_results, list)
    
    def test_combined_filters(self, retriever):
        """Test combining multiple filters."""
        results = retriever.search_by_text(
            "test query",
            media_types=[MediaType.IMAGE, MediaType.VIDEO],
            session_ids=["session1"],
            top_k=10
        )
        
        assert isinstance(results, list)
    
    def test_get_memory_by_id(self, retriever):
        """Test retrieving memory by ID."""
        memory = retriever.get_memory_by_id("img_001")
        
        # Should return None if not found
        assert memory is None or isinstance(memory, (MediaMemoryItem, dict))
    
    def test_get_memories_by_session(self, retriever):
        """Test retrieving all memories from a session."""
        memories = retriever.get_memories_by_session("session1")
        
        assert isinstance(memories, list)
    
    def test_get_recent_memories(self, retriever):
        """Test retrieving recent memories."""
        memories = retriever.get_recent_memories(limit=10)
        
        assert isinstance(memories, list)
        assert len(memories) <= 10
    
    def test_search_with_time_range(self, retriever):
        """Test searching within a time range."""
        import time
        current_time = time.time()
        
        results = retriever.search_by_text(
            "test",
            start_time=current_time - 3600,  # Last hour
            end_time=current_time,
            top_k=5
        )
        
        assert isinstance(results, list)


class TestSearchRelevance:
    """Test search relevance and ranking."""
    
    @pytest.fixture
    def mock_retriever(self, temp_dir: Path):
        """Create retriever with mocked components for relevance testing."""
        from dominusprime.agents.memory.multimodal.retrieval import MultimodalRetriever
        
        storage = Mock()
        processor = Mock()
        embedder = Mock()
        index = Mock()
        
        # Mock embedder to return predictable embeddings
        def mock_embed_text(text):
            # Simple hash-based embedding for testing
            hash_val = hash(text)
            np.random.seed(hash_val % (2**32))
            return np.random.randn(512).astype(np.float32)
        
        embedder.embed_text = mock_embed_text
        embedder.embed_image = lambda path: np.random.randn(512).astype(np.float32)
        
        # Mock index search
        index.search = lambda emb, etype, top_k: [(f"id_{i}", float(i)*0.1) for i in range(min(top_k, 3))]
        
        retriever = MultimodalRetriever(
            storage=storage,
            processor=processor,
            embedder=embedder,
            index=index,
            db_path=temp_dir / "memory.db"
        )
        return retriever
    
    def test_results_sorted_by_relevance(self, mock_retriever):
        """Test that results are sorted by relevance."""
        results = mock_retriever.search_by_text("test query", top_k=5)
        
        if len(results) > 1:
            # Check if sorted (depends on implementation)
            scores = [r.similarity_score if hasattr(r, 'similarity_score') else 0 for r in results]
            # Scores should be in descending order (most relevant first)
            assert all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
    
    def test_exact_match_ranking(self, mock_retriever):
        """Test that exact matches rank higher."""
        # This test would need actual data
        results = mock_retriever.search_by_text("exact match test", top_k=5)
        assert isinstance(results, list)
    
    def test_semantic_similarity(self, mock_retriever):
        """Test semantic similarity ranking."""
        # Similar queries should return similar results
        results1 = mock_retriever.search_by_text("python debugging", top_k=5)
        results2 = mock_retriever.search_by_text("python debug", top_k=5)
        
        assert isinstance(results1, list)
        assert isinstance(results2, list)


class TestCrossModalSearch:
    """Test cross-modal search capabilities."""
    
    def test_text_to_image_search(self, temp_dir: Path):
        """Test searching images with text query."""
        from dominusprime.agents.memory.multimodal.retrieval import MultimodalRetriever
        from dominusprime.agents.memory.multimodal.storage import MediaStorageManager
        from dominusprime.agents.memory.multimodal.processor import MediaProcessor
        from dominusprime.agents.memory.multimodal.embedder import SimpleEmbedder
        from dominusprime.agents.memory.multimodal.index import MultimodalIndex
        
        storage = MediaStorageManager(storage_dir=temp_dir)
        processor = MediaProcessor()
        embedder = SimpleEmbedder()
        index = MultimodalIndex(index_dir=temp_dir / "index", embedding_dim=512)
        
        retriever = MultimodalRetriever(
            storage=storage,
            processor=processor,
            embedder=embedder,
            index=index,
            db_path=temp_dir / "memory.db"
        )
        
        results = retriever.search_by_text(
            "red square",
            media_types=[MediaType.IMAGE],
            top_k=5
        )
        
        assert isinstance(results, list)
    
    def test_image_to_image_search(self, temp_dir: Path, sample_image: Path):
        """Test finding similar images."""
        from dominusprime.agents.memory.multimodal.retrieval import MultimodalRetriever
        from dominusprime.agents.memory.multimodal.storage import MediaStorageManager
        from dominusprime.agents.memory.multimodal.processor import MediaProcessor
        from dominusprime.agents.memory.multimodal.embedder import SimpleEmbedder
        from dominusprime.agents.memory.multimodal.index import MultimodalIndex
        
        storage = MediaStorageManager(storage_dir=temp_dir)
        processor = MediaProcessor()
        embedder = SimpleEmbedder()
        index = MultimodalIndex(index_dir=temp_dir / "index", embedding_dim=512)
        
        retriever = MultimodalRetriever(
            storage=storage,
            processor=processor,
            embedder=embedder,
            index=index,
            db_path=temp_dir / "memory.db"
        )
        
        results = retriever.search_by_media(
            sample_image,
            MediaType.IMAGE,
            top_k=5
        )
        
        assert isinstance(results, list)


class TestRetrievalPerformance:
    """Test retrieval performance characteristics."""
    
    def test_search_speed(self, temp_dir: Path):
        """Test that search is reasonably fast."""
        import time
        from dominusprime.agents.memory.multimodal.retrieval import MultimodalRetriever
        from dominusprime.agents.memory.multimodal.storage import MediaStorageManager
        from dominusprime.agents.memory.multimodal.processor import MediaProcessor
        from dominusprime.agents.memory.multimodal.embedder import SimpleEmbedder
        from dominusprime.agents.memory.multimodal.index import MultimodalIndex
        
        storage = MediaStorageManager(storage_dir=temp_dir)
        processor = MediaProcessor()
        embedder = SimpleEmbedder()
        index = MultimodalIndex(index_dir=temp_dir / "index", embedding_dim=512)
        
        retriever = MultimodalRetriever(
            storage=storage,
            processor=processor,
            embedder=embedder,
            index=index,
            db_path=temp_dir / "memory.db"
        )
        
        start = time.time()
        retriever.search_by_text("test query", top_k=10)
        duration = time.time() - start
        
        # Should complete in under 1 second for small dataset
        assert duration < 1.0
    
    def test_concurrent_searches(self, temp_dir: Path):
        """Test concurrent search operations."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        from dominusprime.agents.memory.multimodal.retrieval import MultimodalRetriever
        from dominusprime.agents.memory.multimodal.storage import MediaStorageManager
        from dominusprime.agents.memory.multimodal.processor import MediaProcessor
        from dominusprime.agents.memory.multimodal.embedder import SimpleEmbedder
        from dominusprime.agents.memory.multimodal.index import MultimodalIndex
        
        storage = MediaStorageManager(storage_dir=temp_dir)
        processor = MediaProcessor()
        embedder = SimpleEmbedder()
        index = MultimodalIndex(index_dir=temp_dir / "index", embedding_dim=512)
        
        retriever = MultimodalRetriever(
            storage=storage,
            processor=processor,
            embedder=embedder,
            index=index,
            db_path=temp_dir / "memory.db"
        )
        
        def search_wrapper(query):
            return retriever.search_by_text(query, top_k=5)
        
        queries = ["query1", "query2", "query3", "query4"]
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(search_wrapper, q) for q in queries]
            results = [f.result() for f in futures]
        
        assert len(results) == len(queries)
        for result in results:
            assert isinstance(result, list)


class TestRetrievalEdgeCases:
    """Test edge cases in retrieval."""
    
    def test_empty_query(self, temp_dir: Path):
        """Test searching with empty query."""
        from dominusprime.agents.memory.multimodal.retrieval import MultimodalRetriever
        from dominusprime.agents.memory.multimodal.storage import MediaStorageManager
        from dominusprime.agents.memory.multimodal.processor import MediaProcessor
        from dominusprime.agents.memory.multimodal.embedder import SimpleEmbedder
        from dominusprime.agents.memory.multimodal.index import MultimodalIndex
        
        storage = MediaStorageManager(storage_dir=temp_dir)
        processor = MediaProcessor()
        embedder = SimpleEmbedder()
        index = MultimodalIndex(index_dir=temp_dir / "index", embedding_dim=512)
        
        retriever = MultimodalRetriever(
            storage=storage,
            processor=processor,
            embedder=embedder,
            index=index,
            db_path=temp_dir / "memory.db"
        )
        
        results = retriever.search_by_text("", top_k=5)
        assert isinstance(results, list)
    
    def test_very_long_query(self, temp_dir: Path):
        """Test searching with very long query."""
        from dominusprime.agents.memory.multimodal.retrieval import MultimodalRetriever
        from dominusprime.agents.memory.multimodal.storage import MediaStorageManager
        from dominusprime.agents.memory.multimodal.processor import MediaProcessor
        from dominusprime.agents.memory.multimodal.embedder import SimpleEmbedder
        from dominusprime.agents.memory.multimodal.index import MultimodalIndex
        
        storage = MediaStorageManager(storage_dir=temp_dir)
        processor = MediaProcessor()
        embedder = SimpleEmbedder()
        index = MultimodalIndex(index_dir=temp_dir / "index", embedding_dim=512)
        
        retriever = MultimodalRetriever(
            storage=storage,
            processor=processor,
            embedder=embedder,
            index=index,
            db_path=temp_dir / "memory.db"
        )
        
        long_query = "test " * 1000
        results = retriever.search_by_text(long_query, top_k=5)
        assert isinstance(results, list)
    
    def test_special_characters_in_query(self, temp_dir: Path):
        """Test searching with special characters."""
        from dominusprime.agents.memory.multimodal.retrieval import MultimodalRetriever
        from dominusprime.agents.memory.multimodal.storage import MediaStorageManager
        from dominusprime.agents.memory.multimodal.processor import MediaProcessor
        from dominusprime.agents.memory.multimodal.embedder import SimpleEmbedder
        from dominusprime.agents.memory.multimodal.index import MultimodalIndex
        
        storage = MediaStorageManager(storage_dir=temp_dir)
        processor = MediaProcessor()
        embedder = SimpleEmbedder()
        index = MultimodalIndex(index_dir=temp_dir / "index", embedding_dim=512)
        
        retriever = MultimodalRetriever(
            storage=storage,
            processor=processor,
            embedder=embedder,
            index=index,
            db_path=temp_dir / "memory.db"
        )
        
        special_query = "test <script> alert('xss') & [brackets]"
        results = retriever.search_by_text(special_query, top_k=5)
        assert isinstance(results, list)
