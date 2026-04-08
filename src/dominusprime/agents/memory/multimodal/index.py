# -*- coding: utf-8 -*-
"""
FAISS-based vector index for multimodal memory.

Enables fast similarity search across media embeddings.
"""
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from .models import MediaEmbedding, EmbeddingType

logger = logging.getLogger(__name__)


class MultimodalIndex:
    """
    FAISS-based index for fast similarity search.
    
    Maintains separate indices for different embedding types
    (CLIP, text, etc.) for optimal search performance.
    """
    
    def __init__(
        self,
        index_dir: Path,
        embedding_dim: int = 512,
        use_gpu: bool = False,
    ):
        """
        Initialize multimodal index.
        
        Args:
            index_dir: Directory to store index files
            embedding_dim: Dimensionality of embeddings
            use_gpu: Whether to use GPU acceleration
        """
        self.index_dir = Path(index_dir)
        self.embedding_dim = embedding_dim
        self.use_gpu = use_gpu
        
        # Create directory
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # Indices per embedding type
        self.indices: Dict[EmbeddingType, 'faiss.Index'] = {}
        
        # Mapping from index position to embedding ID
        self.id_mappings: Dict[EmbeddingType, List[str]] = {
            et: [] for et in EmbeddingType
        }
        
        # Try to import faiss
        self._faiss = None
        self._load_faiss()
        
        # Initialize indices
        self._init_indices()
        
        logger.info(f"MultimodalIndex initialized at {index_dir}")
    
    def _load_faiss(self):
        """Lazy load FAISS library."""
        try:
            import faiss
            self._faiss = faiss
            logger.info("FAISS loaded successfully")
        except ImportError:
            logger.warning("FAISS not installed. Install with: pip install faiss-cpu")
            logger.warning("Falling back to numpy-based search (slower)")
            self._faiss = None
    
    def _init_indices(self):
        """Initialize FAISS indices for each embedding type."""
        if self._faiss is None:
            # Fallback: store embeddings in memory for numpy search
            self._numpy_embeddings: Dict[EmbeddingType, np.ndarray] = {}
            return
        
        for embedding_type in EmbeddingType:
            # Create flat L2 index (exact search)
            # For large datasets, could use IVF or HNSW for approximate search
            index = self._faiss.IndexFlatL2(self.embedding_dim)
            
            # Optionally use GPU
            if self.use_gpu and self._faiss.get_num_gpus() > 0:
                index = self._faiss.index_cpu_to_gpu(
                    self._faiss.StandardGpuResources(),
                    0,  # GPU 0
                    index
                )
            
            self.indices[embedding_type] = index
            
            logger.debug(f"Initialized index for {embedding_type}")
    
    def add_embedding(
        self,
        embedding: MediaEmbedding,
    ) -> None:
        """
        Add embedding to index.
        
        Args:
            embedding: MediaEmbedding to add
        """
        embedding_type = embedding.embedding_type
        
        if self._faiss is not None:
            # FAISS-based indexing
            index = self.indices[embedding_type]
            
            # Reshape to (1, dim) for single vector
            vector = embedding.embedding.reshape(1, -1).astype(np.float32)
            
            # Add to index
            index.add(vector)
            
            # Store ID mapping
            self.id_mappings[embedding_type].append(embedding.id)
        
        else:
            # Numpy fallback
            if embedding_type not in self._numpy_embeddings:
                self._numpy_embeddings[embedding_type] = embedding.embedding.reshape(1, -1)
                self.id_mappings[embedding_type] = [embedding.id]
            else:
                self._numpy_embeddings[embedding_type] = np.vstack([
                    self._numpy_embeddings[embedding_type],
                    embedding.embedding.reshape(1, -1)
                ])
                self.id_mappings[embedding_type].append(embedding.id)
        
        logger.debug(f"Added embedding {embedding.id} to index")
    
    def search(
        self,
        query_embedding: np.ndarray,
        embedding_type: EmbeddingType,
        top_k: int = 5,
    ) -> List[Tuple[str, float]]:
        """
        Search for similar embeddings.
        
        Args:
            query_embedding: Query vector
            embedding_type: Type of embeddings to search
            top_k: Number of results to return
            
        Returns:
            List of (embedding_id, distance) tuples
        """
        if embedding_type not in self.indices and embedding_type not in self._numpy_embeddings:
            logger.warning(f"No index for {embedding_type}")
            return []
        
        if len(self.id_mappings[embedding_type]) == 0:
            logger.debug(f"Empty index for {embedding_type}")
            return []
        
        # Ensure correct shape and dtype
        query_vector = query_embedding.reshape(1, -1).astype(np.float32)
        
        if self._faiss is not None:
            # FAISS search
            index = self.indices[embedding_type]
            
            # Limit top_k to available items
            k = min(top_k, len(self.id_mappings[embedding_type]))
            
            # Search
            distances, indices = index.search(query_vector, k)
            
            # Map indices to IDs
            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx < len(self.id_mappings[embedding_type]):
                    emb_id = self.id_mappings[embedding_type][idx]
                    results.append((emb_id, float(dist)))
        
        else:
            # Numpy fallback
            embeddings = self._numpy_embeddings[embedding_type]
            
            # Compute L2 distances
            distances = np.linalg.norm(embeddings - query_vector, axis=1)
            
            # Get top k
            k = min(top_k, len(distances))
            top_indices = np.argsort(distances)[:k]
            
            # Map to IDs
            results = [
                (self.id_mappings[embedding_type][idx], float(distances[idx]))
                for idx in top_indices
            ]
        
        logger.debug(f"Search returned {len(results)} results")
        return results
    
    def remove_embedding(
        self,
        embedding_id: str,
        embedding_type: EmbeddingType,
    ) -> bool:
        """
        Remove embedding from index.
        
        Note: FAISS doesn't support efficient removal, so this requires rebuild.
        
        Args:
            embedding_id: ID of embedding to remove
            embedding_type: Type of embedding
            
        Returns:
            True if removed, False if not found
        """
        if embedding_id not in self.id_mappings[embedding_type]:
            return False
        
        # Find index position
        idx = self.id_mappings[embedding_type].index(embedding_id)
        
        # Remove from mapping
        self.id_mappings[embedding_type].pop(idx)
        
        # For numpy fallback, can actually remove
        if self._faiss is None and embedding_type in self._numpy_embeddings:
            self._numpy_embeddings[embedding_type] = np.delete(
                self._numpy_embeddings[embedding_type],
                idx,
                axis=0
            )
        
        # For FAISS, would need to rebuild index (expensive)
        # In practice, better to rebuild periodically
        logger.warning("FAISS removal requires index rebuild (not implemented)")
        
        return True
    
    def save(self) -> None:
        """Save indices to disk."""
        for embedding_type in EmbeddingType:
            index_path = self.index_dir / f"{embedding_type.value}.index"
            mapping_path = self.index_dir / f"{embedding_type.value}.mapping"
            
            # Save FAISS index
            if self._faiss is not None and embedding_type in self.indices:
                self._faiss.write_index(self.indices[embedding_type], str(index_path))
            
            # Save numpy fallback
            elif embedding_type in self._numpy_embeddings:
                np.save(index_path.with_suffix('.npy'), self._numpy_embeddings[embedding_type])
            
            # Save ID mapping
            with open(mapping_path, 'wb') as f:
                pickle.dump(self.id_mappings[embedding_type], f)
        
        logger.info(f"Saved indices to {self.index_dir}")
    
    def load(self) -> None:
        """Load indices from disk."""
        for embedding_type in EmbeddingType:
            index_path = self.index_dir / f"{embedding_type.value}.index"
            mapping_path = self.index_dir / f"{embedding_type.value}.mapping"
            
            # Load FAISS index
            if self._faiss is not None and index_path.exists():
                self.indices[embedding_type] = self._faiss.read_index(str(index_path))
            
            # Load numpy fallback
            npy_path = index_path.with_suffix('.npy')
            if npy_path.exists():
                self._numpy_embeddings[embedding_type] = np.load(npy_path)
            
            # Load ID mapping
            if mapping_path.exists():
                with open(mapping_path, 'rb') as f:
                    self.id_mappings[embedding_type] = pickle.load(f)
        
        logger.info(f"Loaded indices from {self.index_dir}")
    
    def get_stats(self) -> Dict:
        """Get index statistics."""
        stats = {}
        
        for embedding_type in EmbeddingType:
            count = len(self.id_mappings[embedding_type])
            stats[embedding_type.value] = {
                "count": count,
                "has_faiss": self._faiss is not None and embedding_type in self.indices,
            }
        
        return stats


__all__ = ["MultimodalIndex"]
