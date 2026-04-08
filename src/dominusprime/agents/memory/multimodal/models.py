# -*- coding: utf-8 -*-
"""
Data models for multimodal memory system.

Defines the core data structures for storing and retrieving multimedia content.
"""
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np


class MediaType(str, Enum):
    """Supported media types."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


class EmbeddingType(str, Enum):
    """Types of embeddings generated for media."""
    CLIP = "clip"              # For images (vision-language model)
    WHISPER = "whisper"        # For audio transcription
    FRAME = "frame"            # For video frames
    OCR = "ocr"                # For text extraction from images


@dataclass
class MediaMemoryItem:
    """
    Represents a multimedia item stored in memory.
    
    Attributes:
        id: Unique identifier
        session_id: Session this media belongs to
        media_type: Type of media
        file_path: Path to stored media file
        thumbnail_path: Path to thumbnail (if applicable)
        file_size: Size in bytes
        duration_seconds: Duration for audio/video
        width: Width in pixels (for images/video)
        height: Height in pixels (for images/video)
        format: File format (png, jpg, mp4, etc.)
        created_at: Timestamp when stored
        context_text: Text context from conversation
        auto_description: AI-generated description
        ocr_text: Extracted text from image (if any)
        transcription: Audio transcription (if applicable)
        embedding_ids: List of associated embedding IDs
        metadata: Additional metadata
    """
    id: str
    session_id: str
    media_type: MediaType
    file_path: Path
    file_size: int
    format: str
    created_at: float = field(default_factory=time.time)
    
    # Optional media properties
    thumbnail_path: Optional[Path] = None
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    
    # AI-generated content
    context_text: Optional[str] = None
    auto_description: Optional[str] = None
    ocr_text: Optional[str] = None
    transcription: Optional[str] = None
    
    # Embeddings
    embedding_ids: List[str] = field(default_factory=list)
    
    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "media_type": self.media_type.value,
            "file_path": str(self.file_path),
            "thumbnail_path": str(self.thumbnail_path) if self.thumbnail_path else None,
            "file_size": self.file_size,
            "duration_seconds": self.duration_seconds,
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "created_at": self.created_at,
            "context_text": self.context_text,
            "auto_description": self.auto_description,
            "ocr_text": self.ocr_text,
            "transcription": self.transcription,
            "embedding_ids": self.embedding_ids,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MediaMemoryItem":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            media_type=MediaType(data["media_type"]),
            file_path=Path(data["file_path"]),
            thumbnail_path=Path(data["thumbnail_path"]) if data.get("thumbnail_path") else None,
            file_size=data["file_size"],
            duration_seconds=data.get("duration_seconds"),
            width=data.get("width"),
            height=data.get("height"),
            format=data["format"],
            created_at=data.get("created_at", time.time()),
            context_text=data.get("context_text"),
            auto_description=data.get("auto_description"),
            ocr_text=data.get("ocr_text"),
            transcription=data.get("transcription"),
            embedding_ids=data.get("embedding_ids", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MediaEmbedding:
    """
    Represents a vector embedding for a media item.
    
    Attributes:
        id: Unique identifier
        media_id: ID of associated media item
        embedding_type: Type of embedding
        embedding: Numpy array of embedding vector
        model_version: Version of model used
        created_at: Timestamp when generated
    """
    id: str
    media_id: str
    embedding_type: EmbeddingType
    embedding: np.ndarray
    model_version: str
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "media_id": self.media_id,
            "embedding_type": self.embedding_type.value,
            "embedding": self.embedding.tolist(),  # Convert to list for JSON
            "model_version": self.model_version,
            "created_at": self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MediaEmbedding":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            media_id=data["media_id"],
            embedding_type=EmbeddingType(data["embedding_type"]),
            embedding=np.array(data["embedding"]),
            model_version=data["model_version"],
            created_at=data.get("created_at", time.time()),
        )


@dataclass
class MediaSearchResult:
    """
    Represents a search result from multimodal retrieval.
    
    Attributes:
        media_item: The matched media item
        similarity_score: Similarity score (0-1)
        matched_embedding_type: Type of embedding that matched
        rank: Result rank in search results
    """
    media_item: MediaMemoryItem
    similarity_score: float
    matched_embedding_type: EmbeddingType
    rank: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "media_item": self.media_item.to_dict(),
            "similarity_score": self.similarity_score,
            "matched_embedding_type": self.matched_embedding_type.value,
            "rank": self.rank,
        }


@dataclass
class MultimodalQuery:
    """
    Represents a multimodal search query.
    
    Supports querying with text, images, or both.
    
    Attributes:
        text_query: Optional text query
        media_path: Optional path to media file for similarity search
        media_types: Filter by media types
        session_ids: Filter by session IDs
        date_range: Filter by date range (start, end timestamps)
        top_k: Number of results to return
    """
    text_query: Optional[str] = None
    media_path: Optional[Path] = None
    media_types: Optional[List[MediaType]] = None
    session_ids: Optional[List[str]] = None
    date_range: Optional[tuple[float, float]] = None
    top_k: int = 5
    
    def __post_init__(self):
        """Validate query has at least one search criterion."""
        if not self.text_query and not self.media_path:
            raise ValueError("Query must have either text_query or media_path")


__all__ = [
    "MediaType",
    "EmbeddingType",
    "MediaMemoryItem",
    "MediaEmbedding",
    "MediaSearchResult",
    "MultimodalQuery",
]
