# DominusPrime Installer for Windows (self-contained: includes uv download via GitHub)
# Usage: irm <url>/install.ps1 | iex
#    or: .\install.ps1 [-Version X.Y.Z] [-FromSource] [-SourceDir DIR]
#                            [-Extras "llamacpp,mlx"] [-UvPath PATH]
#
# Installs DominusPrime into ~/.dominusprime with a uv-managed Python environment.
# Users do NOT need Python pre-installed — uv handles everything.
#
# uv is obtained automatically (no action required from the user):
#   1. Already on PATH or in common locations
#   2. Downloaded via https://astral.sh/uv/install.ps1
#   3. Downloaded via GitHub Releases if astral.sh is unreachable (e.g. in China)
#
# The entire script is wrapped in & { ... } @args so that `irm | iex` works
# correctly (param() is only valid inside a scriptblock/function/file scope).

& {
param(
    [string]$Version   = "",
    [string]$SourceDir = "",
    [string]$Extras    = "",
    [string]$UvPath    = "",
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# ── Defaults ──────────────────────────────────────────────────────────────────
$DominusPrimeHome     = if ($env:DOMINUSPRIME_HOME) { $env:DOMINUSPRIME_HOME } else { Join-Path $HOME ".dominusprime" }
$DominusPrimeVenv     = Join-Path $DominusPrimeHome "venv"
$DominusPrimeBin      = Join-Path $DominusPrimeHome "bin"
$PythonVersion = "3.12"
$DominusPrimeRepo     = "https://github.com/BattlescarZA/DominusPrime.git"

# ── Colors ────────────────────────────────────────────────────────────────────
function Write-Info { param([string]$Message) Write-Host "[dominusprime] " -ForegroundColor Green  -NoNewline; Write-Host $Message }
function Write-Warn { param([string]$Message) Write-Host "[dominusprime] " -ForegroundColor Yellow -NoNewline; Write-Host $Message }
function Write-Err  { param([string]$Message) Write-Host "[dominusprime] " -ForegroundColor Red    -NoNewline; Write-Host $Message }
function Stop-WithError { param([string]$Message) Write-Err $Message; exit 1 }

# ── Help ──────────────────────────────────────────────────────────────────────
if ($Help) {
    @"
DominusPrime Installer for Windows

Usage: .\install.ps1 [OPTIONS]

Options:
  -Version <VER>        Install a specific version/tag from GitHub (e.g. v0.9.6)
  -SourceDir <DIR>      Install from local source directory instead of GitHub
  -Extras <EXTRAS>      Comma-separated optional extras to install
                        (e.g. llamacpp, mlx, llamacpp,mlx)
  -UvPath <PATH>        Path to a pre-installed uv.exe (skips all auto-install)
  -Help                 Show this help

Environment:
  DOMINUSPRIME_HOME     Installation directory (default: ~/.dominusprime)

Note: This installer always installs from source (GitHub or local directory).
"@
    exit 0
}

Write-Host "[dominusprime] " -ForegroundColor Green -NoNewline
Write-Host "Installing DominusPrime into " -NoNewline
Write-Host "$DominusPrimeHome" -ForegroundColor White

# ── Execution Policy Check ────────────────────────────────────────────────────
$policy = Get-ExecutionPolicy
if ($policy -eq "Restricted") {
    Write-Info "Execution policy is 'Restricted', setting to RemoteSigned for current user..."
    try {
        Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
        Write-Info "Execution policy updated to RemoteSigned"
    } catch {
        Write-Err "PowerShell execution policy is set to 'Restricted' which prevents script execution."
        Write-Err "Please run the following command and retry:"
        Write-Err ""
        Write-Err "  Set-ExecutionPolicy RemoteSigned -Scope CurrentUser"
        Write-Err ""
        exit 1
    }
}

# ── Step 1: Ensure uv is available ───────────────────────────────────────────

function Invoke-UvFromGitHub {
    # Downloads uv from GitHub Releases and prepends its directory to PATH.
    # Used automatically when astral.sh is unreachable (e.g. in China).
    $arch = if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "aarch64" } else { "x86_64" }
    $url  = "https://github.com/astral-sh/uv/releases/latest/download/uv-$arch-pc-windows-msvc.zip"
    $dest = Join-Path $env:LOCALAPPDATA "uv"
    $zip  = Join-Path $env:TEMP "uv-gh-$([System.IO.Path]::GetRandomFileName()).zip"

    Write-Info "Downloading uv ($arch) from GitHub Releases..."
    $ProgressPreference = 'SilentlyContinue'   # prevents 100x slowdown in PS 5.1
    try {
        Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
    } catch {
        throw "GitHub download failed: $_"
    }

    if (-not (Test-Path $dest)) { New-Item -ItemType Directory -Path $dest -Force | Out-Null }

    Write-Info "Extracting uv..."
    try {
        Expand-Archive -Force -Path $zip -DestinationPath $dest
    } catch {
        Remove-Item $zip -ErrorAction SilentlyContinue
        throw "Extraction failed: $_"
    }
    Remove-Item $zip -ErrorAction SilentlyContinue

    $uvExe = Join-Path $dest "uv.exe"
    if (-not (Test-Path $uvExe)) { throw "uv.exe not found after extraction at $dest" }

    $env:PATH = "$dest;$env:PATH"
    Write-Info "uv installed from GitHub: $uvExe"
}

function Ensure-Uv {
    # 0. User-supplied path (-UvPath)
    if ($UvPath) {
        if (-not (Test-Path $UvPath)) { Stop-WithError "Specified uv not found: $UvPath" }
        $env:PATH = "$(Split-Path $UvPath -Parent);$env:PATH"
        Write-Info "uv found: $UvPath"
        return
    }

    # 1. Already on PATH
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        Write-Info "uv found: $((Get-Command uv).Source)"
        return
    }

    # 2. Common install locations not yet on PATH
    $candidates = @(
        (Join-Path $HOME ".local\bin\uv.exe"),
        (Join-Path $HOME ".cargo\bin\uv.exe"),
        (Join-Path $env:LOCALAPPDATA "uv\uv.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            $env:PATH = "$(Split-Path $candidate -Parent);$env:PATH"
            Write-Info "uv found: $candidate"
            return
        }
    }

    # 3. Try astral.sh (standard installer, fast outside China)
    Write-Warn "If automatic uv installation fails, please manually install uv first by following https://github.com/astral-sh/uv/releases, then re-run this installer."
    Write-Warn "Alternatively, if Python is already installed, run: python -m pip install -U uv"
    Write-Info "Installing uv via astral.sh..."
    $astralOk = $false
    try {
        $installScript = Invoke-RestMethod https://astral.sh/uv/install.ps1 -TimeoutSec 15
        Invoke-Expression $installScript
        $astralOk = $true
    } catch {
        Write-Warn "astral.sh unreachable, falling back to GitHub Releases..."
    }

    if ($astralOk) {
        # Refresh PATH after astral.sh install
        $uvPaths = @(
            (Join-Path $HOME ".local\bin"),
            (Join-Path $HOME ".cargo\bin"),
            (Join-Path $env:LOCALAPPDATA "uv")
        )
        foreach ($p in $uvPaths) {
            if ((Test-Path $p) -and ($env:PATH -notlike "*$p*")) {
                $env:PATH = "$p;$env:PATH"
            }
        }
        if (Get-Command uv -ErrorAction SilentlyContinue) {
            Write-Info "uv installed via astral.sh"
            return
        }
        Write-Warn "astral.sh install succeeded but uv not found on PATH, trying GitHub Releases..."
    }

    # 4. GitHub Releases fallback (works in China)
    try {
        Invoke-UvFromGitHub
    } catch {
        Stop-WithError "Failed to install uv automatically: $_`nPlease install uv manually: https://docs.astral.sh/uv/"
    }
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Stop-WithError "Failed to install uv. Please install it manually: https://docs.astral.sh/uv/"
    }
}

Ensure-Uv

# ── Step 2: Create / update virtual environment ──────────────────────────────
if (Test-Path $DominusPrimeVenv) {
    Write-Info "Existing environment found, upgrading..."
} else {
    Write-Info "Creating Python $PythonVersion environment..."
}

uv venv $DominusPrimeVenv --python $PythonVersion --quiet --clear
if ($LASTEXITCODE -ne 0) { Stop-WithError "Failed to create virtual environment" }

$VenvPython = Join-Path $DominusPrimeVenv "Scripts\python.exe"
if (-not (Test-Path $VenvPython)) { Stop-WithError "Failed to create virtual environment" }

$pyVersion = & $VenvPython --version 2>&1
Write-Info "Python environment ready ($pyVersion)"

# ── Step 3: Install DominusPrime ─────────────────────────────────────────────
$ExtrasSuffix = ""
if ($Extras) { $ExtrasSuffix = "[$Extras]" }

$script:ConsoleCopied   = $false
$script:ConsoleAvailable = $false

function Prepare-Console {
    param([string]$RepoDir)

    $consoleSrc  = Join-Path $RepoDir "console\dist"
    $consoleDest = Join-Path $RepoDir "src\dominusprime\console"

    # Already populated
    if (Test-Path (Join-Path $consoleDest "index.html")) { $script:ConsoleAvailable = $true; return }

    # Copy pre-built assets if available
    if ((Test-Path $consoleSrc) -and (Test-Path (Join-Path $consoleSrc "index.html"))) {
        Write-Info "Copying console frontend assets..."
        New-Item -ItemType Directory -Path $consoleDest -Force | Out-Null
        Copy-Item -Path "$consoleSrc\*" -Destination $consoleDest -Recurse -Force
        $script:ConsoleCopied   = $true
        $script:ConsoleAvailable = $true
        return
    }

    # Try to build if npm is available
    $packageJson = Join-Path $RepoDir "console\package.json"
    if (-not (Test-Path $packageJson)) {
        Write-Warn "Console source not found - the web UI won't be available."
        return
    }

    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        Write-Warn "npm not found - skipping console frontend build."
        Write-Warn "Install Node.js from https://nodejs.org/ then re-run this installer,"
        Write-Warn "or run 'cd console && npm ci && npm run build' manually."
        return
    }

    Write-Info "Building console frontend (npm ci && npm run build)..."
    Push-Location (Join-Path $RepoDir "console")
    try {
        npm ci
        if ($LASTEXITCODE -ne 0) { Write-Warn "npm ci failed - the web UI won't be available."; return }
        npm run build
        if ($LASTEXITCODE -ne 0) { Write-Warn "npm run build failed - the web UI won't be available."; return }
    } finally {
        Pop-Location
    }
    if (Test-Path (Join-Path $consoleSrc "index.html")) {
        New-Item -ItemType Directory -Path $consoleDest -Force | Out-Null
        Copy-Item -Path "$consoleSrc\*" -Destination $consoleDest -Recurse -Force
        $script:ConsoleCopied   = $true
        $script:ConsoleAvailable = $true
        Write-Info "Console frontend built successfully"
        return
    }

    Write-Warn "Console build completed but index.html not found - the web UI won't be available."
}

function Cleanup-Console {
    param([string]$RepoDir)
    if ($script:ConsoleCopied) {
        $consoleDest = Join-Path $RepoDir "src\dominusprime\console"
        if (Test-Path $consoleDest) {
            Remove-Item -Path "$consoleDest\*" -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

$VenvDominusPrime = Join-Path $DominusPrimeVenv "Scripts\dominusprime.exe"

# Always install from source (local directory or GitHub clone)
if ($SourceDir) {
    $SourceDir = (Resolve-Path $SourceDir).Path
    Write-Info "Installing DominusPrime from local source: $SourceDir"
    Prepare-Console $SourceDir
    Write-Info "Installing package from source..."
    uv pip install "${SourceDir}${ExtrasSuffix}" --python $VenvPython --prerelease=allow
    if ($LASTEXITCODE -ne 0) { Stop-WithError "Installation from source failed" }
    Cleanup-Console $SourceDir
} else {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Stop-WithError "git is required to install DominusPrime. Please install Git from https://git-scm.com/ or pass a local path: .\install.ps1 -SourceDir C:\path\to\DominusPrime"
    }
    Write-Info "Installing DominusPrime from source (GitHub)..."
    $cloneDir = Join-Path $env:TEMP "dominusprime-install-$(Get-Random)"
    try {
        # Clone specific version if provided, otherwise latest
        if ($Version) {
            Write-Info "Cloning version $Version..."
            git clone --depth 1 --branch $Version $DominusPrimeRepo $cloneDir
        } else {
            git clone --depth 1 $DominusPrimeRepo $cloneDir
        }
        if ($LASTEXITCODE -ne 0) { Stop-WithError "Failed to clone repository" }
        Prepare-Console $cloneDir
        Write-Info "Installing package from source..."
        uv pip install "${cloneDir}${ExtrasSuffix}" --python $VenvPython --prerelease=allow
        if ($LASTEXITCODE -ne 0) { Stop-WithError "Installation from source failed" }
    } finally {
        if (Test-Path $cloneDir) {
            Remove-Item -Path $cloneDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

# Verify the CLI entry point exists
if (-not (Test-Path $VenvDominusPrime)) { Stop-WithError "Installation failed: dominusprime CLI not found in venv" }

Write-Info "DominusPrime installed successfully"

# Check console availability (for PyPI installs, check the installed package)
if (-not $script:ConsoleAvailable) {
    $consoleCheck = & $VenvPython -c "import importlib.resources, dominusprime; p=importlib.resources.files('dominusprime')/'console'/'index.html'; print('yes' if p.is_file() else 'no')" 2>&1
    if ($consoleCheck -eq "yes") { $script:ConsoleAvailable = $true }
}

# ── Step 4: Create wrapper scripts ───────────────────────────────────────────
New-Item -ItemType Directory -Path $DominusPrimeBin -Force | Out-Null

$wrapperPath = Join-Path $DominusPrimeBin "dominusprime.ps1"
$wrapperContent = @'
# DominusPrime CLI wrapper — delegates to the uv-managed environment.
$ErrorActionPreference = "Stop"

$DominusPrimeHome = if ($env:DOMINUSPRIME_HOME) { $env:DOMINUSPRIME_HOME } else { Join-Path $HOME ".dominusprime" }
$RealBin   = Join-Path $DominusPrimeHome "venv\Scripts\dominusprime.exe"

if (-not (Test-Path $RealBin)) {
    Write-Error "DominusPrime environment not found at $DominusPrimeHome\venv"
    Write-Error "Please reinstall: irm <install-url> | iex"
    exit 1
}

& $RealBin @args
'@

Set-Content -Path $wrapperPath -Value $wrapperContent -Encoding UTF8
Write-Info "Wrapper created at $wrapperPath"

# Also create a .cmd wrapper for use from cmd.exe
$cmdWrapperPath = Join-Path $DominusPrimeBin "dominusprime.cmd"
$cmdWrapperContent = @"
@echo off
REM DominusPrime CLI wrapper — delegates to the uv-managed environment.
set "DOMINUSPRIME_HOME=%DOMINUSPRIME_HOME%"
if "%DOMINUSPRIME_HOME%"=="" set "DOMINUSPRIME_HOME=%USERPROFILE%\.dominusprime"
set "REAL_BIN=%DOMINUSPRIME_HOME%\venv\Scripts\dominusprime.exe"
if not exist "%REAL_BIN%" (
    echo Error: DominusPrime environment not found at %DOMINUSPRIME_HOME%\venv >&2
    echo Please reinstall: irm ^<install-url^> ^| iex >&2
    exit /b 1
)
"%REAL_BIN%" %*
"@

Set-Content -Path $cmdWrapperPath -Value $cmdWrapperContent -Encoding UTF8
Write-Info "CMD wrapper created at $cmdWrapperPath"

# ──Step 5: Update PATH via User Environment Variable ────────────────────────
$targetPath = $DominusPrimeBin
$registryPath = "HKCU:\Environment"
$registryName = "Path"

# 1. Safely get current User PATH (read directly from registry to avoid polluting Machine PATH)
try {
    $currentUserPath = (Get-ItemProperty -Path $registryPath -Name $registryName -ErrorAction SilentlyContinue).Path
    if (-not $currentUserPath) { $currentUserPath = "" }
} catch {
    # If even reading fails (extremely rare), start fresh
    $currentUserPath = ""
    Write-Debug "Could not read User Path from registry, starting fresh."
}

# 2. Precise check for existence (resolves prefix matching false positives)
# Split paths and trim whitespace
$pathArray = $currentUserPath -split ';' | ForEach-Object { $_.Trim() }
$isAlreadyAdded = $pathArray -contains $targetPath

if (-not $isAlreadyAdded) {
    # Build new User PATH string
    if ($currentUserPath) {
        $newUserPath = "$targetPath;$currentUserPath"
    } else {
        $newUserPath = $targetPath
    }

    # 3. Core fix: Use SetItemProperty instead of [Environment]::SetEnvironmentVariable
    #    This is a native cmdlet, usually available in Constrained Language Mode
    try {
        # Ensure registry path exists (HKCU:\Environment usually exists by default, but check for robustness)
        if (-not (Test-Path $registryPath)) {
            # This is extremely rare, but if it happens, try to create (usually needs permission, will enter catch if fails)
            New-Item -Path $registryPath -Force | Out-Null
        }

        # Write to registry
        Set-ItemProperty -Path $registryPath -Name $registryName -Value $newUserPath

        # Update current process environment variable to make it immediately effective in current terminal
        $env:Path = "$targetPath;$env:Path"

        Write-Info "Successfully added $targetPath to User PATH (via Registry)"

    } catch {
        # If even SetItemProperty fails (e.g. registry completely locked by group policy)
        $errorMsg = $_.Exception.Message

        Write-Host ""
        Write-Host "[CRITICAL WARNING] Automatic PATH update failed." -ForegroundColor Red
        Write-Host "   Reason: $errorMsg"
        Write-Host "   Context: Your system policy strictly blocks environment modifications."
        Write-Host ""
        Write-Host "ACTION REQUIRED: You must manually add the path to use DominusPrime."
        Write-Host "   Target Path: $targetPath"
        Write-Host ""
        Write-Host "Manual Steps (User Variables):"
        Write-Host "   1. Press Win+R, type 'sysdm.cpl' and press Enter"
        Write-Host "   2. Go to [Advanced] > [Environment Variables...]"
        Write-Host "   3. In the TOP section ('User variables'), select 'Path' > [Edit]"
        Write-Host "      (If 'Path' doesn't exist in User variables, click [New] and name it 'Path')"
        Write-Host "   4. Click [New] and paste: $targetPath"
        Write-Host "   5. Click [OK] everywhere to save."
        Write-Host "   6. CLOSE and REOPEN your terminal."
        Write-Host ""

        # Even if registry write fails, try to update current session for user testing (if it doesn't error)
        # Note: If policy is extremely strict, this line may also be ineffective, but trying it is harmless
        try {
            $env:Path = "$targetPath;$env:Path"
        } catch {}
    }
} else {
    Write-Info "$targetPath is already in your User PATH"
}

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "DominusPrime installed successfully!" -ForegroundColor Green
Write-Host ""

Write-Host "  Install location:  " -NoNewline; Write-Host "$DominusPrimeHome" -ForegroundColor White
Write-Host "  Python:            " -NoNewline; Write-Host "$pyVersion"  -ForegroundColor White
if ($script:ConsoleAvailable) {
    Write-Host "  Console (web UI):  " -NoNewline; Write-Host "available"     -ForegroundColor Green
} else {
    Write-Host "  Console (web UI):  " -NoNewline; Write-Host "not available" -ForegroundColor Yellow
    Write-Host "                     Install Node.js and re-run to enable the web UI."
}
Write-Host ""

Write-Host "To get started, open a new terminal and run:"
Write-Host ""
Write-Host "  dominusprime init" -ForegroundColor White -NoNewline; Write-Host "       # first-time setup"
Write-Host "  dominusprime app"  -ForegroundColor White -NoNewline; Write-Host "        # start DominusPrime"
Write-Host ""
Write-Host "To upgrade later, re-run this installer."
Write-Host "To uninstall, run: " -NoNewline
Write-Host "dominusprime uninstall" -ForegroundColor White

} @args
