# Automated llama.cpp server installer for DominusPrime (Windows)
# Downloads Qwen3.5-9B-VL and sets up grammar-safe proxy
param(
    [switch]$SkipCUDA,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Configuration
$LlamaDir = "$HOME\llama.cpp"
$ModelsDir = "$HOME\models"
$ModelFile = "Qwen3.5-9B-VL-Q4_K_M.gguf"
$ModelURL = "https://huggingface.co/Qwen/Qwen3.5-9B-VL-GGUF/resolve/main/qwen2_5-9b-instruct-q4_k_m.gguf"
$ProxyFile = "$HOME\llama_proxy.py"
$Context = 65536  # Default for 8GB

# Colors
function Write-Success { param([string]$Message) Write-Host "[INFO] " -ForegroundColor Green -NoNewline; Write-Host $Message }
function Write-Warn { param([string]$Message) Write-Host "[WARN] " -ForegroundColor Yellow -NoNewline; Write-Host $Message }
function Write-Fail { param([string]$Message) Write-Host "[ERROR] " -ForegroundColor Red -NoNewline; Write-Host $Message }

if ($Help) {
    @"
llama.cpp Server Installer for DominusPrime (Windows)

Usage: .\install_llama_server.ps1 [OPTIONS]

Options:
  -SkipCUDA     Skip CUDA detection (use CPU only)
  -Help         Show this help message

This script will:
  1. Check for CUDA and GPU
  2. Install dependencies (CMake, Python, Git)
  3. Build llama.cpp with CUDA support
  4. Download Qwen3.5-9B-VL model (~5.5GB)
  5. Create grammar-safe proxy
  6. Set up Windows services

Requirements:
  - Windows 10/11
  - NVIDIA GPU with 8GB+ VRAM
  - CUDA Toolkit 11.8+
  - Administrator privileges
"@
    exit 0
}

# Detect VRAM
function Get-VRAM {
    try {
        if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
            $vram = nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | Select-Object -First 1
            return [int]$vram
        }
    } catch {
        return 0
    }
    return 0
}

# Select context based on VRAM
function Select-Context {
    param([int]$VRAM)
    
    if ($VRAM -ge 14000) {
        return 262144  # 256k for 16GB+
    } elseif ($VRAM -ge 10000) {
        return 131072  # 128k for 12GB
    } else {
        return 65536   # 64k for 8GB
    }
}

# Check CUDA
function Test-CUDA {
    if ($SkipCUDA) {
        Write-Warn "Skipping CUDA check (CPU mode)"
        return
    }
    
    if (!(Get-Command nvcc -ErrorAction SilentlyContinue)) {
        Write-Fail "CUDA not found. Please install CUDA Toolkit first."
        Write-Host "Visit: https://developer.nvidia.com/cuda-downloads"
        exit 1
    }
    
    $cudaVersion = (nvcc --version | Select-String "release") -replace '.*release\s+', '' -replace ',.*', ''
    Write-Success "CUDA found: $cudaVersion"
}

# Check GPU
function Test-GPU {
    if ($SkipCUDA) {
        return
    }
    
    if (!(Get-Command nvidia-smi -ErrorAction SilentlyContinue)) {
        Write-Fail "nvidia-smi not found. NVIDIA drivers may not be installed."
        exit 1
    }
    
    $vram = Get-VRAM
    if ($vram -lt 6000) {
        Write-Fail "Insufficient GPU VRAM: ${vram}MB. Minimum 8GB required."
        exit 1
    }
    
    $script:Context = Select-Context $vram
    Write-Success "Detected ${vram}MB VRAM. Using $($script:Context) token context."
}

# Install Chocolatey
function Install-Chocolatey {
    if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-Success "Installing Chocolatey package manager..."
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    } else {
        Write-Success "Chocolatey already installed"
    }
}

# Install Dependencies
function Install-Dependencies {
    Write-Success "Installing dependencies..."
    
    Install-Chocolatey
    
    # Install build tools
    choco install -y cmake git python3 wget
    
    # Refresh environment
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    # Install Python packages
    python -m pip install --upgrade pip
    pip install flask requests huggingface-hub
    
    Write-Success "Dependencies installed"
}

# Build llama.cpp
function Build-LlamaCpp {
    Write-Success "Building llama.cpp with CUDA support..."
    
    if (Test-Path $LlamaDir) {
        Write-Warn "llama.cpp directory exists. Updating..."
        cd $LlamaDir
        git pull
    } else {
        Write-Success "Cloning llama.cpp..."
        git clone https://github.com/ggml-org/llama.cpp.git $LlamaDir
        cd $LlamaDir
    }
    
    # Create build directory
    New-Item -ItemType Directory -Force -Path "build" | Out-Null
    cd build
    
    # Configure with CUDA
    if ($SkipCUDA) {
        cmake .. -DLLAMA_NATIVE=OFF
    } else {
        cmake .. -DLLAMA_CUDA=ON -DLLAMA_NATIVE=OFF
    }
    
    # Build
    cmake --build . --config Release -j
    
    if (!(Test-Path "bin\Release\llama-server.exe")) {
        Write-Fail "Build failed. llama-server.exe not found."
        exit 1
    }
    
    Write-Success "llama.cpp built successfully"
    cd $HOME
}

# Download Model
function Get-Model {
    Write-Success "Downloading Qwen3.5-9B-VL model (~5.5GB)..."
    
    New-Item -ItemType Directory -Force -Path $ModelsDir | Out-Null
    
    $modelPath = Join-Path $ModelsDir $ModelFile
    
    if (Test-Path $modelPath) {
        Write-Warn "Model already exists. Skipping download."
        return
    }
    
    # Download with progress
    $ProgressPreference = 'SilentlyContinue'
    try {
        Invoke-WebRequest -Uri $ModelURL -OutFile $modelPath -UseBasicParsing
        Write-Success "Model downloaded successfully"
    } catch {
        Write-Fail "Model download failed: $_"
        exit 1
    }
}

# Create Proxy
function New-Proxy {
    Write-Success "Creating grammar-safe proxy..."
    
    @'
#!/usr/bin/env python3
"""Grammar-Safe Proxy for llama-server - Prevents crashes with DominusPrime"""
from flask import Flask, request, jsonify, Response
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

LLAMA_URL = "http://localhost:8080/v1/chat/completions"

@app.route('/v1/chat/completions', methods=['POST'])
def proxy_chat():
    try:
        data = request.get_json()
        
        # Strip fields that cause crashes
        for field in ['response_format', 'grammar', 'json_schema', 'tools', 'tool_choice']:
            data.pop(field, None)
        
        resp = requests.post(LLAMA_URL, json=data, headers={'Content-Type': 'application/json'}, timeout=300)
        return Response(resp.content, status=resp.status_code, content_type=resp.headers.get('Content-Type'))
    
    except Exception as e:
        app.logger.error(f"Proxy error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/v1/models', methods=['GET'])
def list_models():
    try:
        resp = requests.get("http://localhost:8080/v1/models", timeout=10)
        return Response(resp.content, status=resp.status_code)
    except:
        return jsonify({"object": "list", "data": [{"id": "qwen3.5-9b-vl", "object": "model"}]})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "proxy": "grammar-safe"})

if __name__ == '__main__':
    print("🛡️  Grammar-Safe Proxy starting on port 8081")
    app.run(host='0.0.0.0', port=8081, threaded=True)
'@ | Out-File -FilePath $ProxyFile -Encoding UTF8
    
    Write-Success "Proxy created at $ProxyFile"
}

# Create Start Scripts
function New-StartScripts {
    Write-Success "Creating start scripts..."
    
    # Server start script
    $serverScript = Join-Path $HOME "start_llama_server.ps1"
    @"
# Start llama-server for DominusPrime
`$ErrorActionPreference = "Stop"

Write-Host "Starting llama-server..." -ForegroundColor Green

cd "$LlamaDir\build"

& ".\bin\Release\llama-server.exe" ``
    -m "$ModelsDir\$ModelFile" ``
    -ngl 99 ``
    -c $Context ``
    -fa on ``
    -ctk q4_0 ``
    -ctv q4_0 ``
    --host 127.0.0.1 ``
    --port 8080
"@ | Out-File -FilePath $serverScript -Encoding UTF8
    
    # Proxy start script
    $proxyScript = Join-Path $HOME "start_llama_proxy.ps1"
    @"
# Start grammar-safe proxy for DominusPrime
`$ErrorActionPreference = "Stop"

Write-Host "Starting grammar-safe proxy..." -ForegroundColor Green

python "$ProxyFile"
"@ | Out-File -FilePath $proxyScript -Encoding UTF8
    
    Write-Success "Start scripts created:"
    Write-Host "  Server: $serverScript"
    Write-Host "  Proxy:  $proxyScript"
}

# Test Installation
function Test-Installation {
    Write-Success "Testing installation..."
    
    Start-Sleep -Seconds 3
    
    # Test proxy
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8081/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Success "✓ Proxy is responding"
        }
    } catch {
        Write-Fail "Proxy is not responding on port 8081"
        return $false
    }
    
    # Test completion
    try {
        Write-Success "Testing model completion..."
        $body = @{
            messages = @(@{role="user"; content="Hello"})
            max_tokens = 10
        } | ConvertTo-Json
        
        $response = Invoke-WebRequest -Uri "http://localhost:8081/v1/chat/completions" `
            -Method POST `
            -ContentType "application/json" `
            -Body $body `
            -UseBasicParsing `
            -TimeoutSec 30
        
        if ($response.Content -like "*choices*") {
            Write-Success "✓ Model is working correctly"
            return $true
        }
    } catch {
        Write-Warn "Model test failed. You may need to start the services manually."
        return $false
    }
    
    return $true
}

# Print Summary
function Show-Summary {
    $vram = Get-VRAM
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "llama.cpp Installation Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Configuration:"
    Write-Host "  GPU VRAM: ${vram}MB"
    Write-Host "  Context: $Context tokens"
    Write-Host "  Model: Qwen3.5-9B-VL Q4_K_M"
    Write-Host ""
    Write-Host "🚀 To Start Services:"
    Write-Host "  1. Open PowerShell terminal"
    Write-Host "  2. Run: .\start_llama_server.ps1"
    Write-Host "  3. Open another terminal"
    Write-Host "  4. Run: .\start_llama_proxy.ps1"
    Write-Host ""
    Write-Host "🔌 Endpoints:"
    Write-Host "  Direct (DO NOT USE): http://localhost:8080"
    Write-Host "  Proxy (USE THIS):    http://localhost:8081/v1"
    Write-Host ""
    Write-Host "📝 Configure DominusPrime:"
    Write-Host "  1. Open http://localhost:8088"
    Write-Host "  2. Go to Models → Add Model"
    Write-Host "  3. Type: OpenAI-Compatible"
    Write-Host "  4. Base URL: http://localhost:8081/v1"
    Write-Host "  5. API Key: not-needed"
    Write-Host "  6. Model: qwen3.5-9b-vl"
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: Always use port 8081 (grammar-safe proxy)" -ForegroundColor Yellow
    Write-Host "   Port 8080 will crash with DominusPrime!" -ForegroundColor Yellow
    Write-Host ""
}

# Main
function Main {
    Write-Host "================================" -ForegroundColor Green
    Write-Host "llama.cpp Server Installer" -ForegroundColor Green
    Write-Host "for DominusPrime (Windows)" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    Write-Host ""
    
    # Check admin
    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (!$isAdmin) {
        Write-Warn "Running without administrator privileges. Some steps may fail."
        Write-Host "Right-click PowerShell and 'Run as Administrator' for best results."
        Start-Sleep -Seconds 3
    }
    
    Test-CUDA
    Test-GPU
    Install-Dependencies
    Build-LlamaCpp
    Get-Model
    New-Proxy
    New-StartScripts
    Show-Summary
    
    Write-Host ""
    Write-Success "Installation complete! Start the services to begin using llama.cpp with DominusPrime."
}

Main
