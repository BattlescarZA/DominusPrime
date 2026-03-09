# -*- coding: utf-8 -*-
# pylint: disable=too-many-branches
"""WhatsApp channel: QR code authentication (like WhatsApp Web)."""

from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any, Optional, Union

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
_TYPING_TIMEOUT_S = 180

_MEDIA_ATTRS: list[tuple[str, type, Any, str]] = [
    ("document", FileContent, ContentType.FILE, "file_url"),
    ("video", VideoContent, ContentType.VIDEO, "video_url"),
    ("voice", AudioContent, ContentType.AUDIO, "data"),
    ("audio", AudioContent, ContentType.AUDIO, "data"),
    ("image", ImageContent, ContentType.IMAGE, "image_url"),
]


async def _download_whatsapp_file(
    *,
    message: Any,
    media_dir: Path,
    filename_hint: str = "",
) -> Optional[str]:
    """Download a WhatsApp file to local media_dir; return local path.
    
    Uses whatsapp-web.js downloadMedia() method.
    """
    try:
        media = await message.downloadMedia()
        if not media:
            return None
            
        media_dir.mkdir(parents=True, exist_ok=True)
        
        # Get file extension from mimetype or filename
        suffix = ""
        if hasattr(media, "mimetype") and media.mimetype:
            mime = media.mimetype.lower()
            if "/" in mime:
                ext = mime.split("/")[-1]
                suffix = f".{ext}"
        
        if filename_hint and not suffix:
            suffix = Path(filename_hint).suffix
            
        local_name = f"{uuid.uuid4().hex[:12]}{suffix or '.bin'}"
        local_path = media_dir / local_name
        
        # Write media data to file
        if hasattr(media, "data"):
            import base64
            file_data = base64.b64decode(media.data)
            local_path.write_bytes(file_data)
            return str(local_path)
            
        return None
    except Exception:
        logger.exception("whatsapp: download failed for message")
        return None


class WhatsAppChannel(BaseChannel):
    """WhatsApp channel using QR code authentication (like WhatsApp Web).
    
    Uses whatsapp-web.js library for Node.js integration.
    Requires:
        - Node.js installed
        - whatsapp-web.js npm package
        - Puppeteer for browser automation
    
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
        self._session_dir = Path(session_dir).expanduser()
        self._media_dir = Path(media_dir).expanduser()
        self._show_typing = show_typing
        self._dm_policy = dm_policy
        self._group_policy = group_policy
        self._allow_from = set(allow_from or [])
        self._deny_message = deny_message
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        
        # WhatsApp client (will be initialized in start())
        self._client: Optional[Any] = None
        self._ready = asyncio.Event()
        self._stop_event = asyncio.Event()
        self._typing_tasks: dict[str, asyncio.Task] = {}
        
        # Session state
        self._authenticated = False
        self._qr_code: Optional[str] = None

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
        """Start WhatsApp client with QR code authentication."""
        try:
            # Import whatsapp-web.js (requires Node.js bridge)
            from whatsapp_web import Client, LocalAuth
            
            logger.info("whatsapp: initializing client")
            self._session_dir.mkdir(parents=True, exist_ok=True)
            
            # Create client with local authentication
            self._client = Client(
                auth_strategy=LocalAuth(client_id="dominusprime"),
                puppeteer_options={
                    "headless": True,
                    "args": ["--no-sandbox", "--disable-setuid-sandbox"],
                },
                user_data_dir=str(self._session_dir),
            )
            
            # Register event handlers
            self._client.on("qr", self._on_qr)
            self._client.on("authenticated", self._on_authenticated)
            self._client.on("auth_failure", self._on_auth_failure)
            self._client.on("ready", self._on_ready)
            self._client.on("message", self._on_message)
            self._client.on("message_create", self._on_message_create)
            self._client.on("disconnected", self._on_disconnected)
            
            # Initialize client
            await self._client.initialize()
            
            # Wait for ready or timeout
            try:
                await asyncio.wait_for(self._ready.wait(), timeout=120)
                logger.info("whatsapp: client ready")
            except asyncio.TimeoutError:
                logger.error("whatsapp: initialization timeout")
                raise
                
        except ImportError:
            logger.error(
                "whatsapp: whatsapp-web.js not available. "
                "Install: pip install whatsapp-web.py (Python bridge)"
            )
            raise
        except Exception:
            logger.exception("whatsapp: failed to start")
            raise

    async def stop(self) -> None:
        """Stop WhatsApp client."""
        logger.info("whatsapp: stopping")
        self._stop_event.set()
        
        # Cancel all typing tasks
        for task in list(self._typing_tasks.values()):
            if not task.done():
                task.cancel()
        self._typing_tasks.clear()
        
        # Destroy client
        if self._client:
            try:
                await self._client.destroy()
            except Exception:
                logger.exception("whatsapp: error destroying client")
            self._client = None
            
        logger.info("whatsapp: stopped")

    def _on_qr(self, qr: str) -> None:
        """Handle QR code generation."""
        self._qr_code = qr
        logger.info("whatsapp: QR code generated")
        logger.info("=" * 50)
        logger.info("WhatsApp QR Code:")
        logger.info("Please scan this QR code with your WhatsApp mobile app")
        logger.info("=" * 50)
        logger.info(qr)
        logger.info("=" * 50)
        
        # You could also save QR code to file or display in console UI
        try:
            import qrcode
            qr_img = qrcode.make(qr)
            qr_path = self._session_dir / "qr_code.png"
            qr_img.save(str(qr_path))
            logger.info(f"QR code saved to: {qr_path}")
        except ImportError:
            pass

    def _on_authenticated(self) -> None:
        """Handle successful authentication."""
        self._authenticated = True
        logger.info("whatsapp: authenticated successfully")

    def _on_auth_failure(self, msg: str) -> None:
        """Handle authentication failure."""
        logger.error(f"whatsapp: authentication failed: {msg}")
        self._authenticated = False

    def _on_ready(self) -> None:
        """Handle client ready."""
        logger.info("whatsapp: client is ready")
        self._ready.set()

    def _on_disconnected(self, reason: str) -> None:
        """Handle disconnection."""
        logger.warning(f"whatsapp: disconnected: {reason}")
        self._authenticated = False
        self._ready.clear()

    async def _on_message(self, message: Any) -> None:
        """Handle incoming message."""
        if not message or self._stop_event.is_set():
            return
            
        try:
            # Get message details
            chat = await message.getChat()
            contact = await message.getContact()
            
            # Extract sender info
            sender_id = contact.id._serialized if hasattr(contact, "id") else str(contact.number)
            sender_name = contact.name or contact.pushname or sender_id
            
            # Check if this is a group message
            is_group = chat.isGroup if hasattr(chat, "isGroup") else False
            chat_id = chat.id._serialized if hasattr(chat, "id") else ""
            
            # Apply security policies
            if not self._is_allowed(sender_id, is_group):
                if self._deny_message:
                    await message.reply(self._deny_message)
                logger.debug(f"whatsapp: message from {sender_id} blocked by policy")
                return
            
            # Build content parts
            content_parts = []
            
            # Text content
            if hasattr(message, "body") and message.body:
                content_parts.append(
                    TextContent(text=message.body, type=ContentType.TEXT)
                )
            
            # Media content
            if hasattr(message, "hasMedia") and message.hasMedia:
                media_type = getattr(message, "type", "").lower()
                
                if media_type == "image":
                    file_path = await _download_whatsapp_file(
                        message=message,
                        media_dir=self._media_dir,
                        filename_hint="image.jpg",
                    )
                    if file_path:
                        content_parts.append(
                            ImageContent(
                                image_url=f"file://{file_path}",
                                type=ContentType.IMAGE,
                            )
                        )
                        
                elif media_type == "video":
                    file_path = await _download_whatsapp_file(
                        message=message,
                        media_dir=self._media_dir,
                        filename_hint="video.mp4",
                    )
                    if file_path:
                        content_parts.append(
                            VideoContent(
                                video_url=f"file://{file_path}",
                                type=ContentType.VIDEO,
                            )
                        )
                        
                elif media_type in ("audio", "ptt"):  # ptt = voice message
                    file_path = await _download_whatsapp_file(
                        message=message,
                        media_dir=self._media_dir,
                        filename_hint="audio.ogg",
                    )
                    if file_path:
                        content_parts.append(
                            AudioContent(
                                data=f"file://{file_path}",
                                type=ContentType.AUDIO,
                            )
                        )
                        
                elif media_type == "document":
                    file_path = await _download_whatsapp_file(
                        message=message,
                        media_dir=self._media_dir,
                        filename_hint="document.pdf",
                    )
                    if file_path:
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
                    "message_id": message.id._serialized if hasattr(message, "id") else "",
                    "sender_name": sender_name,
                    "is_group": is_group,
                    "message": message,
                },
            }
            
            if self._enqueue:
                self._enqueue(native_payload)
                
        except Exception:
            logger.exception("whatsapp: error handling message")

    async def _on_message_create(self, message: Any) -> None:
        """Handle outgoing messages (sent by us)."""
        # Could be used for tracking sent messages
        pass

    def _is_allowed(self, sender_id: str, is_group: bool) -> bool:
        """Check if sender is allowed based on security policy."""
        policy = self._group_policy if is_group else self._dm_policy
        
        if policy == "open":
            return True
            
        # allowlist policy
        return sender_id in self._allow_from

    async def consume_one(self, payload: Any) -> None:
        """Send agent response to WhatsApp chat."""
        if not self._client or not self._authenticated:
            logger.warning("whatsapp: client not ready, dropping message")
            return
            
        try:
            meta = payload.get("meta") or {}
            chat_id = meta.get("chat_id", "")
            content_parts = payload.get("content_parts") or []
            
            if not chat_id:
                logger.warning("whatsapp: no chat_id in payload")
                return
            
            # Get chat
            chat = await self._client.getChatById(chat_id)
            if not chat:
                logger.warning(f"whatsapp: chat not found: {chat_id}")
                return
            
            # Show typing indicator
            if self._show_typing:
                await self._start_typing(chat_id, chat)
            
            # Send content parts
            for part in content_parts:
                await self._send_content_part(chat, part)
                await asyncio.sleep(0.5)  # Small delay between messages
            
            # Stop typing
            if self._show_typing:
                await self._stop_typing(chat_id)
                
        except Exception:
            logger.exception("whatsapp: error sending message")

    async def _send_content_part(self, chat: Any, part: OutgoingContentPart) -> None:
        """Send a single content part to WhatsApp."""
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
                        await chat.sendMessage(chunk)
                        await asyncio.sleep(0.3)
                else:
                    await chat.sendMessage(text)
                    
            elif isinstance(part, ImageContent):
                url = part.image_url or ""
                if url.startswith("file://"):
                    path = url[7:]
                    from whatsapp_web import MessageMedia
                    media = MessageMedia.fromFilePath(path)
                    await chat.sendMessage(media)
                    
            elif isinstance(part, VideoContent):
                url = part.video_url or ""
                if url.startswith("file://"):
                    path = url[7:]
                    from whatsapp_web import MessageMedia
                    media = MessageMedia.fromFilePath(path)
                    await chat.sendMessage(media)
                    
            elif isinstance(part, AudioContent):
                data = part.data or ""
                if data.startswith("file://"):
                    path = data[7:]
                    from whatsapp_web import MessageMedia
                    media = MessageMedia.fromFilePath(path)
                    await chat.sendMessage(media, {"sendAudioAsVoice": True})
                    
            elif isinstance(part, FileContent):
                url = part.file_url or ""
                if url.startswith("file://"):
                    path = url[7:]
                    from whatsapp_web import MessageMedia
                    media = MessageMedia.fromFilePath(path)
                    await chat.sendMessage(media)
                    
        except Exception:
            logger.exception("whatsapp: error sending content part")

    async def _start_typing(self, chat_id: str, chat: Any) -> None:
        """Start showing typing indicator."""
        if chat_id in self._typing_tasks:
            return
            
        async def typing_loop():
            try:
                while not self._stop_event.is_set():
                    await chat.sendStateTyping()
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


def _is_whatsapp_available() -> bool:
    """Check if WhatsApp Web bridge is available."""
    try:
        import whatsapp_web
        return True
    except ImportError:
        return False
