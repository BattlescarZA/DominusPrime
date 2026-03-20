#!/usr/bin/env pwsh
# Build DominusPrime Windows Installer
# This script builds the executable and creates the installer

Write-Host "========================================"
Write-Host "DominusPrime Windows Installer Builder"
Write-Host "Version: 0.9.7"
Write-Host "========================================"
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version
    Write-Host "Found: $pythonVersion"
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.10+ from python.org"
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "ERROR: Please run this script from the project root directory" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Step 1: Installing build dependencies..." -ForegroundColor Cyan
Write-Host ""
pip install pyinstaller

Write-Host ""
Write-Host "Step 2: Building frontend (console)..." -ForegroundColor Cyan
Write-Host ""
Push-Location console
npm install
npm run build
Pop-Location

Write-Host ""
Write-Host "Step 3: Building executable with PyInstaller..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Gray

# Check if DominusPrime is running
Write-Host "Checking for running DominusPrime processes..." -ForegroundColor Gray
$dominusProcesses = Get-Process -Name "dominusprime" -ErrorAction SilentlyContinue
if ($dominusProcesses) {
    Write-Host "WARNING: DominusPrime is currently running. Please close it before building." -ForegroundColor Yellow
    Write-Host "Found processes:" -ForegroundColor Yellow
    $dominusProcesses | ForEach-Object { Write-Host "  - PID: $($_.Id)" -ForegroundColor Yellow }
    $response = Read-Host "Would you like to stop these processes? (y/n)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        $dominusProcesses | Stop-Process -Force
        Write-Host "Processes stopped. Waiting 2 seconds..." -ForegroundColor Green
        Start-Sleep -Seconds 2
    } else {
        Write-Host "Please close DominusPrime manually and run this script again." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Uninstall existing installation if any
Write-Host "Uninstalling any existing DominusPrime installation..." -ForegroundColor Gray
pip uninstall dominusprime -y 2>$null

# Install the package in development mode
Write-Host "Installing DominusPrime in development mode..." -ForegroundColor Gray
pip install -e .

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: pip install failed" -ForegroundColor Red
    Write-Host "This might be because DominusPrime is still running." -ForegroundColor Red
    Write-Host "Please close all DominusPrime windows and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Now run PyInstaller
pyinstaller scripts\build_windows_exe.spec --clean --noconfirm

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: PyInstaller build failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Step 4: Creating installer with Inno Setup..." -ForegroundColor Cyan
Write-Host ""

# Try to find Inno Setup in common locations
$innoPath = $null
$possiblePaths = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $innoPath = $path
        break
    }
}

if (-not $innoPath) {
    Write-Host "WARNING: Inno Setup not found in default locations" -ForegroundColor Yellow
    Write-Host "Please install Inno Setup from https://jrsoftware.org/isdl.php"
    Write-Host "Or manually run: ISCC.exe scripts\windows_installer.iss"
    Read-Host "Press Enter to exit"
    exit 1
}

& $innoPath scripts\windows_installer.iss

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Inno Setup installer creation failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================"
Write-Host "BUILD COMPLETED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "========================================"
Write-Host ""
Write-Host "The installer has been created at:"
Write-Host "dist\installer\DominusPrime-0.9.7-Setup.exe" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"
