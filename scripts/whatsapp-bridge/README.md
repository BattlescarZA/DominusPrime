# DominusPrime WhatsApp Bridge

This is a standalone Node.js bridge that connects to WhatsApp using the [Baileys](https://github.com/WhiskeySockets/Baileys) library and exposes HTTP endpoints for the Python adapter.

## Features

- ✅ **Modern**: Uses Baileys 7.0.0-rc.9 (actively maintained)
- ✅ **Native message editing**: Edit sent messages directly
- ✅ **Superior media handling**: Images, videos, audio, documents
- ✅ **Session persistence**: Multi-file auth state for reliability
- ✅ **User allowlist**: Security controls for bot mode
- ✅ **Self-chat & bot modes**: Flexible deployment options
- ✅ **QR code pairing**: Simple authentication flow

## Prerequisites

- Node.js 16+ (check: `node --version`)
- npm or yarn package manager

## Installation

Dependencies are automatically installed by DominusPrime setup scripts, but you can also install manually:

```bash
cd scripts/whatsapp-bridge
npm install
```

## Usage

### Quick Start (Pairing Mode)

Pair your WhatsApp account first:

```bash
node bridge.js --pair-only --session ~/.dominusprime/whatsapp/session
```

Scan the QR code with WhatsApp mobile app (Settings → Linked Devices → Link a Device).

### Running the Bridge

Start the bridge server:

```bash
node bridge.js --port 3000 --session ~/.dominusprime/whatsapp/session
```

The bridge will:
1. Load saved session credentials
2. Connect to WhatsApp
3. Start HTTP server on port 3000
4. Poll for incoming messages

### Environment Variables

- `WHATSAPP_MODE`: `self-chat` (default) or `bot`
  - `self-chat`: Send/receive in your own WhatsApp chat
  - `bot`: Separate phone number for bot
- `WHATSAPP_ALLOWED_USERS`: Comma-separated phone numbers (e.g., `19175395595,34652029134`)
  - Use `*` to allow all users
  - Only applies in bot mode
- `WHATSAPP_REPLY_PREFIX`: Custom prefix for bot replies (default: `🤖 *DominusPrime*\n────────────\n`)
- `WHATSAPP_DEBUG`: Set to `1` or `true` for verbose logging

### Command Line Options

- `--port <number>`: HTTP server port (default: 3000)
- `--session <path>`: Session directory path (default: `~/.dominusprime/whatsapp/session`)
- `--mode <mode>`: WhatsApp mode: `self-chat` or `bot`
- `--pair-only`: QR pairing mode (exits after successful pairing)

## HTTP Endpoints

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "connected",
  "queueLength": 0,
  "uptime": 123.45
}
```

### GET /messages
Long-poll for new incoming messages. Returns array of message events.

**Response:**
```json
[
  {
    "messageId": "ABC123",
    "chatId": "1234567890@s.whatsapp.net",
    "senderId": "1234567890@s.whatsapp.net",
    "senderName": "John Doe",
    "chatName": "John Doe",
    "isGroup": false,
    "body": "Hello!",
    "hasMedia": false,
    "mediaType": "",
    "mediaUrls": [],
    "timestamp": 1234567890
  }
]
```

### POST /send
Send a text message.

**Request:**
```json
{
  "chatId": "1234567890@s.whatsapp.net",
  "message": "Hello from DominusPrime!",
  "replyTo": "messageId123" 
}
```

**Response:**
```json
{
  "success": true,
  "messageId": "ABC123"
}
```

### POST /edit
Edit a previously sent message.

**Request:**
```json
{
  "chatId": "1234567890@s.whatsapp.net",
  "messageId": "ABC123",
  "message": "Updated message text"
}
```

**Response:**
```json
{
  "success": true
}
```

### POST /send-media
Send media (image, video, audio, document).

**Request:**
```json
{
  "chatId": "1234567890@s.whatsapp.net",
  "filePath": "/path/to/file.jpg",
  "mediaType": "image",
  "caption": "Check out this image!",
  "fileName": "custom-name.jpg"
}
```

**Response:**
```json
{
  "success": true,
  "messageId": "ABC123"
}
```

### POST /typing
Send typing indicator.

**Request:**
```json
{
  "chatId": "1234567890@s.whatsapp.net"
}
```

### GET /chat/:id
Get chat information.

**Response:**
```json
{
  "name": "John Doe",
  "isGroup": false,
  "participants": []
}
```

## Session Management

Session files are stored in the session directory (default: `~/.dominusprime/whatsapp/session`):

- `creds.json`: Authentication credentials
- `app-state-sync-*.json`: WhatsApp state sync data
- `lid-mapping-*.json`: Phone number ↔ LID mapping files

**Important**: Keep these files secure! They contain your WhatsApp authentication tokens.

## Troubleshooting

### QR Code Not Appearing
- Check `bridge.log` in the session parent directory
- Ensure no firewall is blocking WhatsApp Web connection
- Try deleting session directory and re-pairing

### Connection Drops
- WhatsApp may request restart (code 515) - bridge auto-reconnects
- Check if another instance is using the same session
- Verify internet connectivity

### Message Echo Loops
- In self-chat mode, the bridge filters messages starting with the reply prefix
- Customize `WHATSAPP_REPLY_PREFIX` to match your bot's style

### Port Already in Use
- Kill existing bridge: `fuser -k 3000/tcp` (Linux) or Task Manager (Windows)
- Or use a different port: `--port 3001`

## Security

### User Allowlist (Bot Mode)

Restrict which users can message your bot:

```bash
export WHATSAPP_ALLOWED_USERS="19175395595,34652029134"
node bridge.js
```

The allowlist handles both classic phone numbers and new LID (Linked Identity Device) format transparently.

### Session Lock

Only one bridge instance can use a session at a time. DominusPrime's Python adapter enforces this with a session lock.

## Architecture

```
┌─────────────────┐      HTTP/JSON      ┌──────────────────┐
│                 │◄────────────────────►│                  │
│  Python Adapter │                      │  Node.js Bridge  │
│  (DominusPrime) │                      │  (Baileys)       │
│                 │                      │                  │
└─────────────────┘                      └──────────────────┘
                                                   │
                                                   │ WebSocket
                                                   │ (E2EE)
                                                   ▼
                                         ┌──────────────────┐
                                         │                  │
                                         │  WhatsApp Servers│
                                         │                  │
                                         └──────────────────┘
```

## Comparison: Baileys vs whatsapp-web.js

| Feature | Baileys | whatsapp-web.js |
|---------|---------|-----------------|
| **Maintenance** | ✅ Active | ❌ Deprecated |
| **Message Editing** | ✅ Yes | ❌ No |
| **Media Handling** | ✅ Native | ⚠️ Base64 |
| **Session Format** | ✅ Multi-file | ⚠️ Single file |
| **Connection Stability** | ✅ Excellent | ⚠️ Moderate |
| **Group Support** | ✅ Yes | ✅ Yes |
| **Authentication** | ✅ QR + Pairing | ✅ QR only |

## License

Part of DominusPrime. Baileys library is MIT licensed.

## Credits

- [Baileys](https://github.com/WhiskeySockets/Baileys) by WhiskeySockets
- Bridge pattern adapted from [Hermes Agent](https://github.com/nousresearch/hermes-agent)
