# -*- coding: utf-8 -*-
"""Base classes and enums for security module."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


class RiskLevel(Enum):
    """Risk levels for commands and tools."""
    
    SAFE = "safe"           # Read-only operations, info commands
    LOW = "low"             # Simple file operations
    MEDIUM = "medium"       # File modifications, network operations
    HIGH = "high"           # System modifications, privileged operations
    CRITICAL = "critical"   # Data deletion, system-wide changes


class PermissionLevel(Enum):
    """Permission levels for tool access."""
    
    DENIED = "denied"       # Tool is blocked
    PROMPT = "prompt"       # Ask user each time
    SESSION = "session"     # Allow for current session
    ALWAYS = "always"       # Always allow (use with caution)


class ApprovalDecision(Enum):
    """Approval decision results."""
    
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"
    AUTO_APPROVED = "auto_approved"


class InterceptAction(Enum):
    """Actions that can be taken when intercepting commands."""
    
    EXECUTE_IMMEDIATELY = "execute_immediately"
    REQUIRE_APPROVAL = "require_approval"
    BLOCKED = "blocked"


@dataclass
class ExecutionContext:
    """Context information for command/tool execution."""
    
    user_id: str
    session_id: str
    channel: str
    working_dir: str
    timestamp: datetime
    
    @classmethod
    def from_current(cls) -> "ExecutionContext":
        """Create context from current environment."""
        from ..constant import WORKING_DIR
        return cls(
            user_id="system",
            session_id="",
            channel="console",
            working_dir=str(WORKING_DIR),
            timestamp=datetime.utcnow()
        )


@dataclass
class RiskAssessment:
    """Risk assessment result for a command or tool."""
    
    level: RiskLevel
    score: float  # 0.0 to 1.0
    reasons: list[str]
    affected_paths: list[str]
    detected_patterns: list[str]
    
    def is_high_risk(self) -> bool:
        """Check if risk level is high or critical."""
        return self.level in (RiskLevel.HIGH, RiskLevel.CRITICAL)


@dataclass
class InterceptResult:
    """Result of command interception."""
    
    action: InterceptAction
    risk_assessment: Optional[RiskAssessment]
    reason: str


@dataclass
class ApprovalResult:
    """Result of approval request."""
    
    decision: ApprovalDecision
    reason: str
    remember: bool = False  # Whether to remember this decision
