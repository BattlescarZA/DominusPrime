# -*- coding: utf-8 -*-
"""CLI commands for WhatsApp management."""

import subprocess
import sys
from pathlib import Path
from typing import Optional

import click


def get_bridge_path() -> Path:
    """Get the path to the WhatsApp bridge script."""
    # Assuming we're in src/dominusprime/cli, go up to project root
    project_root = Path(__file__).resolve().parents[3]
    bridge_path = project_root / "scripts" / "whatsapp-bridge" / "bridge.js"
    return bridge_path


def get_default_session_path() -> Path:
    """Get the default session path."""
    return Path.home() / ".dominusprime" / "whatsapp" / "session"


@click.group("whatsapp")
def whatsapp_group():
    """WhatsApp integration commands."""
    pass


@whatsapp_group.command("pair")
@click.option(
    "--session",
    default=None,
    help="Session directory path (default: ~/.dominusprime/whatsapp/session)",
)
def pair_command(session: Optional[str]):
    """
    Pair WhatsApp account via QR code.
    
    This command starts the bridge in pairing mode, displays a QR code,
    and saves the session after successful pairing.
    
    Scan the QR code with WhatsApp mobile app:
    Settings → Linked Devices → Link a Device
    """
    bridge_path = get_bridge_path()
    if not bridge_path.exists():
        click.echo(f"❌ Bridge script not found: {bridge_path}", err=True)
        click.echo("Make sure DominusPrime is properly installed.", err=True)
        sys.exit(1)
    
    session_path = Path(session) if session else get_default_session_path()
    session_path.mkdir(parents=True, exist_ok=True)
    
    click.echo("📱 Starting WhatsApp pairing...")
    click.echo(f"📁 Session: {session_path}")
    click.echo()
    
    # Check if Node.js is available
    try:
        subprocess.run(
            ["node", "--version"],
            capture_output=True,
            check=True,
            timeout=5
        )
    except Exception:
        click.echo("❌ Node.js not found. Install Node.js to use WhatsApp.", err=True)
        click.echo("   Download: https://nodejs.org/", err=True)
        sys.exit(1)
    
    # Install dependencies if needed
    bridge_dir = bridge_path.parent
    if not (bridge_dir / "node_modules").exists():
        click.echo("📦 Installing bridge dependencies...")
        try:
            result = subprocess.run(
                ["npm", "install"],
                cwd=str(bridge_dir),
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                click.echo(f"❌ npm install failed: {result.stderr}", err=True)
                sys.exit(1)
            click.echo("✅ Dependencies installed")
        except Exception as e:
            click.echo(f"❌ Failed to install dependencies: {e}", err=True)
            sys.exit(1)
    
    # Run bridge in pair-only mode
    try:
        subprocess.run(
            [
                "node",
                str(bridge_path),
                "--pair-only",
                "--session",
                str(session_path),
            ],
            check=False,  # Don't raise on exit code 0
        )
    except KeyboardInterrupt:
        click.echo("\n⚠️  Pairing cancelled")
        sys.exit(1)


@whatsapp_group.command("status")
@click.option(
    "--port",
    default=3000,
    help="Bridge port (default: 3000)",
)
def status_command(port: int):
    """
    Check WhatsApp bridge status.
    
    Queries the bridge health endpoint to check connection status.
    """
    import urllib.request
    import urllib.error
    import json
    
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as response:
            data = json.loads(response.read().decode())
            status = data.get("status", "unknown")
            queue_length = data.get("queueLength", 0)
            uptime = data.get("uptime", 0)
            
            if status == "connected":
                click.echo(f"✅ WhatsApp bridge is connected")
            elif status == "disconnected":
                click.echo(f"⚠️  WhatsApp bridge is disconnected")
            else:
                click.echo(f"❓ WhatsApp bridge status: {status}")
            
            click.echo(f"📊 Queue length: {queue_length}")
            click.echo(f"⏱️  Uptime: {uptime:.1f}s")
    except urllib.error.URLError:
        click.echo(f"❌ Bridge is not running on port {port}", err=True)
        click.echo(f"   Start it with: dominusprime run", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error checking status: {e}", err=True)
        sys.exit(1)


@whatsapp_group.command("start")
@click.option(
    "--port",
    default=3000,
    help="Bridge port (default: 3000)",
)
@click.option(
    "--session",
    default=None,
    help="Session directory path (default: ~/.dominusprime/whatsapp/session)",
)
@click.option(
    "--mode",
    type=click.Choice(["self-chat", "bot"]),
    default="self-chat",
    help="WhatsApp mode: self-chat (default) or bot",
)
def start_command(port: int, session: Optional[str], mode: str):
    """
    Start WhatsApp bridge manually.
    
    Normally the bridge is started automatically by DominusPrime,
    but this command allows manual testing.
    """
    bridge_path = get_bridge_path()
    if not bridge_path.exists():
        click.echo(f"❌ Bridge script not found: {bridge_path}", err=True)
        sys.exit(1)
    
    session_path = Path(session) if session else get_default_session_path()
    
    click.echo(f"🌉 Starting WhatsApp bridge on port {port}")
    click.echo(f"📁 Session: {session_path}")
    click.echo(f"🔧 Mode: {mode}")
    click.echo()
    click.echo("Press Ctrl+C to stop")
    click.echo()
    
    try:
        subprocess.run(
            [
                "node",
                str(bridge_path),
                "--port",
                str(port),
                "--session",
                str(session_path),
                "--mode",
                mode,
            ],
            check=False,
        )
    except KeyboardInterrupt:
        click.echo("\n⚠️  Bridge stopped")


@whatsapp_group.command("reset")
@click.option(
    "--session",
    default=None,
    help="Session directory path (default: ~/.dominusprime/whatsapp/session)",
)
@click.confirmation_option(
    prompt="Are you sure you want to reset the WhatsApp session? You'll need to re-pair."
)
def reset_command(session: Optional[str]):
    """
    Reset WhatsApp session (deletes saved credentials).
    
    Use this if you want to pair a different WhatsApp account
    or if the session is corrupted.
    """
    import shutil
    
    session_path = Path(session) if session else get_default_session_path()
    
    if not session_path.exists():
        click.echo(f"ℹ️  Session directory doesn't exist: {session_path}")
        return
    
    try:
        shutil.rmtree(session_path)
        click.echo(f"✅ Session reset: {session_path}")
        click.echo(f"   Re-pair with: dominusprime whatsapp pair")
    except Exception as e:
        click.echo(f"❌ Failed to reset session: {e}", err=True)
        sys.exit(1)
