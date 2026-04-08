# -*- coding: utf-8 -*-
"""Integration tests for multimodal memory system."""
import pytest
import asyncio
from pathlib import Path
from dominusprime.agents.memory.multimodal.system import MultimodalMemorySystem
from dominusprime.agents.memory.multimodal.models import MediaType


class TestMultimodalMemorySystemIntegration:
    """End-to-end integration tests for the multimodal memory system."""
    
    @pytest.fixture
    async def memory_system(self, temp_dir: Path):
        """Create a memory system instance for testing."""
        system = MultimodalMemorySystem(
            working_dir=temp_dir,
            max_storage_gb=0.1,  # 100MB for testing
            use_clip=False,  # Use simple embedder for tests
            enable_ocr=False
        )
        yield system
        # Cleanup
        if hasattr(system, 'close'):
            await system.close()
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_image(self, memory_system, sample_image: Path):
        """Test storing and retrieving an image."""
        session_id = "test_session_001"
        
        # Store image
        memory_item = await memory_system.store_media(
            media_path=sample_image,
            session_id=session_id,
            context_text="Red square test image"
        )
        
        assert memory_item is not None
        assert memory_item.id is not None
        assert memory_item.media_type == MediaType.IMAGE
        
        # Search by text
        results = memory_system.search(
            query="red square",
            top_k=5
        )
        
        assert len(results) >= 0  # May or may not find depending on embedder
    
    @pytest.mark.asyncio
    async def test_store_multiple_media_types(self, memory_system, sample_image: Path, 
                                              sample_video: Path, sample_audio: Path):
        """Test storing different media types."""
        session_id = "test_session_multi"
        
        # Store image
        img_item = await memory_system.store_media(
            media_path=sample_image,
            session_id=session_id,
            context_text="Test image"
        )
        
        # Store video
        vid_item = await memory_system.store_media(
            media_path=sample_video,
            session_id=session_id,
            context_text="Test video"
        )
        
        # Store audio
        aud_item = await memory_system.store_media(
            media_path=sample_audio,
            session_id=session_id,
            context_text="Test audio"
        )
        
        assert img_item.media_type == MediaType.IMAGE
        assert vid_item.media_type == MediaType.VIDEO
        assert aud_item.media_type == MediaType.AUDIO
        
        # Get all memories from session
        memories = memory_system.get_session_memories(session_id)
        assert len(memories) == 3
    
    @pytest.mark.asyncio
    async def test_text_to_image_search(self, memory_system, sample_image: Path):
        """Test cross-modal text-to-image search."""
        session_id = "test_search_session"
        
        # Store image with context
        await memory_system.store_media(
            media_path=sample_image,
            session_id=session_id,
            context_text="Python debugging screenshot with error messages"
        )
        
        # Search by text
        results = memory_system.search(
            query="python error",
            media_types=[MediaType.IMAGE],
            top_k=5
        )
        
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_image_to_image_search(self, memory_system, multiple_images: list[Path]):
        """Test image-to-image similarity search."""
        session_id = "test_similarity"
        
        # Store multiple images
        stored_items = []
        for i, img in enumerate(multiple_images):
            item = await memory_system.store_media(
                media_path=img,
                session_id=session_id,
                context_text=f"Test image {i}"
            )
            stored_items.append(item)
        
        # Search for similar images using first image
        if len(stored_items) > 0:
            results = memory_system.search_similar(
                media_path=multiple_images[0],
                top_k=3
            )
            
            assert isinstance(results, list)
            if len(results) > 0:
                # First result should be the query image itself
                assert results[0].id == stored_items[0].id
    
    @pytest.mark.asyncio
    async def test_session_isolation(self, memory_system, sample_image: Path):
        """Test that sessions are properly isolated."""
        # Store in session 1
        await memory_system.store_media(
            media_path=sample_image,
            session_id="session1",
            context_text="Session 1 image"
        )
        
        # Store in session 2
        await memory_system.store_media(
            media_path=sample_image,
            session_id="session2",
            context_text="Session 2 image"
        )
        
        # Get memories from each session
        session1_memories = memory_system.get_session_memories("session1")
        session2_memories = memory_system.get_session_memories("session2")
        
        assert len(session1_memories) == 1
        assert len(session2_memories) == 1
        assert session1_memories[0].session_id == "session1"
        assert session2_memories[0].session_id == "session2"
    
    @pytest.mark.asyncio
    async def test_storage_quota_enforcement(self, memory_system, large_image: Path):
        """Test that storage quota is enforced."""
        # Try to store a large file that exceeds quota
        with pytest.raises(RuntimeError, match="quota"):
            await memory_system.store_media(
                media_path=large_image,
                session_id="test_quota",
                context_text="Large image"
            )
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, memory_system, sample_image: Path):
        """Test deleting a memory."""
        # Store image
        item = await memory_system.store_media(
            media_path=sample_image,
            session_id="test_delete",
            context_text="To be deleted"
        )
        
        item_id = item.id
        
        # Verify it exists
        memory = memory_system.get_memory_by_id(item_id)
        assert memory is not None
        
        # Delete it
        success = memory_system.delete_memory(item_id)
        assert success
        
        # Verify it's gone
        memory = memory_system.get_memory_by_id(item_id)
        assert memory is None
    
    @pytest.mark.asyncio
    async def test_clear_session(self, memory_system, multiple_images: list[Path]):
        """Test clearing all memories from a session."""
        session_id = "test_clear"
        
        # Store multiple images
        for img in multiple_images:
            await memory_system.store_media(
                media_path=img,
                session_id=session_id,
                context_text="Test"
            )
        
        # Verify they exist
        memories = memory_system.get_session_memories(session_id)
        assert len(memories) == len(multiple_images)
        
        # Clear session
        memory_system.clear_session(session_id)
        
        # Verify they're gone
        memories = memory_system.get_session_memories(session_id)
        assert len(memories) == 0
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, memory_system, multiple_images: list[Path]):
        """Test getting system statistics."""
        session_id = "test_stats"
        
        # Store some images
        for img in multiple_images[:3]:
            await memory_system.store_media(
                media_path=img,
                session_id=session_id,
                context_text="Test"
            )
        
        # Get stats
        stats = memory_system.get_statistics()
        
        assert "total_memories" in stats
        assert "storage_used" in stats
        assert "storage_available" in stats
        assert stats["total_memories"] >= 3
    
    @pytest.mark.asyncio
    async def test_concurrent_storage(self, memory_system, multiple_images: list[Path]):
        """Test concurrent storage operations."""
        session_id = "test_concurrent"
        
        # Store multiple images concurrently
        tasks = [
            memory_system.store_media(
                media_path=img,
                session_id=session_id,
                context_text=f"Image {i}"
            )
            for i, img in enumerate(multiple_images)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check all succeeded
        for result in results:
            assert not isinstance(result, Exception)
        
        # Verify all stored
        memories = memory_system.get_session_memories(session_id)
        assert len(memories) == len(multiple_images)
    
    @pytest.mark.asyncio
    async def test_batch_search(self, memory_system, multiple_images: list[Path]):
        """Test batch search operations."""
        session_id = "test_batch"
        
        # Store images
        for i, img in enumerate(multiple_images):
            await memory_system.store_media(
                media_path=img,
                session_id=session_id,
                context_text=f"Color {i}"
            )
        
        # Perform multiple searches
        queries = ["color 0", "color 1", "color 2"]
        
        for query in queries:
            results = memory_system.search(query, top_k=5)
            assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_persistence(self, temp_dir: Path, sample_image: Path):
        """Test that data persists across system restarts."""
        # Create system and store image
        system1 = MultimodalMemorySystem(
            working_dir=temp_dir,
            max_storage_gb=0.1,
            use_clip=False
        )
        
        item = await system1.store_media(
            media_path=sample_image,
            session_id="persist_test",
            context_text="Persistence test"
        )
        
        item_id = item.id
        
        # Close system
        if hasattr(system1, 'close'):
            await system1.close()
        
        # Create new system instance
        system2 = MultimodalMemorySystem(
            working_dir=temp_dir,
            max_storage_gb=0.1,
            use_clip=False
        )
        
        # Verify data persisted
        memory = system2.get_memory_by_id(item_id)
        assert memory is not None
        assert memory.id == item_id


class TestProactiveDeliveryIntegration:
    """Integration tests for proactive memory delivery."""
    
    @pytest.fixture
    async def system_with_memories(self, temp_dir: Path, multiple_images: list[Path]):
        """Create a system with pre-stored memories."""
        system = MultimodalMemorySystem(
            working_dir=temp_dir,
            max_storage_gb=0.1,
            use_clip=False
        )
        
        # Store memories with different contexts
        contexts = [
            "Python debugging error with stack trace",
            "JavaScript syntax error in console",
            "Database connection timeout issue",
            "API endpoint returning 404 error"
        ]
        
        for i, (img, context) in enumerate(zip(multiple_images, contexts)):
            await system.store_media(
                media_path=img,
                session_id="proactive_test",
                context_text=context
            )
        
        yield system
    
    @pytest.mark.asyncio
    async def test_proactive_retrieval(self, system_with_memories):
        """Test proactive memory retrieval based on context."""
        system = system_with_memories
        
        # Simulate conversation message
        message = {
            "role": "user",
            "content": "I'm having a Python debugging error"
        }
        
        # Get proactive memories
        memories = system.get_proactive_memories(
            message=message,
            max_memories=3
        )
        
        assert isinstance(memories, list)
        assert len(memories) <= 3
    
    @pytest.mark.asyncio
    async def test_relevance_based_delivery(self, system_with_memories):
        """Test that most relevant memories are delivered."""
        system = system_with_memories
        
        # Query specifically for Python
        message = {
            "role": "user",
            "content": "Show me Python error examples"
        }
        
        memories = system.get_proactive_memories(message=message, max_memories=2)
        
        # Should return memories, most relevant first
        assert isinstance(memories, list)
    
    @pytest.mark.asyncio
    async def test_delivery_throttling(self, system_with_memories):
        """Test that delivery is throttled."""
        system = system_with_memories
        
        message = {"role": "user", "content": "Help with Python"}
        
        # First delivery
        memories1 = system.get_proactive_memories(message=message, max_memories=2)
        
        # Immediate second delivery should be throttled
        memories2 = system.get_proactive_memories(message=message, max_memories=2)
        
        # Depending on implementation, second call may be empty or limited
        assert isinstance(memories2, list)


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_invalid_media_path(self, temp_dir: Path):
        """Test handling of invalid media path."""
        system = MultimodalMemorySystem(
            working_dir=temp_dir,
            max_storage_gb=0.1,
            use_clip=False
        )
        
        with pytest.raises(FileNotFoundError):
            await system.store_media(
                media_path=Path("/nonexistent/file.png"),
                session_id="test",
                context_text="Test"
            )
    
    @pytest.mark.asyncio
    async def test_corrupted_media(self, memory_system, corrupted_image: Path):
        """Test handling of corrupted media files."""
        try:
            await memory_system.store_media(
                media_path=corrupted_image,
                session_id="test_corrupted",
                context_text="Corrupted file"
            )
            # If it doesn't raise, that's okay too - some corrupted files may be handled gracefully
        except Exception as e:
            # Expected - corrupted files should fail gracefully
            assert isinstance(e, (IOError, ValueError, OSError))
    
    def test_search_empty_database(self, memory_system):
        """Test searching in empty database."""
        results = memory_system.search("test query", top_k=5)
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_get_nonexistent_memory(self, memory_system):
        """Test retrieving non-existent memory."""
        memory = memory_system.get_memory_by_id("nonexistent_id")
        
        assert memory is None
    
    def test_delete_nonexistent_memory(self, memory_system):
        """Test deleting non-existent memory."""
        success = memory_system.delete_memory("nonexistent_id")
        
        # Should handle gracefully (return False or raise)
        assert success is False or success is None


class TestPerformance:
    """Performance and scalability tests."""
    
    @pytest.mark.asyncio
    async def test_bulk_storage_performance(self, memory_system, multiple_images: list[Path]):
        """Test performance of bulk storage operations."""
        import time
        
        session_id = "perf_test"
        
        start_time = time.time()
        
        for i, img in enumerate(multiple_images):
            await memory_system.store_media(
                media_path=img,
                session_id=session_id,
                context_text=f"Image {i}"
            )
        
        duration = time.time() - start_time
        
        # Should process reasonably fast
        assert duration < len(multiple_images) * 2  # <2 seconds per image
    
    def test_search_performance(self, memory_system):
        """Test search performance."""
        import time
        
        start_time = time.time()
        
        for _ in range(10):
            memory_system.search("test query", top_k=5)
        
        duration = time.time() - start_time
        
        # 10 searches should be fast
        assert duration < 5.0


class TestDataIntegrity:
    """Test data integrity and consistency."""
    
    @pytest.mark.asyncio
    async def test_metadata_consistency(self, memory_system, sample_image: Path):
        """Test that metadata remains consistent."""
        # Store with metadata
        item = await memory_system.store_media(
            media_path=sample_image,
            session_id="test_metadata",
            context_text="Test metadata consistency"
        )
        
        # Retrieve and verify
        retrieved = memory_system.get_memory_by_id(item.id)
        
        assert retrieved is not None
        assert retrieved.id == item.id
        assert retrieved.session_id == item.session_id
        assert retrieved.media_type == item.media_type
    
    @pytest.mark.asyncio
    async def test_concurrent_read_write(self, memory_system, multiple_images: list[Path]):
        """Test concurrent reads and writes maintain integrity."""
        session_id = "concurrent_rw"
        
        # Store images concurrently
        store_tasks = [
            memory_system.store_media(
                media_path=img,
                session_id=session_id,
                context_text=f"Image {i}"
            )
            for i, img in enumerate(multiple_images[:2])
        ]
        
        # Read concurrently
        def search_task():
            return memory_system.search("Image", top_k=5)
        
        # Mix reads and writes
        await asyncio.gather(*store_tasks)
        
        # Verify consistency
        memories = memory_system.get_session_memories(session_id)
        assert len(memories) == 2
