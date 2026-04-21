# Qwen3.6 Model Guide

Released April 2026 by Alibaba/Qwen team. Apache 2.0 license.

Qwen3.6 builds on Qwen3.5's breakthroughs with a focused improvement on **agentic coding**, **stability**, and **real-world developer utility**, shaped directly by community feedback. Currently one model: **Qwen3.6-35B-A3B**.

---

## Model Overview

| Model ID | Arch | Total Params | Active Params | Context | Context (extended) | Vision | 201 Languages |
|----------|------|-------------|--------------|---------|-------------------|--------|---------------|
| `Qwen/Qwen3.6-35B-A3B` | MoE | 35B | 3B active | 256K | 1M (via YaRN) | Yes | Yes |

**Recommended GGUF** (Unsloth Dynamic 2.0, higher quality than standard quants):
- `unsloth/Qwen3.6-35B-A3B-GGUF` — GGUF variants
- `unsloth/Qwen3.6-35B-A3B-UD-MLX-4bit` — Apple Silicon MLX

---

## Memory Requirements

| Quantization | Total Memory (RAM + VRAM) | Notes |
|-------------|--------------------------|-------|
| 3-bit (UD-Q2_K_XL dynamic) | ~17 GB | Fits 16 GB Mac / 16 GB VRAM GPU with room |
| 4-bit (UD-Q4_K_XL) | ~23 GB | **Sweet spot** — recommended for most hardware |
| 6-bit (Q6_K) | ~30 GB | Excellent quality, needs 32 GB+ |
| 8-bit (Q8_0) | ~38 GB | Near-lossless, needs 40 GB+ |
| BF16 | ~70 GB | Full precision, 2× 40 GB or 1× 80 GB |

> Total memory = VRAM + system RAM. llama.cpp can split layers across GPU VRAM and CPU RAM, though CPU layers run slower. Plan for at least VRAM = model file size for full GPU offload.

### Consumer GPU Quick Reference

![Hardware Selector — Decision Schematic](../diagrams/rendered/hardware_selector.png)
*[view / edit source](https://mermaid.live/edit#pako:bZNfb5swFMW/yhV52ZSw8SclgYdVELKMLTRtunSRKA8emAbVYOSQdhXku8+YJAVt8ICv/TvnnmuJSopojCVLSgh9jXaIlfDTfcyBP/aH4NcOlcA341fEMMQUPF694OvwI8jyF3Cqxe0GPkNBUJlQll0fW6XTnNY3D57r2TXMgtnGteEel4ci7AK279bgCo8nnPfFdlEQDPcpSSOa1zAP/OWWd/Jxich/rGbcg+bkrYavASEoQ5+iogC+y6mWcwXne7qiCCNP1662wxoWwcty6cMQLrKwK1hvwVAUhSsm/FPDt479EFaiuPSYiVvxqoe17Z/H8YTNFBZODd+DuebA3ZS7zcd8MQ67jKoJ6EcgzhpIm/CF3ocMAS0DzXBkW5icwb6bNhag/w4aHNSveKH/A4+nQ0HfBBeg6a9qGq9U5cS3irkYclVt8jRJcQwZzih7O4+7OqWUT/1v+0Hb0cIuqxuy0bJ3792N81B91jRk1WyvaR100jVhdXPSyxkRtN+7OIHf9A8kKSHWQEUq0vBoXzL6jK3BGJlKbI4iSiizBlhp3sdcGkkZZhlKY8mqpHKHs+b3iBF7lo4j6VDEqMRuip4YyiSrZAd8/As=)*

| GPU | VRAM | Recommendation |
|-----|------|---------------|
| RTX 4090 / 3090 Ti | 24 GB | Q4 full GPU, or Q6 with some CPU offload |
| RTX 4080 / 3090 | 16 GB | Q4 with ~7 GB CPU offload |
| RX 7900 XTX (ROCm) | 24 GB | Q4 full GPU (llama.cpp only) |
| M3 Max 48 GB | 48 GB unified | Q6 full metal, excellent |
| M3 Max 36 GB | 36 GB unified | Q4 full metal, great |
| M2 Pro 16 GB | 16 GB unified | Q3 full metal, usable |
| M4 Max 64 GB | 64 GB unified | Q8 or BF16 comfortable |

---

## Architecture Highlights

- **Hybrid MoE**: 3B parameters active per forward pass from 35B total — drastically reduces compute vs. dense 35B
- **Hybrid attention**: alternating local (sliding window) and global attention for long-context efficiency
- **Native multimodal**: image + text input via mmproj-F16 projector (GGUF) or built-in (safetensors)
- **Hybrid thinking**: toggle reasoning chains on/off per request
- **Agentic tools**: improved nested object parsing for tool calling; `developer` role support for coding agents
- **SWE-bench**: 73.4% at 3B active parameters — state of the art for its compute class

---

## Inference Parameters

### Thinking Mode — General Tasks

```
temperature        = 1.0
top_p              = 0.95
top_k              = 20
min_p              = 0.0
presence_penalty   = 1.5
repetition_penalty = 1.0
```

### Thinking Mode — Precise Coding (WebDev, exact output)

```
temperature        = 0.6
top_p              = 0.95
top_k              = 20
min_p              = 0.0
presence_penalty   = 0.0
repetition_penalty = 1.0
```

### Non-thinking / Instruct Mode — General

```
temperature        = 0.7
top_p              = 0.8
top_k              = 20
min_p              = 0.0
presence_penalty   = 1.5
repetition_penalty = 1.0
```

### Non-thinking — Reasoning Tasks

```
temperature        = 1.0
top_p              = 0.95
top_k              = 20
min_p              = 0.0
presence_penalty   = 1.5
repetition_penalty = 1.0
```

**Recommended output budget**: 32,768 tokens max for most queries. Thinking traces can be long.

**If getting gibberish output**:
1. Check CUDA is not 13.2 (use 12.x or 13.0)
2. Context length might be too low — increase `--ctx-size`
3. Try `--cache-type-k bf16 --cache-type-v bf16` in llama.cpp

---

## Enabling / Disabling Thinking

```bash
# llama.cpp / llama-server flags (Linux/macOS)
--chat-template-kwargs '{"enable_thinking":true}'
--chat-template-kwargs '{"enable_thinking":false}'

# Windows PowerShell
--chat-template-kwargs "{\"enable_thinking\":true}"
--chat-template-kwargs "{\"enable_thinking\":false}"
```

Via vLLM API (pass in chat template extras):

```python
response = client.chat.completions.create(
    model="Qwen/Qwen3.6-35B-A3B",
    messages=[{"role": "user", "content": "Write a binary search in Python."}],
    extra_body={"chat_template_kwargs": {"enable_thinking": True}},
    max_tokens=32768,
)
# Access reasoning content (thinking trace)
print(response.choices[0].message.reasoning_content)
# Access final answer
print(response.choices[0].message.content)
```

---

## Quick Start

### Download GGUF

```bash
pip install huggingface_hub hf_transfer

# 4-bit + vision projector
hf download unsloth/Qwen3.6-35B-A3B-GGUF \
  --local-dir ./models/qwen3.6-35b-a3b \
  --include "*mmproj-F16*" \
  --include "*UD-Q4_K_XL*"

# 3-bit (for 22 GB RAM setups)
hf download unsloth/Qwen3.6-35B-A3B-GGUF \
  --local-dir ./models/qwen3.6-35b-a3b \
  --include "*UD-Q2_K_XL*"
```

### llama.cpp CLI (stream from HF, no pre-download)

```bash
export LLAMA_CACHE="./models"

# Thinking mode, general tasks
./llama.cpp/llama-cli \
  -hf unsloth/Qwen3.6-35B-A3B-GGUF:UD-Q4_K_XL \
  --temp 1.0 \
  --top-p 0.95 \
  --top-k 20 \
  --min-p 0.0 \
  --chat-template-kwargs '{"enable_thinking":true}'

# Thinking mode, precise coding
./llama.cpp/llama-cli \
  -hf unsloth/Qwen3.6-35B-A3B-GGUF:UD-Q4_K_XL \
  --temp 0.6 \
  --top-p 0.95 \
  --top-k 20 \
  --min-p 0.0 \
  --chat-template-kwargs '{"enable_thinking":true}'
```

### llama-server (non-thinking, OpenAI API)

```bash
./llama.cpp/llama-server \
  -hf unsloth/Qwen3.6-35B-A3B-GGUF:UD-Q4_K_XL \
  --alias "qwen3.6-35b" \
  --ctx-size 16384 \
  --n-gpu-layers 999 \
  --temp 0.7 \
  --top-p 0.8 \
  --top-k 20 \
  --min-p 0.0 \
  --port 8001 \
  --chat-template-kwargs '{"enable_thinking":false}'
```

### llama-server (thinking, vision, full featured)

```bash
./llama.cpp/llama-server \
  --model ./models/qwen3.6-35b-a3b/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf \
  --mmproj ./models/qwen3.6-35b-a3b/mmproj-F16.gguf \
  --alias "qwen3.6-35b" \
  --ctx-size 16384 \
  --n-gpu-layers 999 \
  --temp 0.6 \
  --top-p 0.95 \
  --top-k 20 \
  --min-p 0.0 \
  --port 8001 \
  --chat-template-kwargs '{"enable_thinking":true}'
```

### Ollama

```bash
ollama pull qwen3.6:35b-a3b
ollama run qwen3.6:35b-a3b
```

### vLLM (single A100/H100 or MI300X)

```bash
vllm serve Qwen/Qwen3.6-35B-A3B \
  --port 8000 \
  --tensor-parallel-size 1 \
  --max-model-len 65536 \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder
```

For larger context (262K):

```bash
vllm serve Qwen/Qwen3.6-35B-A3B \
  --port 8000 \
  --tensor-parallel-size 8 \
  --max-model-len 262144 \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder
```

### Apple Silicon (MLX)

```bash
curl -fsSL https://raw.githubusercontent.com/unslothai/unsloth/refs/heads/main/scripts/install_qwen3_6_mlx.sh | sh
source ~/.unsloth/unsloth_qwen3_6_mlx/bin/activate
python -m mlx_vlm.chat \
  --model unsloth/Qwen3.6-35B-A3B-UD-MLX-4bit \
  --chat-template-kwargs '{"enable_thinking":true}'
```

---

## OpenAI API Usage

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8001/v1",
    api_key="none",
)

# Text query
response = client.chat.completions.create(
    model="qwen3.6-35b",
    messages=[{"role": "user", "content": "Create a Snake game in Python."}],
    max_tokens=32768,
)
print(response.choices[0].message.content)

# With thinking — access reasoning trace
response = client.chat.completions.create(
    model="qwen3.6-35b",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    extra_body={"chat_template_kwargs": {"enable_thinking": True}},
)
print("Thinking:", response.choices[0].message.reasoning_content)
print("Answer:", response.choices[0].message.content)
```

### Tool Calling (Agentic)

```python
tools = [{
    "type": "function",
    "function": {
        "name": "run_bash",
        "description": "Execute a bash command and return stdout",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The bash command to run"}
            },
            "required": ["command"]
        }
    }
}]

response = client.chat.completions.create(
    model="qwen3.6-35b",
    messages=[{"role": "user", "content": "List the files in /tmp sorted by size."}],
    tools=tools,
    tool_choice="auto",
)
```

---

## YaRN Context Extension (1M tokens)

The native 256K context can be extended to 1M tokens using YaRN rope scaling. This requires significant additional VRAM for the KV cache. Not practical on consumer hardware for long contexts, but available:

```python
# Transformers / safetensors
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen3.6-35B-A3B",
    torch_dtype=torch.bfloat16,
    device_map="auto",
    rope_scaling={"type": "yarn", "factor": 4.0},  # 256K × 4 = 1M
)
```

---

## Benchmarks

| Benchmark | Qwen3.6-35B-A3B |
|-----------|----------------|
| SWE-bench Verified | 73.4% |
| AIME 2025 | Competitive with leading models |
| LiveCodeBench | Top tier at MoE scale |

Source: [Qwen3.6 release blog](https://www.alibabacloud.com/blog/qwen3-6-35b-a3b-agentic-coding-power-now-open-to-all_603043)
