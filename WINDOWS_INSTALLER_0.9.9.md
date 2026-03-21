# DominusPrime 0.9.9 Windows Installer Guide

## What's New in 0.9.9

### WhatsApp Web Integration 🎉

DominusPrime now supports full WhatsApp Web functionality with QR code authentication!

**Key Features:**
- ✅ QR code authentication (scan with your phone)
- ✅ Individual and group chat support
- ✅ Media handling (images, videos, audio, documents)
- ✅ Real-time message delivery
- ✅ Typing indicators and read receipts
- ✅ Session persistence (no re-scanning after restart)

**⚠️ IMPORTANT: WhatsApp requires Node.js 18+ to be installed separately**

---

## For Build Engineers

### Building the Installer

#### Prerequisites

1. **Python 3.10+** - [Download](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download](https://nodejs.org/)
3. **Inno Setup 6** - [Download](https://jrsoftware.org/isdl.php)

#### Quick Build

```powershell
# From project root directory:
.\scripts\build_windows_installer.ps1
```

This will:
1. ✅ Build the React frontend (console)
2. ✅ Create Windows executable with PyInstaller
3. ✅ Package everything into an installer with Inno Setup

#### Output

```
dist\installer\DominusPrime-0.9.9-Setup.exe
```

---

## For End Users

### System Requirements

- **Windows 10/11** (64-bit)
- **Python 3.10+** (automatically checked during installation)
- **Node.js 18+** (required ONLY for WhatsApp channel)

### Installation Steps

1. **Download** `DominusPrime-0.9.9-Setup.exe`

2. **Run the installer**
   - Follow the installation wizard
   - Choose installation directory (default: `C:\Program Files\DominusPrime`)
   - Optionally create desktop shortcut

3. **Launch DominusPrime**
   - Double-click desktop icon or find in Start menu
   - Server starts automatically and browser opens to `http://localhost:7788`

### Setting Up WhatsApp (Optional)

If you want to use WhatsApp integration:

#### Step 1: Install Node.js

1. Download Node.js 18+ from [nodejs.org](https://nodejs.org/)
2. Run the installer with default options
3. Verify installation:
   ```cmd
   node --version
   npm --version
   ```

#### Step 2: Install WhatsApp Bridge Dependencies

1. Navigate to the DominusPrime installation directory:
   ```cmd
   cd "C:\Program Files\DominusPrime"
   ```

2. Navigate to WhatsApp channel directory:
   ```cmd
   cd dominusprime\app\channels\whatsapp
   ```

3. Install Node.js dependencies:
   ```cmd
   npm install
   ```

#### Step 3: Start WhatsApp Bridge

Before using WhatsApp in DominusPrime, start the bridge service:

```cmd
node bridge.js
```

Leave this terminal window open. The bridge runs on `http://localhost:8765`.

#### Step 4: Configure WhatsApp in DominusPrime

1. Open DominusPrime web interface (`http://localhost:7788`)
2. Go to **Control** → **Channels**
3. Click **WhatsApp**
4. Fill in the settings:
   - **Bridge URL**: `http://localhost:8765` (default)
   - **Allowed Phone Numbers**: Add your allowed contacts (optional)
   - **Allowed Group IDs**: Add allowed groups (optional)
5. Click **Save**

#### Step 5: Scan QR Code

1. A QR code will appear in the WhatsApp settings panel
2. Open WhatsApp on your phone
3. Go to **Settings** → **Linked Devices** → **Link a Device**
4. Scan the QR code displayed in DominusPrime
5. Wait for authentication to complete

✅ **Done!** Messages sent to your WhatsApp will now be handled by DominusPrime agents.

---

## Using WhatsApp Channel

### Individual Chats

Send a message to your WhatsApp number from any contact. If the contact is in your allowed list (or no restrictions are set), the agent will respond.

### Group Chats

Add your WhatsApp account to a group. The agent will respond to messages in allowed groups.

### Media Support

The agent can receive and process:
- 📷 Images
- 🎥 Videos
- 🎵 Audio files
- 📄 Documents

### Typing Indicators

When the agent is processing a response, WhatsApp will show "typing..." indicator.

---

## Troubleshooting

### WhatsApp Bridge Won't Start

**Error**: `npm: command not found`
- **Solution**: Install Node.js from [nodejs.org](https://nodejs.org/)

**Error**: `Cannot find module 'whatsapp-web.js'`
- **Solution**: Run `npm install` in the WhatsApp channel directory

**Error**: `Port 8765 already in use`
- **Solution**: Another instance is already running, or change the port in `bridge.js`

### QR Code Not Displayed

1. Ensure the bridge service is running (`node bridge.js`)
2. Check that bridge URL is set correctly (`http://localhost:8765`)
3. Refresh the WhatsApp settings page

### WhatsApp Session Expired

1. Stop the bridge service
2. Delete the `.wwebjs_auth` folder in the WhatsApp channel directory
3. Restart the bridge service
4. Scan the QR code again

### Agent Not Responding to WhatsApp Messages

1. Check that the WhatsApp channel is enabled in DominusPrime
2. Verify the contact/group is in your allowed list
3. Check DominusPrime logs for errors
4. Ensure the bridge service is running

---

## Advanced Configuration

### Custom Bridge Port

To use a different port for the WhatsApp bridge:

1. Edit [`bridge.js`](src/dominusprime/app/channels/whatsapp/bridge.js):
   ```javascript
   const PORT = 8765; // Change to your desired port
   ```

2. Update the Bridge URL in WhatsApp channel settings

### Auto-Start Bridge Service

Create a Windows Task Scheduler task to start the bridge automatically:

1. Open Task Scheduler
2. Create new task
3. Set trigger: At system startup
4. Set action: Start a program
   - Program: `node.exe`
   - Arguments: `"C:\Program Files\DominusPrime\dominusprime\app\channels\whatsapp\bridge.js"`
   - Start in: `"C:\Program Files\DominusPrime\dominusprime\app\channels\whatsapp"`

### Session Data Location

WhatsApp authentication data is stored in:
```
C:\Program Files\DominusPrime\dominusprime\app\channels\whatsapp\.wwebjs_auth\
```

This directory persists your WhatsApp session. Keep it secure!

---

## Security Notes

### WhatsApp Authentication

- Your WhatsApp session is stored locally
- Never share your `.wwebjs_auth` folder
- Use allowed phone numbers/groups to restrict access

### Bridge Service Security

The bridge service runs locally on `http://localhost:8765` by default. If you need to expose it:

1. Use HTTPS with proper certificates
2. Implement authentication (API keys)
3. Use a reverse proxy (nginx, Apache)
4. Set firewall rules

**⚠️ Never expose the bridge service to the internet without proper security!**

---

## Uninstallation

### Uninstall DominusPrime

1. Go to **Settings** → **Apps** → **Installed apps**
2. Find **DominusPrime**
3. Click **Uninstall**

OR use the uninstaller in the Start menu:
- **Start Menu** → **DominusPrime** → **Uninstall DominusPrime**

### Clean Up WhatsApp Data

If you want to completely remove WhatsApp session data:

```cmd
del /S /Q "%LOCALAPPDATA%\DominusPrime\.wwebjs_auth"
```

---

## Support & Documentation

- **Full Documentation**: [docs/0.9.8-QUICK_START.md](docs/0.9.8-QUICK_START.md)
- **WhatsApp Setup Guide**: [src/dominusprime/app/channels/whatsapp/README.md](src/dominusprime/app/channels/whatsapp/README.md)
- **Configuration Guide**: [docs/0.9.8-CONFIGURATION_GUIDE.md](docs/0.9.8-CONFIGURATION_GUIDE.md)
- **API Reference**: [docs/0.9.8-API_REFERENCE.md](docs/0.9.8-API_REFERENCE.md)
- **GitHub Issues**: [github.com/quantanova/dominus_prime_ui/issues](https://github.com/quantanova/dominus_prime_ui/issues)

---

## Version History

### 0.9.9 (2026-03-21)
- ✨ **NEW**: WhatsApp Web integration with QR code authentication
- ✨ **NEW**: Node.js bridge service for WhatsApp
- ✨ **NEW**: Real-time message delivery via WebSocket
- ✨ **NEW**: Media handling for WhatsApp messages
- 🔧 **IMPROVED**: Channel configuration UI
- 🔧 **FIXED**: Removed Bot Prefix field from WhatsApp settings

### 0.9.8 (2026-03-20)
- ✨ Experience Distillation & Skill Extraction
- ✨ Multimodal Memory Fusion (images, audio, video)
- ✨ Context-Aware Proactive Delivery
- ✨ Shell Command Execution Security
- ✨ Tool & Skills Permission System

---

## License

DominusPrime is released under the Apache License 2.0.
See [LICENSE](LICENSE) for details.

---

**Enjoy using DominusPrime with WhatsApp! 🎉**
