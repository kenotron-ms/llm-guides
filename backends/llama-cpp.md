# llama.cpp Guide

**llama.cpp** is a C/C++ LLM inference engine for GGUF models. It supports every hardware backend in this guide (CUDA, ROCm, Metal/MLX, CPU) with no Python dependencies and produces a minimal-footprint local server.

- Repo: https://github.com/ggml-org/llama.cpp
- Format: GGUF (`.gguf` files)
- API: OpenAI-compatible REST (`/v1/chat/completions`, `/v1/completions`)
- Primary binaries: `llama-cli` (interactive), `llama-server` (API), `llama-mtmd-cli` (multimodal)

---

![Backend Selector — Decision Schematic](../diagrams/rendered/backend_selector.png)

## Installation

### Option A — Pre-built Binaries (fastest)

Download from the [GitHub Releases](https://github.com/ggml-org/llama.cpp/releases) page. Pick the right archive:

| Archive suffix | Use for |
|----------------|---------|
| `...-cuda-cu12...` | NVIDIA, CUDA 12.x |
| `...-hip-...` | AMD ROCm |
| `...-metal-...` | Apple Silicon / macOS |
| `...-noavx...` | CPU-only, older CPUs |
| `...-avx2...` | CPU-only, modern x86 |

### Option B — Build from Source

**Prerequisites** (all platforms):

```bash
# Linux / Debian/Ubuntu
apt-get update
apt-get install -y pciutils build-essential cmake curl libcurl4-openssl-dev git
```

```bash
# macOS (via Homebrew)
brew install cmake curl
```

**Clone**:

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
```

**Build — NVIDIA CUDA**:

```bash
cmake -B build \
  -DBUILD_SHARED_LIBS=OFF \
  -DGGML_CUDA=ON
cmake --build build --config Release -j \
  --clean-first \
  --target llama-cli llama-mtmd-cli llama-server llama-gguf-split
cp build/bin/llama-* .
```

**Build — AMD ROCm** (Linux):

```bash
# Ensure ROCm 6.3+ is installed first — see hardware/rocm.md
cmake -B build \
  -DBUILD_SHARED_LIBS=OFF \
  -DGGML_HIP=ON \
  -DAMDGPU_TARGETS="gfx1100;gfx1030"   # RX 7000=gfx1100, RX 6000=gfx1030
cmake --build build --config Release -j \
  --clean-first \
  --target llama-cli llama-mtmd-cli llama-server
cp build/bin/llama-* .
```

See [hardware/rocm.md](../hardware/rocm.md) for the full `AMDGPU_TARGETS` table.

**Build — Apple Silicon (Metal)**:

```bash
# Metal is auto-detected on macOS — no extra flags needed
cmake -B build \
  -DBUILD_SHARED_LIBS=OFF \
  -DGGML_CUDA=OFF
cmake --build build --config Release -j \
  --clean-first \
  --target llama-cli llama-mtmd-cli llama-server
cp build/bin/llama-* .
```

**Build — CPU only**:

```bash
cmake -B build \
  -DBUILD_SHARED_LIBS=OFF \
  -DGGML_CUDA=OFF
cmake --build build --config Release -j \
  --target llama-cli llama-server
cp build/bin/llama-* .
```

---

## Downloading Models

### Via Hugging Face CLI (recommended)

```bash
pip install huggingface_hub hf_transfer

# Set a cache directory
export LLAMA_CACHE="./models"

# Gemma 4 26B-A4B (4-bit + multimodal projector)
hf download unsloth/gemma-4-26B-A4B-it-GGUF \
  --local-dir ./models/gemma4-26b \
  --include "*mmproj-BF16*" \
  --include "*UD-Q4_K_XL*"

# Qwen3.6-35B-A3B (4-bit + mmproj)
hf download unsloth/Qwen3.6-35B-A3B-GGUF \
  --local-dir ./models/qwen3.6-35b \
  --include "*mmproj-F16*" \
  --include "*UD-Q4_K_XL*"
```

### Stream Directly (no pre-download)

llama.cpp can stream GGUF files from Hugging Face on first run, caching to `LLAMA_CACHE`:

```bash
export LLAMA_CACHE="./models"
./llama-cli -hf unsloth/gemma-4-26B-A4B-it-GGUF:UD-Q4_K_XL ...
```

---

## Key Flags Reference

| Flag | Description |
|------|-------------|
| `-m` / `--model` | Path to `.gguf` model file |
| `-hf` | Stream model from Hugging Face (format: `owner/repo:filename`) |
| `--mmproj` | Path to multimodal projector `.gguf` (vision models) |
| `-n` / `--n-gpu-layers` | Layers to offload to GPU. `-1` or `999` = all |
| `--ctx-size` | Context window size in tokens (0 = auto from model) |
| `--temp` | Temperature |
| `--top-p` | Top-p nucleus sampling |
| `--top-k` | Top-k sampling |
| `--min-p` | Min-p sampling |
| `--repeat-penalty` | Repetition penalty (1.0 = off) |
| `-fa` / `--flash-attn` | Enable flash attention (reduces memory, speeds up) |
| `--cache-type-k` | KV cache type: `f16`, `bf16`, `q8_0`, `q4_0` |
| `--cache-type-v` | Same for V cache |
| `--port` | llama-server port (default 8080) |
| `--alias` | Model alias returned in `/v1/models` |
| `--chat-template-kwargs` | JSON kwargs passed to chat template |
| `-np` / `--parallel` | Number of parallel request slots (server) |
| `--cont-batching` | Continuous batching for server |

---

## Running Models

### Interactive Chat (llama-cli)

```bash
# Gemma 4 26B-A4B, thinking on
export LLAMA_CACHE="./models"
./llama-cli \
  -hf unsloth/gemma-4-26B-A4B-it-GGUF:UD-Q4_K_XL \
  -n 999 \
  --temp 1.0 \
  --top-p 0.95 \
  --top-k 64 \
  --chat-template-kwargs '{"enable_thinking":true}'

# Qwen3.6 35B-A3B, coding mode
./llama-cli \
  -hf unsloth/Qwen3.6-35B-A3B-GGUF:UD-Q4_K_XL \
  -n 999 \
  --temp 0.6 \
  --top-p 0.95 \
  --top-k 20 \
  --chat-template-kwargs '{"enable_thinking":true}'
```

### Multimodal Chat (llama-mtmd-cli)

```bash
./llama-mtmd-cli \
  --model ./models/gemma4-26b/gemma-4-26B-A4B-it-UD-Q4_K_XL.gguf \
  --mmproj ./models/gemma4-26b/mmproj-BF16.gguf \
  -n 999 \
  --temp 1.0 \
  --top-p 0.95 \
  --top-k 64
```

### API Server (llama-server)

```bash
./llama-server \
  --model ./models/gemma4-26b/gemma-4-26B-A4B-it-UD-Q4_K_XL.gguf \
  --mmproj ./models/gemma4-26b/mmproj-BF16.gguf \
  --alias "gemma4-26b" \
  --ctx-size 32768 \
  --n-gpu-layers 999 \
  --flash-attn \
  --temp 1.0 \
  --top-p 0.95 \
  --top-k 64 \
  --parallel 4 \
  --cont-batching \
  --port 8001
```

The server exposes:
- `GET  /v1/models` — list loaded models
- `POST /v1/chat/completions` — OpenAI-compatible chat
- `POST /v1/completions` — raw completion
- `GET  /health` — readiness check

---

## GPU Offloading

### Full GPU Offload

```bash
-n 999   # or --n-gpu-layers 999 — offloads all layers
```

### Partial Offload (split between GPU and CPU RAM)

If the model is larger than VRAM, llama.cpp automatically splits layers. CPU layers are slower. Control the split explicitly:

```bash
# Offload only 40 layers (roughly half a 35B model) to GPU
--n-gpu-layers 40
```

Check how many layers your model has — it's shown in the load output:

```
load_tensors: offloading 40 repeating layers to GPU
load_tensors: CPU_Mapped model buffer size = ...
load_tensors: CUDA0 model buffer size = ...
```

### Multi-GPU (split across GPUs)

```bash
# Split evenly across 2 GPUs
--n-gpu-layers 999 --split-mode layer

# Pin GPU 1 as main compute
--main-gpu 0
```

### Flash Attention (memory reduction)

Enabled with `--flash-attn` / `-fa`. Reduces KV cache memory at long context lengths. Use when running near the edge of VRAM.

### KV Cache Quantization (memory reduction)

```bash
# Q8 KV cache — good quality, ~50% smaller than F16
--cache-type-k q8_0 --cache-type-v q8_0

# BF16 KV cache — near-lossless, needed for some models with gibberish issues
--cache-type-k bf16 --cache-type-v bf16
```

---

## Serving Multiple Requests

```bash
./llama-server \
  --model ./models/qwen3.6-35b/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf \
  --alias "qwen3.6-35b" \
  --ctx-size 8192 \
  --n-gpu-layers 999 \
  --parallel 8 \
  --cont-batching \
  --port 8001
```

- `--parallel N`: number of simultaneous request slots. Each slot uses `ctx-size` tokens of KV cache.
- `--cont-batching`: enables continuous batching — new requests start processing as soon as a slot frees mid-generation.
- Total KV cache = `ctx-size × parallel`. With 8K ctx and 8 slots = 64K tokens of KV cache VRAM.

---

## OpenAI API Examples

### Python

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8001/v1",
    api_key="none",  # llama-server doesn't validate the key
)

response = client.chat.completions.create(
    model="gemma4-26b",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain how KV cache works in transformers."}
    ],
    max_tokens=2048,
    temperature=1.0,
    top_p=0.95,
)
print(response.choices[0].message.content)
```

### cURL

```bash
curl http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma4-26b",
    "messages": [{"role": "user", "content": "What is 2+2?"}],
    "max_tokens": 256,
    "temperature": 1.0
  }'
```

---

## Per-Model Configuration Snippets

### Gemma 4 26B-A4B (server, thinking on)

```bash
./llama-server \
  --model ./models/gemma4-26b/gemma-4-26B-A4B-it-UD-Q4_K_XL.gguf \
  --mmproj ./models/gemma4-26b/mmproj-BF16.gguf \
  --alias "gemma4-26b" \
  --ctx-size 32768 \
  -n 999 -fa \
  --temp 1.0 --top-p 0.95 --top-k 64 \
  --parallel 2 --cont-batching \
  --chat-template-kwargs '{"enable_thinking":true}' \
  --port 8001
```

### Gemma 4 31B (server, no thinking)

```bash
./llama-server \
  --model ./models/gemma4-31b/gemma-4-31B-it-UD-Q4_K_XL.gguf \
  --mmproj ./models/gemma4-31b/mmproj-BF16.gguf \
  --alias "gemma4-31b" \
  --ctx-size 16384 \
  -n 999 -fa \
  --temp 1.0 --top-p 0.95 --top-k 64 \
  --chat-template-kwargs '{"enable_thinking":false}' \
  --port 8002
```

### Qwen3.6-35B-A3B (server, non-thinking instruct)

```bash
./llama-server \
  --model ./models/qwen3.6-35b/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf \
  --mmproj ./models/qwen3.6-35b/mmproj-F16.gguf \
  --alias "qwen3.6-35b" \
  --ctx-size 16384 \
  -n 999 -fa \
  --temp 0.7 --top-p 0.8 --top-k 20 \
  --chat-template-kwargs '{"enable_thinking":false}' \
  --port 8003
```

### Qwen3.5-27B (server, thinking, general tasks)

```bash
./llama-server \
  --model ./models/qwen3.5-27b/Qwen3.5-27B-Instruct-UD-Q4_K_XL.gguf \
  --alias "qwen3.5-27b" \
  --ctx-size 32768 \
  -n 999 -fa \
  --temp 1.0 --top-p 0.95 --top-k 20 \
  --chat-template-kwargs '{"enable_thinking":true}' \
  --port 8004
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Gibberish / random output | CUDA 13.2 runtime | Use CUDA 12.x or 13.0 |
| Gibberish / random output | Context too small | Increase `--ctx-size` or try `--cache-type-k bf16 --cache-type-v bf16` |
| `CUDA out of memory` | Model too large for VRAM | Reduce `--n-gpu-layers`, reduce `--ctx-size`, or use smaller quant |
| Very slow (< 1 tok/s) | Layers offloaded to CPU | Reduce model size or increase `--n-gpu-layers` with a GPU |
| Model stops too early | Wrong EOS token (Gemma 4) | Update llama.cpp to latest release |
| ROCm build fails | Missing `AMDGPU_TARGETS` | See `hardware/rocm.md` for your GPU's gfx ID |
| `Segmentation fault` on AMD multi-GPU | Known llama.cpp ROCm issue | Use single GPU or check latest ROCm/llama.cpp issues |