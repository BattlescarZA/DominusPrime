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
dist\installer\DominusPrime-0.9.7-Setup.exe
```

This is your distributable installer!

## What the Installer Does

✅ Creates standard Windows installation
✅ Adds DominusPrime to Start menu
✅ Creates desktop icon (optional)
✅ Includes uninstaller
✅ Auto-launches server and opens browser

## For End Users

1. Download `DominusPrime-0.9.7-Setup.exe`
2. Run the installer
3. Click the desktop icon or find it in Start menu
4. Browser opens automatically to DominusPrime!

## Need Help?

See [`WINDOWS_INSTALLER.md`](../WINDOWS_INSTALLER.md) for detailed documentation.
