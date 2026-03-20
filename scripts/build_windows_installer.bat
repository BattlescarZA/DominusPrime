@echo off
REM Build DominusPrime Windows Installer
REM This script builds the executable and creates the installer

echo ========================================
echo DominusPrime Windows Installer Builder
echo Version: 0.9.7
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "pyproject.toml" (
    echo ERROR: Please run this script from the project root directory
    pause
    exit /b 1
)

echo Step 1: Installing build dependencies...
echo.
pip install pyinstaller

echo.
echo Step 2: Building frontend (console)...
echo.
cd console
call npm install
call npm run build
cd ..

echo.
echo Step 3: Building executable with PyInstaller...
echo.
echo Current directory: %CD%

REM Check if DominusPrime is running
echo Checking for running DominusPrime processes...
tasklist /FI "IMAGENAME eq dominusprime.exe" 2>NUL | find /I /N "dominusprime.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo WARNING: DominusPrime is currently running. Please close it before building.
    set /p response=Would you like to stop it? (y/n):
    if /i "%response%"=="y" (
        echo Stopping DominusPrime processes...
        taskkill /F /IM dominusprime.exe /T 2>NUL
        timeout /t 2 /nobreak >NUL
    ) else (
        echo Please close DominusPrime manually and run this script again.
        pause
        exit /b 1
    )
)

REM Uninstall existing installation if any
echo Uninstalling any existing DominusPrime installation...
pip uninstall dominusprime -y 2>NUL

REM Install the package in development mode
echo Installing DominusPrime in development mode...
pip install -e .

if %errorlevel% neq 0 (
    echo ERROR: pip install failed
    echo This might be because DominusPrime is still running.
    echo Please close all DominusPrime windows and try again.
    pause
    exit /b 1
)

REM Now run PyInstaller
pyinstaller scripts\build_windows_exe.spec --clean --noconfirm

if %errorlevel% neq 0 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)

echo.
echo Step 4: Creating installer with Inno Setup...
echo.

REM Try to find Inno Setup in common locations
set INNO_PATH=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set INNO_PATH=C:\Program Files\Inno Setup 6\ISCC.exe
) else (
    echo WARNING: Inno Setup not found in default locations
    echo Please install Inno Setup from https://jrsoftware.org/isdl.php
    echo Or manually run: ISCC.exe scripts\windows_installer.iss
    pause
    exit /b 1
)

"%INNO_PATH%" scripts\windows_installer.iss

if %errorlevel% neq 0 (
    echo ERROR: Inno Setup installer creation failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo BUILD COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo The installer has been created at:
echo dist\installer\DominusPrime-0.9.7-Setup.exe
echo.
pause
