# Quick Start: Building DominusPrime Windows Installer

## Prerequisites

1. **Python 3.10+** - [Download](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download](https://nodejs.org/)
3. **Inno Setup 6** - [Download](https://jrsoftware.org/isdl.php)

## Build the Installer (Quick)

### PowerShell (Recommended)
```powershell
.\scripts\build_windows_installer.ps1
```

### Command Prompt
```cmd
scripts\build_windows_installer.bat
```

## Output

After successful build:
```
dist\installer\DominusPrime-0.9.9-Setup.exe
```

This is your distributable installer!

## WhatsApp Integration (New in 0.9.9)

The WhatsApp channel requires **Node.js 18+** to be installed separately.

After installing DominusPrime, users need to:
1. Install [Node.js 18+](https://nodejs.org/)
2. Navigate to the WhatsApp bridge directory
3. Run `npm install` to install dependencies
4. Start the bridge service before using WhatsApp channel

See `src/dominusprime/app/channels/whatsapp/README.md` for details.

## What the Installer Does

✅ Creates standard Windows installation
✅ Adds DominusPrime to Start menu
✅ Creates desktop icon (optional)
✅ Includes uninstaller
✅ Auto-launches server and opens browser

## For End Users

1. Download `DominusPrime-0.9.9-Setup.exe`
2. Run the installer
3. Click the desktop icon or find it in Start menu
4. Browser opens automatically to DominusPrime!

**For WhatsApp Integration:**
- Install Node.js 18+ from [nodejs.org](https://nodejs.org/)
- Follow setup instructions in the WhatsApp channel settings

## Need Help?

See [`WINDOWS_INSTALLER.md`](../WINDOWS_INSTALLER.md) for detailed documentation.
