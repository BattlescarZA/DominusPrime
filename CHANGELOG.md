# Changelog

All notable changes to this project will be documented in this file.

## [0.9.7] - 2026-03-14

### Added

- **Windows Installer Support**: Complete Windows installer (.exe) solution for easy deployment
  - One-click Windows installer using Inno Setup
  - Automatic server launch and browser opening
  - Desktop icon and Start menu integration
  - Professional uninstaller
  
- **New Files**:
  - [`scripts/windows_launcher.py`](scripts/windows_launcher.py) - Launcher script that starts server and opens browser
  - [`scripts/build_windows_exe.spec`](scripts/build_windows_exe.spec) - PyInstaller configuration
  - [`scripts/windows_installer.iss`](scripts/windows_installer.iss) - Inno Setup installer script
  - [`scripts/build_windows_installer.bat`](scripts/build_windows_installer.bat) - Build script for Command Prompt
  - [`scripts/build_windows_installer.ps1`](scripts/build_windows_installer.ps1) - Build script for PowerShell
  - [`WINDOWS_INSTALLER.md`](WINDOWS_INSTALLER.md) - Complete documentation for the Windows installer
  - [`scripts/README_WINDOWS_BUILD.md`](scripts/README_WINDOWS_BUILD.md) - Quick start guide

### Changed

- Updated version from 0.9.6 to 0.9.7
- Enhanced [`README.md`](README.md) with Windows installer section

### Features

- Windows users can now install DominusPrime with a standard .exe installer
- Desktop shortcut automatically launches server and opens browser
- No manual command-line interaction required for end users
- Professional Windows application experience

## [0.9.6] - Previous Release

(Previous changelog entries...)
