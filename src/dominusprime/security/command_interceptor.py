# -*- coding: utf-8 -*-
"""Command interceptor for shell command security."""

import logging
from typing import Optional

from .base import (
    ExecutionContext,
    InterceptResult,
    InterceptAction,
    RiskLevel,
)
from .config import ShellSecurityConfig
from .risk_analyzer import RiskAnalyzer

logger = logging.getLogger(__name__)


class CommandInterceptor:
    """Intercepts and analyzes shell commands before execution."""

    def __init__(self, config: ShellSecurityConfig):
        """Initialize command interceptor.

        Args:
            config: Shell security configuration
        """
        self.config = config
        self.risk_analyzer = RiskAnalyzer(config)
        self.approval_handler = None  # Lazy init

    async def intercept(
        self,
        command: str,
        context: ExecutionContext
    ) -> InterceptResult:
        """Intercept and analyze command before execution.

        Args:
            command: Shell command to intercept
            context: Execution context

        Returns:
            InterceptResult with action to take
        """
        logger.info(f"Intercepting command: {command[:100]}")

        # Check if security is enabled
        if not self.config.enabled:
            logger.debug("Security disabled, allowing command")
            return InterceptResult(
                action=InterceptAction.EXECUTE_IMMEDIATELY,
                risk_assessment=None,
                reason="Security not enabled"
            )

        # Analyze risk
        risk_assessment = await self.risk_analyzer.analyze_risk(command, context)

        # Check if blocked
        if risk_assessment.level == RiskLevel.CRITICAL:
            logger.warning(
                f"Blocking command due to critical risk: {command[:100]}"
            )
            return InterceptResult(
                action=InterceptAction.BLOCKED,
                risk_assessment=risk_assessment,
                reason=f"Command blocked: {', '.join(risk_assessment.reasons)}"
            )

        # Check if safe and can execute immediately
        if risk_assessment.level == RiskLevel.SAFE:
            logger.debug("Command assessed as safe, allowing")
            return InterceptResult(
                action=InterceptAction.EXECUTE_IMMEDIATELY,
                risk_assessment=risk_assessment,
                reason="Command assessed as safe"
            )

        # Check if auto-approval enabled for safe commands
        if (self.config.auto_approve_safe_commands and
            risk_assessment.level == RiskLevel.LOW):
            logger.debug("Auto-approving low-risk command")
            return InterceptResult(
                action=InterceptAction.EXECUTE_IMMEDIATELY,
                risk_assessment=risk_assessment,
                reason="Auto-approved low-risk command"
            )

        # Require approval for medium/high risk
        if self.config.require_approval:
            logger.info(
                f"Approval required for {risk_assessment.level.value} risk command"
            )
            return InterceptResult(
                action=InterceptAction.REQUIRE_APPROVAL,
                risk_assessment=risk_assessment,
                reason=f"Approval required for {risk_assessment.level.value} risk"
            )

        # Default: allow execution
        return InterceptResult(
            action=InterceptAction.EXECUTE_IMMEDIATELY,
            risk_assessment=risk_assessment,
            reason="Approval not required"
        )

    def update_config(self, new_profile):
        """Update configuration from security profile.

        Args:
            new_profile: New security profile
        """
        self.config.require_approval = new_profile.shell_require_approval
        self.config.auto_approve_safe_commands = new_profile.shell_auto_approve_safe
        self.config.blocked_commands = new_profile.shell_blocked_patterns
        
        logger.info(f"Updated command interceptor config from profile: {new_profile.level.value}")
