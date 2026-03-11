# Automated llama.cpp server installer for DominusPrime (Windows)
# Downloads Qwen3.5-9B and sets up llama server with GPU acceleration

$ErrorActionPreference = "Stop"

Write-Host "================================" -ForegroundColor Green
Write-Host "llama.cpp Server Installer" -ForegroundColor Green
Write-Host "for DominusPrime (Windows)" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# Create the llamaserver folder
Write-Host "[INFO] Creating llamaserver directory..." -ForegroundColor Cyan
New-Item -Path .\llamaserver -ItemType Directory -Force | Out-Null

# Create the models subfolder
Write-Host "[INFO] Creating models directory..." -ForegroundColor Cyan
New-Item -Path .\llamaserver\models -ItemType Directory -Force | Out-Null

# Download the model file
Write-Host "[INFO] Downloading Qwen3.5-9B-Q4_K_M model (~5.5GB)..." -ForegroundColor Cyan
Write-Host "       This may take several minutes depending on your connection..." -ForegroundColor Yellow
$modelUrl = "https://huggingface.co/unsloth/Qwen3.5-9B-GGUF/resolve/main/Qwen3.5-9B-Q4_K_M.gguf?download=true"
$modelPath = ".\llamaserver\models\Qwen3.5-9B-Q4_K_M.gguf"

if (Test-Path $modelPath) {
    Write-Host "[INFO] Model already exists, skipping download." -ForegroundColor Green
} else {
    try {
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $modelUrl -OutFile $modelPath -UseBasicParsing
        Write-Host "[SUCCESS] Model downloaded successfully!" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Model download failed: $_" -ForegroundColor Red
        exit 1
    }
}

# Detect GPU
Write-Host "[INFO] Detecting GPU configuration..." -ForegroundColor Cyan
$gpus = Get-WmiObject Win32_VideoController | Where-Object { $_.Status -eq "OK" }
$gpuType = $null
$detectedGPU = $null

foreach ($gpu in $gpus) {
    $vramBytes = $gpu.AdapterRAM
    if ($null -ne $vramBytes -and $vramBytes -is [int]) {
        $vramGB = $vramBytes / 1GB
        if ($vramGB -ge 8) {
            if ($gpu.Name -like "*NVIDIA*") {
                $gpuType = "NVIDIA"
                $detectedGPU = $gpu.Name
                Write-Host "[SUCCESS] Detected NVIDIA GPU: $detectedGPU" -ForegroundColor Green
                Write-Host "          VRAM: $([math]::Round($vramGB, 2))GB" -ForegroundColor Green
                break
            } elseif ($gpu.Name -like "*AMD*" -or $gpu.Name -like "*Radeon*") {
                $gpuType = "AMD"
                $detectedGPU = $gpu.Name
                Write-Host "[SUCCESS] Detected AMD GPU: $detectedGPU" -ForegroundColor Green
                Write-Host "          VRAM: $([math]::Round($vramGB, 2))GB" -ForegroundColor Green
                break
            }
        }
    }
}

if ($null -eq $gpuType) {
    Write-Host "[ERROR] No compatible GPU with at least 8GB VRAM found." -ForegroundColor Red
    Write-Host "        Supported GPUs:" -ForegroundColor Yellow
    Write-Host "        - NVIDIA (8GB+ VRAM)" -ForegroundColor Yellow
    Write-Host "        - AMD Radeon (8GB+ VRAM)" -ForegroundColor Yellow
    exit 1
}

# Set URLs based on GPU type
$releaseTag = "b8253"
Write-Host "[INFO] Downloading llama.cpp binaries (release $releaseTag)..." -ForegroundColor Cyan

if ($gpuType -eq "NVIDIA") {
    $llamaZipUrl = "https://github.com/ggml-org/llama.cpp/releases/download/$releaseTag/llama-$releaseTag-bin-win-cuda-12.4-x64.zip"
    $dllsUrl = "https://github.com/ggml-org/llama.cpp/releases/download/$releaseTag/cudart-llama-bin-win-cuda-12.4-x64.zip"
    $llamaZipPath = ".\llamaserver\llama-bin.zip"
    $dllsZipPath = ".\llamaserver\dlls.zip"
    
    Write-Host "       Downloading CUDA binaries..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $llamaZipUrl -OutFile $llamaZipPath -UseBasicParsing
    Write-Host "       Downloading CUDA DLLs..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $dllsUrl -OutFile $dllsZipPath -UseBasicParsing
    
    Write-Host "       Extracting binaries..." -ForegroundColor Cyan
    Expand-Archive -Path $llamaZipPath -DestinationPath .\llamaserver -Force
    Expand-Archive -Path $dllsZipPath -DestinationPath .\llamaserver -Force
    
    Remove-Item -Path $llamaZipPath, $dllsZipPath
    Write-Host "[SUCCESS] NVIDIA CUDA binaries installed!" -ForegroundColor Green
    
} elseif ($gpuType -eq "AMD") {
    $llamaZipUrl = "https://github.com/ggml-org/llama.cpp/releases/download/$releaseTag/llama-$releaseTag-bin-win-hip-radeon-x64.zip"
    $llamaZipPath = ".\llamaserver\llama-bin.zip"
    
    Write-Host "       Downloading AMD ROCm binaries..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $llamaZipUrl -OutFile $llamaZipPath -UseBasicParsing
    
    Write-Host "       Extracting binaries..." -ForegroundColor Cyan
    Expand-Archive -Path $llamaZipPath -DestinationPath .\llamaserver -Force
    
    Remove-Item -Path $llamaZipPath
    Write-Host "[SUCCESS] AMD ROCm binaries installed!" -ForegroundColor Green
}

# Create start script
$startScript = @"
@echo off
echo ========================================
echo Starting llama.cpp server with GPU acceleration
echo GPU: $gpuType
echo ========================================
echo.
cd llamaserver
server.exe -m .\models\Qwen3.5-9B-Q4_K_M.gguf -c 131072 --host 127.0.0.1 --port 9080 --cache-type-k q4_0 --cache-type-v q4_0 -ngl 999
"@

$startScript | Out-File -FilePath ".\start_llama_server.bat" -Encoding ASCII

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Configuration:" -ForegroundColor Cyan
Write-Host "   GPU Type: $gpuType" -ForegroundColor White
Write-Host "   Model: Qwen3.5-9B-Q4_K_M" -ForegroundColor White
Write-Host "   Context: 131,072 tokens" -ForegroundColor White
Write-Host "   GPU Layers: 999 (full offload)" -ForegroundColor White
Write-Host ""
Write-Host "🚀 To Start Server:" -ForegroundColor Cyan
Write-Host "   Run: .\start_llama_server.bat" -ForegroundColor Yellow
Write-Host ""
Write-Host "🔌 Server Endpoint:" -ForegroundColor Cyan
Write-Host "   URL: http://127.0.0.1:9080" -ForegroundColor Yellow
Write-Host ""
Write-Host "📝 Configure DominusPrime:" -ForegroundColor Cyan
Write-Host "   1. Open DominusPrime console" -ForegroundColor White
Write-Host "   2. Go to Settings → Models" -ForegroundColor White
Write-Host "   3. Add OpenAI-Compatible Model" -ForegroundColor White
Write-Host "   4. Base URL: http://127.0.0.1:9080/v1" -ForegroundColor White
Write-Host "   5. Model Name: Qwen3.5-9B" -ForegroundColor White
Write-Host ""
