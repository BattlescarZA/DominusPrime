# -*- coding: utf-8 -*-
"""Pytest fixtures for multimodal memory tests."""
import tempfile
import shutil
from pathlib import Path
from typing import Generator
import pytest
import numpy as np
from PIL import Image


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    tmpdir = tempfile.mkdtemp()
    try:
        yield Path(tmpdir)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def sample_image(temp_dir: Path) -> Path:
    """Create a sample test image."""
    img_path = temp_dir / "test_image.png"
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img.save(img_path)
    return img_path


@pytest.fixture
def sample_image_with_text(temp_dir: Path) -> Path:
    """Create a sample image with text-like patterns."""
    from PIL import ImageDraw, ImageFont
    
    img_path = temp_dir / "test_image_text.png"
    img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to use a default font, fallback to basic if not available
        draw.text((10, 10), "Python Debugging", fill=(0, 0, 0))
    except Exception:
        # Fallback if font not available
        pass
    
    img.save(img_path)
    return img_path


@pytest.fixture
def sample_video(temp_dir: Path) -> Path:
    """Create a minimal test video file."""
    video_path = temp_dir / "test_video.mp4"
    # Create a minimal valid MP4 file structure
    # This is a minimal MP4 header that tools can recognize
    minimal_mp4 = bytes([
        0x00, 0x00, 0x00, 0x20, 0x66, 0x74, 0x79, 0x70,  # ftyp box
        0x69, 0x73, 0x6f, 0x6d, 0x00, 0x00, 0x02, 0x00,
        0x69, 0x73, 0x6f, 0x6d, 0x69, 0x73, 0x6f, 0x32,
        0x61, 0x76, 0x63, 0x31, 0x6d, 0x70, 0x34, 0x31,
    ])
    video_path.write_bytes(minimal_mp4)
    return video_path


@pytest.fixture
def sample_audio(temp_dir: Path) -> Path:
    """Create a minimal test audio file."""
    audio_path = temp_dir / "test_audio.mp3"
    # Minimal MP3 header
    minimal_mp3 = bytes([
        0xFF, 0xFB, 0x90, 0x00,  # MP3 frame header
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ])
    audio_path.write_bytes(minimal_mp3)
    return audio_path


@pytest.fixture
def sample_document(temp_dir: Path) -> Path:
    """Create a sample document."""
    doc_path = temp_dir / "test_doc.txt"
    doc_path.write_text("This is a test document with some content.")
    return doc_path


@pytest.fixture
def large_image(temp_dir: Path) -> Path:
    """Create a large test image."""
    img_path = temp_dir / "large_image.png"
    img = Image.new("RGB", (2000, 2000), color=(0, 255, 0))
    img.save(img_path)
    return img_path


@pytest.fixture
def corrupted_image(temp_dir: Path) -> Path:
    """Create a corrupted image file."""
    img_path = temp_dir / "corrupted.png"
    img_path.write_bytes(b"not a real image")
    return img_path


@pytest.fixture
def mock_embedding() -> np.ndarray:
    """Create a mock embedding vector."""
    np.random.seed(42)
    return np.random.randn(512).astype(np.float32)


@pytest.fixture
def multiple_images(temp_dir: Path) -> list[Path]:
    """Create multiple test images with different colors."""
    images = []
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
    
    for i, color in enumerate(colors):
        img_path = temp_dir / f"image_{i}.png"
        img = Image.new("RGB", (100, 100), color=color)
        img.save(img_path)
        images.append(img_path)
    
    return images
