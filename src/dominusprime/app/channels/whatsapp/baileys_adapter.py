# -*- coding: utf-8 -*-
"""
WhatsApp Baileys adapter using HTTP bridge pattern.

This is a simpler, more reliable alternative to the WebSocket-based whatsapp-web.js approach.
Uses the Baileys library (maintained, actively developed) via a Node.js bridge process.

Architecture:
1. Node.js bridge (scripts/whatsapp-bridge/bridge.js) connects to WhatsApp via Baileys
2. Python adapter communicates with bridge via HTTP endpoints
3. Messages are polled via long-polling from /messages endpoint

Benefits over whatsapp-web.js:
- Baileys is actively maintained (whatsapp-web.js is deprecated)
- Native message editing support
- Better media handling
- More reliable connection management
- Simpler authentication flow
"""

import asyncio
import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import Dict, Optional, Any, List

from .....config.config import WhatsAppConfig
from ..base import BaseChannel, ProcessHandler, OnReplySent
from ..schema import MessageEvent, MessageType, SendResult

logger = logging.getLogger(__name__)

_IS_WINDOWS = platform.system() == "Windows"


def _kill_port_process(port: int) -> None:
    """Kill any process listening on the given TCP port."""
    try:
        if _IS_WINDOWS:
            result = subprocess.run(
                ["netstat", "-ano", "-p", "TCP"],
                capture_output=True, text=True, timeout=5,
            )
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 5 and parts[3] == "LISTENING":
                    local_addr = parts[1]
                    if local_addr.endswith(f":{port}"):
                        try:
                            subprocess.run(
                                ["taskkill", "/PID", parts[4], "/F"],
                                capture_output=True, timeout=5,
                            )
                        except subprocess.SubprocessError:
                            pass
        else:
            result = subprocess.run(
                ["fuser", f"{port}/tcp"],
                capture_output=True, timeout=5,
            )
            if result.returncode == 0:
                subprocess.run(
                    ["fuser", "-k", f"{port}/tcp"],
                    capture_output=True, timeout=5,
                )
    except Exception:
        pass


def check_whatsapp_requirements() -> bool:
    """Check if WhatsApp dependencies (Node.js) are available."""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


class WhatsAppBaileysAdapter(BaseChannel):
    """
    WhatsApp adapter using Baileys library via HTTP bridge.
    
    Configuration:
    - bridge_port: Port for HTTP communication (default: 3000)
    - session_path: Path to store WhatsApp session data
    - bridge_script: Path to the Node.js bridge script (auto-detected)
    - reply_prefix: Optional prefix for bot replies in self-chat mode
    """
    
    channel = "whatsapp"
    uses_manager_queue = True
    
    # Default bridge location
    _DEFAULT_BRIDGE_DIR = Path(__file__).resolve().parents[4] / "scripts" / "whatsapp-bridge"
    
    def __init__(
        self,
        process: ProcessHandler,
        enabled: bool,
        bridge_port: int = 3000,
        session_path: Optional[str] = None,
        bridge_script: Optional[str] = None,
        reply_prefix: Optional[str] = None,
        on_reply_sent: OnReplySent = None,
        show_tool_details: bool = True,
        filter_tool_messages: bool = False,
        filter_thinking: bool = False,
    ):
        super().__init__(
            process,
            on_reply_sent,
            show_tool_details,
            filter_tool_messages,
            filter_thinking,
        )
        self._enabled = enabled
        self._bridge_port = bridge_port
        self._bridge_script = bridge_script or str(self._DEFAULT_BRIDGE_DIR / "bridge.js")
        self._session_path = Path(session_path or Path.home() / ".dominusprime" / "whatsapp" / "session")
        self._reply_prefix = reply_prefix
        
        # Runtime state
        self._bridge_process: Optional[subprocess.Popen] = None
        self._http_session: Optional[Any] = None  # aiohttp.ClientSession
        self._poll_task: Optional[asyncio.Task] = None
        self._running = False
        self._bridge_log_fh = None
        self._bridge_log: Optional[Path] = None

    @classmethod
    def from_config(
        cls,
        process: ProcessHandler,
        config: WhatsAppConfig,
        on_reply_sent: OnReplySent = None,
        show_tool_details: bool = True,
        filter_tool_messages: bool = False,
        filter_thinking: bool = False,
    ) -> "WhatsAppBaileysAdapter":
        """Create adapter from config."""
        return cls(
            process=process,
            enabled=config.enabled,
            bridge_port=config.extra.get("bridge_port", 3000),
            session_path=config.extra.get("session_path"),
            bridge_script=config.extra.get("bridge_script"),
            reply_prefix=config.extra.get("reply_prefix"),
            on_reply_sent=on_reply_sent,
            show_tool_details=show_tool_details,
            filter_tool_messages=filter_tool_messages,
            filter_thinking=filter_thinking,
        )

    async def start(self) -> None:
        """Start the WhatsApp Baileys bridge and connect."""
        if not self._enabled:
            logger.info("[WhatsApp] Disabled in config")
            return
        
        if not check_whatsapp_requirements():
            logger.error("[WhatsApp] Node.js not found. Install Node.js to use WhatsApp.")
            return
        
        bridge_path = Path(self._bridge_script)
        if not bridge_path.exists():
            logger.error("[WhatsApp] Bridge script not found: %s", bridge_path)
            return
        
        logger.info("[WhatsApp] Starting Baileys bridge at %s", bridge_path)
        
        # Auto-install npm dependencies if needed
        bridge_dir = bridge_path.parent
        if not (bridge_dir / "node_modules").exists():
            logger.info("[WhatsApp] Installing bridge dependencies...")
            try:
                result = subprocess.run(
                    ["npm", "install", "--silent"],
                    cwd=str(bridge_dir),
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if result.returncode != 0:
                    logger.error("[WhatsApp] npm install failed: %s", result.stderr)
                    return
                logger.info("[WhatsApp] Dependencies installed")
            except Exception as e:
                logger.error("[WhatsApp] Failed to install dependencies: %s", e)
                return
        
        try:
            # Ensure session directory exists
            self._session_path.mkdir(parents=True, exist_ok=True)
            
            # Check if bridge is already running
            import aiohttp
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"http://127.0.0.1:{self._bridge_port}/health",
                        timeout=aiohttp.ClientTimeout(total=2)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get("status") == "connected":
                                logger.info("[WhatsApp] Using existing bridge (status: connected)")
                                self._bridge_process = None  # Not managed by us
                                self._http_session = aiohttp.ClientSession()
                                self._running = True
                                self._poll_task = asyncio.create_task(self._poll_messages())
                                return
                            else:
                                logger.info("[WhatsApp] Bridge found but not connected, restarting")
            except Exception:
                pass  # Bridge not running, start new one
            
            # Kill any orphaned bridge
            _kill_port_process(self._bridge_port)
            await asyncio.sleep(1)
            
            # Start bridge process
            whatsapp_mode = os.getenv("WHATSAPP_MODE", "self-chat")
            self._bridge_log = self._session_path.parent / "bridge.log"
            self._bridge_log_fh = open(self._bridge_log, "a")
            
            # Build environment with reply prefix
            bridge_env = os.environ.copy()
            if self._reply_prefix is not None:
                bridge_env["WHATSAPP_REPLY_PREFIX"] = self._reply_prefix
            
            self._bridge_process = subprocess.Popen(
                [
                    "node",
                    str(bridge_path),
                    "--port", str(self._bridge_port),
                    "--session", str(self._session_path),
                    "--mode", whatsapp_mode,
                ],
                stdout=self._bridge_log_fh,
                stderr=self._bridge_log_fh,
                preexec_fn=None if _IS_WINDOWS else os.setsid,
                env=bridge_env,
            )
            
            # Wait for bridge to be ready (Phase 1: HTTP up, Phase 2: WhatsApp connected)
            import aiohttp
            http_ready = False
            data = {}
            
            for attempt in range(15):
                await asyncio.sleep(1)
                if self._bridge_process.poll() is not None:
                    logger.error("[WhatsApp] Bridge process died (exit code %s)", self._bridge_process.returncode)
                    logger.error("[WhatsApp] Check log: %s", self._bridge_log)
                    self._close_bridge_log()
                    return
                
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"http://127.0.0.1:{self._bridge_port}/health",
                            timeout=aiohttp.ClientTimeout(total=2)
                        ) as resp:
                            if resp.status == 200:
                                http_ready = True
                                data = await resp.json()
                                if data.get("status") == "connected":
                                    logger.info("[WhatsApp] Bridge ready (status: connected)")
                                    break
                except Exception:
                    continue
            
            if not http_ready:
                logger.error("[WhatsApp] Bridge HTTP server did not start in 15s")
                logger.error("[WhatsApp] Check log: %s", self._bridge_log)
                self._close_bridge_log()
                return
            
            # Phase 2: Wait for WhatsApp connection
            if data.get("status") != "connected":
                logger.info("[WhatsApp] Bridge HTTP ready, waiting for WhatsApp connection...")
                for attempt in range(15):
                    await asyncio.sleep(1)
                    if self._bridge_process.poll() is not None:
                        logger.error("[WhatsApp] Bridge died during connection")
                        logger.error("[WhatsApp] Check log: %s", self._bridge_log)
                        self._close_bridge_log()
                        return
                    
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(
                                f"http://127.0.0.1:{self._bridge_port}/health",
                                timeout=aiohttp.ClientTimeout(total=2)
                            ) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    if data.get("status") == "connected":
                                        logger.info("[WhatsApp] Bridge ready (status: connected)")
                                        break
                    except Exception:
                        continue
                else:
                    logger.warning("[WhatsApp] WhatsApp not connected after 30s")
                    logger.warning("[WhatsApp] Bridge log: %s", self._bridge_log)
                    logger.warning("[WhatsApp] If session expired, re-pair with QR code")
            
            # Create persistent HTTP session
            self._http_session = aiohttp.ClientSession()
            self._running = True
            
            # Start message polling
            self._poll_task = asyncio.create_task(self._poll_messages())
            
            logger.info("[WhatsApp] Bridge started on port %s", self._bridge_port)
            
        except Exception as e:
            logger.error("[WhatsApp] Failed to start bridge: %s", e, exc_info=True)
            self._close_bridge_log()

    async def stop(self) -> None:
        """Stop the WhatsApp bridge and clean up."""
        self._running = False
        
        # Cancel poll task
        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        
        # Close HTTP session
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()
        
        # Stop bridge process if we started it
        if self._bridge_process:
            try:
                import signal
                try:
                    if _IS_WINDOWS:
                        self._bridge_process.terminate()
                    else:
                        os.killpg(os.getpgid(self._bridge_process.pid), signal.SIGTERM)
                except (ProcessLookupError, PermissionError):
                    self._bridge_process.terminate()
                
                await asyncio.sleep(1)
                if self._bridge_process.poll() is None:
                    try:
                        if _IS_WINDOWS:
                            self._bridge_process.kill()
                        else:
                            os.killpg(os.getpgid(self._bridge_process.pid), signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        self._bridge_process.kill()
            except Exception as e:
                logger.error("[WhatsApp] Error stopping bridge: %s", e)
        
        self._close_bridge_log()
        logger.info("[WhatsApp] Disconnected")

    def _close_bridge_log(self) -> None:
        """Close the bridge log file handle."""
        if self._bridge_log_fh:
            try:
                self._bridge_log_fh.close()
            except Exception:
                pass
            self._bridge_log_fh = None

    async def _check_bridge_exit(self) -> Optional[str]:
        """Check if bridge process exited unexpectedly."""
        if self._bridge_process is None:
            return None
        
        returncode = self._bridge_process.poll()
        if returncode is None:
            return None
        
        return f"WhatsApp bridge process exited unexpectedly (code {returncode})"

    async def _poll_messages(self) -> None:
        """Poll the bridge for incoming messages via long-polling."""
        import aiohttp
        
        while self._running:
            if not self._http_session:
                break
            
            # Check if bridge died
            exit_msg = await self._check_bridge_exit()
            if exit_msg:
                logger.error("[WhatsApp] %s", exit_msg)
                break
            
            try:
                async with self._http_session.get(
                    f"http://127.0.0.1:{self._bridge_port}/messages",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        messages = await resp.json()
                        for msg_data in messages:
                            event = await self._build_message_event(msg_data)
                            if event:
                                # Forward to channel's message handler
                                await self._handle_incoming_message(event)
            except asyncio.CancelledError:
                break
            except Exception as e:
                exit_msg = await self._check_bridge_exit()
                if exit_msg:
                    logger.error("[WhatsApp] %s", exit_msg)
                    break
                logger.debug("[WhatsApp] Poll error: %s", e)
                await asyncio.sleep(5)
            
            await asyncio.sleep(1)  # Poll interval

    async def _build_message_event(self, data: Dict[str, Any]) -> Optional[MessageEvent]:
        """Build a MessageEvent from bridge message data."""
        try:
            # Determine message type
            msg_type = MessageType.TEXT
            if data.get("hasMedia"):
                media_type = data.get("mediaType", "")
                if "image" in media_type:
                    msg_type = MessageType.PHOTO
                elif "video" in media_type:
                    msg_type = MessageType.VIDEO
                elif "audio" in media_type or "ptt" in media_type:
                    msg_type = MessageType.VOICE
                else:
                    msg_type = MessageType.DOCUMENT
            
            # Build message event (adapt to DominusPrime's structure)
            # TODO: Adapt to DominusPrime's actual MessageEvent structure
            return {
                "type": msg_type,
                "chat_id": data.get("chatId"),
                "sender_id": data.get("senderId"),
                "sender_name": data.get("senderName"),
                "text": data.get("body", ""),
                "message_id": data.get("messageId"),
                "media_urls": data.get("mediaUrls", []),
                "timestamp": data.get("timestamp"),
                "is_group": data.get("isGroup", False),
            }
        except Exception as e:
            logger.error("[WhatsApp] Error building event: %s", e)
            return None

    async def _handle_incoming_message(self, event: Dict[str, Any]) -> None:
        """Handle an incoming message event."""
        # TODO: Implement proper message handling with DominusPrime's process handler
        logger.info("[WhatsApp] Message from %s: %s", event.get("sender_name"), event.get("text"))

    async def send_message(
        self,
        chat_id: str,
        message: str,
        reply_to: Optional[str] = None,
    ) -> SendResult:
        """Send a text message via the bridge."""
        if not self._running or not self._http_session:
            return SendResult(success=False, error="Not connected")
        
        try:
            import aiohttp
            payload = {"chatId": chat_id, "message": message}
            if reply_to:
                payload["replyTo"] = reply_to
            
            async with self._http_session.post(
                f"http://127.0.0.1:{self._bridge_port}/send",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return SendResult(success=True, message_id=data.get("messageId"))
                else:
                    error = await resp.text()
                    return SendResult(success=False, error=error)
        except Exception as e:
            return SendResult(success=False, error=str(e))

    async def edit_message(
        self,
        chat_id: str,
        message_id: str,
        new_message: str,
    ) -> SendResult:
        """Edit a previously sent message (Baileys-specific feature)."""
        if not self._running or not self._http_session:
            return SendResult(success=False, error="Not connected")
        
        try:
            import aiohttp
            async with self._http_session.post(
                f"http://127.0.0.1:{self._bridge_port}/edit",
                json={"chatId": chat_id, "messageId": message_id, "message": new_message},
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    return SendResult(success=True, message_id=message_id)
                else:
                    error = await resp.text()
                    return SendResult(success=False, error=error)
        except Exception as e:
            return SendResult(success=False, error=str(e))

    async def send_media(
        self,
        chat_id: str,
        file_path: str,
        media_type: str = "document",
        caption: Optional[str] = None,
        file_name: Optional[str] = None,
    ) -> SendResult:
        """Send media (image, video, audio, document) via the bridge."""
        if not self._running or not self._http_session:
            return SendResult(success=False, error="Not connected")
        
        if not Path(file_path).exists():
            return SendResult(success=False, error=f"File not found: {file_path}")
        
        try:
            import aiohttp
            payload: Dict[str, Any] = {
                "chatId": chat_id,
                "filePath": file_path,
                "mediaType": media_type,
            }
            if caption:
                payload["caption"] = caption
            if file_name:
                payload["fileName"] = file_name
            
            async with self._http_session.post(
                f"http://127.0.0.1:{self._bridge_port}/send-media",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return SendResult(success=True, message_id=data.get("messageId"))
                else:
                    error = await resp.text()
                    return SendResult(success=False, error=error)
        except Exception as e:
            return SendResult(success=False, error=str(e))

    async def send_typing(self, chat_id: str) -> None:
        """Send typing indicator."""
        if not self._running or not self._http_session:
            return
        
        try:
            import aiohttp
            await self._http_session.post(
                f"http://127.0.0.1:{self._bridge_port}/typing",
                json={"chatId": chat_id},
                timeout=aiohttp.ClientTimeout(total=5)
            )
        except Exception:
            pass  # Ignore typing indicator failures


# Backward compatibility with SendResult
class SendResult:
    def __init__(self, success: bool, message_id: Optional[str] = None, error: Optional[str] = None):
        self.success = success
        self.message_id = message_id
        self.error = error
