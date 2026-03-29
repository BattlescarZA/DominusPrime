# Quick Build Instructions - DominusPrime 0.9.9 Windows Installer

## 🎯 Goal
Create a Windows installer (.exe) for DominusPrime 0.9.9 with WhatsApp Web integration.

## 📋 Prerequisites Checklist

- [ ] **Python 3.10+** installed and in PATH
- [ ] **Node.js 18+** installed and in PATH
- [ ] **Inno Setup 6** installed (for creating the installer)
- [ ] In project root directory (`d:/quantanova/dominus_prime_ui`)
- [ ] On `0.9.9` branch

## 🚀 Build Command

### Option 1: PowerShell (Recommended)
```powershell
.\scripts\build_windows_installer.ps1
```

### Option 2: Command Prompt
```cmd
scripts\build_windows_installer.bat
```

## 📦 What Gets Built

1. **Frontend** - React console built with Vite
   - Location: `console/dist/`
   - Copied to: `src/dominusprime/console/`

2. **Executable** - PyInstaller packages Python + frontend
   - Location: `dist/DominusPrime/`
   - Main executable: `DominusPrime.exe`
   - Includes: Python runtime, all dependencies, console assets, WhatsApp channel files

3. **Installer** - Inno Setup creates Windows installer
   - Location: `dist/installer/DominusPrime-0.9.9-Setup.exe`
   - Size: ~200-300 MB (includes everything)

## ✅ Verification Steps

After build completes:

```powershell
# Check the installer exists
Test-Path "dist\installer\DominusPrime-0.9.9-Setup.exe"

# Check file size (should be 200-300 MB)
(Get-Item "dist\installer\DominusPrime-0.9.9-Setup.exe").Length / 1MB

# Optional: Test the installer
.\dist\installer\DominusPrime-0.9.9-Setup.exe
```

## 📝 Build Process Details

### Step 1: Install Build Dependencies
```powershell
pip install pyinstaller
```

### Step 2: Build Frontend
```powershell
cd console
npm install
npm run build
cd ..
```

### Step 3: Create Executable
```powershell
pyinstaller scripts\build_windows_exe.spec --clean --noconfirm
```

This bundles:
- Python interpreter
- DominusPrime Python code
- All Python dependencies (AgentScope, FastAPI, etc.)
- React frontend (built static files)
- WhatsApp channel files (bridge.js, package.json, README.md)
- Tokenizer files
- Agent skills and templates
- Icons and assets

### Step 4: Create Installer
```powershell
# Find Inno Setup
$innoPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

# Compile installer
& $innoPath scripts\windows_installer.iss
```

## 🔧 Troubleshooting

### Error: "Python not found"
**Solution**: Install Python 3.10+ and add to PATH

### Error: "npm: command not found"
**Solution**: Install Node.js 18+ and add to PATH

### Error: "PyInstaller build failed"
**Solution**: 
1. Close all DominusPrime windows
2. Run: `pip uninstall dominusprime -y`
3. Run: `pip install -e .`
4. Try build again

### Error: "Inno Setup not found"
**Solution**: Install Inno Setup 6 from https://jrsoftware.org/isdl.php

### Error: "Access denied" or "File in use"
**Solution**: 
1. Stop all running DominusPrime instances
2. Delete `dist/` and `build/` directories
3. Try build again

## 📤 Distribution

Once built, distribute the installer:

```
dist\installer\DominusPrime-0.9.9-Setup.exe
```

### End Users Need:
- ✅ Windows 10/11 (64-bit)
- ✅ Python 3.10+ (checked during installation)
- ⚠️ **Node.js 18+** (only for WhatsApp channel - optional)

### WhatsApp Setup for End Users:
1. Install Node.js 18+
2. Navigate to installation directory
3. Go to `dominusprime\app\channels\whatsapp`
4. Run: `npm install`
5. Start bridge: `node bridge.js`
6. Configure in DominusPrime UI

## 📊 File Sizes (Approximate)

| Component | Size |
|-----------|------|
| Python packages | ~100 MB |
| React frontend | ~5 MB |
| AgentScope | ~50 MB |
| PyInstaller overhead | ~50 MB |
| **Total Installer** | **~200-300 MB** |

## 🎯 Version Information

- **Version**: 0.9.9
- **Branch**: 0.9.9
- **Commit**: `d637a1a` (chore: Prepare version 0.9.9 for release)
- **Build Date**: 2026-03-21
- **New Features**: WhatsApp Web integration with QR code authentication

## 📚 Related Documentation

- [`WINDOWS_INSTALLER_0.9.9.md`](WINDOWS_INSTALLER_0.9.9.md) - Complete user guide
- [`scripts/README_WINDOWS_BUILD.md`](scripts/README_WINDOWS_BUILD.md) - Build system overview
- [`src/dominusprime/app/channels/whatsapp/README.md`](src/dominusprime/app/channels/whatsapp/README.md) - WhatsApp setup guide

## 🔄 Continuous Integration

For automated builds, use this GitHub Actions workflow:

```yaml
name: Build Windows Installer
on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install Inno Setup
        run: choco install innosetup
      
      - name: Build Installer
        run: .\scripts\build_windows_installer.ps1
      
      - name: Upload Artifact
        uses: actions/upload-artifact@v3
        with:
          name: DominusPrime-Installer
          path: dist/installer/DominusPrime-0.9.9-Setup.exe
```

## 🎉 Success!

After successful build, you'll see:

```
========================================
BUILD COMPLETED SUCCESSFULLY!
========================================

The installer has been created at:
dist\installer\DominusPrime-0.9.9-Setup.exe

IMPORTANT: WhatsApp channel requires Node.js!
Users need to install Node.js 18+ to use WhatsApp integration.
```

**The installer is ready for distribution! 🚀**
