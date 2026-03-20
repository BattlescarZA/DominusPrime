# -*- coding: utf-8 -*-
"""Security-related data models."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .config import SecurityLevel


@dataclass
class SecurityStatus:
    """Current security status and statistics."""
    
    level: SecurityLevel
    enabled: bool
    commands_executed_today: int
    approvals_pending: int
    tools_blocked: int
    last_audit_time: Optional[datetime]


@dataclass
class ToolRiskProfile:
    """Security profile for a tool."""
    
    name: str
    category: str  # ToolCategory
    risk_level: str  # RiskLevel
    requires_approval: bool
    max_executions_per_hour: Optional[int]
    allowed_in_channels: list[str]
    description: str
    potential_impact: str


@dataclass
class PendingApproval:
    """Pending approval request."""
    
    id: str
    command: str
    risk_assessment: any  # RiskAssessment
    user_id: str
    channel: str
    requested_at: datetime
    timeout_seconds: int
