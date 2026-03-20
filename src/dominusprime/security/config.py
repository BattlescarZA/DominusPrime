# -*- coding: utf-8 -*-
"""Security configuration models."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class SecurityLevel(Enum):
    """Pre-defined security levels."""
    
    OPEN = "open"           # Minimal restrictions
    RELAXED = "relaxed"     # Basic safety checks
    BALANCED = "balanced"   # Default, recommended
    STRICT = "strict"       # High security
    PARANOID = "paranoid"   # Maximum security


class ShellSecurityConfig(BaseModel):
    """Configuration for shell command security."""
    
    enabled: bool = True
    require_approval: bool = True
    approval_timeout_seconds: int = 300
    auto_approve_safe_commands: bool = True
    safe_commands: List[str] = Field(default_factory=lambda: [
        "ls", "pwd", "echo", "cat", "grep", "find",
        "git status", "git log", "docker ps", "which"
    ])
    blocked_commands: List[str] = Field(default_factory=lambda: [
        "rm -rf /",
        "dd if=/dev/zero",
        "mkfs"
    ])
    log_all_executions: bool = True
    audit_retention_days: int = 90


class ToolSecurityConfig(BaseModel):
    """Configuration for tool/skills security."""
    
    enabled: bool = True
    default_permission: str = "prompt"  # PermissionLevel
    auto_approve_read_only: bool = True
    rate_limiting_enabled: bool = True
    rate_limiting: dict = Field(default_factory=lambda: {
        "default_hourly_limit": 100
    })
    tool_overrides: dict = Field(default_factory=dict)


class SkillsSecurityConfig(BaseModel):
    """Configuration for skills security."""
    
    scan_on_load: bool = True
    block_unsigned: bool = False
    require_approval_for_new: bool = True
    trusted_sources: List[str] = Field(default_factory=lambda: [
        "builtin",
        "verified_repository"
    ])


class SecurityConfig(BaseModel):
    """Main security configuration."""
    
    enabled: bool = True
    level: SecurityLevel = SecurityLevel.BALANCED
    
    shell_commands: ShellSecurityConfig = Field(
        default_factory=ShellSecurityConfig
    )
    tools: ToolSecurityConfig = Field(
        default_factory=ToolSecurityConfig
    )
    skills: SkillsSecurityConfig = Field(
        default_factory=SkillsSecurityConfig
    )
