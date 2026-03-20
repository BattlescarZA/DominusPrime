# -*- coding: utf-8 -*-
"""Security manager - central security management."""

import logging
from typing import Optional
from pathlib import Path

from .config import SecurityConfig, SecurityLevel
from .base import ExecutionContext

logger = logging.getLogger(__name__)


class SecurityManager:
    """Central security management singleton.
    
    Coordinates all security features:
    - Command interception and approval
    - Tool permissions
    - Security levels
    - Audit logging
    """

    _instance: Optional['SecurityManager'] = None

    def __init__(self, config: SecurityConfig, db_dir: Path):
        """Initialize security manager.

        Args:
            config: Security configuration
            db_dir: Directory for security database
        """
        self.config = config
        self.db_dir = db_dir
        self.current_level = config.level
        
        # Components will be initialized lazily
        self._command_interceptor = None
        self._permission_manager = None
        self._execution_guard = None
        self._execution_logger = None
        
        logger.info(f"SecurityManager initialized with level: {self.current_level.value}")

    @classmethod
    def get_instance(cls) -> 'SecurityManager':
        """Get singleton instance.

        Returns:
            SecurityManager instance

        Raises:
            RuntimeError: If not initialized
        """
        if cls._instance is None:
            raise RuntimeError(
                "SecurityManager not initialized. "
                "Call SecurityManager.initialize() first."
            )
        return cls._instance

    @classmethod
    def initialize(
        cls,
        config: SecurityConfig,
        db_dir: Path
    ) -> 'SecurityManager':
        """Initialize security manager singleton.

        Args:
            config: Security configuration
            db_dir: Directory for security database

        Returns:
            SecurityManager instance
        """
        if cls._instance is None:
            cls._instance = cls(config, db_dir)
        return cls._instance

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if security manager is initialized."""
        return cls._instance is not None

    def is_enabled(self) -> bool:
        """Check if security features are enabled.

        Returns:
            True if security is enabled
        """
        return self.config.enabled

    @property
    def command_interceptor(self):
        """Get command interceptor (lazy initialization)."""
        if self._command_interceptor is None and self.is_enabled():
            from .command_interceptor import CommandInterceptor
            self._command_interceptor = CommandInterceptor(self.config)
        return self._command_interceptor

    @property
    def permission_manager(self):
        """Get permission manager (lazy initialization)."""
        if self._permission_manager is None and self.is_enabled():
            from .permission_manager import PermissionManager
            self._permission_manager = PermissionManager(
                self.config,
                self.db_dir
            )
        return self._permission_manager

    @property
    def execution_logger(self):
        """Get execution logger (lazy initialization)."""
        if self._execution_logger is None and self.is_enabled():
            from .execution_logger import ExecutionLogger
            self._execution_logger = ExecutionLogger(self.db_dir)
        return self._execution_logger

    async def change_security_level(
        self,
        level: SecurityLevel,
        user_id: str = "system"
    ):
        """Change security level and apply new profile.

        Args:
            level: New security level
            user_id: User requesting the change
        """
        from .profiles import SECURITY_PROFILES
        
        old_level = self.current_level
        new_profile = SECURITY_PROFILES[level]
        
        logger.info(
            f"Changing security level from {old_level.value} to {level.value}"
        )
        
        # Apply new profile settings
        self.config.level = level
        self.current_level = level
        
        # Update component configurations
        if self._command_interceptor:
            self._command_interceptor.update_config(new_profile)
        if self._permission_manager:
            self._permission_manager.update_config(new_profile)
        
        # Log the change
        if self.execution_logger:
            await self.execution_logger.log_security_event(
                event_type="security_level_changed",
                user_id=user_id,
                details={
                    "old_level": old_level.value,
                    "new_level": level.value
                }
            )
        
        logger.info(f"Security level changed to: {level.value}")

    async def get_security_status(self):
        """Get current security status and statistics.

        Returns:
            SecurityStatus object with current state
        """
        from .models import SecurityStatus
        
        status = SecurityStatus(
            level=self.current_level,
            enabled=self.is_enabled(),
            commands_executed_today=0,
            approvals_pending=0,
            tools_blocked=0,
            last_audit_time=None
        )
        
        # Populate statistics if logger is available
        if self.execution_logger:
            status.commands_executed_today = \
                await self.execution_logger.count_executions_today()
            status.last_audit_time = \
                await self.execution_logger.get_last_audit_time()
        
        if self._command_interceptor and self._command_interceptor.approval_handler:
            status.approvals_pending = \
                len(self._command_interceptor.approval_handler.pending_approvals)
        
        return status

    async def shutdown(self):
        """Shutdown security manager and cleanup resources."""
        logger.info("Shutting down SecurityManager")
        
        # Cleanup components
        if self._execution_logger:
            await self._execution_logger.close()
        
        # Reset singleton
        SecurityManager._instance = None
