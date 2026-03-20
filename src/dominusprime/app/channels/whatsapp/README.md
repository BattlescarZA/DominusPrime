# WhatsApp Web Integration

This directory contains the WhatsApp Web bridge service for DominusPrime.

## Architecture

```
┌─────────────────┐         HTTP/WS          ┌──────────────────┐
│  Python         │ <──────────────────────> │  Node.js Bridge  │
│  WhatsAppChannel│                           │  (bridge.js)     │
└─────────────────┘                           └──────────────────┘
                                                       │
                                                       │ whatsapp-web.js
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │  WhatsApp Web    │
                                              │  (Puppeteer)     │
                                              └──────────────────┘
```

## Installation

### 1. Install Node.js Dependencies

```bash
cd src/dominusprime/app/channels/whatsapp
npm install
```

### 2. Start the Bridge Service

#### Option A: Standalone (Recommended for Development)
```bash
npm start
```

#### Option B: As a Service (Production)

**Linux/macOS with systemd:**
```bash
# Create service file
sudo nano /etc/systemd/system/whatsapp-bridge.service
```

```ini
[Unit]
Description=DominusPrime WhatsApp Bridge
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/path/to/src/dominusprime/app/channels/whatsapp
ExecStart=/usr/bin/node bridge.js
Restart=always
Environment=WHATSAPP_BRIDGE_PORT=8765
Environment=WHATSAPP_SESSION_DIR=/home/YOUR_USER/.dominusprime/whatsapp/session

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable whatsapp-bridge
sudo systemctl start whatsapp-bridge
sudo systemctl status whatsapp-bridge
```

**Windows with PM2:**
```bash
npm install -g pm2
pm2 start bridge.js --name whatsapp-bridge
pm2 save
pm2 startup
```

## Configuration

### Environment Variables

- `WHATSAPP_BRIDGE_PORT` - HTTP/WebSocket port (default: 8765)
- `WHATSAPP_SESSION_DIR` - Session storage directory (default: ~/.dominusprime/whatsapp/session)

### Python Configuration

Edit your DominusPrime config:

```json
{
  "channels": {
    "whatsapp": {
      "enabled": true,
      "bridge_url": "http://localhost:8765",
      "session_dir": "~/.dominusprime/whatsapp/session",
      "media_dir": "~/.dominusprime/media/whatsapp",
      "show_typing": true,
      "dm_policy": "open",
      "group_policy": "open"
    }
  }
}
```

## Usage

### 1. Start the Bridge Service
```bash
npm start
```

### 2. Start DominusPrime
```bash
dominusprime app start
```

### 3. Scan QR Code

The QR code will be available at:
- **Console**: Check logs for ASCII QR code
- **API**: `GET http://localhost:8000/whatsapp/qr`
- **Frontend**: Navigate to WhatsApp channel settings in the web UI

### 4. Chat!

Once authenticated, send messages to your WhatsApp number and the agent will respond.

## API Endpoints

### Bridge Service (Port 8765)

- `GET /health` - Health check
- `GET /status` - Connection status
- `GET /qr` - Get QR code for authentication
- `POST /send` - Send message
- `GET /chat/:chatId` - Get chat information
- `POST /typing/:chatId` - Set typing indicator
- `POST /logout` - Logout and clear session
- `POST /restart` - Restart client

### WebSocket Events

**Client → Server:**
- (none currently)

**Server → Client:**
- `qr` - QR code generated
- `authenticated` - Authentication successful
- `auth_failure` - Authentication failed
- `ready` - Client ready
- `message` - Incoming message
- `message_sent` - Outgoing message sent
- `disconnected` - Client disconnected
- `status` - Status update

## Troubleshooting

### QR Code Not Appearing

1. Check if bridge service is running:
   ```bash
   curl http://localhost:8765/health
   ```

2. Check logs:
   ```bash
   # If using systemd
   sudo journalctl -u whatsapp-bridge -f
   
   # If running directly
   # Check terminal output
   ```

3. Clear session and restart:
   ```bash
   rm -rf ~/.dominusprime/whatsapp/session/*
   npm start
   ```

### Authentication Fails

1. Make sure you're scanning with the correct WhatsApp account
2. QR code expires after ~20 seconds - get a fresh one
3. Clear browser cache in Puppeteer:
   ```bash
   rm -rf ~/.dominusprime/whatsapp/session/*
   ```

### Messages Not Sending/Receiving

1. Check if authenticated:
   ```bash
   curl http://localhost:8765/status
   ```

2. Check Python logs:
   ```bash
   dominusprime app logs
   ```

3. Restart bridge service

### High Memory Usage

Puppeteer can use significant memory. To reduce:

1. Edit `bridge.js` and add more Chrome flags:
   ```javascript
   args: [
       '--no-sandbox',
       '--disable-setuid-sandbox',
       '--disable-dev-shm-usage',
       '--disable-accelerated-2d-canvas',
       '--no-first-run',
       '--no-zygote',
       '--disable-gpu',
       '--single-process',  // Add this
       '--disable-features=IsolateOrigins,site-per-process'  // Add this
   ]
   ```

2. Restart the bridge service

## Security Notes

1. **Session Files**: Keep `session_dir` secure - it contains authentication tokens
2. **Network**: Bridge service should only be accessible locally (127.0.0.1)
3. **Firewall**: Don't expose port 8765 to the internet
4. **Permissions**: Limit file permissions on session directory:
   ```bash
   chmod 700 ~/.dominusprime/whatsapp/session
   ```

## Development

### Run with Auto-Reload
```bash
npm run dev
```

### Debug Mode

Set Node.js debug environment:
```bash
DEBUG=* npm start
```

### Test Endpoints

```bash
# Status
curl http://localhost:8765/status

# QR Code
curl http://localhost:8765/qr

# Send test message (after authentication)
curl -X POST http://localhost:8765/send \
  -H "Content-Type: application/json" \
  -d '{
    "chatId": "1234567890@c.us",
    "message": "Hello from DominusPrime!"
  }'
```

## Dependencies

- **whatsapp-web.js**: WhatsApp Web API client
- **express**: HTTP server
- **socket.io**: WebSocket support
- **qrcode-terminal**: QR code in terminal (optional)

## License

MIT
