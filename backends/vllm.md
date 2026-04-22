# vLLM Guide

**vLLM** is a production-grade LLM inference engine optimized for high throughput and efficient memory use via PagedAttention. Use it when serving models to multiple users, running multi-GPU setups, or when you need maximum tokens-per-second on server-class hardware.

- Repo: https://github.com/vllm-project/vllm
- Format: Hugging Face safetensors (BF16/FP16/FP8/AWQ/GPTQ)
- API: OpenAI-compatible at `http://localhost:8000`
- GPU support: NVIDIA CUDA, AMD ROCm (MI300X+), Google TPU
- **Not supported on Apple Silicon** (use llama.cpp Metal or mlx_vlm instead)

---

## When to Use vLLM

![vLLM Backend Decision — Flow Schematic](../diagrams/rendered/vllm_decision.png)

| Use Case | vLLM | llama.cpp/Ollama |
|----------|------|----------------|
| Single user, local dev | Not needed | Preferred |
| Multiple concurrent users | Best | Possible (slower) |
| Multi-GPU tensor parallelism | Native | Possible (limited) |
| Maximum tokens/sec on NVIDIA | Best | Good |
| Consumer AMD GPU (RX 6000/7000) | Not supported | Use llama.cpp |
| Apple Silicon | Not supported | Use llama.cpp Metal |
| GGUF quantized models | Not natively | Native |
| BF16/FP8 full precision | Native | Possible (large) |
| Tool calling + structured output | First-class | via server flags |

---

## Installation

### pip — NVIDIA CUDA

```bash
# Python 3.12 recommended
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Latest nightly (CUDA 12.9)
pip install -U vllm --pre \
  --extra-index-url https://wheels.vllm.ai/nightly/cu129 \
  --extra-index-url https://download.pytorch.org/whl/cu129 \
  --index-strategy unsafe-best-match

# Stable release (CUDA 12.8)
pip install vllm
```

### pip — AMD ROCm (MI300X, MI325X, MI350X, MI355X only)

> Requires Python 3.12, ROCm 7.2.1, glibc >= 2.35 (Ubuntu 22.04+)

```bash
python3.12 -m venv .venv
source .venv/bin/activate

pip install vllm --pre \
  --extra-index-url https://wheels.vllm.ai/rocm/nightly/rocm721 \
  --upgrade
```

### Docker — NVIDIA CUDA

```bash
# Gemma 4 tagged image
docker pull vllm/vllm-openai:gemma4

# CUDA 13.0 variant
docker pull vllm/vllm-openai:gemma4-cu130

# General latest
docker pull vllm/vllm-openai:latest
```

### Docker — AMD ROCm

```bash
docker pull vllm/vllm-openai-rocm:gemma4
```

---

## Supported Models

| Model | HuggingFace ID | Min GPU (BF16) |
|-------|---------------|----------------|
| Gemma 4 E2B | `google/gemma-4-E2B-it` | 1× 24 GB NVIDIA or MI300X+ |
| Gemma 4 E4B | `google/gemma-4-E4B-it` | 1× 24 GB NVIDIA or MI300X+ |
| Gemma 4 26B-A4B | `google/gemma-4-26B-A4B-it` | 1× 80 GB (A100/H100/MI300X) |
| Gemma 4 31B | `google/gemma-4-31B-it` | 1× 80 GB or 2× 40 GB |
| Qwen3.5-27B | `Qwen/Qwen3.5-27B-Instruct` | 1× 80 GB or 2× 40 GB |
| Qwen3.5-35B-A3B | `Qwen/Qwen3.5-35B-A3B-Instruct` | 1× 80 GB |
| Qwen3.5-122B-A10B | `Qwen/Qwen3.5-122B-A10B-Instruct` | 2× 80 GB (TP2) |
| Qwen3.6-35B-A3B | `Qwen/Qwen3.6-35B-A3B` | 1× 80 GB |

> For consumer GPUs (RTX 3090/4090, 24 GB), use quantized GGUF with llama.cpp/Ollama instead.

---

## Serving Models

### Gemma 4 — Single GPU

```bash
# E4B (any 24 GB+ GPU)
vllm serve google/gemma-4-E4B-it \
  --max-model-len 65536 \
  --gpu-memory-utilization 0.90

# 26B-A4B (80 GB GPU)
vllm serve google/gemma-4-26B-A4B-it \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.90

# 31B (80 GB GPU)
vllm serve google/gemma-4-31B-it \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.90
```

### Gemma 4 — Multi-GPU (tensor parallel)

```bash
# 31B on 2× A100/H100 (TP2)
vllm serve google/gemma-4-31B-it \
  --tensor-parallel-size 2 \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.90
```

### Gemma 4 — With Tool Calling and Thinking

```bash
vllm serve google/gemma-4-26B-A4B-it \
  --max-model-len 32768 \
  --enable-auto-tool-choice \
  --tool-call-parser gemma4 \
  --gpu-memory-utilization 0.92
```

### Qwen3.6-35B-A3B

```bash
# Single 80 GB GPU (BF16)
vllm serve Qwen/Qwen3.6-35B-A3B \
  --port 8000 \
  --max-model-len 65536 \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --gpu-memory-utilization 0.90

# 8× GPU for full 262K context
vllm serve Qwen/Qwen3.6-35B-A3B \
  --tensor-parallel-size 8 \
  --max-model-len 262144 \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder
```

### Qwen3.5-122B-A10B — 2× A100

```bash
vllm serve Qwen/Qwen3.5-122B-A10B-Instruct \
  --tensor-parallel-size 2 \
  --max-model-len 32768 \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --gpu-memory-utilization 0.90
```

### AMD ROCm via Docker

```bash
docker run -itd --name vllm-gemma4 \
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

## Key Flags

| Flag | Description |
|------|-------------|
| `--tensor-parallel-size N` | Split model across N GPUs (TP) |
| `--max-model-len N` | Maximum context length (reduces KV cache) |
| `--gpu-memory-utilization F` | Fraction of GPU VRAM for KV cache (0.0–1.0) |
| `--dtype` | `bfloat16`, `float16`, `float8`, `auto` |
| `--quantization` | `awq`, `gptq`, `fp8`, `bitsandbytes` |
| `--reasoning-parser` | `qwen3` (Qwen models) |
| `--enable-auto-tool-choice` | Enable automatic tool selection |
| `--tool-call-parser` | `qwen3_coder`, `gemma4`, `llama3_json` |
| `--limit-mm-per-prompt` | `image=N,audio=0` — constrain multimodal memory |
| `--mm-processor-kwargs` | JSON kwargs for vision processor (e.g. token budget) |
| `--async-scheduling` | Overlap scheduling with decoding for throughput |
| `--host` | Bind address (default `127.0.0.1`) |
| `--port` | Port (default `8000`) |
| `--served-model-name` | Override model name in API responses |

---

## API Usage

### Python — Text

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="EMPTY",
)

response = client.chat.completions.create(
    model="google/gemma-4-31B-it",
    messages=[{"role": "user", "content": "Explain quantum entanglement."}],
    max_tokens=1024,
    temperature=1.0,
)
print(response.choices[0].message.content)
```

### Python — Thinking Mode (Qwen3.x)

```python
response = client.chat.completions.create(
    model="Qwen/Qwen3.6-35B-A3B",
    messages=[{"role": "user", "content": "Implement quicksort in Python."}],
    max_tokens=32768,
    extra_body={
        "chat_template_kwargs": {"enable_thinking": True}
    },
)
# Reasoning trace (thinking steps)
print(response.choices[0].message.reasoning_content)
# Final answer
print(response.choices[0].message.content)
```

### Python — Vision (Gemma 4)

```python
response = client.chat.completions.create(
    model="google/gemma-4-26B-A4B-it",
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/diagram.png"
                }
            },
            {
                "type": "text",
                "text": "Describe all elements in this architecture diagram."
            }
        ]
    }],
    max_tokens=2048,
)
print(response.choices[0].message.content)
```

### Python — Tool Calling

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name"
                }
            },
            "required": ["location"]
        }
    }
}]

response = client.chat.completions.create(
    model="google/gemma-4-26B-A4B-it",
    messages=[{"role": "user", "content": "What's the weather in Seattle?"}],
    tools=tools,
    tool_choice="auto",
)

if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    print(f"Tool: {tool_call.function.name}")
    print(f"Args: {tool_call.function.arguments}")
```

### cURL — Text

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-4-31B-it",
    "messages": [
      {"role": "user", "content": "What are three key ideas in linear algebra?"}
    ],
    "max_tokens": 512,
    "temperature": 1.0
  }'
```

---

## Memory Optimization

### Reduce Context Length

The single biggest memory lever. KV cache is proportional to `max_model_len × num_heads × head_dim × 2 (K+V) × dtype_bytes`. Halving `max_model_len` nearly halves KV cache memory.

```bash
--max-model-len 16384   # conservative, frees VRAM
--max-model-len 131072  # large, uses more VRAM
```

### Text-Only Workloads (no vision)

```bash
--limit-mm-per-prompt image=0,audio=0
```

This skips multimodal memory profiling and saves ~2–4 GB VRAM.

### Image-Only (no audio)

```bash
--limit-mm-per-prompt audio=0
```

### FP8 Quantization (NVIDIA Hopper/Ada only)

```bash
vllm serve google/gemma-4-31B-it \
  --dtype float8 \
  --max-model-len 32768
```

### AWQ / GPTQ (pre-quantized models)

```bash
vllm serve <awq-quantized-model-on-hf> \
  --quantization awq \
  --max-model-len 32768
```

---

## Production Docker Deployment

```bash
docker run -itd \
  --name vllm-qwen36 \
  --ipc=host \
  --network host \
  --shm-size 16G \
  --gpus all \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -e HF_TOKEN=$HF_TOKEN \
  vllm/vllm-openai:latest \
    --model Qwen/Qwen3.6-35B-A3B \
    --tensor-parallel-size 2 \
    --max-model-len 65536 \
    --reasoning-parser qwen3 \
    --enable-auto-tool-choice \
    --tool-call-parser qwen3_coder \
    --gpu-memory-utilization 0.90 \
    --host 0.0.0.0 \
    --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

---

## Offline Inference (Batch)

For batch processing without a server:

```python
from vllm import LLM, SamplingParams
from transformers import AutoTokenizer

model_id = "google/gemma-4-26B-A4B-it"
tokenizer = AutoTokenizer.from_pretrained(model_id)

llm = LLM(
    model=model_id,
    tensor_parallel_size=1,
    max_model_len=8192,
    gpu_memory_utilization=0.90,
    trust_remote_code=True,
)

prompts = [
    [{"role": "user", "content": "What is 2 + 2?"}],
    [{"role": "user", "content": "Name three planets."}],
]

formatted = [
    tokenizer.apply_chat_template(p, tokenize=False, add_generation_prompt=True)
    for p in prompts
]

outputs = llm.generate(formatted, SamplingParams(temperature=1.0, max_tokens=256))
for o in outputs:
    print(o.outputs[0].text)
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `CUDA out of memory` during startup | Model too large for VRAM | Reduce `--max-model-len`, add GPUs, or switch to GGUF |
| `RuntimeError: ROCm not supported` on consumer AMD | vLLM only supports MI300X+ | Use llama.cpp for RX 6000/7000 |
| Slow throughput | `--async-scheduling` not set | Add `--async-scheduling` flag |
| Tool calls not parsed | Missing parser flag | Add `--enable-auto-tool-choice --tool-call-parser <parser>` |
| Model loads but zero throughput | `gpu-memory-utilization` too low | Increase to `0.90`–`0.95` |
| `trust_remote_code` error | Custom architecture | Add `--trust-remote-code` flag |
| Gemma 4 audio fails | Audio not in vLLM yet | Use E2B/E4B with llama.cpp for audio |