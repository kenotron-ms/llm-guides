# NVIDIA CUDA Setup

All four backends (llama.cpp, Ollama, vLLM, LM Studio) support NVIDIA CUDA. This guide covers driver installation, CUDA toolkit setup, and backend-specific notes.

---

## Supported GPUs

![Hardware Selector — Decision Schematic](../diagrams/rendered/hardware_selector.png)

Any NVIDIA GPU with compute capability 6.0+ works for llama.cpp and Ollama.  
vLLM requires compute capability 7.0+ (Volta and newer) for optimal performance, 8.0+ for BF16 and FP8.

| GPU Class | Compute Cap | VRAM | Recommended Use |
|-----------|-------------|------|-----------------|
| RTX 50xx (Blackwell) | 10.0 | 16–24 GB | Any model up to 35B-A3B |
| RTX 40xx (Ada Lovelace) | 8.9 | 12–24 GB | Any model up to 35B-A3B (Q4) |
| RTX 30xx (Ampere) | 8.6 | 8–24 GB | Up to 35B-A3B Q4 (24 GB) |
| A100 / H100 | 8.0 / 9.0 | 40–80 GB | All models including 31B BF16 |
| A6000 | 8.6 | 48 GB | 31B or 26B-A4B BF16 |
| RTX 20xx (Turing) | 7.5 | 8–11 GB | Small models only (E2B/E4B) |

---

## Step 1 — Install NVIDIA Driver

### Linux

```bash
# Check current driver
nvidia-smi

# Ubuntu — install latest driver via apt
sudo apt-get update
sudo ubuntu-drivers autoinstall
# or specific version:
sudo apt-get install -y nvidia-driver-570

sudo reboot
nvidia-smi  # verify after reboot
```

### Windows

1. Download from [nvidia.com/drivers](https://www.nvidia.com/drivers)
2. Run the installer (choose "Custom" → clean install for fresh setups)
3. Reboot

### macOS

NVIDIA GPUs are not supported on macOS (Apple dropped NVIDIA support in 2019). Use [hardware/mlx.md](mlx.md) instead.

---

## Step 2 — Install CUDA Toolkit

### Linux

```bash
# Ubuntu 22.04 / 24.04 — CUDA 12.8 (stable, compatible with all backends)
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get install -y cuda-toolkit-12-8

# Add to PATH
echo 'export PATH=/usr/local/cuda-12.8/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.8/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# Verify
nvcc --version
```

### Windows

Download the CUDA Toolkit installer from [developer.nvidia.com/cuda-downloads](https://developer.nvidia.com/cuda-downloads).

> **Important**: Do not install CUDA 13.2. It produces garbage output with GGUF models (known bug). Use CUDA 12.x or CUDA 13.0.

### Check CUDA Version

```bash
nvcc --version
nvidia-smi  # shows driver version and max CUDA version supported
```

---

## Step 3 — Verify GPU Compute Capability

```bash
# Quick check
nvidia-smi --query-gpu=name,compute_cap --format=csv

# Python check
python3 -c "import torch; print(torch.cuda.get_device_capability())"
```

---

## Step 4 — Backend Setup

### llama.cpp

Build with `-DGGML_CUDA=ON`:

```bash
cmake llama.cpp -B llama.cpp/build \
  -DBUILD_SHARED_LIBS=OFF \
  -DGGML_CUDA=ON

cmake --build llama.cpp/build --config Release -j \
  --clean-first \
  --target llama-cli llama-mtmd-cli llama-server llama-gguf-split

cp llama.cpp/build/bin/llama-* llama.cpp/
```

Verify CUDA is active:

```bash
./llama.cpp/llama-cli --version
# should show: CUDA backend
```

At runtime, you'll see:

```
ggml_cuda_init: found 1 CUDA devices:
  Device 0: NVIDIA GeForce RTX 4090, compute capability 8.9
```

### Ollama

Ollama auto-detects CUDA. Verify:

```bash
ollama serve &
ollama run gemma4:e4b "hello"
# Check nvidia-smi — GPU memory should increase
nvidia-smi
```

### vLLM

CUDA is the primary target:

```bash
pip install vllm

# Verify
python3 -c "import vllm; print('vLLM OK')"
python3 -c "import torch; print(torch.cuda.is_available())"
```

### LM Studio

Download and run the installer — CUDA is detected automatically.

---

## Multi-GPU Setup

### Verify All GPUs Are Visible

```bash
nvidia-smi -L
# GPU 0: NVIDIA A100-SXM4-80GB (UUID: ...)
# GPU 1: NVIDIA A100-SXM4-80GB (UUID: ...)
```

### llama.cpp — Layer Split Across GPUs

```bash
./llama.cpp/llama-server \
  --model model.gguf \
  --n-gpu-layers 999 \
  --split-mode layer \
  --main-gpu 0 \
  --port 8001
```

### vLLM — Tensor Parallelism

```bash
vllm serve google/gemma-4-31B-it \
  --tensor-parallel-size 2 \
  --max-model-len 32768

# Or select specific GPUs:
CUDA_VISIBLE_DEVICES=0,1 vllm serve model --tensor-parallel-size 2
```

### GPU Isolation

```bash
# Use only GPU 1
CUDA_VISIBLE_DEVICES=1 ./llama.cpp/llama-server ...

# vLLM
CUDA_VISIBLE_DEVICES=0,1 vllm serve ...
```

---

## Flash Attention

Flash Attention 2 significantly reduces VRAM for long context windows. Supported on compute capability 8.0+ (A100, H100, RTX 30xx+).

```bash
# llama.cpp
./llama-server --model model.gguf --flash-attn ...

# vLLM — enabled by default on supported hardware
```

---

## KV Cache Quantization (VRAM Reduction)

When running near VRAM limits, quantize the KV cache:

```bash
# llama.cpp
--cache-type-k q8_0 --cache-type-v q8_0   # ~50% smaller, good quality
--cache-type-k q4_0 --cache-type-v q4_0   # ~75% smaller, slight quality drop

# If seeing gibberish with above:
--cache-type-k bf16 --cache-type-v bf16   # fixes some model quirks
```

---

## Monitoring

```bash
# Watch GPU utilization and VRAM live
watch -n 1 nvidia-smi

# More detail
nvidia-smi dmon -s pucvmet

# GPU memory used by process
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
```

---

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `CUDA_ERROR_NO_DEVICE` | Driver not installed / mismatch | Reinstall driver, reboot |
| Gibberish output (GGUF) | CUDA 13.2 bug | Downgrade to CUDA 12.8 or 13.0 |
| `CUDA out of memory` | Model too large | Reduce `--n-gpu-layers`, smaller quant, reduce context |
| `nvcc not found` | CUDA toolkit not in PATH | Add `/usr/local/cuda/bin` to `PATH` |
| vLLM import fails | PyTorch/CUDA version mismatch | Reinstall with matching versions |
| RTX 20xx slow | No BF16 support (needs Ampere+) | Use FP16 explicitly: `--dtype float16` |