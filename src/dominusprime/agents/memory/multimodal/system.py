# -*- coding: utf-8 -*-
"""
Main multimodal memory system.

Integrates all components to provide a complete multimodal memory solution.
"""
import logging
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from .embedder import ContentEmbedder, get_embedder
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

logger = logging.getLogger(__name__)


class MultimodalMemorySystem:
    """
    Complete multimodal memory system.
    
    Provides end-to-end functionality:
    - Store images, videos, audio
    - Generate embeddings and index
    - Search across modalities
    - Manage storage quotas
    """
    
    def __init__(
        self,
        working_dir: Path,
        max_storage_gb: float = 10.0,
        use_clip: bool = True,
        enable_ocr: bool = False,
        enable_transcription: bool = False,
    ):
        """
        Initialize multimodal memory system.
        
        Args:
            working_dir: Base directory for storage
            max_storage_gb: Maximum storage quota
            use_clip: Use CLIP for embeddings (requires transformers)
            enable_ocr: Enable text extraction from images
            enable_transcription: Enable audio transcription
        """
        self.working_dir = Path(working_dir)
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.db_path = self.working_dir / "multimodal_memory.db"
        self._init_database()
        
        # Initialize components
        self.storage = MediaStorageManager(
            storage_dir=self.working_dir / "media",
            max_storage_gb=max_storage_gb,
        )
        
        self.processor = MediaProcessor(
            enable_ocr=enable_ocr,
            enable_transcription=enable_transcription,
        )
        
        self.embedder = get_embedder(use_clip=use_clip)
        
        self.index = MultimodalIndex(
            index_dir=self.working_dir / "indices",
            embedding_dim=self.embedder.get_embedding_dim(),
        )
        
        self.retriever = MultimodalRetriever(
            db_path=self.db_path,
            index=self.index,
            embedder=self.embedder,
        )
        
        # Load existing indices
        try:
            self.index.load()
            logger.info("Loaded existing indices")
        except Exception as e:
            logger.debug(f"No existing indices to load: {e}")
        
        logger.info(f"MultimodalMemorySystem initialized at {working_dir}")
    
    def _init_database(self) -> None:
        """Initialize SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            # Media memory table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS media_memory (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    thumbnail_path TEXT,
                    file_size INTEGER,
                    duration_seconds REAL,
                    width INTEGER,
                    height INTEGER,
                    format TEXT,
                    created_at REAL DEFAULT (strftime('%s', 'now')),
                    context_text TEXT,
                    auto_description TEXT,
                    ocr_text TEXT,
                    transcription TEXT,
                    embedding_id TEXT,
                    metadata TEXT
                )
            """)
            
            # Media embeddings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS media_embeddings (
                    id TEXT PRIMARY KEY,
                    media_id TEXT NOT NULL,
                    embedding_type TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    model_version TEXT,
                    created_at REAL DEFAULT (strftime('%s', 'now')),
                    FOREIGN KEY (media_id) REFERENCES media_memory(id)
                )
            """)
            
            # Indices for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_media_session ON media_memory(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_media_type ON media_memory(media_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_media_created ON media_memory(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_embedding_media ON media_embeddings(media_id)")
            
            conn.commit()
        
        logger.debug("Database initialized")
    
    async def store_media(
        self,
        media_path: Path,
        session_id: str,
        context_text: Optional[str] = None,
        auto_generate_description: bool = True,
    ) -> MediaMemoryItem:
        """
        Store media file in memory.
        
        Args:
            media_path: Path to media file
            session_id: Session ID
            context_text: Optional context from conversation
            auto_generate_description: Generate AI description
            
        Returns:
            Created MediaMemoryItem
        """
        # Detect media type
        media_type = self.retriever._detect_media_type(media_path)
        
        # Generate unique ID
        media_id = f"media_{uuid.uuid4().hex[:16]}"
        
        # Process media
        metadata = self.processor.process_media(media_path, media_type)
        
        # Store file
        stored_path, thumbnail_path = self.storage.store_media(
            media_path,
            media_type,
            session_id,
            media_id,
        )
        
        # Generate embedding
        embedding_id = await self._generate_and_store_embedding(
            stored_path,
            media_id,
            media_type,
        )
        
        # Create memory item
        memory_item = MediaMemoryItem(
            id=media_id,
            session_id=session_id,
            media_type=media_type,
            file_path=stored_path,
            thumbnail_path=thumbnail_path,
            file_size=metadata.get('file_size', 0),
            duration_seconds=metadata.get('duration_seconds'),
            width=metadata.get('width'),
            height=metadata.get('height'),
            format=metadata.get('format', ''),
            created_at=time.time(),
            context_text=context_text,
            ocr_text=metadata.get('ocr_text'),
            transcription=metadata.get('transcription'),
            embedding_ids=[embedding_id] if embedding_id else [],
            metadata=metadata,
        )
        
        # Save to database
        self._save_media_item(memory_item)
        
        # Save index
        self.index.save()
        
        logger.info(f"Stored media: {media_id} ({media_type.value})")
        return memory_item
    
    async def _generate_and_store_embedding(
        self,
        media_path: Path,
        media_id: str,
        media_type: MediaType,
    ) -> Optional[str]:
        """Generate and store embedding for media."""
        try:
            # Generate embedding based on media type
            if media_type == MediaType.IMAGE:
                embedding_vector = self.embedder.embed_image(media_path)
                embedding_type = EmbeddingType.CLIP
            else:
                logger.debug(f"Embedding not supported for {media_type}")
                return None
            
            # Create embedding object
            embedding_id = f"emb_{uuid.uuid4().hex[:16]}"
            
            embedding = MediaEmbedding(
                id=embedding_id,
                media_id=media_id,
                embedding_type=embedding_type,
                embedding=embedding_vector,
                model_version=self.embedder.model_name,
            )
            
            # Add to index
            self.index.add_embedding(embedding)
            
            # Save to database
            self._save_embedding(embedding)
            
            return embedding_id
        
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def search(self, query: str, **kwargs) -> List[MediaSearchResult]:
        """
        Search media by text query.
        
        Args:
            query: Text search query
            **kwargs: Additional arguments for search
            
        Returns:
            List of search results
        """
        return self.retriever.search_by_text(query, **kwargs)
    
    def search_similar(
        self,
        media_path: Path,
        top_k: int = 5,
    ) -> List[MediaSearchResult]:
        """
        Find similar media.
        
        Args:
            media_path: Path to query media
            top_k: Number of results
            
        Returns:
            List of similar media
        """
        media_type = self.retriever._detect_media_type(media_path)
        return self.retriever.search_by_media(media_path, media_type, top_k)
    
    def get_session_media(
        self,
        session_id: str,
        media_types: Optional[List[MediaType]] = None,
    ) -> List[MediaMemoryItem]:
        """Get all media from a session."""
        return self.retriever.search_by_session(session_id, media_types)
    
    def _save_media_item(self, item: MediaMemoryItem) -> None:
        """Save media item to database."""
        import json
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO media_memory VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                item.id,
                item.session_id,
                item.media_type.value,
                str(item.file_path),
                str(item.thumbnail_path) if item.thumbnail_path else None,
                item.file_size,
                item.duration_seconds,
                item.width,
                item.height,
                item.format,
                item.created_at,
                item.context_text,
                item.auto_description,
                item.ocr_text,
                item.transcription,
                json.dumps(item.embedding_ids),
                json.dumps(item.metadata),
            ))
            conn.commit()
    
    def _save_embedding(self, embedding: MediaEmbedding) -> None:
        """Save embedding to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO media_embeddings VALUES (?, ?, ?, ?, ?, ?)
            """, (
                embedding.id,
                embedding.media_id,
                embedding.embedding_type.value,
                embedding.embedding.tobytes(),
                embedding.model_version,
                embedding.created_at,
            ))
            conn.commit()
    
    def get_stats(self) -> Dict:
        """Get system statistics."""
        with sqlite3.connect(self.db_path) as conn:
            media_count = conn.execute("SELECT COUNT(*) FROM media_memory").fetchone()[0]
            embedding_count = conn.execute("SELECT COUNT(*) FROM media_embeddings").fetchone()[0]
        
        return {
            "media_items": media_count,
            "embeddings": embedding_count,
            "storage": self.storage.get_storage_stats(),
            "index": self.index.get_stats(),
        }


__all__ = ["MultimodalMemorySystem"]
