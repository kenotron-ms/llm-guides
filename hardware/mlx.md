# Apple Silicon (MLX) Setup

Apple Silicon Macs (M1, M2, M3, M4) use unified memory — RAM and GPU memory are the same pool. This means a 32 GB M3 Pro has 32 GB of effective "VRAM" for models. Metal (Apple's GPU API) is used for acceleration.

Two inference paths are available:

![Apple Silicon (MLX) Path Selector — Decision Schematic](../diagrams/rendered/mlx_path_selector.png)

1. **llama.cpp with Metal** — runs GGUF models, auto-detected on macOS
2. **mlx_vlm** — Apple's native MLX framework, higher throughput on Apple Silicon for supported models

---

## Hardware Overview

| Chip | Unified Memory Options | Practical Max Model |
|------|----------------------|-------------------|
| M1 | 8, 16 GB | Gemma 4 E4B Q4, Qwen3.5-27B Q3 |
| M1 Pro | 16, 32 GB | Gemma 4 26B-A4B Q4, Qwen3.5-27B Q4 |
| M1 Max | 32, 64 GB | Gemma 4 31B Q6, Qwen3.6-35B-A3B Q6 |
| M1 Ultra | 64, 128 GB | Qwen3.5-122B-A10B Q4 |
| M2 | 8, 16, 24 GB | Gemma 4 E4B / 26B-A4B Q3 |
| M2 Pro | 16, 32 GB | Same as M1 Pro |
| M2 Max | 32, 96 GB | Gemma 4 31B Q8 (96 GB), all 35B models |
| M2 Ultra | 64, 192 GB | Qwen3.5-122B-A10B Q8 |
| M3 | 8, 16, 24 GB | Gemma 4 E4B / 26B-A4B Q4 |
| M3 Pro | 18, 36 GB | Gemma 4 31B Q4, Qwen3.6-35B-A3B Q4 |
| M3 Max | 36, 48, 96, 128 GB | Gemma 4 31B BF16 (48 GB), all 35B BF16 |
| M3 Ultra | 192 GB | Qwen3.5-122B-A10B BF16 |
| M4 | 16, 32 GB | Gemma 4 26B-A4B Q4 |
| M4 Pro | 24, 48, 64 GB | Gemma 4 31B Q4–Q8, Qwen3.6 Q6 |
| M4 Max | 48, 64, 128 GB | Any 35B model at Q8 or BF16 |

> Rule of thumb: your unified memory ≥ quantized model file size = full-speed Metal inference.

---

## Path 1 — llama.cpp with Metal

Metal acceleration is built into every macOS llama.cpp build. No extra flags needed — just don't disable it.

### Install Dependencies

```bash
# Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Build dependencies
brew install cmake git curl
```

### Build llama.cpp

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp

# Metal is on by default on macOS. GGML_CUDA=OFF is explicit but not required.
cmake -B build \
  -DBUILD_SHARED_LIBS=OFF \
  -DGGML_CUDA=OFF

cmake --build build --config Release -j \
  --clean-first \
  --target llama-cli llama-mtmd-cli llama-server

cp build/bin/llama-* .
```

Verify Metal is active:

```bash
./llama-cli --version
# Should show: Metal

# At runtime you'll see:
# ggml_metal_init: GPU name: Apple M3 Max
# ggml_metal_init: recommendedMaxWorkingSetSize = 49152 MB
```

### Run Models

Metal uses `-n 999` (full offload) by default on macOS:

```bash
export LLAMA_CACHE="./models"

# Gemma 4 26B-A4B (fits 32 GB+ Mac)
./llama-cli \
  -hf unsloth/gemma-4-26B-A4B-it-GGUF:UD-Q4_K_XL \
  -n 999 \
  --temp 1.0 --top-p 0.95 --top-k 64 \
  --chat-template-kwargs '{"enable_thinking":true}'

# Qwen3.6-35B-A3B (fits 36 GB+ Mac at Q4)
./llama-cli \
  -hf unsloth/Qwen3.6-35B-A3B-GGUF:UD-Q4_K_XL \
  -n 999 \
  --temp 0.6 --top-p 0.95 --top-k 20 \
  --chat-template-kwargs '{"enable_thinking":true}'

# Qwen3.5-27B (fits 16 GB Mac at Q4)
./llama-cli \
  -hf unsloth/Qwen3.5-27B-Instruct-GGUF:UD-Q4_K_XL \
  -n 999 \
  --temp 0.6 --top-p 0.95 --top-k 20
```

### API Server on macOS

```bash
./llama-server \
  --model ./models/gemma4-26b/gemma-4-26B-A4B-it-UD-Q4_K_XL.gguf \
  --mmproj ./models/gemma4-26b/mmproj-BF16.gguf \
  --alias "gemma4-26b" \
  --ctx-size 32768 \
  -n 999 \
  --flash-attn \
  --temp 1.0 --top-p 0.95 --top-k 64 \
  --parallel 2 --cont-batching \
  --chat-template-kwargs '{"enable_thinking":true}' \
  --port 8001
```

---

## Path 2 — mlx_vlm (Native MLX, higher throughput)

[mlx_vlm](https://github.com/Blaizzy/mlx-vlm) is a VLM inference library built directly on Apple's MLX framework. It generally achieves **higher tokens/sec than llama.cpp Metal** on Apple Silicon for supported models, and is the recommended path for Qwen3.6 and Gemma 4 on Mac.

### Install for Qwen3.6

```bash
# Unsloth installer handles all dependencies
curl -fsSL https://raw.githubusercontent.com/unslothai/unsloth/refs/heads/main/scripts/install_qwen3_6_mlx.sh | sh

# Activate the environment
source ~/.unsloth/unsloth_qwen3_6_mlx/bin/activate
```

### Install for Gemma 4

```bash
curl -fsSL https://raw.githubusercontent.com/unslothai/unsloth/refs/heads/main/scripts/install_gemma4_mlx.sh | sh
source ~/.unsloth/unsloth_gemma4_mlx/bin/activate
```

### Manual Install (if needed)

```bash
pip install mlx mlx-vlm
```

### MLX Model Variants (Unsloth Dynamic)

| Model | 4-bit MLX | 8-bit MLX |
|-------|-----------|-----------|
| Gemma 4 31B | `unsloth/gemma-4-31b-it-UD-MLX-4bit` | `unsloth/gemma-4-31b-it-UD-MLX-8bit` |
| Gemma 4 26B-A4B | `unsloth/gemma-4-26b-a4b-it-UD-MLX-4bit` | `unsloth/gemma-4-26b-a4b-it-UD-MLX-8bit` |
| Gemma 4 E4B | `unsloth/gemma-4-e4b-it-UD-MLX-4bit` | `unsloth/gemma-4-e4b-it-UD-MLX-8bit` |
| Gemma 4 E2B | `unsloth/gemma-4-e2b-it-UD-MLX-4bit` | `unsloth/gemma-4-e2b-it-UD-MLX-8bit` |
| Qwen3.6-35B-A3B | `unsloth/Qwen3.6-35B-A3B-UD-MLX-4bit` | — |

### Run Chat (MLX)

```bash
# Gemma 4 26B-A4B, thinking on
python -m mlx_vlm.chat \
  --model unsloth/gemma-4-26b-a4b-it-UD-MLX-4bit \
  --chat-template-kwargs '{"enable_thinking":true}'

# Qwen3.6, thinking on
python -m mlx_vlm.chat \
  --model unsloth/Qwen3.6-35B-A3B-UD-MLX-4bit \
  --chat-template-kwargs '{"enable_thinking":true}'

# Gemma 4 E4B (small/fast model for laptop)
python -m mlx_vlm.chat \
  --model unsloth/gemma-4-e4b-it-UD-MLX-4bit \
  --chat-template-kwargs '{"enable_thinking":false}'
```

### MLX API Server

mlx_vlm doesn't include a built-in server. For API access on macOS, use llama.cpp Metal (llama-server) or Ollama.

---

## Ollama on macOS

Ollama uses Metal automatically on macOS. Best for simple one-command setup:

```bash
# Download macOS app from https://ollama.com/download/mac
# Or:
curl -fsSL https://ollama.com/install.sh | sh

ollama pull gemma4:26b
ollama run gemma4:26b
```

---

## LM Studio on macOS

LM Studio supports Metal natively. The macOS app is the recommended way for non-technical team members. See [backends/lmstudio.md](../backends/lmstudio.md).

For best performance, look for MLX-format models in LM Studio's catalog — these use the native MLX engine.

---

## Memory Management on macOS

macOS manages unified memory dynamically. When a model is loaded, macOS may swap other apps out of the memory pool. This is normal.

### Check Memory Pressure

```bash
# via vm_stat
vm_stat | head -20

# via memory pressure tool
memory_pressure

# Activity Monitor → Memory tab → Memory Pressure graph
```

### Free Memory Before Loading Large Models

```bash
# Quit memory-heavy apps (Chrome, Xcode, Docker, etc.)
# Then load the model
```

### Model Swaps to Disk (wired memory)

If the model is larger than your Mac's free RAM, macOS will use swap (SSD). Inference will be very slow. Either:
- Use a smaller quantization
- Close other applications
- Use a Mac with more unified memory

---

## Performance Comparison on Apple Silicon

For Gemma 4 26B-A4B Q4 on M3 Max 48 GB (approximate):

| Backend | Tokens/sec (generation) | Notes |
|---------|------------------------|-------|
| mlx_vlm | ~35–45 tok/s | Native MLX, best throughput |
| llama.cpp Metal | ~25–35 tok/s | More control, multimodal support |
| Ollama (Metal) | ~20–30 tok/s | Easy setup, slightly lower throughput |

> Numbers vary by model size, quantization, context length, and Mac generation. M4 chips are ~20–30% faster than M3 for the same memory config.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Model loads but very slow | Check if model fits in RAM — use `vm_stat` or Activity Monitor |
| `ggml_metal_init: error` | Update macOS (Metal bugs fixed in updates); check Xcode CLI tools are installed |
| `xcrun: error` on cmake | `xcode-select --install` |
| MLX install fails | Ensure Python 3.10+ and macOS 13+ (Ventura minimum for MLX) |
| Out of memory with MLX | Switch to 4-bit variant or smaller model |
| Model downloads slow | Enable `hf_transfer`: `export HF_HUB_ENABLE_HF_TRANSFER=1` |
| Metal not detected in llama.cpp | Rebuild with `cmake -DGGML_CUDA=OFF -DGGML_METAL=ON` (or just default macOS build) |