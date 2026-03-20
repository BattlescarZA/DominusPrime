#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DominusPrime Windows Launcher
Starts the DominusPrime server and opens browser automatically
"""
from __future__ import annotations

import os
import sys
import time
import webbrowser
import subprocess
import threading
from pathlib import Path


def check_port_available(port: int) -> bool:
    """Check if a port is available."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False


def wait_for_server(host: str, port: int, timeout: int = 30) -> bool:
    """Wait for the server to be ready."""
    import socket
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect((host, port))
                return True
        except (socket.error, ConnectionRefusedError):
            time.sleep(0.5)
    return False


def open_browser_delayed(url: str, delay: float = 2.0) -> None:
    """Open browser after a delay."""
    time.sleep(delay)
    try:
        webbrowser.open(url)
        print(f"Browser opened at {url}")
    except Exception as e:
        print(f"Could not open browser automatically: {e}")
        print(f"Please open your browser and navigate to: {url}")


def main() -> None:
    """Main launcher function."""
    host = "127.0.0.1"
    port = 9999
    
    # Check if server is already running
    if not check_port_available(port):
        print(f"DominusPrime server appears to be already running on {host}:{port}")
        url = f"http://{host}:{port}"
        print(f"Opening browser at {url}")
        webbrowser.open(url)
        input("\nPress Enter to exit...")
        return
    
    print("=" * 60)
    print("DominusPrime - Starting...")
    print("=" * 60)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print("=" * 60)
    
    # Start browser opener thread
    url = f"http://{host}:{port}"
    browser_thread = threading.Thread(
        target=open_browser_delayed,
        args=(url, 3.0),
        daemon=True
    )
    browser_thread.start()
    
    # Start the DominusPrime server
    try:
        # Import and run the CLI
        from dominusprime.cli.main import cli
        
        # Run with app command
        sys.argv = ["dominusprime", "app", "--host", host, "--port", str(port)]
        cli()
    except KeyboardInterrupt:
        print("\n\nShutting down DominusPrime...")
    except Exception as e:
        print(f"\nError starting DominusPrime: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
