# -*- coding: utf-8 -*-
"""Experience knowledge base - storage and retrieval of experiences."""

import logging
import sqlite3
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from ....database.connection import DatabaseManager
from ....database.models import Experience

logger = logging.getLogger(__name__)


class ExperienceKnowledgeBase:
    """Storage and retrieval system for experiences."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize knowledge base.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager

    async def store_experience(self, experience: Experience) -> bool:
        """Store an experience in the knowledge base.

        Args:
            experience: Experience to store

        Returns:
            True if stored successfully
        """
        try:
            with self.db_manager.transaction("experiences") as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO experiences
                    (id, type, title, description, context, content,
                     confidence, frequency, success_rate,
                     created_at, last_used, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        experience.id,
                        experience.type,
                        experience.title,
                        experience.description,
                        str(experience.context),
                        str(experience.content),
                        experience.confidence,
                        experience.frequency,
                        experience.success_rate,
                        experience.created_at.isoformat(),
                        experience.last_used.isoformat() if experience.last_used else None,
                        experience.updated_at.isoformat()
                    )
                )
            logger.info(f"Stored experience: {experience.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store experience {experience.id}: {e}")
            return False

    async def get_experience(self, experience_id: str) -> Optional[Experience]:
        """Retrieve an experience by ID.

        Args:
            experience_id: Experience identifier

        Returns:
            Experience object or None if not found
        """
        try:
            conn = self.db_manager.get_connection("experiences")
            cursor = conn.execute(
                "SELECT * FROM experiences WHERE id = ?",
                (experience_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return Experience.from_row(row)
            return None
        except Exception as e:
            logger.error(f"Failed to get experience {experience_id}: {e}")
            return None

    async def list_experiences(
        self,
        experience_type: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 100
    ) -> List[Experience]:
        """List experiences with optional filtering.

        Args:
            experience_type: Filter by type
            min_confidence: Minimum confidence threshold
            limit: Maximum number to return

        Returns:
            List of experiences
        """
        try:
            conn = self.db_manager.get_connection("experiences")
            
            query = """
                SELECT * FROM experiences
                WHERE confidence >= ?
            """
            params = [min_confidence]
            
            if experience_type:
                query += " AND type = ?"
                params.append(experience_type)
            
            query += " ORDER BY confidence DESC, frequency DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            return [Experience.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to list experiences: {e}")
            return []

    async def search_experiences(
        self,
        keywords: List[str],
        limit: int = 10
    ) -> List[Experience]:
        """Search experiences by keywords.

        Args:
            keywords: Keywords to search for
            limit: Maximum results

        Returns:
            List of matching experiences
        """
        try:
            conn = self.db_manager.get_connection("experiences")
            
            # Simple keyword search (can be enhanced with vector search)
            query = """
                SELECT * FROM experiences
                WHERE 
            """
            
            conditions = []
            params = []
            for keyword in keywords:
                conditions.append(
                    "(title LIKE ? OR description LIKE ? OR context LIKE ?)"
                )
                pattern = f"%{keyword}%"
                params.extend([pattern, pattern, pattern])
            
            query += " OR ".join(conditions)
            query += " ORDER BY confidence DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            return [Experience.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to search experiences: {e}")
            return []

    async def update_usage(self, experience_id: str) -> bool:
        """Update usage statistics for an experience.

        Args:
            experience_id: Experience identifier

        Returns:
            True if updated successfully
        """
        try:
            with self.db_manager.transaction("experiences") as conn:
                conn.execute(
                    """
                    UPDATE experiences
                    SET frequency = frequency + 1,
                        last_used = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        datetime.utcnow().isoformat(),
                        datetime.utcnow().isoformat(),
                        experience_id
                    )
                )
            logger.info(f"Updated usage for experience: {experience_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update experience usage: {e}")
            return False

    async def delete_experience(self, experience_id: str) -> bool:
        """Delete an experience.

        Args:
            experience_id: Experience identifier

        Returns:
            True if deleted successfully
        """
        try:
            with self.db_manager.transaction("experiences") as conn:
                conn.execute(
                    "DELETE FROM experiences WHERE id = ?",
                    (experience_id,)
                )
            logger.info(f"Deleted experience: {experience_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete experience: {e}")
            return False

    async def get_statistics(self) -> dict:
        """Get knowledge base statistics.

        Returns:
            Dictionary with statistics
        """
        try:
            conn = self.db_manager.get_connection("experiences")
            
            # Total experiences
            cursor = conn.execute("SELECT COUNT(*) FROM experiences")
            total = cursor.fetchone()[0]
            
            # By type
            cursor = conn.execute(
                """
                SELECT type, COUNT(*) as count
                FROM experiences
                GROUP BY type
                """
            )
            by_type = {row["type"]: row["count"] for row in cursor.fetchall()}
            
            # Average confidence
            cursor = conn.execute("SELECT AVG(confidence) FROM experiences")
            avg_confidence = cursor.fetchone()[0] or 0.0
            
            return {
                "total_experiences": total,
                "by_type": by_type,
                "average_confidence": avg_confidence
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
