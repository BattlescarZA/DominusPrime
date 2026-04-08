# WhatsApp Baileys Integration - Implementation Guide

## Overview

DominusPrime now includes a modern WhatsApp integration using the [Baileys](https://github.com/WhiskeySockets/Baileys) library, replacing the deprecated whatsapp-web.js implementation. This integration uses a Node.js HTTP bridge pattern for reliability and maintainability.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      DominusPrime Process                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Python WhatsApp Adapter                                 │   │
│  │  (src/dominusprime/app/channels/whatsapp/)               │   │
│  │                                                          │   │
│  │  - Manages bridge subprocess                            │   │
│  │  - Long-polling for messages                            │   │
│  │  - HTTP client for sending                              │   │
│  └──────────────┬───────────────────────────────────────────┘   │
│                 │                                                │
└─────────────────┼────────────────────────────────────────────────┘
                  │
                  │ HTTP/JSON (localhost:3000)
                  │ GET  /messages
                  │ POST /send
                  │ POST /edit
                  │ POST /send-media
                  │ POST /typing
                  │ GET  /health
                  │
┌─────────────────▼────────────────────────────────────────────────┐
│                   Node.js Bridge Process                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Express HTTP Server                                     │   │
│  │  (scripts/whatsapp-bridge/bridge.js)                     │   │
│  │                                                          │   │
│  │  - REST API endpoints                                    │   │
│  │  - Message queue management                              │   │
│  │  - Session state handling                                │   │
│  └──────────────┬───────────────────────────────────────────┘   │
│                 │                                                │
│  ┌──────────────▼───────────────────────────────────────────┐   │
│  │  Baileys WhatsApp Client                                 │   │
│  │  (@whiskeysockets/baileys 7.0.0-rc.9)                    │   │
│  │                                                          │   │
│  │  - Multi-file auth state                                 │   │
│  │  - E2EE message handling                                 │   │
│  │  - Media download/upload                                 │   │
│  └──────────────┬───────────────────────────────────────────┘   │
│                 │                                                │
└─────────────────┼────────────────────────────────────────────────┘
                  │
                  │ WebSocket (wss://web.whatsapp.com)
                  │ End-to-End Encrypted
                  │
┌─────────────────▼────────────────────────────────────────────────┐
│                    WhatsApp Servers                              │
└──────────────────────────────────────────────────────────────────┘
```

## File Structure

```
dominusprime/
├── scripts/whatsapp-bridge/        # Node.js bridge
│   ├── bridge.js                   # Main bridge server (530 lines)
│   ├── package.json                # Dependencies
│   ├── allowlist.js                # User security
│   ├── allowlist.test.mjs          # Tests
│   └── README.md                   # Bridge documentation
│
├── src/dominusprime/
│   ├── app/channels/whatsapp/
│   │   ├── baileys_adapter.py      # Python HTTP adapter (580 lines)
│   │   └── channel.py              # Existing WebSocket-based channel
│   │
│   └── cli/
│       ├── whatsapp_cmd.py         # CLI commands (200+ lines)
│       └── main.py                 # Command registration
│
└── docs/
    └── WHATSAPP_BAILEYS_IMPLEMENTATION.md  # This file
```

## Key Components

### 1. Node.js Bridge (`bridge.js`)

**Purpose**: Connect to WhatsApp via Baileys and expose HTTP endpoints

**Key Features**:
- QR code authentication with session persistence
- Long-polling message queue (max 100 messages)
- Native media handling (images, videos, audio, documents)
- Message editing support (Baileys-exclusive feature)
- User allowlist with phone ↔ LID mapping
- Self-chat and bot modes
- Auto-reconnection on disconnects

**Endpoints**:
```
GET  /health                      - Connection status
GET  /messages                    - Poll for new messages (long-poll)
POST /send                        - Send text message
POST /edit                        - Edit sent message
POST /send-media                  - Send media natively
POST /typing                      - Typing indicator
GET  /chat/:id                    - Get chat metadata
```

**Session Files** (`.dominusprime/whatsapp/session/`):
- `creds.json` - Authentication credentials
- `app-state-sync-*.json` - WhatsApp state sync
- `lid-mapping-*.json` - Phone ↔ LID aliases

### 2. Python Adapter (`baileys_adapter.py`)

**Purpose**: Manage bridge lifecycle and communicate via HTTP

**Responsibilities**:
- Start/stop Node.js bridge subprocess
- Auto-install npm dependencies
- Health checking and auto-reconnection
- Message polling (1-second intervals)
- Media type detection and handling
- Error recovery

**Key Methods**:
```python
async def start()                  # Launch bridge
async def stop()                   # Clean shutdown
async def send_message()           # Send text
async def edit_message()           # Edit message (Baileys feature)
async def send_media()             # Send images/videos/documents
async def send_typing()            # Typing indicator
```

### 3. CLI Commands (`whatsapp_cmd.py`)

**Purpose**: User-friendly WhatsApp management

**Commands**:
```bash
dominusprime whatsapp pair         # QR code pairing
dominusprime whatsapp status       # Check bridge status
dominusprime whatsapp start        # Manual bridge start
dominusprime whatsapp reset        # Reset session
```

## Installation & Setup

### Prerequisites

1. **Node.js 16+** (for bridge)
   ```bash
   node --version  # Should be >= 16.0.0
   ```

2. **npm** (comes with Node.js)
   ```bash
   npm --version
   ```

### First-Time Setup

1. **Pair WhatsApp Account**:
   ```bash
   dominusprime whatsapp pair
   ```
   - Scan QR code with WhatsApp mobile app
   - Settings → Linked Devices → Link a Device
   - Session saved to `~/.dominusprime/whatsapp/session/`

2. **Start DominusPrime**:
   ```bash
   dominusprime run
   ```
   - Bridge auto-starts with DominusPrime
   - Loads saved session automatically

3. **Verify Connection**:
   ```bash
   dominusprime whatsapp status
   ```

## Configuration

### Environment Variables

```bash
# WhatsApp mode (self-chat or bot)
export WHATSAPP_MODE="self-chat"  # or "bot"

# User allowlist (bot mode only)
export WHATSAPP_ALLOWED_USERS="19175395595,34652029134"
# Or allow all:
export WHATSAPP_ALLOWED_USERS="*"

# Custom reply prefix
export WHATSAPP_REPLY_PREFIX="🤖 *DominusPrime*\n────────────\n"

# Debug logging
export WHATSAPP_DEBUG="1"
```

### Python Config

In `config.yaml` or code:
```python
whatsapp_config = WhatsAppConfig(
    enabled=True,
    extra={
        "bridge_port": 3000,
        "session_path": "~/.dominusprime/whatsapp/session",
        "reply_prefix": "🤖 *DominusPrime*\n────────────\n",
    }
)
```

## Usage Examples

### Basic Text Messaging

```python
from dominusprime.app.channels.whatsapp import WhatsAppBaileysAdapter

adapter = WhatsAppBaileysAdapter(
    process=process_handler,
    enabled=True,
)

await adapter.start()

# Send message
result = await adapter.send_message(
    chat_id="1234567890@s.whatsapp.net",
    message="Hello from DominusPrime!",
)

# Edit message (Baileys feature!)
await adapter.edit_message(
    chat_id="1234567890@s.whatsapp.net",
    message_id=result.message_id,
    new_message="Updated message!",
)
```

### Sending Media

```python
# Send image
await adapter.send_media(
    chat_id="1234567890@s.whatsapp.net",
    file_path="/path/to/image.jpg",
    media_type="image",
    caption="Check this out!",
)

# Send document
await adapter.send_media(
    chat_id="1234567890@s.whatsapp.net",
    file_path="/path/to/document.pdf",
    media_type="document",
    file_name="report.pdf",
)
```

### Typing Indicator

```python
await adapter.send_typing("1234567890@s.whatsapp.net")
```

## Comparison: Baileys vs whatsapp-web.js

| Feature | Baileys (New ✅) | whatsapp-web.js (Old ❌) |
|---------|------------------|-------------------------|
| **Maintenance Status** | Active development | Deprecated since 2023 |
| **Last Update** | Regular updates | Abandoned |
| **Message Editing** | ✅ Native support | ❌ Not supported |
| **Media Handling** | ✅ Native binary | ⚠️ Base64 conversion |
| **Session Format** | ✅ Multi-file (reliable) | ⚠️ Single file |
| **Connection Stability** | ✅ Excellent | ⚠️ Frequent drops |
| **E2EE Support** | ✅ Full support | ⚠️ Limited |
| **Group Support** | ✅ Full | ✅ Full |
| **Authentication** | ✅ QR + Pairing code | ✅ QR only |
| **Media Types** | Images, videos, audio, docs, stickers | Images, videos, audio, docs |
| **File Size Limits** | WhatsApp limits (16MB images, 100MB docs) | Same |
| **Memory Usage** | ⚠️ Higher (Baileys overhead) | ✅ Lower |
| **Setup Complexity** | ✅ Simple (auto npm install) | ✅ Simple |

**Verdict**: Baileys is superior in every important aspect. The slightly higher memory usage is negligible compared to the reliability and features gained.

## Troubleshooting

### QR Code Not Appearing

**Problem**: Bridge starts but no QR code shown

**Solutions**:
1. Check bridge log: `tail -f ~/.dominusprime/whatsapp/bridge.log`
2. Ensure no firewall blocking WhatsApp Web
3. Delete session and re-pair: `dominusprime whatsapp reset`

### Connection Drops

**Problem**: Bridge disconnects frequently

**Solutions**:
1. WhatsApp may request restart (code 515) - bridge auto-reconnects
2. Check for duplicate session use (only one bridge per session)
3. Verify internet connectivity
4. Update Node.js to latest LTS version

### Message Echo Loops

**Problem**: Bot replies to its own messages

**Solutions**:
1. In self-chat mode, messages starting with `WHATSAPP_REPLY_PREFIX` are filtered
2. Customize prefix: `export WHATSAPP_REPLY_PREFIX="🤖 "`
3. Switch to bot mode: `export WHATSAPP_MODE="bot"`

### Port Already in Use

**Problem**: Error "EADDRINUSE: address already in use :::3000"

**Solutions**:
```bash
# Linux/macOS
fuser -k 3000/tcp

# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Or use different port
dominusprime whatsapp start --port 3001
```

### npm Install Fails

**Problem**: Bridge dependencies won't install

**Solutions**:
1. Update npm: `npm install -g npm@latest`
2. Clear cache: `npm cache clean --force`
3. Check Node.js version: `node --version` (need 16+)
4. Install manually:
   ```bash
   cd scripts/whatsapp-bridge
   npm install
   ```

## Security Considerations

### Session Security

**Session files contain authentication tokens**. Protect them:

```bash
chmod 700 ~/.dominusprime/whatsapp/session
```

Never commit session files to git:
```gitignore
.dominusprime/
**/whatsapp/session/
```

### User Allowlist (Bot Mode)

Restrict which users can message your bot:

```bash
export WHATSAPP_ALLOWED_USERS="19175395595,34652029134"
```

The allowlist automatically handles:
- Classic phone numbers: `19175395595@s.whatsapp.net`
- LID format: `267383306489914@lid`
- Mapping between formats transparently

### Self-Chat vs Bot Mode

**Self-Chat Mode** (default):
- Messages sent in your own WhatsApp chat
- Prefix identifies bot replies
- Good for personal use

**Bot Mode**:
- Separate phone number for bot
- No prefix needed (different sender)
- Allowlist enforced
- Good for multi-user scenarios

## Performance Characteristics

### Memory Usage

- **Bridge Process**: ~100-200 MB (Node.js + Baileys)
- **Python Adapter**: ~20-30 MB
- **Total**: ~150-250 MB per WhatsApp connection

### Message Throughput

- **Receiving**: ~10 msg/s via long-polling
- **Sending**: Limited by WhatsApp rate limits (~20 msg/minute)
- **Media Upload**: Depends on file size and bandwidth

### Latency

- **Message Reception**: 1-3 seconds (polling interval)
- **Message Sending**: 500ms - 2s (network dependent)
- **Bridge Startup**: 5-15 seconds (depends on saved session)

## Testing

### Manual Testing

```bash
# 1. Pair account
dominusprime whatsapp pair

# 2. Check status
dominusprime whatsapp status

# 3. Start bridge manually (for testing)
dominusprime whatsapp start

# 4. Send test message (from another device)
# Message should appear in DominusPrime logs

# 5. Reset session (cleanup)
dominusprime whatsapp reset
```

### Automated Testing

```bash
# Run allowlist tests
cd scripts/whatsapp-bridge
npm test

# Expected output:
# ✓ normalizeWhatsAppIdentifier strips jid syntax
# ✓ expandWhatsAppIdentifiers resolves aliases
# ✓ matchesAllowedUser accepts mapped lid sender
# ✓ matchesAllowedUser treats * as wildcard
```

## Future Enhancements

### Planned Features

1. **Media Transcoding**: Automatic format conversion for compatibility
2. **Reaction Support**: Send/receive message reactions
3. **Voice Messages**: Native PTT (Push-to-Talk) support
4. **Status Updates**: Post to WhatsApp status
5. **Group Admin Features**: Manage group settings
6. **Message Scheduling**: Schedule messages for later
7. **Multi-Device Sync**: Better handling of linked devices

### API Enhancements

1. **Streaming Responses**: Stream long bot responses
2. **Bulk Operations**: Send to multiple chats efficiently
3. **Webhooks**: Alternative to long-polling
4. **Media Proxying**: Direct media URLs without caching

## Credits

- **Baileys Library**: [@WhiskeySockets](https://github.com/WhiskeySockets/Baileys)
- **Bridge Pattern**: Adapted from [Hermes Agent](https://github.com/nousresearch/hermes-agent)
- **DominusPrime Team**: Integration and adaptation

## License

Part of DominusPrime. Baileys is MIT licensed.

## Support

For issues or questions:
1. Check this document first
2. Review `scripts/whatsapp-bridge/README.md`
3. Check bridge logs: `~/.dominusprime/whatsapp/bridge.log`
4. Open GitHub issue with logs attached
