# WhatsApp Channel

WhatsApp channel integration for DominusPrime using QR code authentication (like WhatsApp Web).

## Features

- **QR Code Authentication**: Scan QR code with your WhatsApp mobile app to authenticate
- **Send/Receive Messages**: Full text message support
- **Media Support**: Send and receive images, videos, audio, and documents
- **Group Chat Support**: Works in both individual and group chats
- **Typing Indicators**: Shows typing status while agent is processing
- **Security Policies**: Allowlist support for controlling who can interact with the agent
- **Session Persistence**: Authentication persists across restarts

## Requirements

### Python Dependencies

```bash
pip install whatsapp-web.py  # Python bridge to whatsapp-web.js
pip install qrcode[pil]      # Optional: for QR code image generation
```

### Node.js Dependencies

WhatsApp channel requires Node.js and the following npm packages:

```bash
npm install whatsapp-web.js
npm install puppeteer
```

**Note**: `whatsapp-web.js` uses Puppeteer to automate a headless Chrome/Chromium browser that connects to WhatsApp Web.

## Configuration

Add to your `config.json`:

```json
{
  "channels": {
    "whatsapp": {
      "enabled": true,
      "session_dir": "~/.dominusprime/whatsapp/session",
      "media_dir": "~/.dominusprime/media/whatsapp",
      "show_typing": true,
      "dm_policy": "open",
      "group_policy": "open",
      "allow_from": [],
      "deny_message": "Sorry, you are not authorized to use this bot.",
      "max_retries": 3,
      "retry_delay": 5
    }
  }
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable/disable WhatsApp channel |
| `session_dir` | string | `~/.dominusprime/whatsapp/session` | Directory to store session data (authentication) |
| `media_dir` | string | `~/.dominusprime/media/whatsapp` | Directory to store received media files |
| `show_typing` | boolean | `null` | Show typing indicator while processing |
| `dm_policy` | string | `"open"` | Direct message policy: `"open"` or `"allowlist"` |
| `group_policy` | string | `"open"` | Group message policy: `"open"` or `"allowlist"` |
| `allow_from` | array | `[]` | List of allowed sender IDs (when policy is `"allowlist"`) |
| `deny_message` | string | `""` | Message shown to unauthorized users |
| `max_retries` | integer | `3` | Maximum connection retry attempts |
| `retry_delay` | integer | `5` | Delay between retries (seconds) |

## Usage

### First-Time Setup

1. **Install Dependencies**:
   ```bash
   pip install whatsapp-web.py qrcode[pil]
   npm install whatsapp-web.js puppeteer
   ```

2. **Configure WhatsApp Channel**: Add configuration to `config.json` (see above)

3. **Start DominusPrime**:
   ```bash
   dominusprime app
   ```

4. **Scan QR Code**: 
   - A QR code will be displayed in the console
   - QR code is also saved to `~/.dominusprime/whatsapp/session/qr_code.png`
   - Open WhatsApp on your mobile device
   - Go to Settings → Linked Devices → Link a Device
   - Scan the QR code displayed in the console

5. **Start Chatting**: Once authenticated, send a message to your WhatsApp number and the agent will respond!

### Subsequent Runs

After the first authentication, the session is saved. Simply start DominusPrime and it will automatically reconnect using the saved session - no need to scan QR code again.

## Security

### Allowlist Mode

To restrict access to specific users or groups:

```json
{
  "channels": {
    "whatsapp": {
      "enabled": true,
      "dm_policy": "allowlist",
      "group_policy": "allowlist",
      "allow_from": [
        "1234567890@c.us",
        "987654321@c.us"
      ],
      "deny_message": "Sorry, you are not authorized to use this bot."
    }
  }
}
```

**Getting Sender IDs**: Sender IDs are logged when messages are received. Check your logs to find the IDs you want to allowlist.

### Open Mode

Default mode - accepts messages from everyone:

```json
{
  "channels": {
    "whatsapp": {
      "enabled": true,
      "dm_policy": "open",
      "group_policy": "open"
    }
  }
}
```

## Media Handling

### Receiving Media

The agent automatically:
- Downloads received media files to `media_dir`
- Processes images, videos, audio, and documents
- Includes media content in the agent's context

### Sending Media

The agent can send media files in responses. Media is sent as:
- Images: `.jpg`, `.png`, etc.
- Videos: `.mp4`, `.avi`, etc.
- Audio: `.ogg`, `.mp3`, etc. (voice messages)
- Documents: `.pdf`, `.docx`, etc.

## Group Chats

WhatsApp channel works in both individual and group chats:

- **Individual Chats**: Direct 1:1 conversations
- **Group Chats**: Agent responds to messages in WhatsApp groups
- **Privacy**: Use `group_policy: "allowlist"` to control which groups can use the agent

## Troubleshooting

### QR Code Not Displaying

- Check that `qrcode` package is installed: `pip install qrcode[pil]`
- QR code is also saved to `session_dir/qr_code.png`
- You can manually view this image to scan

### Authentication Failures

- Delete the session directory and try again:
  ```bash
  rm -rf ~/.dominusprime/whatsapp/session
  ```
- Ensure WhatsApp Web is not open in your browser (only one session allowed)

### Connection Issues

- Check that Node.js and npm packages are installed correctly
- Verify Puppeteer can launch Chrome/Chromium:
  ```bash
  node -e "require('puppeteer').launch().then(b => b.close())"
  ```
- Check firewall/network settings

### Media Not Downloading

- Ensure `media_dir` is writable
- Check available disk space
- Verify network connection

## Architecture

The WhatsApp channel:
1. Uses `whatsapp-web.js` (Node.js library) via Python bridge
2. Connects to WhatsApp Web using Puppeteer (headless Chrome)
3. Authenticates via QR code (first time) or saved session
4. Receives messages via event handlers
5. Sends responses back through the WhatsApp Web API

## Limitations

- **Single Session**: Only one WhatsApp Web session per phone number
- **Phone Required**: Must have WhatsApp installed on a mobile device
- **Internet Required**: Both mobile device and DominusPrime must be online
- **Rate Limits**: WhatsApp may rate limit if too many messages are sent quickly

## Support

For issues, questions, or contributions, please visit the DominusPrime repository.

## License

Part of DominusPrime - see main LICENSE file.
