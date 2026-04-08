# -*- coding: utf-8 -*-
"""Tests for multimodal storage manager."""
import pytest
import shutil
from pathlib import Path
from dominusprime.agents.memory.multimodal.models import MediaType
from dominusprime.agents.memory.multimodal.storage import MediaStorageManager


class TestMediaStorageManager:
    """Test suite for MediaStorageManager."""
    
    def test_initialization(self, temp_dir: Path):
        """Test storage manager initialization."""
        manager = MediaStorageManager(
            storage_dir=temp_dir,
            max_storage_bytes=1024 * 1024  # 1MB
        )
        
        assert manager.storage_dir.exists()
        assert (temp_dir / "images").exists()
        assert (temp_dir / "videos").exists()
        assert (temp_dir / "audio").exists()
        assert (temp_dir / "documents").exists()
        assert (temp_dir / "thumbnails").exists()
    
    def test_store_image(self, temp_dir: Path, sample_image: Path):
        """Test storing an image."""
        manager = MediaStorageManager(storage_dir=temp_dir)
        
        stored_path, thumbnail_path = manager.store_media(
            source_path=sample_image,
            media_type=MediaType.IMAGE,
            session_id="test_session",
            media_id="img_001"
        )
        
        assert stored_path.exists()
        assert stored_path.parent.name == "test_session"
        assert thumbnail_path is not None
        assert thumbnail_path.exists()
    
    def test_store_video(self, temp_dir: Path, sample_video: Path):
        """Test storing a video."""
        manager = MediaStorageManager(storage_dir=temp_dir)
        
        stored_path, thumbnail_path = manager.store_media(
            source_path=sample_video,
            media_type=MediaType.VIDEO,
            session_id="test_session",
            media_id="vid_001"
        )
        
        assert stored_path.exists()
        assert stored_path.suffix == ".mp4"
        # Video thumbnails may or may not be generated depending on opencv
        # Just check the path is returned
        assert thumbnail_path is None or thumbnail_path.exists()
    
    def test_store_audio(self, temp_dir: Path, sample_audio: Path):
        """Test storing audio."""
        manager = MediaStorageManager(storage_dir=temp_dir)
        
        stored_path, thumbnail_path = manager.store_media(
            source_path=sample_audio,
            media_type=MediaType.AUDIO,
            session_id="test_session",
            media_id="aud_001"
        )
        
        assert stored_path.exists()
        assert stored_path.suffix == ".mp3"
        assert thumbnail_path is None  # No thumbnails for audio
    
    def test_store_document(self, temp_dir: Path, sample_document: Path):
        """Test storing a document."""
        manager = MediaStorageManager(storage_dir=temp_dir)
        
        stored_path, thumbnail_path = manager.store_media(
            source_path=sample_document,
            media_type=MediaType.DOCUMENT,
            session_id="test_session",
            media_id="doc_001"
        )
        
        assert stored_path.exists()
        assert stored_path.suffix == ".txt"
        assert thumbnail_path is None  # No thumbnails for documents
    
    def test_quota_enforcement(self, temp_dir: Path, large_image: Path):
        """Test storage quota enforcement."""
        # Set a small quota
        manager = MediaStorageManager(
            storage_dir=temp_dir,
            max_storage_bytes=1024  # 1KB only
        )
        
        # Try to store a large file
        with pytest.raises(RuntimeError, match="Storage quota exceeded"):
            manager.store_media(
                source_path=large_image,
                media_type=MediaType.IMAGE,
                session_id="test_session",
                media_id="large_img"
            )
    
    def test_get_storage_usage(self, temp_dir: Path, sample_image: Path):
        """Test storage usage calculation."""
        manager = MediaStorageManager(storage_dir=temp_dir)
        
        initial_usage = manager.get_storage_usage()
        
        manager.store_media(
            source_path=sample_image,
            media_type=MediaType.IMAGE,
            session_id="test_session",
            media_id="img_001"
        )
        
        after_usage = manager.get_storage_usage()
        assert after_usage > initial_usage
    
    def test_delete_media(self, temp_dir: Path, sample_image: Path):
        """Test media deletion."""
        manager = MediaStorageManager(storage_dir=temp_dir)
        
        stored_path, thumbnail_path = manager.store_media(
            source_path=sample_image,
            media_type=MediaType.IMAGE,
            session_id="test_session",
            media_id="img_001"
        )
        
        assert stored_path.exists()
        
        manager.delete_media(stored_path)
        
        assert not stored_path.exists()
        if thumbnail_path:
            assert not thumbnail_path.exists()
    
    def test_cleanup_session(self, temp_dir: Path, multiple_images: list[Path]):
        """Test cleaning up a session."""
        manager = MediaStorageManager(storage_dir=temp_dir)
        session_id = "test_session"
        
        # Store multiple images
        for i, img in enumerate(multiple_images):
            manager.store_media(
                source_path=img,
                media_type=MediaType.IMAGE,
                session_id=session_id,
                media_id=f"img_{i:03d}"
            )
        
        session_dir = temp_dir / "images" / session_id
        assert session_dir.exists()
        assert len(list(session_dir.glob("*"))) > 0
        
        manager.cleanup_session(session_id, MediaType.IMAGE)
        
        assert not session_dir.exists() or len(list(session_dir.glob("*"))) == 0
    
    def test_duplicate_handling(self, temp_dir: Path, sample_image: Path):
        """Test handling of duplicate media."""
        manager = MediaStorageManager(storage_dir=temp_dir, enable_deduplication=True)
        
        # Store the same image twice
        stored_path1, _ = manager.store_media(
            source_path=sample_image,
            media_type=MediaType.IMAGE,
            session_id="session1",
            media_id="img_001"
        )
        
        stored_path2, _ = manager.store_media(
            source_path=sample_image,
            media_type=MediaType.IMAGE,
            session_id="session2",
            media_id="img_002"
        )
        
        # With deduplication, both should point to same file or have same hash
        # The exact behavior depends on implementation
        assert stored_path1.exists()
        assert stored_path2.exists()
    
    def test_thumbnail_generation(self, temp_dir: Path, sample_image: Path):
        """Test thumbnail generation for images."""
        manager = MediaStorageManager(storage_dir=temp_dir)
        
        _, thumbnail_path = manager.store_media(
            source_path=sample_image,
            media_type=MediaType.IMAGE,
            session_id="test_session",
            media_id="img_001"
        )
        
        assert thumbnail_path is not None
        assert thumbnail_path.exists()
        
        # Check thumbnail is smaller than original
        from PIL import Image
        with Image.open(thumbnail_path) as thumb:
            assert thumb.width <= 256 or thumb.height <= 256
    
    def test_list_media(self, temp_dir: Path, multiple_images: list[Path]):
        """Test listing media in storage."""
        manager = MediaStorageManager(storage_dir=temp_dir)
        session_id = "test_session"
        
        stored_paths = []
        for i, img in enumerate(multiple_images):
            path, _ = manager.store_media(
                source_path=img,
                media_type=MediaType.IMAGE,
                session_id=session_id,
                media_id=f"img_{i:03d}"
            )
            stored_paths.append(path)
        
        listed = manager.list_media(session_id=session_id, media_type=MediaType.IMAGE)
        
        assert len(listed) == len(multiple_images)
        for path in stored_paths:
            assert path in listed
    
    def test_get_media_info(self, temp_dir: Path, sample_image: Path):
        """Test retrieving media information."""
        manager = MediaStorageManager(storage_dir=temp_dir)
        
        stored_path, _ = manager.store_media(
            source_path=sample_image,
            media_type=MediaType.IMAGE,
            session_id="test_session",
            media_id="img_001"
        )
        
        info = manager.get_media_info(stored_path)
        
        assert info is not None
        assert "size" in info
        assert "modified" in info
        assert info["size"] > 0
    
    def test_invalid_media_type(self, temp_dir: Path, sample_image: Path):
        """Test handling of invalid media type."""
        manager = MediaStorageManager(storage_dir=temp_dir)
        
        with pytest.raises((ValueError, AttributeError)):
            manager.store_media(
                source_path=sample_image,
                media_type="invalid_type",  # type: ignore
                session_id="test_session",
                media_id="img_001"
            )
    
    def test_missing_source_file(self, temp_dir: Path):
        """Test handling of missing source file."""
        manager = MediaStorageManager(storage_dir=temp_dir)
        
        with pytest.raises(FileNotFoundError):
            manager.store_media(
                source_path=Path("/nonexistent/file.png"),
                media_type=MediaType.IMAGE,
                session_id="test_session",
                media_id="img_001"
            )
    
    def test_concurrent_storage(self, temp_dir: Path, multiple_images: list[Path]):
        """Test concurrent media storage operations."""
        import asyncio
        
        manager = MediaStorageManager(storage_dir=temp_dir)
        
        async def store_image(img: Path, idx: int):
            return manager.store_media(
                source_path=img,
                media_type=MediaType.IMAGE,
                session_id=f"session_{idx}",
                media_id=f"img_{idx:03d}"
            )
        
        async def run_concurrent():
            tasks = [store_image(img, i) for i, img in enumerate(multiple_images)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        
        results = asyncio.run(run_concurrent())
        
        # All should succeed
        for result in results:
            assert not isinstance(result, Exception)
            assert isinstance(result, tuple)
            assert len(result) == 2
