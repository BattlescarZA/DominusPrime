# -*- coding: utf-8 -*-
"""Secure shell command execution with risk analysis and approval."""

import asyncio
from pathlib import Path
from typing import Optional, Tuple

from ...security.manager import SecurityManager
from ...security.models import ExecutionContext, InterceptAction
from .shell import execute_shell_command


async def execute_shell_command_secure(
    command: str,
    timeout: int = 300,
    working_dir: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    **kwargs,
) -> Tuple[int, str, str]:
    """Execute shell command with security checks.
    
    This is a secure wrapper around execute_shell_command that:
    1. Analyzes command risk
    2. Blocks/approves based on security policy
    3. Logs execution
    4. Returns execution results
    
    Args:
        command: Shell command to execute
        timeout: Command timeout in seconds
        working_dir: Working directory for command
        session_id: Current session ID
        user_id: Current user ID
        **kwargs: Additional arguments passed to execute_shell_command
        
    Returns:
        Tuple of (return_code, stdout, stderr)
        
    Raises:
        PermissionError: If command is blocked by security policy
        TimeoutError: If approval times out
    """
    try:
        # Get security manager
        security = SecurityManager.get_instance()
        
        # Create execution context
        context = ExecutionContext(
            command=command,
            working_dir=working_dir,
            session_id=session_id,
            user_id=user_id,
            environment=dict(kwargs.get("env", {})),
            metadata={
                "timeout": timeout,
                "tool": "execute_shell_command",
            }
        )
        
        # Intercept and analyze
        result = await security.intercept_shell_command(command, context)
        
        # Handle interception result
        if result.action == InterceptAction.BLOCKED:
            # Command blocked - log and raise error
            await security.log_execution(
                command=command,
                context=context,
                approved=False,
                executed=False,
                return_code=-1,
                stdout="",
                stderr=f"BLOCKED: {result.message}",
            )
            raise PermissionError(
                f"Command blocked by security policy: {result.message}\n"
                f"Risk Level: {result.risk_assessment.level.value.upper()}\n"
                f"Reason: {result.risk_assessment.reason}"
            )
        
        elif result.action == InterceptAction.REQUIRE_APPROVAL:
            # Request user approval
            approved = await security.request_approval(
                command=command,
                risk_assessment=result.risk_assessment,
                timeout=120,  # 2 minute timeout for approval
            )
            
            if not approved:
                # User rejected or timeout
                await security.log_execution(
                    command=command,
                    context=context,
                    approved=False,
                    executed=False,
                    return_code=-1,
                    stdout="",
                    stderr="User rejected command execution",
                )
                raise PermissionError(
                    f"Command execution rejected by user or timed out.\n"
                    f"Command: {command}"
                )
        
        # Execute command (approved or auto-allowed)
        return_code, stdout, stderr = await execute_shell_command(
            command=command,
            timeout=timeout,
            working_dir=working_dir,
            **kwargs
        )
        
        # Log successful execution
        await security.log_execution(
            command=command,
            context=context,
            approved=True,
            executed=True,
            return_code=return_code,
            stdout=stdout[:1000],  # Limit log size
            stderr=stderr[:1000],
        )
        
        return return_code, stdout, stderr
    
    except Exception as e:
        # Log failed execution
        try:
            security = SecurityManager.get_instance()
            context = ExecutionContext(
                command=command,
                working_dir=working_dir,
                session_id=session_id,
                user_id=user_id,
            )
            await security.log_execution(
                command=command,
                context=context,
                approved=False,
                executed=False,
                return_code=-1,
                stdout="",
                stderr=str(e),
            )
        except:
            pass  # Don't fail on logging errors
        
        raise


async def execute_shell_command_with_fallback(
    command: str,
    timeout: int = 300,
    working_dir: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    use_security: bool = True,
    **kwargs,
) -> Tuple[int, str, str]:
    """Execute shell command with optional security (fallback mode).
    
    If security manager is not initialized, falls back to direct execution.
    
    Args:
        command: Shell command to execute
        timeout: Command timeout in seconds
        working_dir: Working directory
        session_id: Current session ID
        user_id: Current user ID
        use_security: Whether to use security checks (default: True)
        **kwargs: Additional arguments
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    if use_security:
        try:
            # Try secure execution
            return await execute_shell_command_secure(
                command=command,
                timeout=timeout,
                working_dir=working_dir,
                session_id=session_id,
                user_id=user_id,
                **kwargs
            )
        except RuntimeError as e:
            if "not initialized" in str(e):
                # Security not initialized, fall back to direct execution
                pass
            else:
                raise
    
    # Direct execution (no security)
    return await execute_shell_command(
        command=command,
        timeout=timeout,
        working_dir=working_dir,
        **kwargs
    )
