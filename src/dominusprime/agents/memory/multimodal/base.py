# -*- coding: utf-8 -*-
"""Base classes for multimodal memory."""

from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import numpy as np


class MediaType(Enum):
    """Supported media types."""
    
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


@dataclass
class ProcessedMedia:
    """Result of media processing."""
    
    media_id: str
    media_type: MediaType
    original_path: Path
    storage_path: Path
    thumbnail_path: Optional[Path]
    
    # Extracted content
    extracted_text: Optional[str]  # OCR or transcription
    ai_description: Optional[str]
    tags: List[str]
    
    # Metadata
    file_size: int
    width: Optional[int]
    height: Optional[int]
    duration: Optional[float]  # seconds for audio/video
    
    created_at: datetime
    processing_time_ms: int


@dataclass
class MultimodalQuery:
    """Query for multimodal search."""
    
    text_query: Optional[str] = None
    media_path: Optional[Path] = None
    media_type: Optional[MediaType] = None
    time_range: Optional[tuple[datetime, datetime]] = None
    session_id: Optional[str] = None
    tags: Optional[List[str]] = None
    max_results: int = 5


@dataclass
class MediaSearchResult:
    """Result from multimodal search."""
    
    media_id: str
    media_type: MediaType
    storage_path: Path
    thumbnail_path: Optional[Path]
    description: str
    relevance_score: float
    tags: List[str]
    created_at: datetime
    session_id: Optional[str]


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""
    
    embedding_id: str
    vector: np.ndarray
    model_name: str
    dimensions: int
    created_at: datetime
