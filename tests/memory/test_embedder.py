# -*- coding: utf-8 -*-
"""Tests for content embedder."""
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch
from dominusprime.agents.memory.multimodal.embedder import (
    ContentEmbedder,
    SimpleEmbedder,
    get_embedder
)


class TestContentEmbedder:
    """Test suite for ContentEmbedder (CLIP-based)."""
    
    def test_initialization_default(self):
        """Test embedder initialization with defaults."""
        embedder = ContentEmbedder()
        assert embedder is not None
        assert embedder.model_name == "clip-vit-base-patch32"
        assert embedder.device == "cpu"
    
    def test_initialization_custom(self):
        """Test embedder initialization with custom settings."""
        embedder = ContentEmbedder(model_name="custom-model", device="cpu")
        assert embedder.model_name == "custom-model"
        assert embedder.device == "cpu"
    
    @pytest.mark.skipif(True, reason="Requires CLIP dependencies")
    def test_embed_image(self, sample_image: Path):
        """Test embedding an image with CLIP."""
        embedder = ContentEmbedder()
        
        embedding = embedder.embed_image(sample_image)
        
        assert embedding is not None
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (512,)
        assert embedding.dtype == np.float32
    
    @pytest.mark.skipif(True, reason="Requires CLIP dependencies")
    def test_embed_text(self):
        """Test embedding text with CLIP."""
        embedder = ContentEmbedder()
        
        embedding = embedder.embed_text("Python debugging session")
        
        assert embedding is not None
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (512,)
        assert embedding.dtype == np.float32
    
    @pytest.mark.skipif(True, reason="Requires CLIP dependencies")
    def test_embed_multiple_images(self, multiple_images: list[Path]):
        """Test embedding multiple images."""
        embedder = ContentEmbedder()
        
        embeddings = [embedder.embed_image(img) for img in multiple_images]
        
        assert len(embeddings) == len(multiple_images)
        for emb in embeddings:
            assert emb.shape == (512,)
    
    @pytest.mark.skipif(True, reason="Requires CLIP dependencies")
    def test_embedding_similarity(self, sample_image: Path):
        """Test that similar texts produce similar embeddings."""
        embedder = ContentEmbedder()
        
        emb1 = embedder.embed_text("Python debugging error")
        emb2 = embedder.embed_text("Python debugging session")
        emb3 = embedder.embed_text("Cat playing piano")
        
        # Cosine similarity
        sim_12 = np.dot(emb1, emb2)
        sim_13 = np.dot(emb1, emb3)
        
        # Similar texts should have higher similarity
        assert sim_12 > sim_13
    
    def test_lazy_loading(self):
        """Test that CLIP model is loaded lazily."""
        embedder = ContentEmbedder()
        
        # Model should not be loaded on initialization
        assert embedder._clip_model is None
        assert embedder._clip_processor is None
    
    @pytest.mark.skipif(True, reason="Requires CLIP dependencies")
    def test_model_caching(self):
        """Test that model is cached after first use."""
        embedder = ContentEmbedder()
        
        embedder.embed_text("test")
        
        # Model should now be loaded
        assert embedder._clip_model is not None
        assert embedder._clip_processor is not None


class TestSimpleEmbedder:
    """Test suite for SimpleEmbedder (fallback)."""
    
    def test_initialization(self):
        """Test simple embedder initialization."""
        embedder = SimpleEmbedder()
        assert embedder is not None
    
    def test_embed_image(self, sample_image: Path):
        """Test embedding an image with simple embedder."""
        embedder = SimpleEmbedder()
        
        embedding = embedder.embed_image(sample_image)
        
        assert embedding is not None
        assert isinstance(embedding, np.ndarray)
        assert len(embedding.shape) == 1
        assert embedding.dtype == np.float32
    
    def test_embed_text(self):
        """Test embedding text with simple embedder."""
        embedder = SimpleEmbedder()
        
        embedding = embedder.embed_text("Python debugging session")
        
        assert embedding is not None
        assert isinstance(embedding, np.ndarray)
        assert len(embedding.shape) == 1
        assert embedding.dtype == np.float32
    
    def test_embed_multiple_images(self, multiple_images: list[Path]):
        """Test embedding multiple images with simple embedder."""
        embedder = SimpleEmbedder()
        
        embeddings = [embedder.embed_image(img) for img in multiple_images]
        
        assert len(embeddings) == len(multiple_images)
        
        # All embeddings should have same dimension
        dims = [emb.shape[0] for emb in embeddings]
        assert len(set(dims)) == 1
    
    def test_deterministic_embeddings(self, sample_image: Path):
        """Test that embeddings are deterministic."""
        embedder = SimpleEmbedder()
        
        emb1 = embedder.embed_image(sample_image)
        emb2 = embedder.embed_image(sample_image)
        
        np.testing.assert_array_almost_equal(emb1, emb2)
    
    def test_different_images_different_embeddings(self, multiple_images: list[Path]):
        """Test that different images produce different embeddings."""
        embedder = SimpleEmbedder()
        
        embeddings = [embedder.embed_image(img) for img in multiple_images[:2]]
        
        # Embeddings should be different
        assert not np.allclose(embeddings[0], embeddings[1])
    
    def test_text_embedding_deterministic(self):
        """Test that text embeddings are deterministic."""
        embedder = SimpleEmbedder()
        
        emb1 = embedder.embed_text("test text")
        emb2 = embedder.embed_text("test text")
        
        np.testing.assert_array_almost_equal(emb1, emb2)
    
    def test_different_texts_different_embeddings(self):
        """Test that different texts produce different embeddings."""
        embedder = SimpleEmbedder()
        
        emb1 = embedder.embed_text("Python debugging")
        emb2 = embedder.embed_text("JavaScript error")
        
        assert not np.allclose(emb1, emb2)
    
    def test_normalization(self, sample_image: Path):
        """Test that embeddings are normalized."""
        embedder = SimpleEmbedder()
        
        embedding = embedder.embed_image(sample_image)
        
        # Check L2 norm is close to 1
        norm = np.linalg.norm(embedding)
        assert np.isclose(norm, 1.0, atol=0.1)
    
    def test_corrupted_image_handling(self, corrupted_image: Path):
        """Test handling of corrupted images."""
        embedder = SimpleEmbedder()
        
        try:
            embedding = embedder.embed_image(corrupted_image)
            # If it doesn't raise, should return a valid embedding or None
            if embedding is not None:
                assert isinstance(embedding, np.ndarray)
        except Exception as e:
            # Expected - corrupted file should fail
            assert isinstance(e, (IOError, ValueError, OSError))


class TestGetEmbedder:
    """Test suite for get_embedder factory function."""
    
    def test_get_embedder_with_clip(self):
        """Test getting embedder with CLIP enabled."""
        embedder = get_embedder(use_clip=True)
        
        # Should return ContentEmbedder or SimpleEmbedder depending on availability
        assert embedder is not None
        assert hasattr(embedder, 'embed_image')
        assert hasattr(embedder, 'embed_text')
    
    def test_get_embedder_without_clip(self):
        """Test getting embedder with CLIP disabled."""
        embedder = get_embedder(use_clip=False)
        
        assert isinstance(embedder, SimpleEmbedder)
    
    def test_get_embedder_custom_model(self):
        """Test getting embedder with custom model name."""
        embedder = get_embedder(use_clip=True, model_name="custom-model")
        
        assert embedder is not None
    
    def test_get_embedder_custom_device(self):
        """Test getting embedder with custom device."""
        embedder = get_embedder(use_clip=False, device="cpu")
        
        assert embedder is not None


class TestEmbeddingBatch:
    """Test batch embedding operations."""
    
    def test_batch_image_embedding(self, multiple_images: list[Path]):
        """Test batch embedding of images."""
        embedder = SimpleEmbedder()
        
        embeddings = []
        for img in multiple_images:
            emb = embedder.embed_image(img)
            embeddings.append(emb)
        
        assert len(embeddings) == len(multiple_images)
        
        # Check all have same dimension
        dims = [emb.shape[0] for emb in embeddings]
        assert len(set(dims)) == 1
    
    def test_batch_text_embedding(self):
        """Test batch embedding of texts."""
        embedder = SimpleEmbedder()
        
        texts = [
            "Python debugging error",
            "JavaScript syntax issue",
            "Database connection timeout",
            "Network request failed"
        ]
        
        embeddings = [embedder.embed_text(text) for text in texts]
        
        assert len(embeddings) == len(texts)
        
        # Check all have same dimension
        dims = [emb.shape[0] for emb in embeddings]
        assert len(set(dims)) == 1
    
    def test_mixed_embedding(self, sample_image: Path):
        """Test mixing image and text embeddings."""
        embedder = SimpleEmbedder()
        
        img_emb = embedder.embed_image(sample_image)
        text_emb = embedder.embed_text("test image")
        
        # Both should have compatible dimensions for similarity search
        assert img_emb.shape == text_emb.shape


class TestEmbeddingPerformance:
    """Test embedding performance characteristics."""
    
    def test_embedding_speed(self, sample_image: Path):
        """Test that embedding is reasonably fast."""
        import time
        
        embedder = SimpleEmbedder()
        
        start = time.time()
        embedder.embed_image(sample_image)
        duration = time.time() - start
        
        # Should take less than 1 second for simple embedder
        assert duration < 1.0
    
    def test_concurrent_embedding(self, multiple_images: list[Path]):
        """Test concurrent embedding operations."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        embedder = SimpleEmbedder()
        
        def embed_wrapper(img_path):
            return embedder.embed_image(img_path)
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(embed_wrapper, img) for img in multiple_images]
            results = [f.result() for f in futures]
        
        assert len(results) == len(multiple_images)
        for result in results:
            assert isinstance(result, np.ndarray)


class TestEmbeddingEdgeCases:
    """Test edge cases in embedding."""
    
    def test_empty_text(self):
        """Test embedding empty text."""
        embedder = SimpleEmbedder()
        
        embedding = embedder.embed_text("")
        
        assert embedding is not None
        assert isinstance(embedding, np.ndarray)
    
    def test_very_long_text(self):
        """Test embedding very long text."""
        embedder = SimpleEmbedder()
        
        long_text = "test " * 1000
        embedding = embedder.embed_text(long_text)
        
        assert embedding is not None
        assert isinstance(embedding, np.ndarray)
    
    def test_special_characters(self):
        """Test embedding text with special characters."""
        embedder = SimpleEmbedder()
        
        text = "Python 🐍 debugging <error> & [warning]"
        embedding = embedder.embed_text(text)
        
        assert embedding is not None
        assert isinstance(embedding, np.ndarray)
    
    def test_unicode_text(self):
        """Test embedding unicode text."""
        embedder = SimpleEmbedder()
        
        text = "Python 调试 エラー ошибка"
        embedding = embedder.embed_text(text)
        
        assert embedding is not None
        assert isinstance(embedding, np.ndarray)
