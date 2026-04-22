# Qwen3.6 Model Guide

Released April 2026 by Alibaba/Qwen team. Apache 2.0 license.

Qwen3.6 builds on Qwen3.5's breakthroughs with a focused improvement on **agentic coding**, **stability**, and **real-world developer utility**, shaped directly by community feedback. The family now includes two models:

- **Qwen3.6-27B** (dense) — flagship-level agentic coding in a 27B dense model; surpasses Qwen3.5-397B-A17B across all major coding benchmarks at 15× lower memory
- **Qwen3.6-35B-A3B** (MoE) — 3B active params per pass; best single-GPU efficiency for agentic coding

---

## Model Overview

| Model ID | Arch | Total Params | Active Params | Context | Context (extended) | 4-bit RAM |
|----------|------|-------------|--------------|---------|-------------------|-----------|
| `Qwen/Qwen3.6-27B` | Dense | 27B | all | 262K | 1M (via YaRN) | ~17 GB |
| `Qwen/Qwen3.6-35B-A3B` | MoE | 35B | 3B active | 256K | 1M (via YaRN) | ~23 GB |

Both models support 201 languages, hybrid thinking (on/off per request), and tool calling.

---

## Qwen3.6-27B (Dense)

The 27B dense is the standout drop. A 55.6 GB BF16 model that outperforms the 807 GB Qwen3.5-397B-A17B MoE across all major coding benchmarks — and fits in Q4 on a single RTX 4080 (16 GB VRAM).

**Recommended GGUF** (Unsloth, direct stream from HF supported):
- `unsloth/Qwen3.6-27B-GGUF:Q4_K_M` — 4-bit, ~16.8 GB, sweet spot for 16 GB VRAM
- `unsloth/Qwen3.6-27B-GGUF:Q8_0` — near-lossless, ~29 GB

### Memory Requirements

| Quantization | Total Memory | Notes |
|-------------|-------------|-------|
| Q3_K_M | ~13 GB | Fits 12 GB VRAM; noticeable quality drop |
| Q4_K_M | ~17 GB | **Sweet spot** — fits 16 GB VRAM; reduce `--ctx-size` if OOM |
| Q6_K | ~22 GB | Excellent quality, needs 24 GB VRAM |
| Q8_0 | ~29 GB | Near-lossless, needs 32 GB+ |
| BF16 | ~56 GB | Full precision; 2× RTX 3090/A6000 or 1× A100 80G |

> llama.cpp can split layers across VRAM + system RAM. CPU layers are slower but allow larger quants on smaller GPUs.

### Consumer GPU Quick Reference

| GPU | VRAM | Recommendation |
|-----|------|----------------|
| RTX 4090 | 24 GB | Q6 full GPU, excellent |
| RTX 4080 / 3090 | 16–24 GB | Q4 full GPU (16 GB: keep ctx-size ≤ 32K) |
| RTX 3080 10G | 10 GB | Q3 with CPU offload; slow |
| RX 7900 XTX (ROCm) | 24 GB | Q6 full GPU (llama.cpp only) |
| M4 Max 64 GB | 64 GB unified | BF16 comfortable |
| M3 Max 48 GB | 48 GB unified | Q8 or BF16, excellent |
| M3 Max 36 GB | 36 GB unified | Q6 full metal, great |
| M2/M3 Pro 16 GB | 16 GB unified | Q4 full metal, good |

### Architecture Highlights

- **Dense transformer** — all 27B parameters are active every forward pass (no expert routing overhead)
- **Hybrid thinking** — toggle reasoning chains on/off per request via chat template kwargs
- **Long context** — 262K native; extensible to 1M via YaRN rope scaling
- **Tool calling** — improved nested object parsing for agentic scaffolds; `developer` role support
- **201 languages** — multilingual instruction following

### Inference Parameters

#### Thinking Mode (coding, reasoning)

```
temperature        = 0.6
top_p              = 0.95
top_k              = 20
min_p              = 0.0
presence_penalty   = 0.0
repeat_penalty     = 1.0
```

#### Non-thinking / Instruct Mode

```
temperature        = 0.7
top_p              = 0.8
top_k              = 20
min_p              = 0.0
presence_penalty   = 1.5
repeat_penalty     = 1.0
```

**Recommended max output**: 32,768 tokens. Thinking traces can be long; set `--reasoning on` in llama.cpp to properly handle `<think>` blocks.

### Quick Start

#### Download GGUF

```bash
pip install huggingface_hub

# Q4 (recommended, 16-17 GB)
huggingface-cli download unsloth/Qwen3.6-27B-GGUF \
  --include "Qwen3.6-27B-Q4_K_M.gguf" \
  --local-dir ./models/qwen3.6-27b

# Q8 (near-lossless, 29 GB)
huggingface-cli download unsloth/Qwen3.6-27B-GGUF \
  --include "Qwen3.6-27B-Q8_0.gguf" \
  --local-dir ./models/qwen3.6-27b
```

#### llama-server (stream from HF, no pre-download)

```bash
# Thinking mode — coding tasks (recommended)
llama-server \
  -hf unsloth/Qwen3.6-27B-GGUF:Q4_K_M \
  --alias "qwen3.6-27b" \
  --ctx-size 65536 \
  --n-gpu-layers 999 \
  --cache-ram 4096 \
  --temp 0.6 \
  --top-p 0.95 \
  --top-k 20 \
  --min-p 0.0 \
  --presence-penalty 0.0 \
  --repeat-penalty 1.0 \
  --port 8001 \
  --jinja \
  --reasoning on \
  --chat-template-kwargs '{"enable_thinking":true}'
```

```bash
# Non-thinking mode — fast instruct / chat
llama-server \
  -hf unsloth/Qwen3.6-27B-GGUF:Q4_K_M \
  --alias "qwen3.6-27b" \
  --ctx-size 32768 \
  --n-gpu-layers 999 \
  --temp 0.7 \
  --top-p 0.8 \
  --top-k 20 \
  --min-p 0.0 \
  --presence-penalty 1.5 \
  --repeat-penalty 1.0 \
  --port 8001 \
  --jinja \
  --chat-template-kwargs '{"enable_thinking":false}'
```

> **Windows PowerShell** — escape inner quotes: `--chat-template-kwargs '{\"enable_thinking\":true}'`

#### Ollama

```bash
ollama pull qwen3.6:27b
ollama run qwen3.6:27b
```

#### vLLM (single A100 80G / H100 / MI300X)

```bash
vllm serve Qwen/Qwen3.6-27B \
  --port 8000 \
  --tensor-parallel-size 1 \
  --max-model-len 65536 \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder
```

For 262K context (multi-GPU):

```bash
vllm serve Qwen/Qwen3.6-27B \
  --port 8000 \
  --tensor-parallel-size 4 \
  --max-model-len 262144 \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder
```

#### Apple Silicon (MLX)

```bash
# Via mlx-lm
pip install mlx-lm

mlx_lm.generate \
  --model mlx-community/Qwen3.6-27B-4bit \
  --max-tokens 32768 \
  --temp 0.6
```

> `mlx-community/Qwen3.6-27B-4bit` will appear on HuggingFace within hours of the release. Check `mlx-community` org for available quantizations.

### OpenAI API Usage

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8001/v1", api_key="none")

# Thinking mode — coding task
response = client.chat.completions.create(
    model="qwen3.6-27b",
    messages=[{"role": "user", "content": "Write a red-black tree in Python with full test suite."}],
    extra_body={"chat_template_kwargs": {"enable_thinking": True}},
    max_tokens=32768,
)
# Access the reasoning trace (thinking chain)
print(response.choices[0].message.reasoning_content)
# Access the final answer
print(response.choices[0].message.content)
```

### Benchmarks

Qwen3.6-27B surpasses Qwen3.5-397B-A17B (397B total / 17B active MoE) across all major coding benchmarks. Key claims from the release:

- **SWE-bench Verified** — flagship-level performance at 27B dense scale
- **Terminal-Bench 2.0** — strong agentic terminal task completion
- **LiveCodeBench** — competitive with much larger models

> The comparison is striking: 807 GB (Qwen3.5-397B-A17B) vs 55.6 GB BF16 (Qwen3.6-27B), with the smaller model winning on every coding metric. See the [official blog post](https://qwen.ai/blog/qwen3.6-27b) for full benchmark tables.

---

## Qwen3.6-35B-A3B (MoE)

**Recommended GGUF** (Unsloth Dynamic 2.0, higher quality than standard quants):
- `unsloth/Qwen3.6-35B-A3B-GGUF` — GGUF variants
- `unsloth/Qwen3.6-35B-A3B-UD-MLX-4bit` — Apple Silicon MLX

### Memory Requirements

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

| GPU | VRAM | Recommendation |
|-----|------|---------------|
| RTX 4090 / 3090 Ti | 24 GB | Q4 full GPU, or Q6 with some CPU offload |
| RTX 4080 / 3090 | 16 GB | Q4 with ~7 GB CPU offload |
| RX 7900 XTX (ROCm) | 24 GB | Q4 full GPU (llama.cpp only) |
| M3 Max 48 GB | 48 GB unified | Q6 full metal, excellent |
| M3 Max 36 GB | 36 GB unified | Q4 full metal, great |
| M2 Pro 16 GB | 16 GB unified | Q3 full metal, usable |
| M4 Max 64 GB | 64 GB unified | Q8 or BF16 comfortable |

### Architecture Highlights

- **Hybrid MoE**: 3B parameters active per forward pass from 35B total — drastically reduces compute vs. dense 35B
- **Hybrid attention**: alternating local (sliding window) and global attention for long-context efficiency
- **Native multimodal**: image + text input via mmproj-F16 projector (GGUF) or built-in (safetensors)
- **Hybrid thinking**: toggle reasoning chains on/off per request
- **Agentic tools**: improved nested object parsing for tool calling; `developer` role support for coding agents
- **SWE-bench**: 73.4% at 3B active parameters — state of the art for its compute class

### Inference Parameters

#### Thinking Mode — General Tasks

```
temperature        = 1.0
top_p              = 0.95
top_k              = 20
min_p              = 0.0
presence_penalty   = 1.5
repetition_penalty = 1.0
```

#### Thinking Mode — Precise Coding (WebDev, exact output)

```
temperature        = 0.6
top_p              = 0.95
top_k              = 20
min_p              = 0.0
presence_penalty   = 0.0
repetition_penalty = 1.0
```

#### Non-thinking / Instruct Mode — General

```
temperature        = 0.7
top_p              = 0.8
top_k              = 20
min_p              = 0.0
presence_penalty   = 1.5
repetition_penalty = 1.0
```

#### Non-thinking — Reasoning Tasks

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

### Enabling / Disabling Thinking

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

### Quick Start

#### Download GGUF

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

#### llama.cpp CLI (stream from HF, no pre-download)

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

#### llama-server (non-thinking, OpenAI API)

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

#### llama-server (thinking, vision, full featured)

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

#### Ollama

```bash
ollama pull qwen3.6:35b-a3b
ollama run qwen3.6:35b-a3b
```

#### vLLM (single A100/H100 or MI300X)

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

#### Apple Silicon (MLX)

```bash
curl -fsSL https://raw.githubusercontent.com/unslothai/unsloth/refs/heads/main/scripts/install_qwen3_6_mlx.sh | sh
source ~/.unsloth/unsloth_qwen3_6_mlx/bin/activate
python -m mlx_vlm.chat \
  --model unsloth/Qwen3.6-35B-A3B-UD-MLX-4bit \
  --chat-template-kwargs '{"enable_thinking":true}'
```

### OpenAI API Usage

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

### YaRN Context Extension (1M tokens)

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

### Benchmarks

| Benchmark | Qwen3.6-35B-A3B |
|-----------|----------------|
| SWE-bench Verified | 73.4% |
| AIME 2025 | Competitive with leading models |
| LiveCodeBench | Top tier at MoE scale |

Source: [Qwen3.6 release blog](https://www.alibabacloud.com/blog/qwen3-6-35b-a3b-agentic-coding-power-now-open-to-all_603043)