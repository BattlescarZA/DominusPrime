# -*- coding: utf-8 -*-
"""Database connection management for DominusPrime."""

import logging
import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and migrations."""

    def __init__(self, db_dir: Path):
        """Initialize database manager.

        Args:
            db_dir: Directory where database files will be stored
        """
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        
        # Database files
        self.experiences_db = self.db_dir / "experiences.db"
        self.security_db = self.db_dir / "security.db"
        self.multimodal_db = self.db_dir / "multimodal.db"
        
        self._connections: dict[str, Optional[sqlite3.Connection]] = {
            "experiences": None,
            "security": None,
            "multimodal": None,
        }

    def get_connection(self, db_name: str) -> sqlite3.Connection:
        """Get database connection.

        Args:
            db_name: Name of database ('experiences', 'security', 'multimodal')

        Returns:
            SQLite connection object

        Raises:
            ValueError: If db_name is invalid
        """
        if db_name not in self._connections:
            raise ValueError(
                f"Invalid database name: {db_name}. "
                f"Must be one of: {list(self._connections.keys())}"
            )

        if self._connections[db_name] is None:
            db_path = getattr(self, f"{db_name}_db")
            conn = sqlite3.connect(str(db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            self._connections[db_name] = conn
            logger.info(f"Connected to {db_name} database: {db_path}")

        return self._connections[db_name]

    @contextmanager
    def transaction(self, db_name: str):
        """Context manager for database transactions.

        Args:
            db_name: Name of database

        Yields:
            Database connection with transaction
        """
        conn = self.get_connection(db_name)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction failed for {db_name}: {e}")
            raise

    def close_all(self):
        """Close all database connections."""
        for db_name, conn in self._connections.items():
            if conn is not None:
                conn.close()
                logger.info(f"Closed {db_name} database connection")
                self._connections[db_name] = None

    def run_migrations(self):
        """Run all pending database migrations."""
        from .migrations import run_all_migrations
        run_all_migrations(self)
        logger.info("All migrations completed successfully")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def initialize_database(db_dir: Path) -> DatabaseManager:
    """Initialize global database manager.

    Args:
        db_dir: Directory for database files

    Returns:
        DatabaseManager instance
    """
    global _db_manager
    _db_manager = DatabaseManager(db_dir)
    _db_manager.run_migrations()
    return _db_manager


def get_db_connection(db_name: str) -> sqlite3.Connection:
    """Get database connection from global manager.

    Args:
        db_name: Name of database

    Returns:
        SQLite connection

    Raises:
        RuntimeError: If database manager not initialized
    """
    if _db_manager is None:
        raise RuntimeError(
            "Database manager not initialized. "
            "Call initialize_database() first."
        )
    return _db_manager.get_connection(db_name)
