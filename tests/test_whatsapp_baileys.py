# -*- coding: utf-8 -*-
"""Tests for WhatsApp Baileys integration."""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio


@pytest.fixture
def process_handler():
    """Mock process handler."""
    async def mock_process(request):
        yield {"type": "message", "content": "test"}
    return mock_process


@pytest.fixture
def baileys_adapter(process_handler):
    """Create a Baileys adapter instance for testing."""
    from src.dominusprime.app.channels.whatsapp.baileys_adapter import WhatsAppBaileysAdapter
    
    adapter = WhatsAppBaileysAdapter(
        process=process_handler,
        enabled=True,
        bridge_port=3000,
        session_path="/tmp/test_whatsapp_session",
    )
    return adapter


def test_baileys_adapter_init(baileys_adapter):
    """Test Baileys adapter initialization."""
    assert baileys_adapter._enabled is True
    assert baileys_adapter._bridge_port == 3000
    assert baileys_adapter._running is False
    assert baileys_adapter._bridge_process is None


def test_check_whatsapp_requirements():
    """Test Node.js requirement check."""
    from src.dominusprime.app.channels.whatsapp.baileys_adapter import check_whatsapp_requirements
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        assert check_whatsapp_requirements() is True
        
        mock_run.return_value.returncode = 1
        assert check_whatsapp_requirements() is False


@pytest.mark.asyncio
async def test_send_message_not_connected(baileys_adapter):
    """Test sending message when not connected."""
    result = await baileys_adapter.send_message(
        chat_id="test@s.whatsapp.net",
        message="Hello",
    )
    assert result.success is False
    assert result.error == "Not connected"


@pytest.mark.asyncio
async def test_edit_message_not_connected(baileys_adapter):
    """Test editing message when not connected."""
    result = await baileys_adapter.edit_message(
        chat_id="test@s.whatsapp.net",
        message_id="ABC123",
        new_message="Updated",
    )
    assert result.success is False
    assert result.error == "Not connected"


@pytest.mark.asyncio
async def test_send_media_not_connected(baileys_adapter):
    """Test sending media when not connected."""
    result = await baileys_adapter.send_media(
        chat_id="test@s.whatsapp.net",
        file_path="/tmp/test.jpg",
        media_type="image",
    )
    assert result.success is False
    assert result.error == "Not connected"


def test_bridge_path_detection(baileys_adapter):
    """Test that bridge path is properly detected."""
    bridge_script = Path(baileys_adapter._bridge_script)
    assert bridge_script.name == "bridge.js"
    assert "whatsapp-bridge" in str(bridge_script.parent)


@pytest.mark.asyncio
async def test_build_message_event(baileys_adapter):
    """Test building message event from bridge data."""
    data = {
        "messageId": "ABC123",
        "chatId": "1234567890@s.whatsapp.net",
        "senderId": "1234567890@s.whatsapp.net",
        "senderName": "John Doe",
        "body": "Hello!",
        "hasMedia": False,
        "mediaType": "",
        "mediaUrls": [],
        "timestamp": 1234567890,
        "isGroup": False,
    }
    
    event = await baileys_adapter._build_message_event(data)
    assert event is not None
    assert event["chat_id"] == "1234567890@s.whatsapp.net"
    assert event["text"] == "Hello!"
    assert event["message_id"] == "ABC123"


@pytest.mark.asyncio
async def test_build_message_event_with_media(baileys_adapter):
    """Test building message event with media."""
    data = {
        "messageId": "ABC123",
        "chatId": "1234567890@s.whatsapp.net",
        "senderId": "1234567890@s.whatsapp.net",
        "senderName": "John Doe",
        "body": "Check this out",
        "hasMedia": True,
        "mediaType": "image",
        "mediaUrls": ["/tmp/cached_image.jpg"],
        "timestamp": 1234567890,
        "isGroup": False,
    }
    
    event = await baileys_adapter._build_message_event(data)
    assert event is not None
    assert event["type"] == "photo"  # MessageType.PHOTO
    assert len(event["media_urls"]) == 1


def test_kill_port_process():
    """Test port cleanup function."""
    from src.dominusprime.app.channels.whatsapp.baileys_adapter import _kill_port_process
    
    # Should not raise even if port is not in use
    _kill_port_process(9999)


@pytest.mark.asyncio
async def test_check_bridge_exit_no_process(baileys_adapter):
    """Test checking bridge exit when no process exists."""
    result = await baileys_adapter._check_bridge_exit()
    assert result is None


@pytest.mark.asyncio
async def test_stop_when_not_started(baileys_adapter):
    """Test stopping adapter when it was never started."""
    # Should not raise
    await baileys_adapter.stop()
    assert baileys_adapter._running is False


def test_send_result_class():
    """Test SendResult class."""
    from src.dominusprime.app.channels.whatsapp.baileys_adapter import SendResult
    
    # Success case
    result = SendResult(success=True, message_id="ABC123")
    assert result.success is True
    assert result.message_id == "ABC123"
    assert result.error is None
    
    # Failure case
    result = SendResult(success=False, error="Connection failed")
    assert result.success is False
    assert result.error == "Connection failed"
    assert result.message_id is None


def test_default_bridge_dir():
    """Test default bridge directory detection."""
    from src.dominusprime.app.channels.whatsapp.baileys_adapter import WhatsAppBaileysAdapter
    
    default_bridge_dir = WhatsAppBaileysAdapter._DEFAULT_BRIDGE_DIR
    assert default_bridge_dir.name == "whatsapp-bridge"
    assert (default_bridge_dir / "bridge.js").name == "bridge.js"


@pytest.mark.asyncio
async def test_from_config(process_handler):
    """Test creating adapter from config."""
    from src.dominusprime.app.channels.whatsapp.baileys_adapter import WhatsAppBaileysAdapter
    from src.dominusprime.config.config import WhatsAppConfig
    
    config = WhatsAppConfig(
        enabled=True,
        extra={
            "bridge_port": 3001,
            "session_path": "/custom/path",
            "reply_prefix": "🤖 Test Bot\n",
        }
    )
    
    adapter = WhatsAppBaileysAdapter.from_config(process_handler, config)
    assert adapter._enabled is True
    assert adapter._bridge_port == 3001
    assert adapter._reply_prefix == "🤖 Test Bot\n"
