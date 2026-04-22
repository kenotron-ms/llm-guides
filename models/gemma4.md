# Gemma 4 Model Guide

Released April 2026 by Google DeepMind. Apache 2.0 license.

Gemma 4 is a unified multimodal family designed for everything from phone-edge inference (E2B) to datacenter-grade reasoning (31B). All models support thinking/reasoning mode, function calling, and 140+ languages.

---

## Model Lineup

| Variant | Arch | Effective Params | Context | Modalities | 4-bit RAM | 8-bit RAM | BF16 RAM |
|---------|------|-----------------|---------|-----------|-----------|----------|---------|
| **E2B** | Dense + PLE | 2B eff. | 128K | Text, Image, Audio | ~3.2 GB | ~4.6 GB | ~9.6 GB |
| **E4B** | Dense + PLE | 4B eff. | 128K | Text, Image, Audio | ~5 GB | ~7.5 GB | ~15 GB |
| **26B-A4B** | MoE | 26B total / 4B active | 256K | Text, Image | ~15.6 GB | ~25 GB | ~48 GB |
| **31B** | Dense | 31B | 256K | Text, Image | ~17.4 GB | ~30.4 GB | ~58.3 GB |

> **"E" = Effective parameters** — E2B/E4B use Per-Layer Embeddings (PLE), where each decoder layer gets its own small embedding table. Static weight memory is higher than the parameter count implies; use the RAM numbers above.

### Hugging Face Model IDs

```
google/gemma-4-E2B-it      (instruct)
google/gemma-4-E4B-it
google/gemma-4-26B-A4B-it
google/gemma-4-31B-it
```

**Recommended GGUF** (Unsloth Dynamic 2.0):
```
unsloth/gemma-4-E2B-it-GGUF
unsloth/gemma-4-E4B-it-GGUF
unsloth/gemma-4-26B-A4B-it-GGUF
unsloth/gemma-4-31B-it-GGUF
```

---

## Picking the Right Variant

![Gemma 4 Variant Selector — Hardware Schematic](../diagrams/rendered/gemma4_variant.png)

### 26B-A4B vs 31B — Which to Pick?

| | 26B-A4B (MoE) | 31B (Dense) |
|--|--------------|------------|
| Speed | Faster (only 4B active) | Slower |
| Quality | Slightly lower | Highest |
| VRAM (Q4) | ~16 GB | ~17 GB |
| Best for | Speed, RAM-limited, agentic loops | Max quality, offline research |

---

## Architecture Details

### E2B and E4B — Per-Layer Embeddings (PLE)

PLE gives each transformer layer its own small embedding table rather than sharing one global embedding. This dramatically improves parameter efficiency at small scales. The large static weight memory (9.6 GB for a "2B" model) comes from these per-layer tables — they're large but only used for fast lookups, not active computation.

### 26B-A4B — Mixture of Experts

- 128 routed fine-grained experts, top-8 activated per token
- All 26B parameters must be loaded into memory even though only 4B are active per token
- Custom GELU-activated FFN per expert
- Alternating sliding-window (local) + global attention (dual attention)

### Thinking Mode Architecture

Thinking is controlled via explicit channel delimiters in the output stream:

```
<|channel>thought
[internal reasoning here]
<channel|>
[final answer here]
```

Enable in system prompt: `<|think|>` at the start of the system message content.

---

## Inference Parameters

Google's recommended defaults for all Gemma 4 models:

```
temperature = 1.0
top_p       = 0.95
top_k       = 64
```

**Practical local inference defaults**:
- Start with 32K context, increase as needed
- Keep repetition/presence penalty disabled (1.0 / 0.0) unless you see output loops
- EOS token is `<turn|>` — ensure your inference runtime recognizes it

---

## Enabling Thinking Mode

```bash
# Thinking ON — add <|think|> to system prompt
# In llama.cpp / llama-server:
--chat-template-kwargs '{"enable_thinking":true}'

# Thinking OFF
--chat-template-kwargs '{"enable_thinking":false}'

# Windows PowerShell
--chat-template-kwargs "{\"enable_thinking\":true}"
```

With thinking enabled, the model outputs its reasoning before the answer. With thinking disabled, larger models (26B/31B) may still emit an empty thought block — this is normal.

### System Prompt for Thinking

```
<|think|>
You are a precise reasoning assistant.
```

### System Prompt Without Thinking

```
You are a helpful assistant.
```

---

## Quick Start

### Download GGUF

```bash
pip install huggingface_hub hf_transfer

# E4B — 8-bit (best quality for small model)
hf download unsloth/gemma-4-E4B-it-GGUF \
  --local-dir ./models/gemma4-e4b \
  --include "*Q8_0*"

# 26B-A4B — 4-bit + mmproj (multimodal)
hf download unsloth/gemma-4-26B-A4B-it-GGUF \
  --local-dir ./models/gemma4-26b \
  --include "*mmproj-BF16*" \
  --include "*UD-Q4_K_XL*"

# 31B — 4-bit + mmproj
hf download unsloth/gemma-4-31B-it-GGUF \
  --local-dir ./models/gemma4-31b \
  --include "*mmproj-BF16*" \
  --include "*UD-Q4_K_XL*"
```

### llama.cpp CLI

```bash
export LLAMA_CACHE="./models"

# E2B (very fast, phone-class)
./llama.cpp/llama-cli \
  -hf unsloth/gemma-4-E2B-it-GGUF:Q8_0 \
  --temp 1.0 --top-p 0.95 --top-k 64

# E4B
./llama.cpp/llama-cli \
  -hf unsloth/gemma-4-E4B-it-GGUF:Q8_0 \
  --temp 1.0 --top-p 0.95 --top-k 64

# 26B-A4B (thinking on)
./llama.cpp/llama-cli \
  -hf unsloth/gemma-4-26B-A4B-it-GGUF:UD-Q4_K_XL \
  --temp 1.0 --top-p 0.95 --top-k 64 \
  --chat-template-kwargs '{"enable_thinking":true}'

# 31B
./llama.cpp/llama-cli \
  -hf unsloth/gemma-4-31B-it-GGUF:UD-Q4_K_XL \
  --temp 1.0 --top-p 0.95 --top-k 64
```

### llama-server (multimodal, OpenAI API)

```bash
# 26B-A4B with vision + thinking
./llama.cpp/llama-server \
  --model ./models/gemma4-26b/gemma-4-26B-A4B-it-UD-Q4_K_XL.gguf \
  --mmproj ./models/gemma4-26b/mmproj-BF16.gguf \
  --alias "gemma4-26b" \
  --ctx-size 32768 \
  --n-gpu-layers 999 \
  --temp 1.0 \
  --top-p 0.95 \
  --top-k 64 \
  --port 8001 \
  --chat-template-kwargs '{"enable_thinking":true}'
```

### Ollama

```bash
# Pull specific variants
ollama pull gemma4:e2b
ollama pull gemma4:e4b
ollama pull gemma4:26b     # 26B-A4B (MoE)
ollama pull gemma4:31b

# Run
ollama run gemma4:26b
```

### vLLM (NVIDIA CUDA)

```bash
# E4B single GPU (24 GB+)
vllm serve google/gemma-4-E4B-it \
  --max-model-len 65536

# 26B-A4B single A100/H100 (80 GB)
vllm serve google/gemma-4-26B-A4B-it \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.90

# 31B on 2× A100/H100
vllm serve google/gemma-4-31B-it \
  --tensor-parallel-size 2 \
  --max-model-len 32768 \
  --gpu-memory-utilization 0.90
```

### Apple Silicon (MLX)

```bash
# Install MLX environment
curl -fsSL https://raw.githubusercontent.com/unslothai/unsloth/refs/heads/main/scripts/install_gemma4_mlx.sh | sh
source ~/.unsloth/unsloth_gemma4_mlx/bin/activate

# Run 26B-A4B at 4-bit (vision supported)
python -m mlx_vlm.chat \
  --model unsloth/gemma-4-26b-a4b-it-UD-MLX-4bit \
  --chat-template-kwargs '{"enable_thinking":true}'
```

MLX available variants:

| Model | 4-bit | 8-bit |
|-------|-------|-------|
| 31B | `unsloth/gemma-4-31b-it-UD-MLX-4bit` | `unsloth/gemma-4-31b-it-UD-MLX-8bit` |
| 26B-A4B | `unsloth/gemma-4-26b-a4b-it-UD-MLX-4bit` | `unsloth/gemma-4-26b-a4b-it-UD-MLX-8bit` |
| E4B | `unsloth/gemma-4-e4b-it-UD-MLX-4bit` | `unsloth/gemma-4-e4b-it-UD-MLX-8bit` |
| E2B | `unsloth/gemma-4-e2b-it-UD-MLX-4bit` | `unsloth/gemma-4-e2b-it-UD-MLX-8bit` |

---

## Multimodal Usage

### Image Input (OpenAI API)

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8001/v1", api_key="none")

# Single image
response = client.chat.completions.create(
    model="gemma4-26b",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": "https://example.com/img.jpg"}},
            {"type": "text", "text": "Describe this image."}
        ]
    }],
    max_tokens=1024,
    temperature=1.0,
)
print(response.choices[0].message.content)
```

### OCR Prompt (high visual token budget)

```python
response = client.chat.completions.create(
    model="gemma4-26b",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
            {
                "type": "text",
                "text": "Extract all text from this receipt. Return line items, total, merchant, and date as JSON."
            }
        ]
    }],
    max_tokens=2048,
)
```

> For OCR/document tasks, use vLLM with `--mm-processor-kwargs '{"max_soft_tokens": 560}'` or `1120` for maximum visual resolution.

### Audio Input (E2B/E4B only — llama.cpp)

Audio processing requires building `llama-mtmd-cli`. E2B/E4B support:
- Transcription (any language)
- Translation (source → target language)

```
[audio first]
Transcribe the following speech segment in English into English text.
Follow these specific instructions for formatting the answer:
* Only output the transcription, with no newlines.
* When transcribing numbers, write the digits.
```

---

## Vision Resolution (vLLM)

Gemma 4 supports configurable vision token budgets per request (affects detail level):

| Token Budget | Detail Level | Compute |
|-------------|-------------|---------|
| 70 tokens | Low | Minimal |
| 140 tokens | Medium-low | Low |
| 280 tokens | **Default** | Moderate |
| 560 tokens | High | High |
| 1120 tokens | Maximum (OCR) | Heavy |

Set at server launch:

```bash
vllm serve google/gemma-4-31B-it \
  --mm-processor-kwargs '{"max_soft_tokens": 560}'
```

---

## Function Calling

vLLM supports Gemma 4 tool calling natively:

```bash
vllm serve google/gemma-4-31B-it \
  --enable-auto-tool-choice \
  --tool-call-parser gemma4 \
  --max-model-len 32768
```

```python
tools = [{
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "Search the web for information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }
    }
}]

response = client.chat.completions.create(
    model="google/gemma-4-31B-it",
    messages=[{"role": "user", "content": "What is the latest version of Python?"}],
    tools=tools,
    tool_choice="auto",
)
```

---

## Official Benchmarks

| Benchmark | 31B | 26B-A4B | E4B | E2B |
|-----------|-----|---------|-----|-----|
| MMLU Pro | 85.2% | 82.6% | 69.4% | 60.0% |
| AIME 2026 (no tools) | 89.2% | 88.3% | 42.5% | 37.5% |
| LiveCodeBench v6 | 80.0% | 77.1% | 52.0% | 44.0% |
| MMMU Pro | 76.9% | 73.8% | 52.6% | 44.2% |

Source: Unsloth benchmarks, April 2026

---

## Known Issues

- **CUDA 13.2 + GGUF**: Do not use — produces garbage output. Use CUDA 12.x or CUDA 13.0.
- **EOS token**: `<turn|>` — older inference wrappers may not stop at this token. Update llama.cpp to latest.
- **Empty thought blocks**: With thinking disabled, 26B/31B may emit an empty `<|channel>thought\n<channel|>` block. This is expected and harmless.
- **E2B/E4B audio in vLLM**: Not yet supported in vLLM (as of April 2026). Use llama.cpp for audio tasks with small models.
- **26B-A4B BF16 in vLLM**: Requires a full 80 GB GPU (MI300X or A100). For consumer GPUs use quantized GGUF with llama.cpp.