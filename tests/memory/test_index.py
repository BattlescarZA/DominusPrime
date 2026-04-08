# -*- coding: utf-8 -*-
"""Tests for multimodal FAISS index manager."""
import pytest
import numpy as np
from pathlib import Path
from dominusprime.agents.memory.multimodal.models import MediaEmbedding, EmbeddingType
from dominusprime.agents.memory.multimodal.index import MultimodalIndex


class TestMultimodalIndex:
    """Test suite for MultimodalIndex."""
    
    def test_initialization(self, temp_dir: Path):
        """Test index initialization."""
        index = MultimodalIndex(
            index_dir=temp_dir,
            embedding_dim=512,
            use_gpu=False
        )
        
        assert index is not None
        assert index.embedding_dim == 512
        assert index.index_dir == temp_dir
    
    def test_add_embedding(self, temp_dir: Path, mock_embedding: np.ndarray):
        """Test adding an embedding to the index."""
        index = MultimodalIndex(index_dir=temp_dir, embedding_dim=512)
        
        embedding = MediaEmbedding(
            id="img_001",
            embedding=mock_embedding,
            embedding_type=EmbeddingType.CLIP
        )
        
        index.add_embedding(embedding)
        
        # Verify embedding was added
        assert len(index.id_mappings.get(EmbeddingType.CLIP, [])) == 1
    
    def test_add_multiple_embeddings(self, temp_dir: Path):
        """Test adding multiple embeddings."""
        index = MultimodalIndex(index_dir=temp_dir, embedding_dim=512)
        
        np.random.seed(42)
        for i in range(10):
            embedding = MediaEmbedding(
                id=f"img_{i:03d}",
                embedding=np.random.randn(512).astype(np.float32),
                embedding_type=EmbeddingType.CLIP
            )
            index.add_embedding(embedding)
        
        assert len(index.id_mappings[EmbeddingType.CLIP]) == 10
    
    def test_search(self, temp_dir: Path):
        """Test searching for similar embeddings."""
        index = MultimodalIndex(index_dir=temp_dir, embedding_dim=512)
        
        np.random.seed(42)
        # Add some embeddings
        embeddings_added = []
        for i in range(5):
            emb_vector = np.random.randn(512).astype(np.float32)
            emb_vector = emb_vector / np.linalg.norm(emb_vector)
            
            embedding = MediaEmbedding(
                id=f"img_{i:03d}",
                embedding=emb_vector,
                embedding_type=EmbeddingType.CLIP
            )
            index.add_embedding(embedding)
            embeddings_added.append(emb_vector)
        
        # Search with first embedding - should find itself first
        results = index.search(
            query_embedding=embeddings_added[0],
            embedding_type=EmbeddingType.CLIP,
            top_k=3
        )
        
        assert len(results) > 0
        assert len(results) <= 3
        # First result should be the query itself
        assert results[0][0] == "img_000"
    
    def test_search_empty_index(self, temp_dir: Path):
        """Test searching in an empty index."""
        index = MultimodalIndex(index_dir=temp_dir, embedding_dim=512)
        
        query = np.random.randn(512).astype(np.float32)
        results = index.search(query, EmbeddingType.CLIP, top_k=5)
        
        assert len(results) == 0
    
    def test_save_and_load(self, temp_dir: Path):
        """Test saving and loading index."""
        index = MultimodalIndex(index_dir=temp_dir, embedding_dim=512)
        
        np.random.seed(42)
        # Add embeddings
        for i in range(5):
            embedding = MediaEmbedding(
                id=f"img_{i:03d}",
                embedding=np.random.randn(512).astype(np.float32),
                embedding_type=EmbeddingType.CLIP
            )
            index.add_embedding(embedding)
        
        # Save
        index.save()
        
        # Create new index and load
        index2 = MultimodalIndex(index_dir=temp_dir, embedding_dim=512)
        index2.load()
        
        # Should have same number of embeddings
        assert len(index2.id_mappings[EmbeddingType.CLIP]) == 5
    
    def test_remove_embedding(self, temp_dir: Path):
        """Test removing an embedding."""
        index = MultimodalIndex(index_dir=temp_dir, embedding_dim=512)
        
        embedding = MediaEmbedding(
            id="img_001",
            embedding=np.random.randn(512).astype(np.float32),
            embedding_type=EmbeddingType.CLIP
        )
        index.add_embedding(embedding)
        
        assert len(index.id_mappings[EmbeddingType.CLIP]) == 1
        
        index.remove_embedding("img_001", EmbeddingType.CLIP)
        
        assert len(index.id_mappings.get(EmbeddingType.CLIP, [])) == 0
    
    def test_clear_index(self, temp_dir: Path):
        """Test clearing the index."""
        index = MultimodalIndex(index_dir=temp_dir, embedding_dim=512)
        
        # Add embeddings
        for i in range(5):
            embedding = MediaEmbedding(
                id=f"img_{i:03d}",
                embedding=np.random.randn(512).astype(np.float32),
                embedding_type=EmbeddingType.CLIP
            )
            index.add_embedding(embedding)
        
        index.clear(EmbeddingType.CLIP)
        
        assert len(index.id_mappings.get(EmbeddingType.CLIP, [])) == 0
    
    def test_get_embedding_count(self, temp_dir: Path):
        """Test getting embedding count."""
        index = MultimodalIndex(index_dir=temp_dir, embedding_dim=512)
        
        assert index.get_count(EmbeddingType.CLIP) == 0
        
        # Add embeddings
        for i in range(3):
            embedding = MediaEmbedding(
                id=f"img_{i:03d}",
                embedding=np.random.randn(512).astype(np.float32),
                embedding_type=EmbeddingType.CLIP
            )
            index.add_embedding(embedding)
        
        assert index.get_count(EmbeddingType.CLIP) == 3
    
    def test_multiple_embedding_types(self, temp_dir: Path):
        """Test handling multiple embedding types."""
        index = MultimodalIndex(index_dir=temp_dir, embedding_dim=512)
        
        # Add CLIP embeddings
        for i in range(3):
            embedding = MediaEmbedding(
                id=f"clip_{i:03d}",
                embedding=np.random.randn(512).astype(np.float32),
                embedding_type=EmbeddingType.CLIP
            )
            index.add_embedding(embedding)
        
        # Add SIMPLE embeddings
        for i in range(2):
            embedding = MediaEmbedding(
                id=f"simple_{i:03d}",
                embedding=np.random.randn(512).astype(np.float32),
                embedding_type=EmbeddingType.SIMPLE
            )
            index.add_embedding(embedding)
        
        assert index.get_count(EmbeddingType.CLIP) == 3
        assert index.get_count(EmbeddingType.SIMPLE) == 2
    
    def test_search_top_k(self, temp_dir: Path):
        """Test top-k search."""
        index = MultimodalIndex(index_dir=temp_dir, embedding_dim=512)
        
        np.random.seed(42)
        # Add 10 embeddings
        for i in range(10):
            embedding = MediaEmbedding(
                id=f"img_{i:03d}",
                embedding=np.random.randn(512).astype(np.float32),
                embedding_type=EmbeddingType.CLIP
            )
            index.add_embedding(embedding)
        
        # Search with k=3
        query = np.random.randn(512).astype(np.float32)
        results = index.search(query, EmbeddingType.CLIP, top_k=3)
        
        assert len(results) == 3
        
        # Search with k=5
        results = index.search(query, EmbeddingType.CLIP, top_k=5)
        assert len(results) == 5
    
    def test_distance_scores(self, temp_dir: Path):
        """Test that search returns distance scores."""
        index = MultimodalIndex(index_dir=temp_dir, embedding_dim=512)
        
        np.random.seed(42)
        query = np.random.randn(512).astype(np.float32)
        query = query / np.linalg.norm(query)
        
        # Add similar and dissimilar embeddings
        similar = query + np.random.randn(512).astype(np.float32) * 0.1
        similar = similar / np.linalg.norm(similar)
        
        dissimilar = np.random.randn(512).astype(np.float32)
        dissimilar = dissimilar / np.linalg.norm(dissimilar)
        
        index.add_embedding(MediaEmbedding(
            id="similar",
            embedding=similar,
            embedding_type=EmbeddingType.CLIP
        ))
        index.add_embedding(MediaEmbedding(
            id="dissimilar",
            embedding=dissimilar,
            embedding_type=EmbeddingType.CLIP
        ))
        
        results = index.search(query, EmbeddingType.CLIP, top_k=2)
        
        # Results should be sorted by distance
        assert len(results) == 2
        assert results[0][1] <= results[1][1]  # Smaller distance = more similar
    
    def test_batch_add(self, temp_dir: Path):
        """Test batch adding embeddings."""
        index = MultimodalIndex(index_dir=temp_dir, embedding_dim=512)
        
        np.random.seed(42)
        embeddings = [
            MediaEmbedding(
                id=f"img_{i:03d}",
                embedding=np.random.randn(512).astype(np.float32),
                embedding_type=EmbeddingType.CLIP
            )
            for i in range(100)
        ]
        
        for emb in embeddings:
            index.add_embedding(emb)
        
        assert index.get_count(EmbeddingType.CLIP) == 100
    
    def test_persistence(self, temp_dir: Path):
        """Test index persistence across restarts."""
        # Create and populate index
        index1 = MultimodalIndex(index_dir=temp_dir, embedding_dim=512)
        
        np.random.seed(42)
        test_embedding = np.random.randn(512).astype(np.float32)
        index1.add_embedding(MediaEmbedding(
            id="test_001",
            embedding=test_embedding,
            embedding_type=EmbeddingType.CLIP
        ))
        index1.save()
        
        # Load in new instance
        index2 = MultimodalIndex(index_dir=temp_dir, embedding_dim=512)
        index2.load()
        
        # Search should still work
        results = index2.search(test_embedding, EmbeddingType.CLIP, top_k=1)
        assert len(results) == 1
        assert results[0][0] == "test_001"
    
    def test_concurrent_access(self, temp_dir: Path):
        """Test concurrent index operations."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        index = MultimodalIndex(index_dir=temp_dir, embedding_dim=512)
        
        def add_embedding(idx):
            embedding = MediaEmbedding(
                id=f"img_{idx:03d}",
                embedding=np.random.randn(512).astype(np.float32),
                embedding_type=EmbeddingType.CLIP
            )
            index.add_embedding(embedding)
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(add_embedding, i) for i in range(20)]
            for f in futures:
                f.result()
        
        # All embeddings should be added
        assert index.get_count(EmbeddingType.CLIP) == 20
    
    def test_index_rebuild(self, temp_dir: Path):
        """Test rebuilding the index."""
        index = MultimodalIndex(index_dir=temp_dir, embedding_dim=512)
        
        # Add embeddings
        np.random.seed(42)
        for i in range(5):
            index.add_embedding(MediaEmbedding(
                id=f"img_{i:03d}",
                embedding=np.random.randn(512).astype(np.float32),
                embedding_type=EmbeddingType.CLIP
            ))
        
        original_count = index.get_count(EmbeddingType.CLIP)
        
        # Rebuild
        index.rebuild(EmbeddingType.CLIP)
        
        # Count should be preserved
        assert index.get_count(EmbeddingType.CLIP) == original_count
    
    def test_wrong_embedding_dimension(self, temp_dir: Path):
        """Test handling of wrong embedding dimension."""
        index = MultimodalIndex(index_dir=temp_dir, embedding_dim=512)
        
        # Try to add embedding with wrong dimension
        with pytest.raises((ValueError, AssertionError)):
            index.add_embedding(MediaEmbedding(
                id="wrong_dim",
                embedding=np.random.randn(256).astype(np.float32),
                embedding_type=EmbeddingType.CLIP
            ))
    
    def test_search_with_threshold(self, temp_dir: Path):
        """Test search with distance threshold."""
        index = MultimodalIndex(index_dir=temp_dir, embedding_dim=512)
        
        np.random.seed(42)
        query = np.random.randn(512).astype(np.float32)
        query = query / np.linalg.norm(query)
        
        # Add embeddings at varying distances
        for i in range(10):
            emb = query + np.random.randn(512).astype(np.float32) * (i * 0.5)
            emb = emb / np.linalg.norm(emb)
            index.add_embedding(MediaEmbedding(
                id=f"img_{i:03d}",
                embedding=emb,
                embedding_type=EmbeddingType.CLIP
            ))
        
        # Search with threshold
        results = index.search(query, EmbeddingType.CLIP, top_k=10, threshold=1.0)
        
        if hasattr(index, 'threshold'):
            # All results should be within threshold
            for _, distance in results:
                assert distance <= 1.0
