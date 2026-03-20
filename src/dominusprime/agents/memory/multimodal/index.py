# -*- coding: utf-8 -*-
"""Multimodal memory index for storage and retrieval."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from .models import (
    MediaItem,
    MediaEmbedding,
    MultimodalMemory,
    SearchResult,
    MediaType,
    ProcessingStatus,
)
from .embedder import MultimodalEmbedder


class MultimodalIndex:
    """Stores and retrieves multimodal memories."""
    
    def __init__(
        self,
        db_path: Path,
        embedder: Optional[MultimodalEmbedder] = None,
    ):
        """Initialize multimodal index.
        
        Args:
            db_path: Path to SQLite database
            embedder: MultimodalEmbedder instance for similarity search
        """
        self.db_path = Path(db_path)
        self.embedder = embedder or MultimodalEmbedder()
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure database tables exist (already created in migrations)."""
        # Tables created in migrations/003_multimodal.sql
        pass
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    async def store_memory(
        self,
        media_item: MediaItem,
        embeddings: List[MediaEmbedding],
        text_content: Optional[str] = None,
        experience_id: Optional[str] = None,
    ) -> MultimodalMemory:
        """Store multimodal memory in database.
        
        Args:
            media_item: MediaItem to store
            embeddings: List of embeddings for the media
            text_content: Associated text content
            experience_id: Associated experience ID
            
        Returns:
            Stored MultimodalMemory
        """
        conn = self._get_connection()
        try:
            # Store media item
            conn.execute(
                """
                INSERT OR REPLACE INTO media_items (
                    id, media_type, file_path, original_filename, mime_type,
                    file_size, status, width, height, duration, description,
                    tags, detected_objects, detected_text, session_id,
                    conversation_id, user_context, created_at, processed_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    media_item.id,
                    media_item.media_type.value,
                    media_item.file_path,
                    media_item.original_filename,
                    media_item.mime_type,
                    media_item.file_size,
                    media_item.status.value,
                    media_item.width,
                    media_item.height,
                    media_item.duration,
                    media_item.description,
                    json.dumps(media_item.tags),
                    json.dumps(media_item.detected_objects),
                    media_item.detected_text,
                    media_item.session_id,
                    media_item.conversation_id,
                    media_item.user_context,
                    media_item.created_at.isoformat(),
                    media_item.processed_at.isoformat() if media_item.processed_at else None,
                    json.dumps(media_item.metadata),
                ),
            )
            
            # Store embeddings
            for embedding in embeddings:
                conn.execute(
                    """
                    INSERT INTO embeddings (
                        media_item_id, embedding_type, vector, model_name,
                        dimension, created_at, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        embedding.media_item_id,
                        embedding.embedding_type,
                        json.dumps(embedding.vector),
                        embedding.model_name,
                        embedding.dimension,
                        embedding.created_at.isoformat(),
                        json.dumps(embedding.metadata),
                    ),
                )
            
            # Store association if experience_id provided
            if experience_id:
                conn.execute(
                    """
                    INSERT INTO experience_media_associations (
                        experience_id, media_item_id, relevance_score
                    ) VALUES (?, ?, ?)
                    """,
                    (experience_id, media_item.id, 1.0),
                )
            
            conn.commit()
            
            # Create and return MultimodalMemory
            memory = MultimodalMemory(
                id=media_item.id,
                media_item=media_item,
                embeddings=embeddings,
                text_content=text_content,
                experience_id=experience_id,
            )
            
            return memory
        
        finally:
            conn.close()
    
    async def get_memory(self, media_id: str) -> Optional[MultimodalMemory]:
        """Retrieve multimodal memory by ID.
        
        Args:
            media_id: Media item ID
            
        Returns:
            MultimodalMemory if found, None otherwise
        """
        conn = self._get_connection()
        try:
            # Get media item
            row = conn.execute(
                "SELECT * FROM media_items WHERE id = ?",
                (media_id,),
            ).fetchone()
            
            if not row:
                return None
            
            media_item = self._row_to_media_item(row)
            
            # Get embeddings
            emb_rows = conn.execute(
                "SELECT * FROM embeddings WHERE media_item_id = ?",
                (media_id,),
            ).fetchall()
            
            embeddings = [self._row_to_embedding(r) for r in emb_rows]
            
            # Get association
            assoc_row = conn.execute(
                "SELECT * FROM experience_media_associations WHERE media_item_id = ? LIMIT 1",
                (media_id,),
            ).fetchone()
            
            experience_id = assoc_row["experience_id"] if assoc_row else None
            
            # Update access count
            conn.execute(
                """
                UPDATE media_items
                SET access_count = access_count + 1,
                    last_accessed_at = ?
                WHERE id = ?
                """,
                (datetime.utcnow().isoformat(), media_id),
            )
            conn.commit()
            
            return MultimodalMemory(
                id=media_id,
                media_item=media_item,
                embeddings=embeddings,
                experience_id=experience_id,
            )
        
        finally:
            conn.close()
    
    async def search(
        self,
        query: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        media_type: Optional[MediaType] = None,
        session_id: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.5,
    ) -> List[SearchResult]:
        """Search for similar multimodal memories.
        
        Args:
            query: Text query
            query_embedding: Pre-computed query embedding
            media_type: Filter by media type
            session_id: Filter by session ID
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of SearchResult objects
        """
        conn = self._get_connection()
        try:
            # Build query
            conditions = ["status = ?"]
            params: List[Any] = [ProcessingStatus.COMPLETED.value]
            
            if media_type:
                conditions.append("media_type = ?")
                params.append(media_type.value)
            
            if session_id:
                conditions.append("session_id = ?")
                params.append(session_id)
            
            where_clause = " AND ".join(conditions)
            
            # Get candidate media items
            rows = conn.execute(
                f"""
                SELECT m.*, GROUP_CONCAT(e.id) as embedding_ids
                FROM media_items m
                LEFT JOIN embeddings e ON m.id = e.media_item_id
                WHERE {where_clause}
                GROUP BY m.id
                ORDER BY m.created_at DESC
                """,
                params,
            ).fetchall()
            
            # Compute similarities if query provided
            results = []
            
            for row in rows:
                media_item = self._row_to_media_item(row)
                
                # Get embeddings
                emb_rows = conn.execute(
                    "SELECT * FROM embeddings WHERE media_item_id = ?",
                    (media_item.id,),
                ).fetchall()
                embeddings = [self._row_to_embedding(r) for r in emb_rows]
                
                # Compute similarity
                similarity = 0.0
                match_type = "default"
                
                if query_embedding and embeddings:
                    # Compare with best matching embedding
                    similarities = []
                    for emb in embeddings:
                        sim = await self.embedder.compute_similarity(
                            query_embedding, emb.vector
                        )
                        similarities.append((sim, emb.embedding_type))
                    
                    if similarities:
                        similarity, match_type = max(similarities, key=lambda x: x[0])
                
                elif query:
                    # Text-based search: check description and tags
                    query_lower = query.lower()
                    if media_item.description and query_lower in media_item.description.lower():
                        similarity = 0.8
                        match_type = "text"
                    elif any(query_lower in tag.lower() for tag in media_item.tags):
                        similarity = 0.7
                        match_type = "tag"
                    else:
                        similarity = 0.3
                        match_type = "default"
                else:
                    # No query: return recent items
                    similarity = 1.0
                    match_type = "recent"
                
                if similarity >= similarity_threshold:
                    memory = MultimodalMemory(
                        id=media_item.id,
                        media_item=media_item,
                        embeddings=embeddings,
                    )
                    
                    results.append(
                        SearchResult(
                            memory=memory,
                            similarity_score=similarity,
                            match_type=match_type,
                        )
                    )
            
            # Sort by similarity and limit
            results.sort(key=lambda r: r.similarity_score, reverse=True)
            return results[:limit]
        
        finally:
            conn.close()
    
    def _row_to_media_item(self, row: sqlite3.Row) -> MediaItem:
        """Convert database row to MediaItem."""
        return MediaItem(
            id=row["id"],
            media_type=MediaType(row["media_type"]),
            file_path=row["file_path"],
            original_filename=row["original_filename"],
            mime_type=row["mime_type"],
            file_size=row["file_size"],
            status=ProcessingStatus(row["status"]),
            width=row["width"],
            height=row["height"],
            duration=row["duration"],
            description=row["description"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            detected_objects=json.loads(row["detected_objects"]) if row["detected_objects"] else [],
            detected_text=row["detected_text"],
            session_id=row["session_id"],
            conversation_id=row["conversation_id"],
            user_context=row["user_context"],
            created_at=datetime.fromisoformat(row["created_at"]),
            processed_at=datetime.fromisoformat(row["processed_at"]) if row["processed_at"] else None,
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )
    
    def _row_to_embedding(self, row: sqlite3.Row) -> MediaEmbedding:
        """Convert database row to MediaEmbedding."""
        return MediaEmbedding(
            media_item_id=row["media_item_id"],
            embedding_type=row["embedding_type"],
            vector=json.loads(row["vector"]),
            model_name=row["model_name"],
            dimension=row["dimension"],
            created_at=datetime.fromisoformat(row["created_at"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )
    
    async def delete_memory(self, media_id: str) -> bool:
        """Delete multimodal memory.
        
        Args:
            media_id: Media item ID to delete
            
        Returns:
            True if deleted successfully
        """
        conn = self._get_connection()
        try:
            # Delete embeddings
            conn.execute("DELETE FROM embeddings WHERE media_item_id = ?", (media_id,))
            
            # Delete associations
            conn.execute(
                "DELETE FROM experience_media_associations WHERE media_item_id = ?",
                (media_id,),
            )
            
            # Delete media item
            conn.execute("DELETE FROM media_items WHERE id = ?", (media_id,))
            
            conn.commit()
            return True
        
        except Exception:
            conn.rollback()
            return False
        
        finally:
            conn.close()
