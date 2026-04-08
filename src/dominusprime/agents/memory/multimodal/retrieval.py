# -*- coding: utf-8 -*-
"""
Multimodal retrieval engine.

Provides cross-modal search capabilities:
- Text → Media
- Media → Media  
- Cross-modal queries
"""
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from .embedder import ContentEmbedder
from .index import MultimodalIndex
from .models import (
    EmbeddingType,
    MediaMemoryItem,
    MediaSearchResult,
    MediaType,
    MultimodalQuery,
)

logger = logging.getLogger(__name__)


class MultimodalRetriever:
    """
    High-level interface for searching multimodal memories.
    
    Supports:
    - Text-to-media search ("find images of cats")
    - Media-to-media search (find similar images)
    - Cross-modal search (query with image, get related text)
    - Temporal and contextual filtering
    """
    
    def __init__(
        self,
        db_path: Path,
        index: MultimodalIndex,
        embedder: ContentEmbedder,
    ):
        """
        Initialize retriever.
        
        Args:
            db_path: Path to SQLite database
            index: Multimodal index for similarity search
            embedder: Content embedder for generating query embeddings
        """
        self.db_path = db_path
        self.index = index
        self.embedder = embedder
        
        logger.info("MultimodalRetriever initialized")
    
    def search_by_text(
        self,
        query: str,
        media_types: Optional[List[MediaType]] = None,
        session_ids: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> List[MediaSearchResult]:
        """
        Search for media matching text description.
        
        Args:
            query: Text query
            media_types: Filter by media types
            session_ids: Filter by session IDs
            top_k: Number of results
            
        Returns:
            List of search results ranked by relevance
        """
        # Generate query embedding
        query_embedding = self.embedder.embed_text(query)
        
        # Search in CLIP index (works for both images and text)
        embedding_ids = self.index.search(
            query_embedding,
            EmbeddingType.CLIP,
            top_k=top_k * 2,  # Get more candidates for filtering
        )
        
        # Retrieve media items from database
        results = []
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            for emb_id, distance in embedding_ids:
                # Get media ID from embedding
                row = conn.execute(
                    "SELECT media_id FROM media_embeddings WHERE id = ?",
                    (emb_id,)
                ).fetchone()
                
                if not row:
                    continue
                
                media_id = row['media_id']
                
                # Get media item
                media_row = conn.execute(
                    "SELECT * FROM media_memory WHERE id = ?",
                    (media_id,)
                ).fetchone()
                
                if not media_row:
                    continue
                
                # Apply filters
                if media_types and media_row['media_type'] not in [mt.value for mt in media_types]:
                    continue
                
                if session_ids and media_row['session_id'] not in session_ids:
                    continue
                
                # Create result
                media_item = self._row_to_media_item(media_row)
                
                # Convert distance to similarity (L2 to cosine-like)
                similarity = 1.0 / (1.0 + distance)
                
                result = MediaSearchResult(
                    media_item=media_item,
                    similarity_score=similarity,
                    matched_embedding_type=EmbeddingType.CLIP,
                    rank=len(results),
                )
                
                results.append(result)
                
                if len(results) >= top_k:
                    break
        
        logger.info(f"Text search '{query}' returned {len(results)} results")
        return results
    
    def search_by_media(
        self,
        media_path: Path,
        media_type: MediaType,
        top_k: int = 5,
    ) -> List[MediaSearchResult]:
        """
        Search for similar media.
        
        Args:
            media_path: Path to query media file
            media_type: Type of media
            top_k: Number of results
            
        Returns:
            List of similar media items
        """
        # Generate embedding for query media
        if media_type == MediaType.IMAGE:
            query_embedding = self.embedder.embed_image(media_path)
        else:
            logger.warning(f"Media-to-media search not implemented for {media_type}")
            return []
        
        # Search
        embedding_ids = self.index.search(
            query_embedding,
            EmbeddingType.CLIP,
            top_k=top_k,
        )
        
        # Retrieve results
        results = []
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            for emb_id, distance in embedding_ids:
                row = conn.execute(
                    "SELECT media_id FROM media_embeddings WHERE id = ?",
                    (emb_id,)
                ).fetchone()
                
                if not row:
                    continue
                
                media_row = conn.execute(
                    "SELECT * FROM media_memory WHERE id = ?",
                    (row['media_id'],)
                ).fetchone()
                
                if not media_row:
                    continue
                
                media_item = self._row_to_media_item(media_row)
                similarity = 1.0 / (1.0 + distance)
                
                result = MediaSearchResult(
                    media_item=media_item,
                    similarity_score=similarity,
                    matched_embedding_type=EmbeddingType.CLIP,
                    rank=len(results),
                )
                
                results.append(result)
        
        logger.info(f"Media search returned {len(results)} results")
        return results
    
    def search_multimodal(self, query: MultimodalQuery) -> List[MediaSearchResult]:
        """
        Execute multimodal query with multiple filters.
        
        Args:
            query: MultimodalQuery object
            
        Returns:
            Filtered and ranked results
        """
        if query.text_query:
            results = self.search_by_text(
                query.text_query,
                media_types=query.media_types,
                session_ids=query.session_ids,
                top_k=query.top_k,
            )
        elif query.media_path:
            # Detect media type from path
            media_type = self._detect_media_type(query.media_path)
            results = self.search_by_media(
                query.media_path,
                media_type,
                top_k=query.top_k,
            )
        else:
            results = []
        
        # Apply date range filter if specified
        if query.date_range:
            start_time, end_time = query.date_range
            results = [
                r for r in results
                if start_time <= r.media_item.created_at <= end_time
            ]
        
        return results
    
    def search_by_session(
        self,
        session_id: str,
        media_types: Optional[List[MediaType]] = None,
    ) -> List[MediaMemoryItem]:
        """
        Get all media from a specific session.
        
        Args:
            session_id: Session ID
            media_types: Optional filter by media types
            
        Returns:
            List of media items
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = "SELECT * FROM media_memory WHERE session_id = ?"
            params = [session_id]
            
            if media_types:
                placeholders = ','.join('?' * len(media_types))
                query += f" AND media_type IN ({placeholders})"
                params.extend([mt.value for mt in media_types])
            
            query += " ORDER BY created_at DESC"
            
            rows = conn.execute(query, params).fetchall()
            
            return [self._row_to_media_item(row) for row in rows]
    
    def _row_to_media_item(self, row: sqlite3.Row) -> MediaMemoryItem:
        """Convert database row to MediaMemoryItem."""
        import json
        
        return MediaMemoryItem(
            id=row['id'],
            session_id=row['session_id'],
            media_type=MediaType(row['media_type']),
            file_path=Path(row['file_path']),
            thumbnail_path=Path(row['thumbnail_path']) if row['thumbnail_path'] else None,
            file_size=row['file_size'],
            duration_seconds=row['duration_seconds'],
            width=row['width'],
            height=row['height'],
            format=row['format'],
            created_at=row['created_at'],
            context_text=row['context_text'],
            auto_description=row['auto_description'],
            ocr_text=row['ocr_text'],
            transcription=row['transcription'],
            embedding_ids=json.loads(row['embedding_id']) if row['embedding_id'] else [],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
        )
    
    def _detect_media_type(self, file_path: Path) -> MediaType:
        """Detect media type from file extension."""
        ext = file_path.suffix.lower()
        
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
        audio_exts = {'.mp3', '.wav', '.ogg', '.m4a', '.flac'}
        
        if ext in image_exts:
            return MediaType.IMAGE
        elif ext in video_exts:
            return MediaType.VIDEO
        elif ext in audio_exts:
            return MediaType.AUDIO
        else:
            return MediaType.DOCUMENT


__all__ = ["MultimodalRetriever"]
