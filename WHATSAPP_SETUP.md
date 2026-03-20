# WhatsApp Web Integration Setup Guide

Complete guide to set up WhatsApp Web integration with QR code authentication for DominusPrime.

## Architecture

```
User's Phone (WhatsApp) 
    ↓ [Scan QR Code]
WhatsApp Web (Puppeteer in Node.js)
    ↓ [whatsapp-web.js]
Node.js Bridge Service (port 8765)
    ↓ [HTTP/WebSocket]
Python WhatsAppChannel
    ↓ [AgentScope]
DominusPrime Agent
    ↓ [Response]
WhatsApp User
```

## Prerequisites

- **Node.js** 16+ installed
- **Python** 3.10 installed
- **Chrome/Chromium** (automatically installed by Puppeteer)
- Active WhatsApp account on your phone

## Step 1: Install Node.js Bridge

### 1.1 Navigate to Bridge Directory

```bash
cd src/dominusprime/app/channels/whatsapp
```

### 1.2 Install Dependencies

```bash
npm install
```

This installs:
- `whatsapp-web.js` - WhatsApp Web API
- `express` - HTTP server
- `socket.io` - WebSocket for real-time events
- `qrcode-terminal` - Terminal QR code display

### 1.3 Start the Bridge Service

**Option A: Standalone (Development)**
```bash
npm start
```

**Option B: With Auto-Reload (Development)**
```bash
npm run dev
```

**Option C: As Background Service (Production)**

**Linux/macOS:**
```bash
# Using PM2
npm install -g pm2
pm2 start bridge.js --name whatsapp-bridge
pm2 save
pm2 startup

# Or using systemd (see README.md in whatsapp directory)
```

**Windows:**
```bash
# Using PM2
npm install -g pm2
pm2 start bridge.js --name whatsapp-bridge
pm2 save
```

## Step 2: Install React Frontend Dependencies

```bash
cd console
npm install qrcode.react socket.io-client
npm install
```

## Step 3: Configure DominusPrime

### 3.1 Edit Configuration

Create or edit your config file (e.g., `config.json`):

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

### 3.2 Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | false | Enable WhatsApp channel |
| `bridge_url` | string | http://localhost:8765 | URL of Node.js bridge |
| `session_dir` | string | ~/.dominusprime/whatsapp/session | Session storage |
| `media_dir` | string | ~/.dominusprime/media/whatsapp | Media files storage |
| `show_typing` | boolean | true | Show typing indicator |
| `dm_policy` | string | "open" | DM security policy |
| `group_policy` | string | "open" | Group security policy |
| `allow_from` | array | [] | Allowlist of user IDs |
| `deny_message` | string | "" | Message for blocked users |

## Step 4: Start DominusPrime

```bash
dominusprime app start
```

## Step 5: Authenticate with WhatsApp

### 5.1 Access QR Code

The QR code is available in three places:

1. **Terminal/Console**: Check the logs where the bridge is running
2. **API Endpoint**: `GET http://localhost:8000/whatsapp/qr`
3. **Web UI**: Navigate to the WhatsApp channel settings

### 5.2 Scan QR Code

1. Open WhatsApp on your phone
2. Tap **Menu** (⋮) or **Settings** (⚙️)
3. Tap **Linked Devices**
4. Tap **Link a Device**
5. Point your phone at the QR code on screen

### 5.3 Wait for Authentication

- QR code expires after ~20 seconds
- New QR code will be generated automatically
- Once scanned, authentication is immediate
- Session is saved for future use

## Step 6: Test the Integration

### 6.1 Send Test Message

Send a message to your WhatsApp number (the one you authenticated with):

```
Hello DominusPrime!
```

### 6.2 Expected Behavior

1. Message appears in WhatsApp on your phone
2. DominusPrime receives the message
3. Agent processes and generates response
4. Response is sent back to WhatsApp
5. You receive the response in WhatsApp

## Usage

### React Component

Use the WhatsApp QR code component in your React app:

```typescript
import { WhatsAppQRCode } from './components/WhatsAppQRCode';

function App() {
  return (
    <div>
      <h1>WhatsApp Integration</h1>
      <WhatsAppQRCode
        bridgeUrl="http://localhost:8765"
        onAuthenticated={() => console.log('Authenticated!')}
        onReady={(info) => console.log('Ready:', info)}
        onError={(error) => console.error('Error:', error)}
      />
    </div>
  );
}
```

### API Endpoints

**Bridge Service (port 8765):**

```bash
# Health check
curl http://localhost:8765/health

# Get status
curl http://localhost:8765/status

# Get QR code
curl http://localhost:8765/qr

# Send message
curl -X POST http://localhost:8765/send \
  -H "Content-Type: application/json" \
  -d '{
    "chatId": "1234567890@c.us",
    "message": "Hello from DominusPrime!"
  }'

# Logout
curl -X POST http://localhost:8765/logout

# Restart
curl -X POST http://localhost:8765/restart
```

**DominusPrime API (port 8000):**

```bash
# Get QR code via DominusPrime
curl http://localhost:8000/whatsapp/qr

# Get WhatsApp status
curl http://localhost:8000/whatsapp/status
```

## Troubleshooting

### Bridge Service Won't Start

**Error**: `Cannot find module 'whatsapp-web.js'`

**Solution**:
```bash
cd src/dominusprime/app/channels/whatsapp
npm install
```

### QR Code Not Appearing

1. Check if bridge is running:
   ```bash
   curl http://localhost:8765/health
   ```

2. Check bridge logs for errors

3. Clear session and restart:
   ```bash
   rm -rf ~/.dominusprime/whatsapp/session/*
   # Restart bridge
   ```

### Authentication Keeps Failing

1. Make sure you're scanning with the correct WhatsApp account
2. QR code expires quickly - get a fresh one
3. Clear browser cache (Puppeteer):
   ```bash
   rm -rf ~/.dominusprime/whatsapp/session/*
   ```
4. Try restarting the bridge service

### Messages Not Sending/Receiving

1. Check authentication status:
   ```bash
   curl http://localhost:8765/status
   ```

2. Check Python logs:
   ```bash
   dominusprime app logs
   ```

3. Verify bridge connection in Python:
   ```bash
   # Should show "whatsapp: client ready" in logs
   ```

4. Restart both services:
   ```bash
   # Restart bridge
   pm2 restart whatsapp-bridge
   # Or if running directly: Ctrl+C and npm start
   
   # Restart DominusPrime
   dominusprime app restart
   ```

### High Memory Usage

Puppeteer/Chrome can use significant memory. To reduce:

1. Edit `bridge.js` and add Chrome flags:
   ```javascript
   args: [
       '--no-sandbox',
       '--disable-setuid-sandbox',
       '--disable-dev-shm-usage',
       '--single-process',
       '--disable-features=IsolateOrigins,site-per-process'
   ]
   ```

2. Limit Chrome processes:
   ```bash
   export PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
   ```

3. Consider using a VPS with more RAM (minimum 1GB recommended)

### Port Already in Use

**Error**: `EADDRINUSE: address already in use :::8765`

**Solution**:
```bash
# Find process using port 8765
lsof -i :8765
# Or on Windows
netstat -ano | findstr :8765

# Kill the process
kill -9 <PID>

# Or change port
export WHATSAPP_BRIDGE_PORT=8766
npm start
```

## Security Notes

### Session Files

- Session files in `~/.dominusprime/whatsapp/session` contain authentication tokens
- Keep this directory secure
- Don't commit to git
- Limit file permissions:
  ```bash
  chmod 700 ~/.dominusprime/whatsapp/session
  ```

### Network Security

- Bridge service should only listen on localhost (127.0.0.1)
- Don't expose port 8765 to the internet
- Use firewall to block external access
- For remote access, use SSH tunneling:
  ```bash
  ssh -L 8765:localhost:8765 user@server
  ```

### Allowlist Configuration

For production, use allowlist to restrict access:

```json
{
  "channels": {
    "whatsapp": {
      "dm_policy": "allowlist",
      "group_policy": "allowlist",
      "allow_from": [
        "1234567890@c.us",
        "0987654321@c.us"
      ],
      "deny_message": "Sorry, you are not authorized to use this bot."
    }
  }
}
```

## Advanced Configuration

### Multiple Instances

Run multiple WhatsApp instances with different sessions:

```bash
# Instance 1
WHATSAPP_BRIDGE_PORT=8765 WHATSAPP_SESSION_DIR=~/.dominusprime/wa1 npm start

# Instance 2
WHATSAPP_BRIDGE_PORT=8766 WHATSAPP_SESSION_DIR=~/.dominusprime/wa2 npm start
```

### Custom Chrome Path

```bash
export PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome
npm start
```

### Proxy Configuration

Edit `bridge.js` to add proxy support:

```javascript
puppeteer: {
    headless: true,
    args: [
        '--proxy-server=http://proxy.example.com:8080',
        // ... other args
    ]
}
```

## Monitoring

### Check Status

```bash
# Bridge status
curl http://localhost:8765/status | jq

# DominusPrime status
dominusprime app status
```

### View Logs

```bash
# Bridge logs (if using PM2)
pm2 logs whatsapp-bridge

# DominusPrime logs
dominusprime app logs
```

### Health Monitoring

Set up monitoring with a tool like Uptime Kuma or Prometheus:

```yaml
# Example Prometheus config
- job_name: 'whatsapp-bridge'
  static_configs:
    - targets: ['localhost:8765']
  metrics_path: '/health'
```

## Maintenance

### Backup Session

```bash
# Backup authentication session
tar -czf whatsapp-session-backup.tar.gz ~/.dominusprime/whatsapp/session
```

### Restore Session

```bash
# Restore from backup
tar -xzf whatsapp-session-backup.tar.gz -C ~/
```

### Update Dependencies

```bash
cd src/dominusprime/app/channels/whatsapp
npm update
npm audit fix
```

### Clean Restart

```bash
# Stop bridge
pm2 stop whatsapp-bridge

# Clear everything
rm -rf ~/.dominusprime/whatsapp/session/*
rm -rf node_modules
npm install

# Start fresh
pm2 start whatsapp-bridge
```

## Performance Optimization

### For Low-Resource Systems

1. Use headless mode (already default)
2. Disable unnecessary Chrome features
3. Limit message processing
4. Use message queuing
5. Implement rate limiting

### For High-Traffic Systems

1. Use Redis for session storage
2. Implement message queue (RabbitMQ/Redis)
3. Load balancing with multiple instances
4. Separate media storage (S3/MinIO)
5. Database connection pooling

## Support

- **Documentation**: See `README.md` in `src/dominusprime/app/channels/whatsapp/`
- **GitHub Issues**: Report bugs on GitHub
- **Logs**: Check both bridge and DominusPrime logs
- **Community**: Join Discord/Telegram for support

## License

MIT - See LICENSE file for details
