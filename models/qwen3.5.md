# Qwen3.5 Model Guide

Released February 2026 by Alibaba/Qwen team. Apache 2.0 license.

Qwen3.5 is a native multimodal (text + vision) family with hybrid thinking (reasoning on/off), 262K native context, and four sizes for different hardware targets.

---

## Model Lineup

| Model ID | Arch | Total Params | Active Params | Context | Vision | GGUF 4-bit | GGUF 8-bit | BF16 |
|----------|------|-------------|--------------|---------|--------|-----------|-----------|------|
| `Qwen/Qwen3.5-27B` | Dense | 27B | 27B | 262K | Yes | ~14 GB | ~27 GB | ~54 GB |
| `Qwen/Qwen3.5-35B-A3B` | MoE | 35B | 3B active | 262K | Yes | ~18 GB | ~35 GB | ~70 GB |
| `Qwen/Qwen3.5-122B-A10B` | MoE | 122B | 10B active | 262K | Yes | ~62 GB | ~122 GB | multi-GPU |
| `Qwen/Qwen3.5-397B-A17B` | MoE | 397B | 17B active | 262K | Yes | ~200 GB | multi-node | multi-node |

All instruct variants use the `-Instruct` suffix on Hugging Face: `Qwen/Qwen3.5-27B-Instruct`.

**Recommended Unsloth GGUF variants** (Dynamic 2.0, better quality per bit):
- `unsloth/Qwen3.5-27B-Instruct-GGUF`
- `unsloth/Qwen3.5-35B-A3B-GGUF`
- `unsloth/Qwen3.5-122B-A10B-GGUF`

---

## Architecture Highlights

- **Hybrid attention**: alternating local (sliding window) and global attention layers — enables long context without quadratic cost
- **Native vision**: image tokens natively embedded (multimodal projector built-in, no external mmproj file needed for safetensors; GGUF does use mmproj-F16.gguf)
- **Hybrid thinking**: the model can reason step-by-step (thinking mode) or respond directly (non-thinking/instruct mode) — controlled via chat template kwargs
- **YaRN context extension**: 262K native; can extend further with YaRN interpolation settings

---

## Picking the Right Variant

![Qwen 3.5 Variant Selector — Hardware Schematic](../diagrams/rendered/qwen35_variant.png)
*[view / edit source](https://mermaid.live/edit#pako:fZPdjpswEIZfZcTetCppwZATF63C0qY3qTbdHi6WvZjCJLHCqbZJtMqmz17bhGiTSgXJwvb83/wzNgcnq3NyImdV1Ptsg0LBtyStQD+zVw/LPVXB2yGkLfP8EBqebQFhh4JjpR5fw2DwHuLDbIe8wF8FwY+vs8WHY1p1gNjsP/uhVQf+CObxM/xk44fUYeMYlmGaVn80dh7rj3sl6moNOVWSXFhxJcEqLDN1Hi+Qkw7JQou8PdwJXguunkxuE3Zrwz6hVCQV8GpFgqqMdPZgqLMHw3gwC84OJp0DEw6L+qMLegszxXcEDQos5Tl9x/3M1xvD/d1ioZPaml7aY6eKw4m1lxwSUxTUwtB7i4kNvW+Icmvr5eqyA0NDou/ZctR3bWI8s3Hn+QuhGBS1lAVJ2TXvqlfhqVcTr0P5jGmSHnULfK/vwYh1vEVbKD6Y332Hpt6T2NTtP0DmeW86VDA1R6lHgzofqN7vWAkqzKhSuoh3UFpwpe+axXVAXVcURSXPT9NgeDE1VV8saNd6XqBYU6+YGkKe9cSsQCkTWoEW6UtUFNGNjz4ycqW+X1uKbkKcevnUzeqiFtENeea90toEJ7WXBwHzz2o2Rhp5/1Xn2UnKch897yyl0ZgYu5Y6rlOSKJHnTnRw1IZK8zPmKLbO0XXaJkdFCce1voZOpERLx78=)*

---

## Inference Parameters

### Thinking Mode (reasoning tasks, coding, math)

```
temperature  = 0.6
top_p        = 0.95
top_k        = 20
min_p        = 0.0
repetition_penalty = 1.0  (disabled)
presence_penalty   = 0.0
```

### Non-thinking / Instruct Mode (general tasks, chat, summarization)

```
temperature  = 0.7
top_p        = 0.8
top_k        = 20
min_p        = 0.0
repetition_penalty = 1.0
presence_penalty   = 1.5  (reduces repetitions)
```

### Reasoning Tasks in Non-thinking Mode

```
temperature  = 1.0
top_p        = 0.95
top_k        = 20
min_p        = 0.0
presence_penalty = 1.5
```

**Enabling/disabling thinking** (llama.cpp / llama-server):

```bash
# Thinking ON
--chat-template-kwargs '{"enable_thinking":true}'

# Thinking OFF
--chat-template-kwargs '{"enable_thinking":false}'

# Windows PowerShell
--chat-template-kwargs "{\"enable_thinking\":false}"
```

**Adequate output length**: Set `max_tokens` to at least 32,768 for reasoning tasks.

---

## Downloading GGUF Models

```bash
pip install huggingface_hub hf_transfer

# 27B — 4-bit (recommended for 16 GB VRAM)
hf download unsloth/Qwen3.5-27B-Instruct-GGUF \
  --local-dir ./models/qwen3.5-27b \
  --include "*UD-Q4_K_XL*"

# 27B — with vision mmproj
hf download unsloth/Qwen3.5-27B-Instruct-GGUF \
  --local-dir ./models/qwen3.5-27b \
  --include "*mmproj-F16*" \
  --include "*UD-Q4_K_XL*"

# 35B-A3B — 4-bit (fits 24 GB VRAM)
hf download unsloth/Qwen3.5-35B-A3B-GGUF \
  --local-dir ./models/qwen3.5-35b-a3b \
  --include "*mmproj-F16*" \
  --include "*UD-Q4_K_XL*"

# 122B-A10B — 4-bit (needs 2× 48 GB or multi-GPU)
hf download unsloth/Qwen3.5-122B-A10B-GGUF \
  --local-dir ./models/qwen3.5-122b \
  --include "*UD-Q4_K_XL*"
```

Or stream directly without pre-download (llama.cpp auto-fetches via Hugging Face):

```bash
export LLAMA_CACHE="./models"
./llama.cpp/llama-cli \
  -hf unsloth/Qwen3.5-27B-Instruct-GGUF:UD-Q4_K_XL \
  --temp 0.6 --top-p 0.95 --top-k 20
```

---

## Quick Run Examples

### llama.cpp CLI (thinking mode)

```bash
export LLAMA_CACHE="./models"
./llama.cpp/llama-cli \
  -hf unsloth/Qwen3.5-27B-Instruct-GGUF:UD-Q4_K_XL \
  --temp 0.6 \
  --top-p 0.95 \
  --top-k 20 \
  --min-p 0.0 \
  --chat-template-kwargs '{"enable_thinking":true}'
```

### llama-server (non-thinking, OpenAI API)

```bash
./llama.cpp/llama-server \
  --model ./models/qwen3.5-27b/Qwen3.5-27B-Instruct-UD-Q4_K_XL.gguf \
  --alias "qwen3.5-27b" \
  --ctx-size 16384 \
  --n-gpu-layers 999 \
  --temp 0.7 \
  --top-p 0.8 \
  --top-k 20 \
  --min-p 0.0 \
  --port 8001 \
  --chat-template-kwargs '{"enable_thinking":false}'
```

### llama-server (multimodal — vision)

```bash
./llama.cpp/llama-mtmd-cli \
  --model ./models/qwen3.5-27b/Qwen3.5-27B-Instruct-UD-Q4_K_XL.gguf \
  --mmproj ./models/qwen3.5-27b/mmproj-F16.gguf \
  --temp 0.6 \
  --top-p 0.95 \
  --top-k 20
```

### Ollama

```bash
ollama pull qwen3.5:27b
ollama pull qwen3.5:35b-a3b
ollama run qwen3.5:27b
```

### vLLM (BF16, single A100/H100 for 35B-A3B)

```bash
vllm serve Qwen/Qwen3.5-35B-A3B-Instruct \
  --max-model-len 32768 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --reasoning-parser qwen3
```

### vLLM (122B-A10B, 2× A100)

```bash
vllm serve Qwen/Qwen3.5-122B-A10B-Instruct \
  --tensor-parallel-size 2 \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.90
```

---

## Vision Usage (Multimodal)

All Qwen3.5 models natively support image input. When using the OpenAI-compatible API:

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8001/v1", api_key="none")

response = client.chat.completions.create(
    model="qwen3.5-27b",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
            {"type": "text", "text": "What is in this image?"}
        ]
    }],
    max_tokens=1024,
)
print(response.choices[0].message.content)
```

For local files, encode as base64:

```python
import base64

with open("image.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

response = client.chat.completions.create(
    model="qwen3.5-27b",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            {"type": "text", "text": "Describe this screenshot."}
        ]
    }]
)
```

---

## Context Length Management

- **Native**: 262,144 tokens
- **Practical**: Start at 16K–32K for performance; increase as needed
- **KV cache cost**: At 262K context, expect significant VRAM overhead on top of model weights

```bash
# llama.cpp — let it auto-select context (recommended)
# Or set explicitly:
--ctx-size 32768

# vLLM
--max-model-len 32768
```

---

## Known Issues

- If you see gibberish output, check: (1) CUDA version is not 13.2, (2) context length is not set too small, (3) try `--cache-type-k bf16 --cache-type-v bf16` in llama.cpp
- Non-thinking mode with `temperature=0.6` can produce very short or incomplete answers for complex tasks — switch to thinking mode
- 397B-A17B is not practically runnable on consumer hardware; target is datacenter use via vLLM with multi-node tensor parallelism
