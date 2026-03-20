# -*- coding: utf-8 -*-
"""Database migration system."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..connection import DatabaseManager

logger = logging.getLogger(__name__)


def run_all_migrations(db_manager: "DatabaseManager"):
    """Run all pending migrations.

    Args:
        db_manager: Database manager instance
    """
    migrations_dir = Path(__file__).parent
    
    # Run migrations in order
    migrations = [
        ("001_experiences.sql", "experiences"),
        ("002_security.sql", "security"),
        ("003_multimodal.sql", "multimodal"),
    ]
    
    for migration_file, db_name in migrations:
        migration_path = migrations_dir / migration_file
        if not migration_path.exists():
            logger.warning(f"Migration file not found: {migration_file}")
            continue
        
        logger.info(f"Running migration: {migration_file} on {db_name} database")
        
        with db_manager.transaction(db_name) as conn:
            with open(migration_path, "r", encoding="utf-8") as f:
                sql = f.read()
                conn.executescript(sql)
        
        logger.info(f"Migration {migration_file} completed successfully")
