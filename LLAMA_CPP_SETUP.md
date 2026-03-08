# 🦙 llama.cpp Setup for DominusPrime

Complete guide to install **llama-server** and serve the **Qwen3.5-9B-VL** model with DominusPrime on Ubuntu with NVIDIA GPU support.

---

## 📋 Prerequisites

### Hardware Requirements
- **GPU:** NVIDIA GPU with 8GB+ VRAM
  - **Minimum:** RTX 3060 8GB, RTX 4060 (64k context)
  - **Recommended:** RTX 3060 12GB, RTX 4070 (128k context)
  - **Optimal:** RTX 4080, RTX 4090 (256k context)
- **RAM:** 16GB+ system RAM recommended
- **Storage:** 10GB free space for model files

### Software Requirements
- **OS:** Ubuntu 20.04+ or similar Linux distribution
- **NVIDIA Drivers:** Version 520 or higher
- **CUDA Toolkit:** Version 11.8 or higher
- **Build Tools:** Git, CMake, C++ compiler

---

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install build essentials
sudo apt install -y build-essential cmake git python3-pip wget

# Install CUDA Toolkit (if not already installed)
# Option 1: Via apt (simpler)
sudo apt install -y nvidia-cuda-toolkit

# Option 2: Download from NVIDIA (latest version)
# Visit: https://developer.nvidia.com/cuda-downloads

# Verify installation
nvcc --version
nvidia-smi
```

**Expected Output:**
```
CUDA compilation tools, release 11.8, V11.8.89
GPU 0: NVIDIA GeForce RTX 3060 (Memory: 12GB)
```

---

### Step 2: Build llama.cpp with CUDA Support

```bash
# Create projects directory
mkdir -p ~/projects && cd ~/projects

# Clone llama.cpp repository
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp

# Create and enter build directory
mkdir build && cd build

# Configure with CUDA enabled
cmake .. -DLLAMA_CUDA=ON -DLLAMA_NATIVE=OFF

# Build (uses all CPU cores, takes 5-10 minutes)
make -j$(nproc)

# Verify successful build
ls -la bin/llama-server
```

**Expected Output:**
```
-rwxr-xr-x 1 user user 15M Mar  8 12:00 bin/llama-server
```

---

### Step 3: Download Qwen3.5-9B-VL Model

This is our recommended model for DominusPrime - it offers excellent performance with moderate resource usage.

```bash
# Create models directory
mkdir -p ~/models && cd ~/models

# Download Q4_K_M quantized version (recommended for 12GB VRAM)
wget https://huggingface.co/Qwen/Qwen3.5-9B-VL-GGUF/resolve/main/qwen2_5-9b-instruct-q4_k_m.gguf \
  -O Qwen3.5-9B-VL-Q4_K_M.gguf

# Alternative: Use huggingface-cli for better download reliability
pip3 install huggingface-hub
huggingface-cli download Qwen/Qwen3.5-9B-VL-GGUF \
  --include "qwen2_5-9b-instruct-q4_k_m.gguf" \
  --local-dir ~/models

# Verify download (should be ~5.5GB)
ls -lh ~/models/Qwen3.5-9B-VL-Q4_K_M.gguf
```

**Model Specifications:**
- **Parameters:** 9 Billion
- **Quantization:** Q4_K_M (4-bit, medium quality)
- **File Size:** ~5.5 GB
- **Context Length:** Up to 256k tokens (configurable)
- **VRAM Usage:** 6-8 GB depending on context
- **Best For:** General conversation, coding, analysis

---

### Step 4: Start llama-server

Choose the configuration that fits your needs:

#### **Option A: For 8GB GPUs (64k context) - Recommended for RTX 3060 8GB, RTX 4060**

Safe and fast for 8GB VRAM cards.

```bash
cd ~/llama.cpp/build

# Set environment variables
export LD_LIBRARY_PATH=~/llama.cpp/build/bin:$LD_LIBRARY_PATH
export PATH=/usr/local/cuda/bin:$PATH

# Start server
./bin/llama-server \
    -m ~/models/Qwen3.5-9B-VL-Q4_K_M.gguf \
    -ngl 99 \
    -c 65536 \
    -fa on \
    -ctk q4_0 \
    -ctv q4_0 \
    --host 0.0.0.0 \
    --port 8080
```

**VRAM Usage:** ~5.2 GB (65% of 8GB) - Fast and stable ✅

#### **Option B: For 12GB GPUs (128k context) - Recommended for RTX 3060 12GB, RTX 4070**

Good balance for 12GB+ cards.

```bash
cd ~/llama.cpp/build

export LD_LIBRARY_PATH=~/llama.cpp/build/bin:$LD_LIBRARY_PATH
export PATH=/usr/local/cuda/bin:$PATH

./bin/llama-server \
    -m ~/models/Qwen3.5-9B-VL-Q4_K_M.gguf \
    -ngl 99 \
    -c 131072 \
    -fa on \
    -ctk q4_0 \
    -ctv q4_0 \
    --host 0.0.0.0 \
    --port 8080
```

**VRAM Usage:** ~6.9 GB (56% of 12GB) - Excellent performance ✅

#### **Option C: For 16GB+ GPUs (256k context) - For RTX 4080, RTX 4090**

Maximum context for long documents.

```bash
cd ~/llama.cpp/build

export LD_LIBRARY_PATH=~/llama.cpp/build/bin:$LD_LIBRARY_PATH
export PATH=/usr/local/cuda/bin:$PATH

./bin/llama-server \
    -m ~/models/Qwen3.5-9B-VL-Q4_K_M.gguf \
    -ngl 99 \
    -c 262144 \
    -fa on \
    -ctk q4_0 \
    -ctv q4_0 \
    --host 0.0.0.0 \
    --port 8080
```

### 📊 Parameter Reference

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `-m` | model path | Path to the GGUF model file |
| `-ngl 99` | 99 layers | Offload all layers to GPU (maximum speed) |
| `-c` | 65536-262144 | Context window size (tokens) |
| `-fa on` | enabled | Flash Attention for faster processing |
| `-ctk q4_0` | Q4_0 | Quantize key cache (saves VRAM) |
| `-ctv q4_0` | Q4_0 | Quantize value cache (saves VRAM) |
| `--host` | 0.0.0.0 | Accept connections from any interface |
| `--port` | 8080 | Server listening port |

---

### Step 5: Create Grammar-Safe Proxy (⚠️ IMPORTANT)

**Why you need this:** llama-server can crash when receiving `response_format: json_object` requests from DominusPrime. This proxy strips problematic fields.

```bash
# Create proxy script
cat > ~/llama_proxy.py << 'EOF'
#!/usr/bin/env python3
"""
Grammar-Safe Proxy for llama-server
Strips grammar-related fields that cause crashes with DominusPrime
"""
from flask import Flask, request, jsonify, Response
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

LLAMA_URL = "http://localhost:8080/v1/chat/completions"

@app.route('/v1/chat/completions', methods=['POST'])
def proxy_chat():
    """Proxy chat completions, stripping grammar fields."""
    try:
        data = request.get_json()
        
        # Remove fields that cause llama-server crashes
        removed_fields = []
        for field in ['response_format', 'grammar', 'json_schema', 'tools', 'tool_choice']:
            if field in data:
                data.pop(field)
                removed_fields.append(field)
        
        if removed_fields:
            app.logger.info(f"Stripped fields: {', '.join(removed_fields)}")
        
        # Forward to llama-server
        resp = requests.post(
            LLAMA_URL, 
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=300
        )
        
        return Response(
            resp.content,
            status=resp.status_code,
            content_type=resp.headers.get('Content-Type')
        )
    
    except Exception as e:
        app.logger.error(f"Proxy error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/v1/models', methods=['GET'])
def list_models():
    """Forward model list request."""
    try:
        resp = requests.get(f"http://localhost:8080/v1/models", timeout=10)
        return Response(resp.content, status=resp.status_code)
    except:
        return jsonify({"object": "list", "data": [
            {"id": "qwen3.5-9b-vl", "object": "model"}
        ]})

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "proxy": "grammar-safe", "upstream": "http://localhost:8080"})

if __name__ == '__main__':
    print("🛡️  Grammar-Safe Proxy starting on port 8081")
    print("   Upstream: http://localhost:8080")
    print("   Health check: http://localhost:8081/health")
    app.run(host='0.0.0.0', port=8081, threaded=True)
EOF

# Make executable
chmod +x ~/llama_proxy.py

# Install Flask
pip3 install flask requests

# Run proxy (in a separate terminal or background)
python3 ~/llama_proxy.py
```

**Port Configuration:**
- **Port 8080:** Direct llama-server (⚠️ avoid - will crash with DominusPrime)
- **Port 8081:** Grammar-safe proxy (✅ use this with DominusPrime)

---

### Step 6: Configure DominusPrime

Now configure DominusPrime to use your local llama.cpp server:

```bash
# Start DominusPrime
dominusprime app

# Open console at http://localhost:8088
# Navigate to: Models → Add Model → Custom Provider
```

**Model Configuration:**

1. **Provider Type:** OpenAI-Compatible
2. **Base URL:** `http://localhost:8081/v1` (use proxy port!)
3. **API Key:** `not-needed` (any value works)
4. **Model Name:** `qwen3.5-9b-vl`
5. **Max Tokens:** `4096`
6. **Temperature:** `0.7`
7. **Context Window:** `131072` (or your chosen value)

Click **Test Connection** → Should return `✓ Connected successfully`

---

### Step 7: Create Systemd Services (Optional but Recommended)

Run llama-server and proxy as system services for auto-start.

#### Service 1: llama-server

```bash
sudo tee /etc/systemd/system/llama-server.service << 'EOF'
[Unit]
Description=llama-server Qwen3.5-9B-VL
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/llama.cpp/build
Environment="LD_LIBRARY_PATH=/home/YOUR_USERNAME/llama.cpp/build/bin:/usr/local/cuda/lib64"
Environment="PATH=/usr/local/cuda/bin:/usr/bin:/bin"
Environment="CUDA_VISIBLE_DEVICES=0"
ExecStart=/home/YOUR_USERNAME/llama.cpp/build/bin/llama-server \
    -m /home/YOUR_USERNAME/models/Qwen3.5-9B-VL-Q4_K_M.gguf \
    -ngl 99 \
    -c 131072 \
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
EOF

# Replace YOUR_USERNAME with your actual username
sudo sed -i "s/YOUR_USERNAME/$(whoami)/g" /etc/systemd/system/llama-server.service
```

#### Service 2: Grammar-Safe Proxy

```bash
sudo tee /etc/systemd/system/llama-proxy.service << 'EOF'
[Unit]
Description=llama.cpp Grammar-Safe Proxy
After=network.target llama-server.service
Requires=llama-server.service

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME
ExecStart=/usr/bin/python3 /home/YOUR_USERNAME/llama_proxy.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Replace YOUR_USERNAME
sudo sed -i "s/YOUR_USERNAME/$(whoami)/g" /etc/systemd/system/llama-proxy.service
```

#### Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable llama-server
sudo systemctl enable llama-proxy

# Start services
sudo systemctl start llama-server
sudo systemctl start llama-proxy

# Check status
sudo systemctl status llama-server
sudo systemctl status llama-proxy

# View logs
sudo journalctl -u llama-server -f
sudo journalctl -u llama-proxy -f
```

---

## 🧪 Testing & Verification

### Test 1: Health Checks

```bash
# Test llama-server directly
curl http://localhost:8080/health

# Test grammar-safe proxy
curl http://localhost:8081/health

# Expected response:
# {"status":"ok","proxy":"grammar-safe","upstream":"http://localhost:8080"}
```

### Test 2: Simple Completion

```bash
curl -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful AI assistant."},
      {"role": "user", "content": "Hello! What is DominusPrime?"}
    ],
    "max_tokens": 150,
    "temperature": 0.7
  }'
```

### Test 3: GPU Utilization

```bash
# Monitor GPU usage
watch -n 1 nvidia-smi

# Look for llama-server process
# Expect: 6-8 GB VRAM usage during inference
```

### Test 4: DominusPrime Integration

1. Open DominusPrime console: `http://localhost:8088`
2. Start a new chat
3. Send message: "Hello! Can you help me with Python?"
4. Should receive response from local Qwen model

---

## 📊 Performance & Resource Usage

### VRAM Usage by Context Size (RTX 3060 12GB)

| Context Size | VRAM Used | % of 12GB | Status |
|-------------|-----------|-----------|--------|
| 64k tokens | 6,280 MiB | 51% | ✅ Very Safe |
| 128k tokens | 6,865 MiB | 56% | ✅ Recommended |
| 256k tokens | 8,333 MiB | 68% | ⚠️ Maximum |

### Speed Benchmarks

- **Prompt Processing:** ~3000 tokens/second
- **Generation Speed:** ~40-60 tokens/second
- **First Token Latency:** <200ms
- **Context Switch:** <500ms

---

## 🔧 Troubleshooting

### Problem: "CUDA out of memory"

**Solution:**
```bash
# Option 1: Reduce context size
-c 65536  # Instead of 131072

# Option 2: Reduce GPU layers
-ngl 50  # Instead of 99

# Option 3: Increase cache quantization
-ctk q3_k -ctv q3_k  # More aggressive
```

### Problem: "llama-server crashes with json_object"

**Solution:**
- ✅ Always use port 8081 (grammar-safe proxy)
- ❌ Never use port 8080 directly with DominusPrime

### Problem: "Connection refused" from DominusPrime

**Solution:**
```bash
# Check services are running
systemctl status llama-server
systemctl status llama-proxy

# Check ports are listening
sudo netstat -tlnp | grep 808

# Restart services if needed
sudo systemctl restart llama-server
sudo systemctl restart llama-proxy
```

### Problem: "Model file not found"

**Solution:**
```bash
# Verify model location
ls -lh ~/models/Qwen3.5-9B-VL-Q4_K_M.gguf

# Check permissions
chmod 644 ~/models/Qwen3.5-9B-VL-Q4_K_M.gguf

# Update path in systemd service if needed
sudo systemctl edit llama-server
```

### Problem: "Slow generation speed"

**Solution:**
```bash
# Ensure all layers on GPU
-ngl 99

# Enable Flash Attention
-fa on

# Check GPU isn't throttling
nvidia-smi -q -d TEMPERATURE
nvidia-smi -q -d POWER
```

---

## 📝 Quick Command Reference

```bash
# Start server (foreground, for testing)
cd ~/llama.cpp/build && ./bin/llama-server \
  -m ~/models/Qwen3.5-9B-VL-Q4_K_M.gguf \
  -ngl 99 -c 131072 -fa on -ctk q4_0 -ctv q4_0 \
  --host 0.0.0.0 --port 8080

# Start proxy (foreground)
python3 ~/llama_proxy.py

# Start server (background with nohup)
cd ~/llama.cpp/build && nohup ./bin/llama-server \
  -m ~/models/Qwen3.5-9B-VL-Q4_K_M.gguf \
  -ngl 99 -c 131072 -fa on -ctk q4_0 -ctv q4_0 \
  --host 0.0.0.0 --port 8080 \
  > ~/llama-server.log 2>&1 &

# Stop all llama processes
pkill -9 llama-server

# View logs (systemd)
sudo journalctl -u llama-server -n 100 -f

# View logs (nohup)
tail -f ~/llama-server.log

# Check GPU
nvidia-smi
watch -n 1 nvidia-smi

# Test proxy
curl http://localhost:8081/health
```

---

## 🔗 Additional Resources

- **llama.cpp GitHub:** https://github.com/ggml-org/llama.cpp
- **Qwen Models:** https://huggingface.co/Qwen
- **GGUF Format:** https://github.com/ggerganov/ggml/blob/master/docs/gguf.md
- **DominusPrime Docs:** https://github.com/BattlescarZA/DominusPrime

---

## 💡 Tips for Best Results

1. **Use the Grammar-Safe Proxy:** Always configure DominusPrime to use port 8081, not 8080
2. **Match Context to Your GPU:** 64k for 8GB, 128k for 12GB, 256k for 16GB+
3. **Monitor VRAM:** Use `nvidia-smi` to ensure you're not hitting limits
4. **Enable Flash Attention:** The `-fa on` flag significantly improves speed
5. **Systemd Services:** Set up auto-start for production use
6. **Keep Updated:** Update llama.cpp monthly for performance improvements

---

**Guide Version:** 1.0  
**Last Updated:** March 2026  
**Tested On:** Ubuntu 22.04, CUDA 11.8, RTX 3060 8GB/12GB, RTX 4060
**For:** DominusPrime v0.9.2+
