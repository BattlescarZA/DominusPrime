# -*- coding: utf-8 -*-
"""Data models for multimodal memory system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List


class MediaType(str, Enum):
    """Types of media that can be processed."""
    
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"


class ProcessingStatus(str, Enum):
    """Status of media processing."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class MediaItem:
    """Represents a piece of multimodal content."""
    
    id: str
    media_type: MediaType
    file_path: str
    original_filename: str
    mime_type: str
    file_size: int
    
    # Processing status
    status: ProcessingStatus = ProcessingStatus.PENDING
    
    # Extracted metadata
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None  # seconds for audio/video
    
    # Content analysis
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    detected_objects: List[str] = field(default_factory=list)
    detected_text: Optional[str] = None  # OCR results
    
    # Context
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    user_context: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "media_type": self.media_type.value,
            "file_path": self.file_path,
            "original_filename": self.original_filename,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "status": self.status.value,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "description": self.description,
            "tags": self.tags,
            "detected_objects": self.detected_objects,
            "detected_text": self.detected_text,
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "user_context": self.user_context,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "metadata": self.metadata,
        }


@dataclass
class MediaEmbedding:
    """Embedding vector for multimodal content."""
    
    media_item_id: str
    embedding_type: str  # "visual", "audio", "text", "multimodal"
    vector: List[float]
    model_name: str
    dimension: int
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "media_item_id": self.media_item_id,
            "embedding_type": self.embedding_type,
            "vector": self.vector,
            "model_name": self.model_name,
            "dimension": self.dimension,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class MultimodalMemory:
    """A complete multimodal memory combining media and text."""
    
    id: str
    media_item: MediaItem
    embeddings: List[MediaEmbedding]
    
    # Associated text memory
    text_content: Optional[str] = None
    experience_id: Optional[str] = None
    
    # Relevance scoring
    relevance_score: float = 0.0
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "media_item": self.media_item.to_dict(),
            "embeddings": [emb.to_dict() for emb in self.embeddings],
            "text_content": self.text_content,
            "experience_id": self.experience_id,
            "relevance_score": self.relevance_score,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
        }


@dataclass
class SearchResult:
    """Result from multimodal memory search."""
    
    memory: MultimodalMemory
    similarity_score: float
    match_type: str  # "visual", "text", "semantic", "hybrid"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "memory": self.memory.to_dict(),
            "similarity_score": self.similarity_score,
            "match_type": self.match_type,
        }
