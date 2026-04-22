# AMD ROCm Setup

ROCm (Radeon Open Compute) is AMD's GPU compute platform, equivalent to NVIDIA CUDA. Support levels vary significantly between backends and GPU generations.

---

## GPU Support Matrix

![AMD ROCm Backend Compatibility — Hardware Schematic](../diagrams/rendered/rocm_backend.png)

| GPU Series | Architecture | gfx ID | llama.cpp | vLLM | Ollama |
|-----------|-------------|--------|-----------|------|--------|
| MI300X / MI325X / MI350X / MI355X | CDNA3/3+ | gfx942 | Yes | Yes (primary) | Yes |
| MI250X / MI210 | CDNA2 | gfx90a | Yes | Limited | Yes |
| MI100 | CDNA | gfx908 | Yes | Limited | Yes |
| RX 7900 XTX / XT | RDNA3 | gfx1100 | Yes | No | Yes |
| RX 7800 XT / 7700 XT | RDNA3 | gfx1101/1102 | Yes | No | Yes |
| RX 6900 XT / 6800 XT | RDNA2 | gfx1030 | Yes | No | Yes |
| RX 6700 XT / 6600 XT | RDNA2 | gfx1031/1032 | Yes | No | Yes |

> **vLLM**: only officially supports MI300X, MI325X, MI350X, MI355X. Consumer RDNA2/RDNA3 GPUs are not supported by vLLM. Use llama.cpp for consumer AMD GPUs.

### VRAM on Common AMD GPUs

| GPU | VRAM | Recommended Model (Q4) |
|-----|------|----------------------|
| RX 7900 XTX | 24 GB | Qwen3.6-35B-A3B Q4, Gemma 4 31B Q4 |
| RX 7900 XT | 20 GB | Qwen3.6-35B-A3B Q3, Gemma 4 26B-A4B Q4 |
| RX 6900 XT | 16 GB | Qwen3.5-27B Q4, Gemma 4 26B-A4B Q4 (tight) |
| RX 6800 XT | 16 GB | Same as 6900 XT |
| MI300X | 192 GB HBM3 | Any model including 31B BF16 |

---

## Step 1 — Install ROCm

### Linux (Ubuntu 22.04 / 24.04 — recommended)

```bash
# Add ROCm repository
sudo apt-get update
sudo apt-get install -y wget gnupg

wget https://repo.radeon.com/rocm/rocm.gpg.key \
  -O - | gpg --dearmor | sudo tee /etc/apt/keyrings/rocm.gpg > /dev/null

echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/rocm.gpg] \
  https://repo.radeon.com/rocm/apt/6.4 jammy main" \
  | sudo tee /etc/apt/sources.list.d/rocm.list

sudo apt-get update
sudo apt-get install -y rocm-hip-sdk rocminfo rocm-smi-lib

# Add to PATH
echo 'export PATH=/opt/rocm/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/opt/rocm/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# Add your user to render/video groups
sudo usermod -aG render,video $USER
newgrp render

sudo reboot
```

### Verify Installation

```bash
rocminfo                  # lists all AMD GPU agents
rocm-smi                  # GPU monitoring (like nvidia-smi)
hipcc --version           # HIP compiler version
```

Expected output from `rocminfo`:

```
Agent 2
  Name:                    gfx1100
  ...
  Device Type:             GPU
```

### Windows

ROCm is supported on Windows for consumer RDNA GPUs via the ROCm for Windows package. Download from [rocm.docs.amd.com](https://rocm.docs.amd.com/en/latest/deploy/windows/).

> Note: ROCm Windows support lags Linux. For production workloads, prefer Linux.

---

## Step 2 — Identify Your GPU's gfx ID

```bash
rocminfo | grep -E "Name|gfx"
```

Or:

```bash
rocm-smi --showproductname
```

| GPU | gfx ID | `AMDGPU_TARGETS` value |
|-----|--------|----------------------|
| MI300X/MI325X | gfx942 | `gfx942` |
| MI250X | gfx90a | `gfx90a` |
| RX 7900 XTX/XT | gfx1100 | `gfx1100` |
| RX 7800 XT / 7700 XT | gfx1101 | `gfx1101` |
| RX 6900/6800 XT | gfx1030 | `gfx1030` |
| RX 6700 XT | gfx1031 | `gfx1031` |
| RX 6600 XT | gfx1032 | `gfx1032` |

---

## Step 3 — Build llama.cpp with ROCm (HIP)

```bash
# Dependencies
sudo apt-get install -y \
  build-essential cmake git \
  libcurl4-openssl-dev pciutils

git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp

# Set your GPU target (replace with your gfx ID from the table above)
export AMDGPU_TARGETS="gfx1100"  # RX 7900 XTX

# For multiple GPUs of different types:
# export AMDGPU_TARGETS="gfx1100;gfx1030"

cmake -B build \
  -DBUILD_SHARED_LIBS=OFF \
  -DGGML_HIP=ON \
  -DAMDGPU_TARGETS="$AMDGPU_TARGETS"

cmake --build build --config Release -j \
  --clean-first \
  --target llama-cli llama-mtmd-cli llama-server

cp build/bin/llama-* .
```

Verify ROCm is active at runtime:

```bash
./llama-cli --version
# Output should include: HIP (ROCm)
```

Running a model — you'll see:

```
ggml_hip_init: found 1 ROCm devices:
  Device 0: AMD Radeon RX 7900 XTX, gfx1100
load_tensors: ROCm0 model buffer size = 18000 MiB
```

### Multi-GPU (llama.cpp, ROCm)

```bash
# Split across 2 RX 7900 XTX (48 GB combined)
./llama-server \
  --model model.gguf \
  --n-gpu-layers 999 \
  --split-mode layer \
  --main-gpu 0 \
  --port 8001
```

> Known issue: Multi-GPU on ROCm sometimes causes segfaults. Check [llama.cpp issue #17583](https://github.com/ggml-org/llama.cpp/issues/17583) for status. Single GPU is stable.

---

## Step 4 — vLLM with ROCm (MI300X+ only)

### pip install

```bash
python3.12 -m venv .venv
source .venv/bin/activate

pip install vllm --pre \
  --extra-index-url https://wheels.vllm.ai/rocm/nightly/rocm721 \
  --upgrade
```

Requires: Python 3.12, ROCm 7.2.1, glibc >= 2.35 (Ubuntu 22.04+).

### Docker (recommended for MI300X)

```bash
docker pull vllm/vllm-openai-rocm:gemma4

docker run -itd --name vllm-rocm \
  --ipc=host \
  --network=host \
  --privileged \
  --cap-add=CAP_SYS_ADMIN \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add=video \
  --cap-add=SYS_PTRACE \
  --security-opt=seccomp=unconfined \
  --shm-size 16G \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai-rocm:gemma4 \
  --model google/gemma-4-26B-A4B-it \
  --host 0.0.0.0 \
  --port 8000
```

---

## Step 5 — Ollama with ROCm

Ollama auto-detects ROCm after installation. No extra steps needed if ROCm is installed system-wide.

```bash
# Install Ollama (ROCm-capable builds are included)
curl -fsSL https://ollama.com/install.sh | sh

# Verify GPU is used
ollama run gemma4:e4b "hello"
rocm-smi  # check GPU utilization
```

---

## GPU Offloading (llama.cpp)

```bash
# Full GPU offload (all layers to ROCm GPU)
./llama-server \
  --model model.gguf \
  -n 999 \
  --port 8001

# Partial offload (50 layers to GPU, rest to CPU)
./llama-server \
  --model model.gguf \
  --n-gpu-layers 50 \
  --port 8001
```

Check utilization:

```bash
watch -n 1 rocm-smi
```

---

## Monitoring

```bash
# GPU stats
rocm-smi

# Continuous monitoring
rocm-smi --showmeminfo vram --showuse --showtemp

# Process using GPU
rocm-smi --showpids

# Per-GPU utilization
watch -n 1 rocm-smi
```

---

## Flash Attention on ROCm

Flash Attention is supported on RDNA3 (gfx1100) and CDNA3 (gfx942). Enable in llama.cpp:

```bash
./llama-server --model model.gguf --flash-attn ...
```

---

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `No ROCm devices found` | ROCm not installed or user groups wrong | Add user to `render` and `video` groups, reboot |
| Build fails: `AMDGPU_TARGETS` unrecognized | Wrong gfx ID | Check with `rocminfo | grep gfx` |
| Very slow (1–3 tok/s) | Model not fully on GPU | Check `-n` flag; reduce model size or increase offloaded layers |
| Segfault on multi-GPU | Known ROCm llama.cpp bug | Use single GPU |
| vLLM fails on consumer AMD | vLLM only supports MI300X+ | Use llama.cpp instead |
| `hipErrorNoBinaryForGpu` | Binary compiled for wrong gfx | Set `AMDGPU_TARGETS` correctly and rebuild |
| OOM on RX 7900 XTX (24 GB) | Model + context too large | Reduce `--ctx-size` or use smaller quant |

---

## Performance Tips

- **Flash Attention** (`--flash-attn`): significant VRAM savings on long contexts
- **KV cache quantization**: `--cache-type-k q8_0 --cache-type-v q8_0` saves ~50% KV cache VRAM
- **Batch size**: RDNA3 GPUs have good throughput per watt; with llama-server `--parallel 2` can help throughput without losing single-request latency
- **HIP_VISIBLE_DEVICES**: equivalent to `CUDA_VISIBLE_DEVICES` for GPU selection

```bash
HIP_VISIBLE_DEVICES=0 ./llama-server ...
```