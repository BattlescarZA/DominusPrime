# Install-LlamaServer-GPU-Flash.ps1
# Downloads latest llama.cpp (CUDA 12.4) + creates your easy-run script
# Perfect for RTX 2060 + Flash Attention + 64k context

$ErrorActionPreference = "Stop"
$InstallDir = "D:\folder"

Write-Host "=== llama.cpp GPU + Flash Attention Installer ===" -ForegroundColor Cyan

# Create folder
New-Item -Path $InstallDir -ItemType Directory -Force | Out-Null

# Get latest release
$tag = (Invoke-RestMethod "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest").tag_name
Write-Host "Latest version: $tag" -ForegroundColor Green

$MainZip   = "https://github.com/ggml-org/llama.cpp/releases/download/$tag/llama-${tag}-bin-win-cuda-12.4-x64.zip"
$DllsZip   = "https://github.com/ggml-org/llama.cpp/releases/download/$tag/cudart-llama-bin-win-cuda-12.4-x64.zip"

Write-Host "Downloading CUDA binaries..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $MainZip -OutFile "$env:TEMP\main.zip"
Invoke-WebRequest -Uri $DllsZip -OutFile "$env:TEMP\dlls.zip"

Write-Host "Extracting to D:\folder ..." -ForegroundColor Cyan
Expand-Archive "$env:TEMP\main.zip" -DestinationPath $InstallDir -Force
Expand-Archive "$env:TEMP\dlls.zip" -DestinationPath $InstallDir -Force

# Clean temp files
Remove-Item "$env:TEMP\main.zip","$env:TEMP\dlls.zip" -Force -ErrorAction SilentlyContinue

# === CREATE THE EASY RUN SCRIPT AUTOMATICALLY ===
$RunScript = @'
# Run-Qwen-GPU-Flash.ps1
# ONE-CLICK script: RTX 2060 + Flash Attention ON + 64k context

param(
    [int]$GPUlayers = 32   # Change to 30/28 if OOM, or 34 if it loads
)

$model   = "D:\folder\Qwen3.5-9B-Q4_K_M.gguf"
$exe     = "D:\folder\llama-server.exe"
$port    = 9090

Write-Host "🚀 Starting Qwen3.5-9B on RTX 2060 with Flash Attention ON" -ForegroundColor Cyan
Write-Host "GPU layers : $GPUlayers | Context: 64k | KV cache: Q4 | Port: $port`n"

& $exe `
    -m $model `
    --n-gpu-layers $GPUlayers `
    -c 65536 `
    --cache-type-k q4_0 `
    --cache-type-v q4_0 `
    --port $port `
    --host 0.0.0.0 `
    --flash-attn on `
    --log-colors on `
    --threads 10 `
    --flash-attn on   # forced ON for maximum GPU speed

Write-Host "`nServer stopped." -ForegroundColor Yellow
'@

$RunScript | Out-File "$InstallDir\Run-Qwen-GPU-Flash.ps1" -Encoding UTF8 -Force

Write-Host "`n✅ INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "Folder: D:\folder"
Write-Host "Executable: llama-server.exe (CUDA ready)"
Write-Host ""
Write-Host "To start the server with GPU + Flash Attention:" -ForegroundColor White
Write-Host "    cd D:\folder" -ForegroundColor Yellow
Write-Host "    .\Run-Qwen-GPU-Flash.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "Just double-click Run-Qwen-GPU-Flash.ps1 in File Explorer if you want!" -ForegroundColor Magenta
