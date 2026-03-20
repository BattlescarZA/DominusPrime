# -*- coding: utf-8 -*-
"""Approval handler for requesting user confirmation."""

import logging
import asyncio
import uuid
from typing import Dict
from datetime import datetime

from .base import (
    RiskAssessment,
    ApprovalResult,
    ApprovalDecision,
    PendingApproval,
)

logger = logging.getLogger(__name__)


class ApprovalHandler:
    """Handles user approval requests for risky commands."""

    def __init__(self):
        """Initialize approval handler."""
        self.pending_approvals: Dict[str, PendingApproval] = {}
        self._approval_futures: Dict[str, asyncio.Future] = {}

    async def request_approval(
        self,
        command: str,
        risk: RiskAssessment,
        channel: str,
        user_id: str,
        timeout: int = 300
    ) -> ApprovalResult:
        """Request user approval for command execution.

        Args:
            command: Command requiring approval
            risk: Risk assessment
            channel: Channel for approval request
            user_id: User to approve
            timeout: Timeout in seconds

        Returns:
            ApprovalResult with decision
        """
        approval_id = f"appr_{uuid.uuid4().hex[:12]}"

        logger.info(
            f"Requesting approval for command (risk: {risk.level.value}): "
            f"{command[:100]}"
        )

        # Create pending approval
        pending = PendingApproval(
            id=approval_id,
            command=command,
            risk_assessment=risk,
            user_id=user_id,
            channel=channel,
            requested_at=datetime.utcnow(),
            timeout_seconds=timeout
        )

        self.pending_approvals[approval_id] = pending

        # Create future for async waiting
        future = asyncio.Future()
        self._approval_futures[approval_id] = future

        # Send approval request based on channel
        await self._send_approval_request(pending)

        # Wait for approval or timeout
        try:
            decision = await asyncio.wait_for(future, timeout=timeout)
            return ApprovalResult(
                decision=decision,
                reason=f"User {decision.value}",
                remember=False
            )
        except asyncio.TimeoutError:
            logger.warning(f"Approval request {approval_id} timed out")
            return ApprovalResult(
                decision=ApprovalDecision.TIMEOUT,
                reason=f"Approval request timed out after {timeout}s",
                remember=False
            )
        finally:
            # Cleanup
            self.pending_approvals.pop(approval_id, None)
            self._approval_futures.pop(approval_id, None)

    async def _send_approval_request(
        self,
        pending: PendingApproval
    ):
        """Send approval request to user.

        Args:
            pending: Pending approval information
        """
        # Format approval message
        message = self._format_approval_message(pending)

        # Log the approval request (in real implementation, this would
        # send to the appropriate channel)
        logger.info(
            f"[APPROVAL REQUEST {pending.id}]\n"
            f"{message}\n"
            f"Waiting for user response..."
        )

        # For now, just log. In full implementation:
        # - Console: Print and wait for input
        # - Telegram/Discord: Send message with buttons
        # - Voice: Read command and wait for verbal confirmation

    def _format_approval_message(
        self,
        pending: PendingApproval
    ) -> str:
        """Format approval request message.

        Args:
            pending: Pending approval

        Returns:
            Formatted message
        """
        risk = pending.risk_assessment

        message = f"""
⚠️  Command Approval Required

Risk Level: {risk.level.value.upper()}
Command: {pending.command}

This command will:
{chr(10).join(f'- {reason}' for reason in risk.reasons)}

Options:
[A] Approve once
[D] Deny
[S] Approve for this session (safe commands only)

Approval ID: {pending.id}
Timeout: {pending.timeout_seconds}s
"""
        return message.strip()

    async def provide_decision(
        self,
        approval_id: str,
        decision: ApprovalDecision
    ):
        """Provide approval decision for a pending request.

        Args:
            approval_id: Approval request ID
            decision: Approval decision
        """
        future = self._approval_futures.get(approval_id)

        if future and not future.done():
            future.set_result(decision)
            logger.info(f"Approval {approval_id}: {decision.value}")
        else:
            logger.warning(
                f"Attempted to provide decision for unknown/completed "
                f"approval: {approval_id}"
            )

    async def check_auto_approval(
        self,
        command: str,
        user_id: str
    ) -> bool:
        """Check if command matches pre-approved patterns.

        Args:
            command: Command to check
            user_id: User ID

        Returns:
            True if auto-approved
        """
        # This would check against stored approval patterns
        # For now, return False (no auto-approvals)
        return False
