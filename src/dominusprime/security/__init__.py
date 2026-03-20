# -*- coding: utf-8 -*-
"""Security module for DominusPrime.

Provides security features including:
- Shell command confirmation
- Tool/skills permissions  
- Security level profiles
- Audit logging
"""

from .manager import SecurityManager
from .config import SecurityConfig, SecurityLevel
from .base import RiskLevel, PermissionLevel

__all__ = [
    "SecurityManager",
    "SecurityConfig",
    "SecurityLevel",
    "RiskLevel",
    "PermissionLevel",
]
