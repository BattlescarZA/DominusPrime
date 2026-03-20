# -*- coding: utf-8 -*-
# pylint: disable=too-many-branches
"""WhatsApp channel: QR code authentication via Node.js bridge."""

from __future__ import annotations

import asyncio
import logging
import uuid
import aiohttp
import json
from pathlib import Path
from typing import Any, Optional, Union
from socketio import AsyncClient

from agentscope_runtime.engine.schemas.agent_schemas import (
    TextContent,
    ImageContent,
    VideoContent,
    AudioContent,
    FileContent,
    ContentType,
)

from ....config.config import WhatsAppConfig as WhatsAppChannelConfig
from ..base import (
    BaseChannel,
    OnReplySent,
    ProcessHandler,
    OutgoingContentPart,
)

logger = logging.getLogger(__name__)

WHATSAPP_MAX_MESSAGE_LENGTH = 4096
WHATSAPP_SEND_CHUNK_SIZE = 4000

_DEFAULT_SESSION_DIR = Path("~/.dominusprime/whatsapp/session").expanduser()
_DEFAULT_MEDIA_DIR = Path("~/.dominusprime/media/whatsapp").expanduser()
_DEFAULT_BRIDGE_URL = "http://localhost:8765"

_MEDIA_ATTRS: list[tuple[str, type, Any, str]] = [
    ("document", FileContent, ContentType.FILE, "file_url"),
    ("video", VideoContent, ContentType.VIDEO, "video_url"),
    ("voice", AudioContent, ContentType.AUDIO, "data"),
    ("audio", AudioContent, ContentType.AUDIO, "data"),
    ("image", ImageContent, ContentType.IMAGE, "image_url"),
]


class WhatsAppChannel(BaseChannel):
    """WhatsApp channel using QR code authentication via Node.js bridge.
    
    Communicates with a Node.js service (bridge.js) that handles WhatsApp Web
    integration using whatsapp-web.js library.
    
    Features:
        - QR code authentication (scan with WhatsApp mobile app)
        - Send/receive text messages
        - Send/receive media (images, videos, audio, documents)
        - Group chat support
        - Reply detection
        - Typing indicators
        - Security/allowlist policies
    """

    channel = "whatsapp"
    uses_manager_queue = True

    def __init__(
        self,
        process: ProcessHandler,
        enabled: bool,
        bridge_url: str,
        session_dir: str,
        media_dir: str,
        on_reply_sent: OnReplySent = None,
        show_tool_details: bool = True,
        filter_tool_messages: bool = False,
        filter_thinking: bool = False,
        show_typing: bool = True,
        dm_policy: str = "open",
        group_policy: str = "open",
        allow_from: list = None,
        deny_message: str = "",
        max_retries: int = 3,
        retry_delay: int = 5,
    ):
        super().__init__(
            process,
            on_reply_sent,
            show_tool_details,
            filter_tool_messages,
            filter_thinking,
        )
        self._enabled = enabled
        self._bridge_url = bridge_url.rstrip("/")
        self._session_dir = Path(session_dir).expanduser()
        self._media_dir = Path(media_dir).expanduser()
        self._show_typing = show_typing
        self._dm_policy = dm_policy
        self._group_policy = group_policy
        self._allow_from = set(allow_from or [])
        self._deny_message = deny_message
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        
        # HTTP session
        self._session: Optional[aiohttp.ClientSession] = None
        
        # WebSocket client
        self._sio: Optional[AsyncClient] = None
        self._ready = asyncio.Event()
        self._stop_event = asyncio.Event()
        self._typing_tasks: dict[str, asyncio.Task] = {}
        
        # Session state
        self._authenticated = False
        self._qr_code: Optional[str] = None
        self._client_info: Optional[dict] = None

    @classmethod
    def from_config(
        cls,
        process: ProcessHandler,
        config: Union[WhatsAppChannelConfig, dict],
        on_reply_sent: OnReplySent = None,
        show_tool_details: bool = True,
        filter_tool_messages: bool = False,
        filter_thinking: bool = False,
    ) -> "WhatsAppChannel":
        """Create WhatsAppChannel from config."""
        if isinstance(config, dict):
            c = config
        else:
            c = config.model_dump()

        def _get_str(key: str) -> str:
            return (c.get(key) or "").strip()

        show_typing = c.get("show_typing")
        if show_typing is None:
            show_typing = True

        return cls(
            process=process,
            enabled=bool(c.get("enabled", False)),
            bridge_url=_get_str("bridge_url") or _DEFAULT_BRIDGE_URL,
            session_dir=_get_str("session_dir") or "~/.dominusprime/whatsapp/session",
            media_dir=_get_str("media_dir") or "~/.dominusprime/media/whatsapp",
            on_reply_sent=on_reply_sent,
            show_tool_details=show_tool_details,
            filter_tool_messages=filter_tool_messages,
            filter_thinking=filter_thinking,
            show_typing=show_typing,
            dm_policy=c.get("dm_policy") or "open",
            group_policy=c.get("group_policy") or "open",
            allow_from=c.get("allow_from") or [],
            deny_message=c.get("deny_message") or "",
            max_retries=c.get("max_retries") or 3,
            retry_delay=c.get("retry_delay") or 5,
        )

    async def start(self) -> None:
        """Start WhatsApp channel and connect to bridge service."""
        try:
            logger.info("whatsapp: connecting to bridge service")
            self._session_dir.mkdir(parents=True, exist_ok=True)
            self._media_dir.mkdir(parents=True, exist_ok=True)
            
            # Create HTTP session
            self._session = aiohttp.ClientSession()
            
            # Check bridge health
            try:
                async with self._session.get(f"{self._bridge_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status != 200:
                        raise ConnectionError("Bridge service health check failed")
                    logger.info("whatsapp: bridge service is healthy")
            except Exception as e:
                logger.error(f"whatsapp: cannot connect to bridge service at {self._bridge_url}")
                logger.error(f"whatsapp: make sure to start the Node.js bridge first:")
                logger.error(f"whatsapp:   cd src/dominusprime/app/channels/whatsapp && npm install && npm start")
                raise ConnectionError(f"Bridge service not available: {e}")
            
            # Connect via WebSocket for real-time events
            self._sio = AsyncClient()
            
            # Register event handlers
            @self._sio.event
            async def connect():
                logger.info("whatsapp: websocket connected")
            
            @self._sio.event
            async def disconnect():
                logger.warning("whatsapp: websocket disconnected")
                self._authenticated = False
                self._ready.clear()
            
            @self._sio.on('qr')
            async def on_qr(data):
                await self._on_qr(data.get('qr'))
            
            @self._sio.on('authenticated')
            async def on_authenticated(data):
                await self._on_authenticated()
            
            @self._sio.on('auth_failure')
            async def on_auth_failure(data):
                await self._on_auth_failure(data.get('message', 'Unknown error'))
            
            @self._sio.on('ready')
            async def on_ready(data):
                await self._on_ready(data.get('info'))
            
            @self._sio.on('message')
            async def on_message(data):
                await self._on_message(data)
            
            @self._sio.on('disconnected')
            async def on_disconnected(data):
                await self._on_disconnected(data.get('reason', 'Unknown'))
            
            # Connect to bridge
            await self._sio.connect(self._bridge_url)
            
            # Wait for ready or timeout
            try:
                await asyncio.wait_for(self._ready.wait(), timeout=120)
                logger.info("whatsapp: client ready")
            except asyncio.TimeoutError:
                logger.warning("whatsapp: initialization timeout (still waiting for QR scan)")
                # Don't raise - QR code might not be scanned yet
                
        except Exception:
            logger.exception("whatsapp: failed to start")
            raise

    async def stop(self) -> None:
        """Stop WhatsApp channel."""
        logger.info("whatsapp: stopping")
        self._stop_event.set()
        
        # Cancel all typing tasks
        for task in list(self._typing_tasks.values()):
            if not task.done():
                task.cancel()
        self._typing_tasks.clear()
        
        # Disconnect WebSocket
        if self._sio and self._sio.connected:
            await self._sio.disconnect()
        
        # Close HTTP session
        if self._session:
            await self._session.close()
            
        logger.info("whatsapp: stopped")

    async def _on_qr(self, qr: str) -> None:
        """Handle QR code generation."""
        self._qr_code = qr
        logger.info("whatsapp: QR code generated")
        logger.info("=" * 50)
        logger.info("WhatsApp QR Code:")
        logger.info("Scan this QR code with your WhatsApp mobile app")
        logger.info("Or access it via: http://localhost:8000/whatsapp/qr")
        logger.info("=" * 50)
        
        # Try to display QR in terminal
        try:
            import qrcode
            qr_obj = qrcode.QRCode()
            qr_obj.add_data(qr)
            qr_obj.print_ascii()
        except ImportError:
            logger.info("Install 'qrcode' package to display QR in terminal: pip install qrcode")

    async def _on_authenticated(self) -> None:
        """Handle successful authentication."""
        self._authenticated = True
        self._qr_code = None
        logger.info("whatsapp: authenticated successfully")

    async def _on_auth_failure(self, msg: str) -> None:
        """Handle authentication failure."""
        logger.error(f"whatsapp: authentication failed: {msg}")
        self._authenticated = False

    async def _on_ready(self, info: Optional[dict]) -> None:
        """Handle client ready."""
        self._client_info = info
        if info:
            logger.info(f"whatsapp: ready as {info.get('pushname')} ({info.get('wid', {}).get('user')})")
        else:
            logger.info("whatsapp: client is ready")
        self._ready.set()

    async def _on_disconnected(self, reason: str) -> None:
        """Handle disconnection."""
        logger.warning(f"whatsapp: disconnected: {reason}")
        self._authenticated = False
        self._ready.clear()

    async def _on_message(self, data: dict) -> None:
        """Handle incoming message from bridge."""
        if not data or self._stop_event.is_set():
            return
        
        try:
            # Extract message details
            sender_id = data.get("contactId", "")
            sender_name = data.get("contactName", sender_id)
            is_group = data.get("isGroup", False)
            chat_id = data.get("chatId", "")
            is_from_me = data.get("isFromMe", False)
            
            # Ignore own messages
            if is_from_me:
                return
            
            # Apply security policies
            if not self._is_allowed(sender_id, is_group):
                if self._deny_message:
                    await self._send_to_bridge("/send", {
                        "chatId": chat_id,
                        "message": self._deny_message
                    })
                logger.debug(f"whatsapp: message from {sender_id} blocked by policy")
                return
            
            # Build content parts
            content_parts = []
            
            # Text content
            body = data.get("body", "").strip()
            if body:
                content_parts.append(
                    TextContent(text=body, type=ContentType.TEXT)
                )
            
            # Media content
            media = data.get("media")
            if media:
                media_type = data.get("type", "").lower()
                mimetype = media.get("mimetype", "")
                
                # Save media locally
                import base64
                media_data = base64.b64decode(media.get("data", ""))
                filename = media.get("filename") or f"{uuid.uuid4().hex[:12]}"
                
                if media_type == "image" or mimetype.startswith("image/"):
                    file_path = self._media_dir / "images" / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_bytes(media_data)
                    content_parts.append(
                        ImageContent(
                            image_url=f"file://{file_path}",
                            type=ContentType.IMAGE,
                        )
                    )
                elif media_type == "video" or mimetype.startswith("video/"):
                    file_path = self._media_dir / "videos" / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_bytes(media_data)
                    content_parts.append(
                        VideoContent(
                            video_url=f"file://{file_path}",
                            type=ContentType.VIDEO,
                        )
                    )
                elif media_type in ("audio", "ptt") or mimetype.startswith("audio/"):
                    file_path = self._media_dir / "audio" / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_bytes(media_data)
                    content_parts.append(
                        AudioContent(
                            data=f"file://{file_path}",
                            type=ContentType.AUDIO,
                        )
                    )
                else:
                    # Document/file
                    file_path = self._media_dir / "files" / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_bytes(media_data)
                    content_parts.append(
                        FileContent(
                            file_url=f"file://{file_path}",
                            type=ContentType.FILE,
                        )
                    )
            
            if not content_parts:
                return
            
            # Build session_id
            session_id = f"whatsapp-{sender_id}-{chat_id}" if is_group else f"whatsapp-{sender_id}"
            
            # Enqueue for processing
            native_payload = {
                "content_parts": content_parts,
                "session_id": session_id,
                "sender_id": sender_id,
                "meta": {
                    "chat_id": chat_id,
                    "message_id": data.get("id", ""),
                    "sender_name": sender_name,
                    "is_group": is_group,
                },
            }
            
            if self._enqueue:
                self._enqueue(native_payload)
                
        except Exception:
            logger.exception("whatsapp: error handling message")

    def _is_allowed(self, sender_id: str, is_group: bool) -> bool:
        """Check if sender is allowed based on security policy."""
        policy = self._group_policy if is_group else self._dm_policy
        
        if policy == "open":
            return True
            
        # allowlist policy
        return sender_id in self._allow_from

    async def consume_one(self, payload: Any) -> None:
        """Send agent response to WhatsApp chat."""
        if not self._authenticated:
            logger.warning("whatsapp: not authenticated, dropping message")
            return
            
        try:
            meta = payload.get("meta") or {}
            chat_id = meta.get("chat_id", "")
            content_parts = payload.get("content_parts") or []
            
            if not chat_id:
                logger.warning("whatsapp: no chat_id in payload")
                return
            
            # Show typing indicator
            if self._show_typing:
                await self._start_typing(chat_id)
            
            # Send content parts
            for part in content_parts:
                await self._send_content_part(chat_id, part)
                await asyncio.sleep(0.5)  # Small delay between messages
            
            # Stop typing
            if self._show_typing:
                await self._stop_typing(chat_id)
                
        except Exception:
            logger.exception("whatsapp: error sending message")

    async def _send_content_part(self, chat_id: str, part: OutgoingContentPart) -> None:
        """Send a single content part to WhatsApp via bridge."""
        try:
            if isinstance(part, TextContent):
                text = part.text or ""
                if not text.strip():
                    return
                
                # Split long messages
                if len(text) > WHATSAPP_MAX_MESSAGE_LENGTH:
                    chunks = [
                        text[i : i + WHATSAPP_SEND_CHUNK_SIZE]
                        for i in range(0, len(text), WHATSAPP_SEND_CHUNK_SIZE)
                    ]
                    for chunk in chunks:
                        await self._send_to_bridge("/send", {
                            "chatId": chat_id,
                            "message": chunk
                        })
                        await asyncio.sleep(0.3)
                else:
                    await self._send_to_bridge("/send", {
                        "chatId": chat_id,
                        "message": text
                    })
                    
            elif isinstance(part, (ImageContent, VideoContent, AudioContent, FileContent)):
                # Get file path
                url = None
                if isinstance(part, ImageContent):
                    url = part.image_url
                elif isinstance(part, VideoContent):
                    url = part.video_url
                elif isinstance(part, AudioContent):
                    url = part.data
                elif isinstance(part, FileContent):
                    url = part.file_url
                
                if url and url.startswith("file://"):
                    path = url[7:]
                    await self._send_to_bridge("/send", {
                        "chatId": chat_id,
                        "mediaPath": path,
                        "mediaOptions": {"sendAudioAsVoice": True} if isinstance(part, AudioContent) else {}
                    })
                    
        except Exception:
            logger.exception("whatsapp: error sending content part")

    async def _send_to_bridge(self, endpoint: str, data: dict) -> Optional[dict]:
        """Send HTTP request to bridge service."""
        if not self._session:
            return None
        
        try:
            async with self._session.post(
                f"{self._bridge_url}{endpoint}",
                json=data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    logger.error(f"whatsapp: bridge error ({resp.status}): {error_text}")
                    return None
        except Exception as e:
            logger.error(f"whatsapp: bridge request failed: {e}")
            return None

    async def _start_typing(self, chat_id: str) -> None:
        """Start showing typing indicator."""
        if chat_id in self._typing_tasks:
            return
            
        async def typing_loop():
            try:
                while not self._stop_event.is_set():
                    await self._send_to_bridge(f"/typing/{chat_id}", {})
                    await asyncio.sleep(3)  # Refresh typing state every 3s
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("whatsapp: error in typing loop")
        
        task = asyncio.create_task(typing_loop())
        self._typing_tasks[chat_id] = task

    async def _stop_typing(self, chat_id: str) -> None:
        """Stop showing typing indicator."""
        task = self._typing_tasks.pop(chat_id, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    def get_debounce_key(self, payload: Any) -> str:
        """Get debounce key for message grouping."""
        if isinstance(payload, dict):
            meta = payload.get("meta") or {}
            return meta.get("chat_id", "") or payload.get("session_id", "")
        return super().get_debounce_key(payload)
