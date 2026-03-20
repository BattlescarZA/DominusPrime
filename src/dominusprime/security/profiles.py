# -*- coding: utf-8 -*-
"""Security level profiles with pre-configured settings."""

from dataclasses import dataclass
from typing import List, Optional

from .config import SecurityLevel
from .base import PermissionLevel


@dataclass
class SecurityProfile:
    """Complete security configuration for a level."""
    
    level: SecurityLevel
    description: str
    
    # Shell command security
    shell_require_approval: bool
    shell_auto_approve_safe: bool
    shell_blocked_patterns: List[str]
    
    # Tool security
    tool_default_permission: PermissionLevel
    tool_rate_limiting_enabled: bool
    tool_auto_approve_read_only: bool
    
    # Skills security
    skills_scan_on_load: bool
    skills_block_unsigned: bool
    skills_require_approval_new: bool
    
    # Memory security
    memory_encrypt_sensitive: bool
    memory_auto_expire_days: Optional[int]
    
    # General
    audit_logging: bool
    session_timeout_minutes: Optional[int]


# Predefined security profiles
SECURITY_PROFILES = {
    SecurityLevel.OPEN: SecurityProfile(
        level=SecurityLevel.OPEN,
        description="Minimal restrictions. For experienced users in trusted environments.",
        shell_require_approval=False,
        shell_auto_approve_safe=True,
        shell_blocked_patterns=[],
        tool_default_permission=PermissionLevel.ALWAYS,
        tool_rate_limiting_enabled=False,
        tool_auto_approve_read_only=True,
        skills_scan_on_load=False,
        skills_block_unsigned=False,
        skills_require_approval_new=False,
        memory_encrypt_sensitive=False,
        memory_auto_expire_days=None,
        audit_logging=True,
        session_timeout_minutes=None
    ),
    
    SecurityLevel.RELAXED: SecurityProfile(
        level=SecurityLevel.RELAXED,
        description="Basic safety checks with minimal friction.",
        shell_require_approval=True,
        shell_auto_approve_safe=True,
        shell_blocked_patterns=["rm -rf /", "dd if=/dev/zero"],
        tool_default_permission=PermissionLevel.SESSION,
        tool_rate_limiting_enabled=True,
        tool_auto_approve_read_only=True,
        skills_scan_on_load=True,
        skills_block_unsigned=False,
        skills_require_approval_new=False,
        memory_encrypt_sensitive=False,
        memory_auto_expire_days=180,
        audit_logging=True,
        session_timeout_minutes=None
    ),
    
    SecurityLevel.BALANCED: SecurityProfile(
        level=SecurityLevel.BALANCED,
        description="Balanced security. Recommended for most users.",
        shell_require_approval=True,
        shell_auto_approve_safe=True,
        shell_blocked_patterns=["rm -rf /", "dd if=/dev/zero", "mkfs"],
        tool_default_permission=PermissionLevel.PROMPT,
        tool_rate_limiting_enabled=True,
        tool_auto_approve_read_only=True,
        skills_scan_on_load=True,
        skills_block_unsigned=False,
        skills_require_approval_new=True,
        memory_encrypt_sensitive=True,
        memory_auto_expire_days=90,
        audit_logging=True,
        session_timeout_minutes=1440  # 24 hours
    ),
    
    SecurityLevel.STRICT: SecurityProfile(
        level=SecurityLevel.STRICT,
        description="High security with frequent confirmations.",
        shell_require_approval=True,
        shell_auto_approve_safe=False,  # Approve even safe commands
        shell_blocked_patterns=[
            "rm", "dd", "mkfs", "format", "del",
            "sudo", "chmod 777"
        ],
        tool_default_permission=PermissionLevel.PROMPT,
        tool_rate_limiting_enabled=True,
        tool_auto_approve_read_only=False,  # Approve even reads
        skills_scan_on_load=True,
        skills_block_unsigned=True,
        skills_require_approval_new=True,
        memory_encrypt_sensitive=True,
        memory_auto_expire_days=60,
        audit_logging=True,
        session_timeout_minutes=480  # 8 hours
    ),
    
    SecurityLevel.PARANOID: SecurityProfile(
        level=SecurityLevel.PARANOID,
        description="Maximum security. Approve every action.",
        shell_require_approval=True,
        shell_auto_approve_safe=False,
        shell_blocked_patterns=[
            "rm", "dd", "mkfs", "format", "del",
            "rmdir", "sudo", "chmod", "chown",
            "curl.*|.*sh", "wget.*|.*bash"
        ],
        tool_default_permission=PermissionLevel.PROMPT,
        tool_rate_limiting_enabled=True,
        tool_auto_approve_read_only=False,
        skills_scan_on_load=True,
        skills_block_unsigned=True,
        skills_require_approval_new=True,
        memory_encrypt_sensitive=True,
        memory_auto_expire_days=30,
        audit_logging=True,
        session_timeout_minutes=60  # 1 hour
    )
}


def get_profile(level: SecurityLevel) -> SecurityProfile:
    """Get security profile for a level.
    
    Args:
        level: Security level
        
    Returns:
        SecurityProfile for the level
    """
    return SECURITY_PROFILES[level]
