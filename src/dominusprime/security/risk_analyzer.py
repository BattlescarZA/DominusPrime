# -*- coding: utf-8 -*-
"""Risk analyzer for shell commands."""

import logging
import re
from typing import Optional, List

from .base import RiskLevel, RiskAssessment, ExecutionContext
from .config import ShellSecurityConfig

logger = logging.getLogger(__name__)


class RiskAnalyzer:
    """Analyzes shell commands to determine risk level."""

    # High-risk command patterns
    HIGH_RISK_PATTERNS = [
        r"rm\s+-rf",                    # Recursive force delete
        r"dd\s+.*of=/dev/",            # Disk operations
        r"mkfs",                        # Format filesystem
        r"sudo\s+",                     # Privileged execution
        r"chmod\s+.*777",               # Dangerous permissions
        r">\s*/dev/sd[a-z]",           # Direct disk write
        r"curl.*\|.*sh",                # Pipe to shell
        r"wget.*\|.*bash",              # Pipe to shell
    ]

    # Critical system paths
    CRITICAL_PATHS = [
        "/",
        "/etc",
        "/bin",
        "/sbin",
        "/usr",
        "/System",
        "/boot",
        "C:\\Windows",
        "C:\\Program Files",
        "C:\\System32",
    ]

    # Safe read-only commands
    SAFE_COMMANDS = [
        "ls", "pwd", "echo", "cat", "grep", "find",
        "git status", "git log", "git diff",
        "docker ps", "docker images",
        "which", "whereis", "whoami",
        "date", "uptime", "hostname",
        "pip list", "npm list",
    ]

    def __init__(self, config: ShellSecurityConfig):
        """Initialize risk analyzer.

        Args:
            config: Shell security configuration
        """
        self.config = config

    async def analyze_risk(
        self,
        command: str,
        context: ExecutionContext
    ) -> RiskAssessment:
        """Analyze command risk based on patterns and context.

        Args:
            command: Shell command to analyze
            context: Execution context

        Returns:
            RiskAssessment with level and details
        """
        logger.debug(f"Analyzing risk for command: {command[:100]}")

        reasons = []
        detected_patterns = []
        affected_paths = []
        score = 0.0

        # Check if command is explicitly blocked
        if self._is_blocked(command):
            return RiskAssessment(
                level=RiskLevel.CRITICAL,
                score=1.0,
                reasons=["Command is explicitly blocked by security policy"],
                affected_paths=[],
                detected_patterns=["blocked_command"]
            )

        # Check if command is safe read-only
        if self.is_read_only(command):
            return RiskAssessment(
                level=RiskLevel.SAFE,
                score=0.0,
                reasons=["Read-only command"],
                affected_paths=[],
                detected_patterns=[]
            )

        # Check for high-risk patterns
        for pattern in self.HIGH_RISK_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                detected_patterns.append(pattern)
                reasons.append(f"Dangerous pattern detected: {pattern}")
                score += 0.5

        # Check for critical path operations
        critical_path = self.affects_critical_path(command)
        if critical_path:
            affected_paths.append(critical_path)
            reasons.append(f"Affects critical system path: {critical_path}")
            score += 0.4

        # Check for deletion operations
        if self._is_deletion_command(command):
            reasons.append("Command performs deletion")
            score += 0.3

        # Check for network operations
        if self._has_network_activity(command):
            reasons.append("Command involves network activity")
            score += 0.2

        # Check working directory risk
        if self._is_sensitive_directory(context.working_dir):
            reasons.append(f"Executing in sensitive directory: {context.working_dir}")
            score += 0.2

        # Determine risk level based on score
        if score >= 0.8:
            level = RiskLevel.CRITICAL
        elif score >= 0.6:
            level = RiskLevel.HIGH
        elif score >= 0.4:
            level = RiskLevel.MEDIUM
        elif score >= 0.2:
            level = RiskLevel.LOW
        else:
            level = RiskLevel.SAFE

        assessment = RiskAssessment(
            level=level,
            score=min(score, 1.0),
            reasons=reasons if reasons else ["No significant risks detected"],
            affected_paths=affected_paths,
            detected_patterns=detected_patterns
        )

        logger.info(
            f"Risk analysis: {level.value} (score: {assessment.score:.2f}) "
            f"- {len(reasons)} concerns"
        )

        return assessment

    def is_read_only(self, command: str) -> bool:
        """Check if command is read-only (safe).

        Args:
            command: Command to check

        Returns:
            True if command is read-only
        """
        cmd_lower = command.lower().strip()

        # Check against safe commands list
        for safe_cmd in self.SAFE_COMMANDS:
            if cmd_lower.startswith(safe_cmd):
                return True

        # Check for common read patterns
        read_patterns = [
            r"^cat\s+",
            r"^head\s+",
            r"^tail\s+",
            r"^less\s+",
            r"^more\s+",
            r"^grep\s+",
            r"^find\s+.*-type\s+f",
        ]

        for pattern in read_patterns:
            if re.match(pattern, cmd_lower):
                return True

        return False

    def affects_critical_path(self, command: str) -> Optional[str]:
        """Check if command affects critical system paths.

        Args:
            command: Command to check

        Returns:
            Critical path if affected, None otherwise
        """
        for path in self.CRITICAL_PATHS:
            # Check for exact path or path prefix
            if path in command:
                # Make sure it's not just part of a longer path
                if re.search(rf"\b{re.escape(path)}\b", command):
                    return path

        return None

    def _is_blocked(self, command: str) -> bool:
        """Check if command is explicitly blocked.

        Args:
            command: Command to check

        Returns:
            True if blocked
        """
        for blocked in self.config.blocked_commands:
            if blocked in command:
                return True
        return False

    def _is_deletion_command(self, command: str) -> bool:
        """Check if command performs deletion.

        Args:
            command: Command to check

        Returns:
            True if command deletes files
        """
        deletion_patterns = [
            r"\brm\s+",
            r"\bdel\s+",
            r"\bunlink\s+",
            r"\brmdir\s+",
        ]

        for pattern in deletion_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True

        return False

    def _has_network_activity(self, command: str) -> bool:
        """Check if command involves network activity.

        Args:
            command: Command to check

        Returns:
            True if network activity detected
        """
        network_commands = [
            "curl", "wget", "nc", "telnet", "ssh",
            "scp", "ftp", "sftp", "ping", "nslookup"
        ]

        cmd_lower = command.lower()
        for net_cmd in network_commands:
            if net_cmd in cmd_lower:
                return True

        return False

    def _is_sensitive_directory(self, directory: str) -> bool:
        """Check if directory is sensitive.

        Args:
            directory: Directory path

        Returns:
            True if directory is sensitive
        """
        sensitive_dirs = [
            "/etc", "/root", "/boot", "/sys", "/proc",
            "C:\\Windows", "C:\\System32",
        ]

        for sens_dir in sensitive_dirs:
            if directory.startswith(sens_dir):
                return True

        return False
