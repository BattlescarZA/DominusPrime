# -*- coding: utf-8 -*-
"""Execution logger for security audit trail."""

import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import uuid

from ..database.connection import DatabaseManager
from ..database.models import CommandExecution

logger = logging.getLogger(__name__)


class ExecutionLogger:
    """Logs all command executions for security audit."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize execution logger.

        Args:
            db_manager: Database manager for security database
        """
        self.db_manager = db_manager

    async def log_execution(
        self,
        command: str,
        risk_level: str,
        approval_status: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        exit_code: Optional[int] = None,
        duration_ms: Optional[int] = None,
        working_dir: str = "",
        channel: str = "console"
    ) -> str:
        """Log a command execution.

        Args:
            command: Executed command
            risk_level: Risk level assessed
            approval_status: Approval status
            user_id: User who executed
            session_id: Session identifier
            exit_code: Command exit code
            duration_ms: Execution duration in milliseconds
            working_dir: Working directory
            channel: Channel where executed

        Returns:
            Log entry ID
        """
        log_id = f"exec_{uuid.uuid4().hex[:12]}"

        try:
            with self.db_manager.transaction("security") as conn:
                conn.execute(
                    """
                    INSERT INTO command_executions
                    (id, timestamp, user_id, session_id, command,
                     risk_level, approval_status, exit_code,
                     duration_ms, working_dir, channel)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        log_id,
                        datetime.utcnow().isoformat(),
                        user_id,
                        session_id,
                        command,
                        risk_level,
                        approval_status,
                        exit_code,
                        duration_ms,
                        working_dir,
                        channel
                    )
                )

            logger.debug(f"Logged execution: {log_id}")
            return log_id

        except Exception as e:
            logger.error(f"Failed to log execution: {e}")
            return ""

    async def log_security_event(
        self,
        event_type: str,
        user_id: str,
        details: dict
    ):
        """Log a security-related event.

        Args:
            event_type: Type of security event
            user_id: User associated with event
            details: Event details as dictionary
        """
        import json

        try:
            with self.db_manager.transaction("security") as conn:
                conn.execute(
                    """
                    INSERT INTO security_events
                    (event_type, user_id, details)
                    VALUES (?, ?, ?)
                    """,
                    (
                        event_type,
                        user_id,
                        json.dumps(details)
                    )
                )

            logger.info(f"Logged security event: {event_type} by {user_id}")

        except Exception as e:
            logger.error(f"Failed to log security event: {e}")

    async def count_executions_today(self) -> int:
        """Count command executions today.

        Returns:
            Number of executions today
        """
        try:
            today_start = datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            conn = self.db_manager.get_connection("security")
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM command_executions
                WHERE timestamp >= ?
                """,
                (today_start.isoformat(),)
            )
            count = cursor.fetchone()[0]
            return count

        except Exception as e:
            logger.error(f"Failed to count executions: {e}")
            return 0

    async def get_last_audit_time(self) -> Optional[datetime]:
        """Get timestamp of last audit log entry.

        Returns:
            Last audit timestamp or None
        """
        try:
            conn = self.db_manager.get_connection("security")
            cursor = conn.execute(
                """
                SELECT MAX(timestamp) FROM command_executions
                """
            )
            result = cursor.fetchone()[0]

            if result:
                return datetime.fromisoformat(result)
            return None

        except Exception as e:
            logger.error(f"Failed to get last audit time: {e}")
            return None

    async def get_recent_executions(
        self,
        limit: int = 100,
        risk_level: Optional[str] = None
    ) -> list[CommandExecution]:
        """Get recent command executions.

        Args:
            limit: Maximum results
            risk_level: Filter by risk level

        Returns:
            List of command executions
        """
        try:
            conn = self.db_manager.get_connection("security")

            query = "SELECT * FROM command_executions"
            params = []

            if risk_level:
                query += " WHERE risk_level = ?"
                params.append(risk_level)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [CommandExecution.from_row(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get recent executions: {e}")
            return []

    async def close(self):
        """Close logger and cleanup resources."""
        # Database connection handled by DatabaseManager
        pass
