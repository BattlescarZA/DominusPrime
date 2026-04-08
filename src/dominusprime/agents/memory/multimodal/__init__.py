# -*- coding: utf-8 -*-
"""
Multimodal memory system for DominusPrime.

Enables storage, indexing, and retrieval of images, videos, and audio
alongside text-based memories.
"""

from .embedder import ContentEmbedder, SimpleEmbedder, get_embedder
from .index import MultimodalIndex
from .models import (
    EmbeddingType,
    MediaEmbedding,
    MediaMemoryItem,
    MediaSearchResult,
    MediaType,
    MultimodalQuery,
)
from .processor import MediaProcessor
from .retrieval import MultimodalRetriever
from .storage import MediaStorageManager
from .system import MultimodalMemorySystem

__all__ = [
    # Models
    "MediaType",
    "EmbeddingType",
    "MediaMemoryItem",
    "MediaEmbedding",
    "MediaSearchResult",
    "MultimodalQuery",
    # Components
    "MediaStorageManager",
    "MediaProcessor",
    "ContentEmbedder",
    "SimpleEmbedder",
    "get_embedder",
    "MultimodalIndex",
    "MultimodalRetriever",
    # Main System
    "MultimodalMemorySystem",
]
