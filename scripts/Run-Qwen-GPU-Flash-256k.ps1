# Run-Qwen-GPU-Flash-256k.ps1
# ONE-CLICK script: RTX 2060 + Flash Attention ON + 256k context

param(
    [int]$GPUlayers = 32   # Change to 30/28 if OOM, or 34 if it loads
)

$model   = "D:\folder\Qwen3.5-9B-Q4_K_M.gguf"
$exe     = "D:\folder\llama-server.exe"
$port    = 9090

Write-Host "🚀 Starting Qwen3.5-9B on RTX 2060 with Flash Attention ON (256k context)" -ForegroundColor Cyan
Write-Host "GPU layers : $GPUlayers | Context: 256k | KV cache: Q4 | Port: $port`n"

& $exe `
    -m $model `
    --n-gpu-layers $GPUlayers `
    -c 262144 `
    --cache-type-k q4_0 `
    --cache-type-v q4_0 `
    --port $port `
    --host 0.0.0.0 `
    --flash-attn on `
    --log-colors on `
    --threads 10 `
    --flash-attn on   # forced ON for maximum GPU speed

Write-Host "`nServer stopped." -ForegroundColor Yellow
