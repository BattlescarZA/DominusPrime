# -*- coding: utf-8 -*-
"""CLI commands for security management."""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import click

from ..security.profiles import SECURITY_PROFILES, SecurityLevel
from ..security.manager import SecurityManager
from ..security.config import SecurityConfig
from ..database.connection import DatabaseManager


@click.group()
def security():
    """Security system management commands."""
    pass


@security.command()
@click.option(
    "--config-file",
    type=click.Path(),
    default="./config/security.json",
    help="Path to security configuration",
)
def status(config_file: str):
    """Show security system status."""
    config_path = Path(config_file)
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        click.echo("\n🔒 Security System Status")
        click.echo("=" * 50)
        click.echo(f"  Profile: {config_data.get('security_level', 'BALANCED').upper()}")
        click.echo(f"  Shell Approval: {'Required' if config_data.get('shell_require_approval', True) else 'Auto-approve'}")
        click.echo(f"  Skill Scanning: {'Enabled' if config_data.get('skills_scan_on_load', True) else 'Disabled'}")
        click.echo(f"  Audit Logging: {'Enabled' if config_data.get('audit_logging_enabled', True) else 'Disabled'}")
        click.echo("=" * 50)
    else:
        click.echo(f"⚠️  No configuration found at {config_file}")
        click.echo("Using default BALANCED profile")


@security.command()
@click.argument(
    "profile",
    type=click.Choice(["open", "relaxed", "balanced", "strict", "paranoid"]),
)
@click.option(
    "--config-file",
    type=click.Path(),
    default="./config/security.json",
    help="Path to security configuration",
)
def set_profile(profile: str, config_file: str):
    """Set security profile."""
    config_path = Path(config_file)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get profile settings
    level = SecurityLevel[profile.upper()]
    profile_config = SECURITY_PROFILES[level]
    
    # Create config dict
    config_dict = {
        "security_level": profile.upper(),
        "shell_require_approval": profile_config.shell_require_approval,
        "shell_block_dangerous": profile_config.shell_block_dangerous,
        "tool_default_permission": profile_config.tool_default_permission.value,
        "skills_scan_on_load": profile_config.skills_scan_on_load,
        "skills_require_approval": profile_config.skills_require_approval,
        "audit_logging_enabled": profile_config.audit_logging_enabled,
        "rate_limit_enabled": profile_config.rate_limit_enabled,
        "max_commands_per_minute": profile_config.max_commands_per_minute,
    }
    
    # Save configuration
    with open(config_path, 'w') as f:
        json.dump(config_dict, f, indent=2)
    
    click.echo(f"✅ Security profile set to: {profile.upper()}")
    click.echo(f"\nProfile settings:")
    click.echo(f"  Shell approval: {'Required' if profile_config.shell_require_approval else 'Auto'}")
    click.echo(f"  Dangerous commands: {'Blocked' if profile_config.shell_block_dangerous else 'Allowed with warning'}")
    click.echo(f"  Skill scanning: {'Enabled' if profile_config.skills_scan_on_load else 'Disabled'}")
    click.echo(f"  Rate limiting: {'Enabled' if profile_config.rate_limit_enabled else 'Disabled'}")


@security.command()
@click.option(
    "--db-path",
    type=click.Path(),
    default="./data/security.db",
    help="Path to security database",
)
@click.option(
    "--limit",
    type=int,
    default=20,
    help="Number of executions to show",
)
@click.option(
    "--status",
    type=click.Choice(["all", "approved", "blocked", "failed"]),
    default="all",
    help="Filter by execution status",
)
def audit(db_path: str, limit: int, status: str):
    """Show command execution audit log."""
    db_path = Path(db_path)
    
    if not db_path.exists():
        click.echo(f"❌ Database not found: {db_path}")
        return
    
    async def get_audit_log():
        db_manager = DatabaseManager(db_path.parent)
        await db_manager.initialize()
        
        security_db = db_manager.get_connection("security")
        cursor = security_db.cursor()
        
        query = "SELECT * FROM command_executions"
        params = []
        
        if status == "approved":
            query += " WHERE approved = 1"
        elif status == "blocked":
            query += " WHERE approved = 0 AND executed = 0"
        elif status == "failed":
            query += " WHERE return_code != 0"
        
        query += " ORDER BY executed_at DESC LIMIT ?"
        params.append(limit)
        
        rows = cursor.execute(query, params).fetchall()
        
        entries = []
        for row in rows:
            entries.append({
                "command": row[1],
                "approved": row[2],
                "executed": row[3],
                "return_code": row[4],
                "risk_level": row[5],
                "executed_at": row[9],
            })
        
        return entries
    
    entries = asyncio.run(get_audit_log())
    
    if not entries:
        click.echo("No audit entries found.")
        return
    
    click.echo(f"\n📋 Command Execution Audit Log (showing {len(entries)})")
    click.echo("=" * 70)
    
    for entry in entries:
        # Status indicator
        if entry['approved'] and entry['executed']:
            status_icon = "✅"
            status_text = "EXECUTED"
        elif not entry['approved']:
            status_icon = "🚫"
            status_text = "BLOCKED"
        else:
            status_icon = "❌"
            status_text = "FAILED"
        
        click.echo(f"\n  {status_icon} {status_text}")
        click.echo(f"  Command: {entry['command'][:80]}")
        click.echo(f"  Risk: {entry['risk_level']} | Return Code: {entry['return_code']}")
        click.echo(f"  Time: {entry['executed_at']}")


@security.command()
@click.option(
    "--db-path",
    type=click.Path(),
    default="./data/security.db",
    help="Path to security database",
)
@click.option(
    "--days",
    type=int,
    default=7,
    help="Number of days to analyze",
)
def stats(db_path: str, days: int):
    """Show security statistics."""
    db_path = Path(db_path)
    
    if not db_path.exists():
        click.echo(f"❌ Database not found: {db_path}")
        return
    
    async def get_stats():
        db_manager = DatabaseManager(db_path.parent)
        await db_manager.initialize()
        
        security_db = db_manager.get_connection("security")
        cursor = security_db.cursor()
        
        # Time threshold
        threshold = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Total executions
        total = cursor.execute(
            "SELECT COUNT(*) FROM command_executions WHERE executed_at > ?",
            (threshold,)
        ).fetchone()[0]
        
        # Approved
        approved = cursor.execute(
            "SELECT COUNT(*) FROM command_executions WHERE executed_at > ? AND approved = 1",
            (threshold,)
        ).fetchone()[0]
        
        # Blocked
        blocked = cursor.execute(
            "SELECT COUNT(*) FROM command_executions WHERE executed_at > ? AND approved = 0",
            (threshold,)
        ).fetchone()[0]
        
        # By risk level
        risk_counts = {}
        for risk_level in ["SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            count = cursor.execute(
                "SELECT COUNT(*) FROM command_executions WHERE executed_at > ? AND risk_level = ?",
                (threshold, risk_level)
            ).fetchone()[0]
            risk_counts[risk_level] = count
        
        # Security events
        events = cursor.execute(
            "SELECT COUNT(*) FROM security_events WHERE created_at > ?",
            (threshold,)
        ).fetchone()[0]
        
        return {
            "total": total,
            "approved": approved,
            "blocked": blocked,
            "risk_counts": risk_counts,
            "events": events,
        }
    
    stats_data = asyncio.run(get_stats())
    
    click.echo(f"\n📊 Security Statistics (Last {days} days)")
    click.echo("=" * 50)
    click.echo(f"  Total Commands:     {stats_data['total']:>6}")
    click.echo(f"  Approved:           {stats_data['approved']:>6}")
    click.echo(f"  Blocked:            {stats_data['blocked']:>6}")
    click.echo(f"  Security Events:    {stats_data['events']:>6}")
    click.echo("\n  Risk Distribution:")
    for level, count in stats_data['risk_counts'].items():
        if count > 0:
            click.echo(f"    {level:>10}: {count:>6}")
    click.echo("=" * 50)


@security.command()
@click.option(
    "--db-path",
    type=click.Path(),
    default="./data/security.db",
    help="Path to security database",
)
def list_events(db_path: str):
    """List recent security events."""
    db_path = Path(db_path)
    
    if not db_path.exists():
        click.echo(f"❌ Database not found: {db_path}")
        return
    
    async def get_events():
        db_manager = DatabaseManager(db_path.parent)
        await db_manager.initialize()
        
        security_db = db_manager.get_connection("security")
        cursor = security_db.cursor()
        
        rows = cursor.execute(
            """
            SELECT event_type, severity, description, created_at
            FROM security_events
            ORDER BY created_at DESC
            LIMIT 20
            """
        ).fetchall()
        
        events = []
        for row in rows:
            events.append({
                "type": row[0],
                "severity": row[1],
                "description": row[2],
                "created_at": row[3],
            })
        
        return events
    
    events = asyncio.run(get_events())
    
    if not events:
        click.echo("No security events found.")
        return
    
    click.echo(f"\n🚨 Recent Security Events (showing {len(events)})")
    click.echo("=" * 70)
    
    for event in events:
        # Severity icon
        severity_icons = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🔴",
        }
        icon = severity_icons.get(event['severity'].lower(), "•")
        
        click.echo(f"\n  {icon} {event['type'].upper()} [{event['severity']}]")
        click.echo(f"  {event['description'][:80]}")
        click.echo(f"  Time: {event['created_at']}")


@security.command()
@click.confirmation_option(prompt="Clear all security logs?")
@click.option(
    "--db-path",
    type=click.Path(),
    default="./data/security.db",
    help="Path to security database",
)
def clear_logs(db_path: str):
    """Clear security audit logs."""
    db_path = Path(db_path)
    
    if not db_path.exists():
        click.echo(f"❌ Database not found: {db_path}")
        return
    
    async def clear():
        db_manager = DatabaseManager(db_path.parent)
        await db_manager.initialize()
        
        security_db = db_manager.get_connection("security")
        cursor = security_db.cursor()
        
        cursor.execute("DELETE FROM command_executions")
        cursor.execute("DELETE FROM security_events")
        
        security_db.commit()
        
        click.echo("✅ Security logs cleared.")
    
    asyncio.run(clear())


if __name__ == "__main__":
    security()
