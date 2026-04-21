# Ollama Guide

**Ollama** is the fastest path to a running local LLM. It wraps llama.cpp with automatic GPU detection, a model registry, and a one-command setup. Best for individuals and small teams who want a local OpenAI-compatible API without build steps.

- Site: https://ollama.com
- API: OpenAI-compatible at `http://localhost:11434`
- Format: GGUF (managed internally)
- Supports: CUDA, ROCm, Metal (Apple Silicon), CPU fallback

---

![Backend Selector — Decision Schematic](../diagrams/rendered/backend_selector.png)
*[view / edit source](https://mermaid.live/edit#pako:TZJRT8IwFIX/ypW50TB0qC/0QQMbkCWdYBDUjD3UtUhDt86uVZPBf3dzmaxNmpxz7v3a3LREiWIcYbST6jvZU23g2d9mUK3xRfSypwaYggAyztlDfAmDwT1Myvk6AM0/rdCVe2rKJ3V2fOPFEUi4ikgIK2OZUHE3flRH8MrQSiMGtuAariHXitnECJW1JO9M8svHTeAHY1AawuDWdV/7bZV/rtqQ6IuQMO4G9U3Ei6SkKb1K8jzusutwWj5ZkRyg4MbmDhhOUxgvgxY/PeMXJFr8ceJuVDNm5cxKCfPlGvrgVWeiMqOVbCGzzky8rlU3L8g2a7xqXhjjd/XTyA3pKuJ11eI/a3QiaVH4fAeVBzshJe4N6ZDecKeoHnLguHdHRy4bOYmSSuMed+u9zZCDUq5TKhjCJTJ7ntafgFF9QCcH2ZxRw31BPzRNETba8tMv)*

## Installation

```bash
# Linux / macOS — one-liner
curl -fsSL https://ollama.com/install.sh | sh

# macOS — native app (also handles Metal acceleration)
# Download from https://ollama.com/download/mac

# Windows — download installer from https://ollama.com/download/windows
```

### Verify Installation

```bash
ollama --version
ollama list    # empty at first
```

Ollama starts a background service automatically on Linux (systemd) and macOS.

---

## Pulling Models

### Gemma 4

```bash
ollama pull gemma4:e2b      # ~3 GB, edge/phone class
ollama pull gemma4:e4b      # ~5 GB, laptop class
ollama pull gemma4:26b      # ~16 GB, 26B-A4B MoE (recommended)
ollama pull gemma4:31b      # ~17 GB, 31B dense (highest quality)
```

### Qwen3.6

```bash
ollama pull qwen3.6:35b-a3b     # ~23 GB, 4-bit
```

### Qwen3.5

```bash
ollama pull qwen3.5:27b         # ~14 GB, 4-bit
ollama pull qwen3.5:35b-a3b     # ~18 GB, MoE
```

### Specific Quantizations

Ollama tags follow the pattern `model:size-quantization`:

```bash
# Q4_K_M (default for most models)
ollama pull gemma4:26b

# Q8_0 (higher quality, larger)
ollama pull gemma4:e4b:q8_0

# List available tags
ollama show gemma4 --tags
```

---

## Running Models

### Interactive Chat

```bash
ollama run gemma4:26b
ollama run qwen3.6:35b-a3b
ollama run qwen3.5:27b
```

To exit: type `/bye` or `Ctrl+D`.

### One-Shot Query

```bash
ollama run gemma4:26b "Explain the MoE architecture in 3 sentences."
```

### Stop / Remove

```bash
ollama stop gemma4:26b      # unload from memory
ollama rm gemma4:26b        # delete model files
ollama list                  # show downloaded models
```

---

## API Usage

Ollama runs an OpenAI-compatible server on port `11434` by default.

### Python (openai SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # required but not validated
)

response = client.chat.completions.create(
    model="gemma4:26b",
    messages=[
        {"role": "system", "content": "You are a concise assistant."},
        {"role": "user", "content": "What is Mixture of Experts?"}
    ],
    max_tokens=1024,
    temperature=1.0,
)
print(response.choices[0].message.content)
```

### cURL

```bash
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.6:35b-a3b",
    "messages": [{"role": "user", "content": "Write a Python fibonacci function."}],
    "max_tokens": 512,
    "temperature": 0.6
  }'
```

### Ollama-native API (non-OpenAI)

```bash
# Generate (raw)
curl http://localhost:11434/api/generate \
  -d '{"model": "gemma4:26b", "prompt": "Why is the sky blue?", "stream": false}'

# Chat
curl http://localhost:11434/api/chat \
  -d '{
    "model": "gemma4:26b",
    "messages": [{"role": "user", "content": "Why is the sky blue?"}],
    "stream": false
  }'
```

---

## Modelfiles — Custom System Prompts and Parameters

Ollama lets you package a model with custom defaults in a `Modelfile`:

```Dockerfile
# Modelfile for Qwen3.6 in thinking mode (coding)
FROM qwen3.6:35b-a3b

PARAMETER temperature 0.6
PARAMETER top_p 0.95
PARAMETER top_k 20
PARAMETER num_ctx 32768

SYSTEM """
You are an expert software engineer. Think through problems carefully before answering.
"""

# Enable thinking mode via template override
TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
"""
```

```bash
ollama create qwen3.6-coder -f Modelfile
ollama run qwen3.6-coder
```

### Gemma 4 with Thinking

```Dockerfile
FROM gemma4:26b

PARAMETER temperature 1.0
PARAMETER top_p 0.95
PARAMETER top_k 64
PARAMETER num_ctx 32768

SYSTEM """<|think|>
You are a careful reasoning assistant.
"""
```

---

## Configuration

### Change Default Port

```bash
# Linux systemd
sudo systemctl edit ollama --force
# Add:
# [Service]
# Environment="OLLAMA_HOST=0.0.0.0:11434"
sudo systemctl restart ollama
```

```bash
# macOS / one-shot
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

### Expose to Network (team use)

```bash
# Allow all interfaces — make sure firewall rules are set appropriately
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

### GPU Selection (multi-GPU)

```bash
# Use only GPU 1
CUDA_VISIBLE_DEVICES=1 ollama serve

# Use GPUs 0 and 1
CUDA_VISIBLE_DEVICES=0,1 ollama serve
```

### Context Window Override

Ollama defaults to a conservative context window. Override per model:

```bash
# In a Modelfile
PARAMETER num_ctx 65536

# Or via API
curl http://localhost:11434/api/generate \
  -d '{"model": "gemma4:26b", "prompt": "...", "options": {"num_ctx": 65536}}'
```

### GPU Memory Limits

```bash
# Keep model loaded indefinitely (default: 5 minutes idle)
OLLAMA_KEEP_ALIVE=-1 ollama serve

# Unload after 30 seconds idle
OLLAMA_KEEP_ALIVE=30s ollama serve
```

---

## Concurrency

Ollama handles concurrent requests but loads one model at a time by default. For simultaneous multi-user use:

```bash
# Allow up to 4 parallel requests to the same model
OLLAMA_NUM_PARALLEL=4 ollama serve

# Allow 2 models loaded simultaneously (uses more VRAM)
OLLAMA_MAX_LOADED_MODELS=2 ollama serve
```

---

## Thinking Mode with Ollama

Ollama does not currently expose `chat-template-kwargs` as a first-class API parameter. Options:

1. **Modelfile approach** (recommended): bake the thinking prompt into the system message in a custom Modelfile — see above
2. **System message approach**: pass `<|think|>` at the start of the system message content in API calls

```python
response = client.chat.completions.create(
    model="gemma4:26b",
    messages=[
        {
            "role": "system",
            "content": "<|think|>\nYou are a careful reasoning assistant."
        },
        {"role": "user", "content": "Prove that sqrt(2) is irrational."}
    ],
)
```

3. **llama-server approach**: if you need full control over thinking mode toggle per request, use llama-server directly instead of Ollama — see [backends/llama-cpp.md](llama-cpp.md)

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Error: model not found` | Run `ollama pull <model>` first |
| GPU not detected | Check `ollama logs` — CUDA or ROCm must be installed before Ollama |
| Out of memory | Use a smaller quant, reduce `num_ctx`, or free VRAM from other apps |
| Very slow (CPU only) | Confirm GPU driver and CUDA/ROCm are installed |
| `connection refused` port 11434 | Service not running — run `ollama serve` in a terminal |
| Request hangs | Check `OLLAMA_KEEP_ALIVE` — model may have unloaded; first request reloads |
| Context cutoff mid-response | Increase `num_ctx` in Modelfile or API `options` |

### Check GPU Usage

```bash
# NVIDIA
nvidia-smi

# AMD
rocm-smi

# macOS
# Activity Monitor → GPU History, or:
sudo powermetrics --samplers gpu_power -i1000 -n1
```

---

## Upgrading Ollama

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh  # re-running upgrades in place

# macOS
# Download latest from https://ollama.com/download/mac
```
