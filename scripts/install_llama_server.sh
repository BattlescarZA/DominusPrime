#!/usr/bin/env bash
# Automated llama.cpp server installer for DominusPrime
# Downloads Qwen3.5-9B-VL and sets up grammar-safe proxy
set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
LLAMA_DIR="${HOME}/llama.cpp"
MODELS_DIR="${HOME}/models"
MODEL_FILE="Qwen3.5-9B-VL-Q4_K_M.gguf"
MODEL_URL="https://huggingface.co/Qwen/Qwen3.5-9B-VL-GGUF/resolve/main/qwen2_5-9b-instruct-q4_k_m.gguf"
PROXY_FILE="${HOME}/llama_proxy.py"

# Detect GPU VRAM
detect_vram() {
    if command -v nvidia-smi &> /dev/null; then
        VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
        echo "$VRAM"
    else
        echo "0"
    fi
}

# Select context size based on VRAM
select_context() {
    local vram=$1
    if [ "$vram" -ge 14000 ]; then
        echo "262144"  # 256k for 16GB+
    elif [ "$vram" -ge 10000 ]; then
        echo "131072"  # 128k for 12GB
    else
        echo "65536"   # 64k for 8GB
    fi
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_cuda() {
    if ! command -v nvcc &> /dev/null; then
        log_error "CUDA not found. Please install CUDA Toolkit first."
        log_info "Visit: https://developer.nvidia.com/cuda-downloads"
        exit 1
    fi
    log_info "CUDA found: $(nvcc --version | grep release | cut -d' ' -f5)"
}

check_gpu() {
    if ! command -v nvidia-smi &> /dev/null; then
        log_error "nvidia-smi not found. NVIDIA drivers may not be installed."
        exit 1
    fi
    
    VRAM=$(detect_vram)
    if [ "$VRAM" -lt 6000 ]; then
        log_error "Insufficient GPU VRAM detected: ${VRAM}MB. Minimum 8GB required."
        exit 1
    fi
    
    CONTEXT=$(select_context "$VRAM")
    log_info "Detected ${VRAM}MB VRAM. Using ${CONTEXT} token context."
}

install_dependencies() {
    log_info "Installing dependencies..."
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y build-essential cmake git python3-pip wget curl
    elif command -v yum &> /dev/null; then
        sudo yum groupinstall -y "Development Tools"
        sudo yum install -y cmake git python3-pip wget curl
    elif command -v brew &> /dev/null; then
        brew install cmake git python3 wget
    else
        log_error "Unsupported package manager. Please install manually: cmake, git, python3, wget"
        exit 1
    fi
    
    # Install Python dependencies
    pip3 install --user flask requests huggingface-hub
    
    log_info "Dependencies installed successfully"
}

build_llama_cpp() {
    log_info "Building llama.cpp with CUDA support..."
    
    if [ -d "$LLAMA_DIR" ]; then
        log_warn "llama.cpp directory exists. Updating..."
        cd "$LLAMA_DIR"
        git pull
    else
        log_info "Cloning llama.cpp repository..."
        git clone https://github.com/ggml-org/llama.cpp.git "$LLAMA_DIR"
        cd "$LLAMA_DIR"
    fi
    
    # Build
    mkdir -p build && cd build
    cmake .. -DLLAMA_CUDA=ON -DLLAMA_NATIVE=OFF
    make -j$(nproc)
    
    if [ ! -f "bin/llama-server" ]; then
        log_error "Build failed. llama-server binary not found."
        exit 1
    fi
    
    log_info "llama.cpp built successfully"
}

download_model() {
    log_info "Downloading Qwen3.5-9B-VL model (~5.5GB)..."
    
    mkdir -p "$MODELS_DIR"
    cd "$MODELS_DIR"
    
    if [ -f "$MODEL_FILE" ]; then
        log_warn "Model file already exists. Skipping download."
        return
    fi
    
    # Try wget first, fall back to curl
    if command -v wget &> /dev/null; then
        wget -O "$MODEL_FILE" "$MODEL_URL" --progress=bar:force 2>&1
    elif command -v curl &> /dev/null; then
        curl -L -o "$MODEL_FILE" "$MODEL_URL" --progress-bar
    else
        log_error "Neither wget nor curl available. Cannot download model."
        exit 1
    fi
    
    if [ ! -f "$MODEL_FILE" ]; then
        log_error "Model download failed"
        exit 1
    fi
    
    log_info "Model downloaded successfully"
}

create_proxy() {
    log_info "Creating grammar-safe proxy..."
    
    cat > "$PROXY_FILE" << 'PROXYEOF'
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
PROXYEOF
    
    chmod +x "$PROXY_FILE"
    log_info "Proxy script created at $PROXY_FILE"
}

create_systemd_service() {
    log_info "Creating systemd services..."
    
    local user=$(whoami)
    
    # llama-server service
    sudo tee /etc/systemd/system/llama-server.service > /dev/null << SERVICEEOF
[Unit]
Description=llama-server Qwen3.5-9B-VL for DominusPrime
After=network.target

[Service]
Type=simple
User=$user
WorkingDirectory=$LLAMA_DIR/build
Environment="LD_LIBRARY_PATH=$LLAMA_DIR/build/bin:/usr/local/cuda/lib64"
Environment="PATH=/usr/local/cuda/bin:/usr/bin:/bin"
Environment="CUDA_VISIBLE_DEVICES=0"
ExecStart=$LLAMA_DIR/build/bin/llama-server \
    -m $MODELS_DIR/$MODEL_FILE \
    -ngl 99 \
    -c $CONTEXT \
    -fa on \
    -ctk q4_0 \
    -ctv q4_0 \
    --host 127.0.0.1 \
    --port 8080
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICEEOF
    
    # Proxy service
    sudo tee /etc/systemd/system/llama-proxy.service > /dev/null << PROXYSERVICEEOF
[Unit]
Description=llama.cpp Grammar-Safe Proxy for DominusPrime
After=network.target llama-server.service
Requires=llama-server.service

[Service]
Type=simple
User=$user
WorkingDirectory=$HOME
ExecStart=/usr/bin/python3 $PROXY_FILE
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
PROXYSERVICEEOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable llama-server llama-proxy
    
    log_info "Systemd services created and enabled"
}

start_services() {
    log_info "Starting services..."
    
    sudo systemctl start llama-server
    sleep 5
    sudo systemctl start llama-proxy
    sleep 3
    
    # Check status
    if systemctl is-active --quiet llama-server && systemctl is-active --quiet llama-proxy; then
        log_info "✓ Services started successfully"
    else
        log_error "Services failed to start. Check logs with: journalctl -u llama-server -u llama-proxy"
        exit 1
    fi
}

test_installation() {
    log_info "Testing installation..."
    
    # Test proxy health
    if curl -sf http://localhost:8081/health > /dev/null; then
        log_info "✓ Proxy is responding"
    else
        log_error "Proxy is not responding on port 8081"
        return 1
    fi
    
    # Test completion
    log_info "Testing model completion..."
    RESPONSE=$(curl -s -X POST http://localhost:8081/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{"messages":[{"role":"user","content":"Hello"}],"max_tokens":10}')
    
    if echo "$RESPONSE" | grep -q "choices"; then
        log_info "✓ Model is working correctly"
    else
        log_warn "Model test returned unexpected response"
        return 1
    fi
}

print_summary() {
    local vram=$(detect_vram)
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}llama.cpp Server Installation Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "📊 Configuration:"
    echo "  GPU VRAM: ${vram}MB"
    echo "  Context: $CONTEXT tokens"
    echo "  Model: Qwen3.5-9B-VL Q4_K_M"
    echo ""
    echo "🔌 Endpoints:"
    echo "  Direct (DO NOT USE): http://localhost:8080"
    echo "  Proxy (USE THIS):    http://localhost:8081/v1"
    echo ""
    echo "📝 Configure DominusPrime:"
    echo "  1. Open http://localhost:8088"
    echo "  2. Go to Models → Add Model"
    echo "  3. Type: OpenAI-Compatible"
    echo "  4. Base URL: http://localhost:8081/v1"
    echo "  5. API Key: not-needed"
    echo "  6. Model: qwen3.5-9b-vl"
    echo ""
    echo "🔧 Service Management:"
    echo "  Status:  sudo systemctl status llama-server llama-proxy"
    echo "  Restart: sudo systemctl restart llama-server llama-proxy"
    echo "  Logs:    sudo journalctl -u llama-server -u llama-proxy -f"
    echo ""
    echo "⚠️  IMPORTANT: Always use port 8081 (grammar-safe proxy)"
    echo "   Port 8080 will crash with DominusPrime!"
    echo ""
}

main() {
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}llama.cpp Server Installer${NC}"
    echo -e "${GREEN}for DominusPrime${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    
    check_cuda
    check_gpu
    install_dependencies
    build_llama_cpp
    download_model
    create_proxy
    create_systemd_service
    start_services
    
    if test_installation; then
        print_summary
    else
        log_error "Installation tests failed. Check logs for details."
        exit 1
    fi
}

main "$@"
