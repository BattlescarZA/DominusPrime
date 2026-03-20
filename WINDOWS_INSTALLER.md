# DominusPrime Windows Installer Guide

This guide explains how to build and use the Windows installer for DominusPrime.

## Overview

The Windows installer provides an easy way for Windows users to install and run DominusPrime:

- **One-click installation**: Standard Windows installer experience
- **Desktop icon**: Creates a desktop shortcut for easy access
- **Auto-launch**: Opens the browser automatically when started
- **Start menu integration**: Adds DominusPrime to the Start menu

## For End Users

### Installing DominusPrime

1. Download `DominusPrime-0.9.7-Setup.exe`
2. Double-click the installer
3. Follow the installation wizard
4. Optionally check "Create a desktop icon"
5. Click "Install"

### Running DominusPrime

After installation, you can run DominusPrime by:

1. **Desktop Icon**: Double-click the DominusPrime icon on your desktop
2. **Start Menu**: Search for "DominusPrime" in the Windows Start menu

When you launch DominusPrime:
- A console window will open showing the server logs
- Your default browser will automatically open to `http://127.0.0.1:9999`
- The DominusPrime console interface will be ready to use

### Uninstalling

1. Go to Windows Settings → Apps → Installed apps
2. Find "DominusPrime" in the list
3. Click the three dots and select "Uninstall"
4. Or use the Start menu shortcut "Uninstall DominusPrime"

## For Developers

### Prerequisites

To build the Windows installer, you need:

1. **Python 3.10+**: Install from [python.org](https://www.python.org/downloads/)
2. **Node.js 18+**: Install from [nodejs.org](https://nodejs.org/)
3. **PyInstaller**: Will be installed by the build script
4. **Inno Setup 6**: Download from [jrsoftware.org](https://jrsoftware.org/isdl.php)

### Building the Installer

#### Option 1: Using PowerShell (Recommended)

```powershell
# From the project root directory
.\scripts\build_windows_installer.ps1
```

#### Option 2: Using Command Prompt

```cmd
REM From the project root directory
scripts\build_windows_installer.bat
```

#### Manual Build Steps

If you prefer to build manually:

```powershell
# 1. Install PyInstaller
pip install pyinstaller

# 2. Build the frontend
cd console
npm install
npm run build
cd ..

# 3. Build the executable
pyinstaller scripts\build_windows_exe.spec --clean

# 4. Create the installer (requires Inno Setup)
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" scripts\windows_installer.iss
```

### Output

The build process creates:

- **Executable**: `dist/DominusPrime/DominusPrime.exe`
- **Installer**: `dist/installer/DominusPrime-0.9.7-Setup.exe`

The installer includes all necessary files and dependencies.

## Architecture

### Components

1. **[`scripts/windows_launcher.py`](scripts/windows_launcher.py:1)**: Python launcher script that:
   - Checks if the server is already running
   - Starts the DominusPrime FastAPI server
   - Opens the browser automatically
   - Provides user-friendly error messages

2. **[`scripts/build_windows_exe.spec`](scripts/build_windows_exe.spec:1)**: PyInstaller specification that:
   - Bundles Python code and dependencies
   - Includes all static assets (console, icons, etc.)
   - Creates a standalone executable

3. **[`scripts/windows_installer.iss`](scripts/windows_installer.iss:1)**: Inno Setup script that:
   - Creates a professional Windows installer
   - Adds Start menu shortcuts
   - Adds desktop icon (optional)
   - Includes uninstaller
   - Checks for Python installation

### How It Works

1. User runs the installer
2. Installer extracts files to `Program Files\DominusPrime`
3. Creates shortcuts in Start menu and optionally desktop
4. User clicks icon to launch
5. [`windows_launcher.py`](scripts/windows_launcher.py:1) starts the server
6. Browser opens automatically to the console
7. User interacts with DominusPrime through the web interface

## Configuration

### Changing Host/Port

To modify the default host or port, edit [`scripts/windows_launcher.py`](scripts/windows_launcher.py:1):

```python
def main() -> None:
    """Main launcher function."""
    host = "127.0.0.1"  # Change this
    port = 9999          # Change this
    # ... rest of code
```

Then rebuild the installer.

### Custom Icon

To use a custom icon:

1. Replace [`console/public/favicon.ico`](console/public/favicon.ico:1) with your icon
2. Rebuild the installer

The icon is automatically included in both the executable and installer.

## Troubleshooting

### Build Issues

**PyInstaller fails:**
```powershell
# Ensure all dependencies are installed
pip install -r requirements.txt
pip install pyinstaller

# Clean and rebuild
pyinstaller scripts\build_windows_exe.spec --clean
```

**Frontend build fails:**
```powershell
# Clean and rebuild frontend
cd console
rm -r -fo node_modules
rm package-lock.json
npm install
npm run build
cd ..
```

**Inno Setup not found:**
- Install from [jrsoftware.org](https://jrsoftware.org/isdl.php)
- Or manually run: `ISCC.exe scripts\windows_installer.iss`

### Runtime Issues

**Port already in use:**
- The launcher detects this and just opens the browser
- Or close the existing instance first

**Browser doesn't open:**
- Manually navigate to `http://127.0.0.1:9999`
- Check firewall settings

**Python not found:**
- The installer checks for Python during installation
- Install Python 3.10+ from [python.org](https://www.python.org/)

## Distribution

### Sharing the Installer

The generated installer is completely self-contained and can be distributed:

1. Upload `DominusPrime-0.9.7-Setup.exe` to your distribution platform
2. Users download and run the installer
3. No additional setup required (except Python runtime)

### File Size

The installer size depends on included dependencies:
- Base application: ~50-100 MB
- With all dependencies: ~200-300 MB

### Code Signing (Optional)

For production distribution, consider code signing:

```powershell
# Sign the executable (requires certificate)
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com DominusPrime.exe

# Sign the installer
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com DominusPrime-0.9.7-Setup.exe
```

## Version Management

When releasing a new version:

1. Update [`src/dominusprime/__version__.py`](src/dominusprime/__version__.py:2)
2. Update version in [`scripts/windows_installer.iss`](scripts/windows_installer.iss:6)
3. Update version in [`scripts/build_windows_installer.bat`](scripts/build_windows_installer.bat:5)
4. Update version in [`scripts/build_windows_installer.ps1`](scripts/build_windows_installer.ps1:5)
5. Rebuild the installer

## License

This installer configuration is part of DominusPrime and follows the same license as the main project.
