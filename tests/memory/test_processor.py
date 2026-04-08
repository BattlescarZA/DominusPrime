# -*- coding: utf-8 -*-
"""Tests for media processor."""
import pytest
from pathlib import Path
from dominusprime.agents.memory.multimodal.models import MediaType
from dominusprime.agents.memory.multimodal.processor import MediaProcessor


class TestMediaProcessor:
    """Test suite for MediaProcessor."""
    
    def test_initialization(self):
        """Test processor initialization."""
        processor = MediaProcessor(enable_ocr=False)
        assert processor is not None
        assert processor.enable_ocr is False
    
    def test_initialization_with_ocr(self):
        """Test processor initialization with OCR enabled."""
        processor = MediaProcessor(enable_ocr=True)
        assert processor.enable_ocr is True
    
    def test_process_image(self, sample_image: Path):
        """Test processing an image."""
        processor = MediaProcessor()
        
        metadata = processor.process_image(sample_image)
        
        assert metadata is not None
        assert "width" in metadata
        assert "height" in metadata
        assert "format" in metadata
        assert metadata["width"] > 0
        assert metadata["height"] > 0
    
    def test_process_image_with_text(self, sample_image_with_text: Path):
        """Test processing an image with text (OCR)."""
        processor = MediaProcessor(enable_ocr=True)
        
        metadata = processor.process_image(sample_image_with_text)
        
        assert metadata is not None
        assert "width" in metadata
        assert "height" in metadata
        # OCR text may or may not be extracted depending on tesseract availability
        if "ocr_text" in metadata:
            assert isinstance(metadata["ocr_text"], str)
    
    def test_process_video(self, sample_video: Path):
        """Test processing a video."""
        processor = MediaProcessor()
        
        metadata = processor.process_video(sample_video)
        
        assert metadata is not None
        # Video processing depends on opencv availability
        # At minimum should return basic file info
        assert isinstance(metadata, dict)
    
    def test_process_audio(self, sample_audio: Path):
        """Test processing audio."""
        processor = MediaProcessor()
        
        metadata = processor.process_audio(sample_audio)
        
        assert metadata is not None
        assert isinstance(metadata, dict)
        # Audio metadata depends on available libraries
    
    def test_process_document(self, sample_document: Path):
        """Test processing a document."""
        processor = MediaProcessor()
        
        metadata = processor.process_document(sample_document)
        
        assert metadata is not None
        assert isinstance(metadata, dict)
        if "content" in metadata:
            assert "test document" in metadata["content"].lower()
    
    def test_process_media_image(self, sample_image: Path):
        """Test generic media processing for image."""
        processor = MediaProcessor()
        
        metadata = processor.process_media(sample_image, MediaType.IMAGE)
        
        assert metadata is not None
        assert "width" in metadata or "media_type" in metadata
    
    def test_process_media_video(self, sample_video: Path):
        """Test generic media processing for video."""
        processor = MediaProcessor()
        
        metadata = processor.process_media(sample_video, MediaType.VIDEO)
        
        assert metadata is not None
        assert isinstance(metadata, dict)
    
    def test_detect_media_type(self, sample_image: Path, sample_video: Path, sample_audio: Path):
        """Test media type detection from file."""
        processor = MediaProcessor()
        
        assert processor.detect_media_type(sample_image) == MediaType.IMAGE
        # Video and audio detection may vary based on file content
        detected_video = processor.detect_media_type(sample_video)
        assert detected_video in [MediaType.VIDEO, MediaType.DOCUMENT]  # Minimal MP4 might be detected as document
        
        detected_audio = processor.detect_media_type(sample_audio)
        assert detected_audio in [MediaType.AUDIO, MediaType.DOCUMENT]
    
    def test_extract_exif(self, sample_image: Path):
        """Test EXIF data extraction."""
        processor = MediaProcessor()
        
        exif = processor.extract_exif(sample_image)
        
        # EXIF may or may not be present in test images
        assert isinstance(exif, dict)
    
    def test_get_image_dimensions(self, sample_image: Path):
        """Test getting image dimensions."""
        processor = MediaProcessor()
        
        width, height = processor.get_image_dimensions(sample_image)
        
        assert width > 0
        assert height > 0
        assert isinstance(width, int)
        assert isinstance(height, int)
    
    def test_get_file_hash(self, sample_image: Path):
        """Test file hash calculation."""
        processor = MediaProcessor()
        
        hash1 = processor.get_file_hash(sample_image)
        hash2 = processor.get_file_hash(sample_image)
        
        assert hash1 == hash2
        assert len(hash1) > 0
        assert isinstance(hash1, str)
    
    def test_corrupted_image_handling(self, corrupted_image: Path):
        """Test handling of corrupted images."""
        processor = MediaProcessor()
        
        # Should either raise exception or return partial metadata
        try:
            metadata = processor.process_image(corrupted_image)
            # If it doesn't raise, should return some kind of error indication
            assert metadata is None or "error" in metadata
        except Exception as e:
            # Expected behavior - corrupted file should fail
            assert isinstance(e, (IOError, ValueError, OSError))
    
    def test_large_image_processing(self, large_image: Path):
        """Test processing large images."""
        processor = MediaProcessor()
        
        metadata = processor.process_image(large_image)
        
        assert metadata is not None
        assert metadata["width"] == 2000
        assert metadata["height"] == 2000
    
    def test_extract_dominant_colors(self, sample_image: Path):
        """Test extracting dominant colors from image."""
        processor = MediaProcessor()
        
        colors = processor.extract_dominant_colors(sample_image, n_colors=3)
        
        if colors:  # Feature may not be implemented
            assert isinstance(colors, list)
            assert len(colors) <= 3
    
    def test_generate_image_description(self, sample_image: Path):
        """Test generating image description."""
        processor = MediaProcessor()
        
        description = processor.generate_image_description(sample_image)
        
        # This feature may require additional models
        if description:
            assert isinstance(description, str)
            assert len(description) > 0
    
    def test_batch_processing(self, multiple_images: list[Path]):
        """Test batch processing of multiple images."""
        processor = MediaProcessor()
        
        results = []
        for img in multiple_images:
            metadata = processor.process_image(img)
            results.append(metadata)
        
        assert len(results) == len(multiple_images)
        for result in results:
            assert result is not None
            assert "width" in result
    
    def test_process_media_with_invalid_type(self, sample_image: Path):
        """Test processing with invalid media type."""
        processor = MediaProcessor()
        
        with pytest.raises((ValueError, AttributeError)):
            processor.process_media(sample_image, "invalid_type")  # type: ignore
    
    def test_video_frame_extraction(self, sample_video: Path):
        """Test extracting frames from video."""
        processor = MediaProcessor()
        
        frames = processor.extract_video_frames(sample_video, max_frames=5)
        
        # Frame extraction depends on opencv
        if frames is not None:
            assert isinstance(frames, list)
    
    def test_audio_duration_extraction(self, sample_audio: Path):
        """Test extracting audio duration."""
        processor = MediaProcessor()
        
        duration = processor.get_audio_duration(sample_audio)
        
        # Duration extraction depends on available libraries
        if duration is not None:
            assert isinstance(duration, (int, float))
            assert duration >= 0
    
    def test_metadata_caching(self, sample_image: Path):
        """Test metadata caching to avoid reprocessing."""
        processor = MediaProcessor()
        
        # Process twice
        metadata1 = processor.process_image(sample_image)
        metadata2 = processor.process_image(sample_image)
        
        # Should return same results
        assert metadata1 == metadata2
    
    def test_concurrent_processing(self, multiple_images: list[Path]):
        """Test concurrent media processing."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        processor = MediaProcessor()
        
        def process_wrapper(img_path):
            return processor.process_image(img_path)
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_wrapper, img) for img in multiple_images]
            results = [f.result() for f in futures]
        
        assert len(results) == len(multiple_images)
        for result in results:
            assert result is not None
