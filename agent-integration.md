# Agent Integration Guide

This guide explains how to configure **Amplifier agents** (and any OpenAI-SDK-compatible client) to use local LLMs in place of cloud APIs. All four backends expose an OpenAI-compatible REST API, so switching between local and cloud is a matter of changing `base_url` and `model`.

---

## Quick Reference: Endpoint URLs

| Backend | Default URL | Model Name Source |
|---------|------------|------------------|
| llama-server | `http://localhost:8001/v1` | `--alias` flag at server start |
| Ollama | `http://localhost:11434/v1` | `ollama list` |
| vLLM | `http://localhost:8000/v1` | HuggingFace model ID |
| LM Studio | `http://localhost:1234/v1` | Shown in Developer tab |

---

## Starting a Local Server

Pick one backend and start it before configuring agents.

### Recommended for Agents: llama-server (Qwen3.6-35B-A3B)

Best for coding agents — highest SWE-bench score in its compute class, native tool calling, thinking mode:

```bash
./llama.cpp/llama-server \
  --model ./models/qwen3.6-35b/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf \
  --mmproj ./models/qwen3.6-35b/mmproj-F16.gguf \
  --alias "qwen3.6" \
  --ctx-size 32768 \
  --n-gpu-layers 999 \
  --flash-attn \
  --temp 0.6 \
  --top-p 0.95 \
  --top-k 20 \
  --min-p 0.0 \
  --parallel 4 \
  --cont-batching \
  --chat-template-kwargs '{"enable_thinking":true}' \
  --port 8001
```

### Recommended for Agents: llama-server (Gemma 4 26B-A4B)

Best for multimodal agents (image + text) and reasoning tasks:

```bash
./llama.cpp/llama-server \
  --model ./models/gemma4-26b/gemma-4-26B-A4B-it-UD-Q4_K_XL.gguf \
  --mmproj ./models/gemma4-26b/mmproj-BF16.gguf \
  --alias "gemma4" \
  --ctx-size 32768 \
  --n-gpu-layers 999 \
  --flash-attn \
  --temp 1.0 \
  --top-p 0.95 \
  --top-k 64 \
  --parallel 4 \
  --cont-batching \
  --chat-template-kwargs '{"enable_thinking":true}' \
  --port 8001
```

### Quick Start via Ollama

```bash
ollama serve &
ollama pull qwen3.6:35b-a3b
# Model available at http://localhost:11434/v1, model name: "qwen3.6:35b-a3b"
```

### Multi-GPU Production (vLLM)

```bash
vllm serve Qwen/Qwen3.6-35B-A3B \
  --tensor-parallel-size 2 \
  --max-model-len 65536 \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --host 0.0.0.0 \
  --port 8000
```

---

## Connecting Amplifier Agents

Amplifier agents use the `openai` SDK under the hood and respect `base_url` / `api_key` overrides. Configure in your `.amplifier/config.yaml` or environment:

### Environment Variables

```bash
# Point agent at local llama-server
export OPENAI_BASE_URL="http://localhost:8001/v1"
export OPENAI_API_KEY="none"
export OPENAI_MODEL="qwen3.6"
```

### .amplifier/config.yaml (provider_preferences)

```yaml
model_providers:
  - name: local-llm
    base_url: "http://localhost:8001/v1"
    api_key: "none"
    models:
      - pattern: "qwen3.6*"
        model: "qwen3.6"
      - pattern: "gemma4*"
        model: "gemma4"
```

When delegating to agents, specify provider preferences:

```python
delegate(
    agent="foundation:explorer",
    instruction="Analyze the codebase",
    provider_preferences=[{
        "provider": "local-llm",
        "model": "qwen3.6"
    }]
)
```

---

## Direct Python Usage

```python
from openai import OpenAI

# Connect to local backend
client = OpenAI(
    base_url="http://localhost:8001/v1",  # or :11434/v1 (Ollama), :1234/v1 (LM Studio)
    api_key="none",
)

# Verify the server is up and see available models
models = client.models.list()
for m in models.data:
    print(m.id)
```

### Basic Chat

```python
response = client.chat.completions.create(
    model="qwen3.6",          # use model alias from --alias or from ollama list
    messages=[
        {"role": "system", "content": "You are a senior software engineer."},
        {"role": "user", "content": "Review this Python function for bugs."}
    ],
    max_tokens=8192,
    temperature=0.6,          # thinking mode: 0.6 for coding tasks
)
print(response.choices[0].message.content)
```

### Streaming

```python
stream = client.chat.completions.create(
    model="qwen3.6",
    messages=[{"role": "user", "content": "Write a REST API in FastAPI."}],
    max_tokens=16384,
    temperature=0.6,
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Thinking Mode + Access Reasoning Trace

```python
# Works with llama-server + vLLM (Qwen3.x)
response = client.chat.completions.create(
    model="qwen3.6",
    messages=[{"role": "user", "content": "Find the bug in this code: def fib(n): return fib(n-1)+fib(n-2)"}],
    max_tokens=32768,
    extra_body={
        "chat_template_kwargs": {"enable_thinking": True}
    },
)
# Reasoning trace (what the model thought through)
reasoning = getattr(response.choices[0].message, "reasoning_content", None)
if reasoning:
    print("=== Thinking ===")
    print(reasoning)
print("=== Answer ===")
print(response.choices[0].message.content)
```

### Tool Calling (Agentic Workflows)

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute or relative file path"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command and return stdout",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"}
                },
                "required": ["command"]
            }
        }
    }
]

messages = [
    {"role": "system", "content": "You are a helpful coding assistant."},
    {"role": "user", "content": "Check if there are any Python syntax errors in the src/ directory."}
]

response = client.chat.completions.create(
    model="qwen3.6",
    messages=messages,
    tools=tools,
    tool_choice="auto",
    max_tokens=4096,
)

# Agentic loop
while response.choices[0].finish_reason == "tool_calls":
    tool_calls = response.choices[0].message.tool_calls
    messages.append(response.choices[0].message)  # add assistant message

    for tc in tool_calls:
        import json
        args = json.loads(tc.function.arguments)
        
        # Execute the tool (your implementation)
        if tc.function.name == "run_command":
            import subprocess
            result = subprocess.run(args["command"], shell=True, capture_output=True, text=True)
            tool_result = result.stdout + result.stderr
        else:
            tool_result = f"Tool {tc.function.name} not implemented"

        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": tool_result
        })

    # Next iteration
    response = client.chat.completions.create(
        model="qwen3.6",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_tokens=4096,
    )

print(response.choices[0].message.content)
```

---

## Vision Workflows (Multimodal Agents)

Both Gemma 4 and Qwen3.5/3.6 support image input:

```python
import base64

def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def analyze_image(image_path: str, question: str, model: str = "gemma4") -> str:
    b64 = encode_image(image_path)
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"}
                },
                {"type": "text", "text": question}
            ]
        }],
        max_tokens=2048,
        temperature=1.0,
    )
    return response.choices[0].message.content

# Usage
result = analyze_image(
    "screenshot.png",
    "Identify all UI elements and describe their purpose."
)
print(result)
```

---

## Serverless / Background Process Pattern

For agent workflows that need the model server always available:

```bash
# Start server in background (nohup keeps it alive after shell exit)
nohup ./llama.cpp/llama-server \
  --model ./models/qwen3.6-35b/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf \
  --alias "qwen3.6" \
  --ctx-size 16384 \
  -n 999 -fa \
  --parallel 4 --cont-batching \
  --chat-template-kwargs '{"enable_thinking":true}' \
  --port 8001 \
  > ./logs/llama-server.log 2>&1 &

echo "Server PID: $!"
```

Health check:

```bash
curl -s http://localhost:8001/health
# {"status":"ok"}

# List loaded models
curl -s http://localhost:8001/v1/models | python3 -m json.tool
```

---

## Model Selection Guide for Agent Tasks

![Agent Model Selector — Decision Schematic](diagrams/rendered/agent_model_selector.png)
*[view / edit source](https://mermaid.live/edit#pako:fZNRb5swFIX/ypWjSa2UtAQIWXhYFQLhaZ3aRZmm0gcH3yResJ2BaTWR/PcZGkhWbYOne33P+c6VoSKpYkh8ss7Ua7qluYZFmEgwz/TqabpBqUHTYgf61x7vnq9hMPgEQdUc8BSMmMvN3TGRb5qgPj98x+IAD473lJCHV5TOjQfOKBhMnSBJ5Ndv0WCFMt3C2LlxP5jOYsvlztjAl/uEPF8a3asDzKoQcQ850kLJeuoWBNXbmlkPzs7EsOqchFmqnQibiUf8WfIcWR1stOiSjS6SqRzscQBJaVtDF/RfUoWnVBokIqvNYtdYxSgEBRdsz1i5JytnGHS6WbdNVC15wZWstygzzU1QmrVJo/Musbv8l3Eb3GQ1jauXN78XTkGIfa5+XHfYqMPOq8fpZ3NbstA55RJZi5w3Ix8hDsBYZ1g07OiCHTXcacm4AsOJ7OC2brWMeceI3fYrMFfv+75W+7YcLS7r2DWV4Kytln+WkSkLQbOstUszWhQhrsE4wJpnmd+zmOPYw77ZRu3Q79ljip7VT1Wmcr+HVv2+0xrASTukQ2pjp3XpxGKT/2qbNCe1zSzmntWT1Wiy8t6rSZ8IzAXljPgV0VsU9S/GaL4jxz4p94xqDDnd5FQQX+clHn8D)*

| Task Type | Best Model | Thinking Mode | Temperature |
|-----------|-----------|--------------|-------------|
| Code generation (precise) | Qwen3.6-35B-A3B | On | 0.6 |
| Code review / debugging | Qwen3.6-35B-A3B | On | 0.6 |
| General reasoning | Gemma 4 26B-A4B or 31B | On | 1.0 |
| Multi-step planning | Qwen3.6 or Gemma 4 31B | On | 1.0 |
| Document/image analysis | Gemma 4 26B-A4B | Optional | 1.0 |
| Fast responses / high volume | Gemma 4 E4B | Off | 1.0 |
| Edge / offline-only | Gemma 4 E2B | Off | 1.0 |
| Structured JSON extraction | Any | Off | 0.0–0.3 |

---

## Context Length Planning

| Backend | Practical Max | KV Cache Trade-off |
|---------|-------------|-------------------|
| llama-server | 128K (with -fa and q8 KV) | Each slot costs `ctx × layers × d_model × 2 × dtype` |
| Ollama | 32K default; up to 128K with Modelfile | Increase `num_ctx` carefully |
| vLLM | Up to 262K (Qwen3.x), 256K (Gemma 4) | Reduce `--max-model-len` to free KV cache for batching |
| LM Studio | Up to model max; set in Developer tab | Higher context = slower TTFT |

For agentic coding tasks, 32K is usually sufficient. For document analysis (long files), 64K–128K is more appropriate. Don't set context higher than needed — it costs VRAM and increases latency.

---

## Checking Server Health

```python
import httpx

def check_local_llm(base_url: str = "http://localhost:8001") -> bool:
    try:
        r = httpx.get(f"{base_url}/health", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False

def get_available_models(base_url: str = "http://localhost:8001") -> list[str]:
    client = OpenAI(base_url=f"{base_url}/v1", api_key="none")
    return [m.id for m in client.models.list().data]

if check_local_llm():
    print("Local LLM is up:", get_available_models())
else:
    print("Local LLM not running — falling back to cloud")
```

---

## Fallback Pattern (local → cloud)

![Local / Cloud Fallback — Flow Schematic](diagrams/rendered/local_cloud_fallback.png)
*[view / edit source](https://mermaid.live/edit#pako:fZNfb9owFMW/ylX60kr8DXRV/bCJkgJTYatCNWkFHox9IRaOndlOO4nw3WeS0JU+NH7Jyc3v5Nx7lX3ANMeABBupX1lCjYOnaKnAX4PLxWCLyoHBPzlat7qCZvMr3O0fjV4jSM2oBFQ800K55VIlzmWk3S6fJ9o6kmnj2glS6ZJDZXl3dChitJlW3IJQ4ESKBQwXsc4dgtO1bepDSe8pJU1pi2UZtOFnKfzNy3Q6W703fPImngdtAI3RpoBoP6JSrinb+YR0LZF/qyNEJfEbbQH3+zlKZA6Y1DmHweP3s3d+6AKeFzG63KjKt/7ofVkeai7U1sehxyF5u9EiQszmiDv41fPZfZoHkQp4CFvXZ2SM1GpVwSl1SQHj/2jc/Qwd+rk2LSornHjxg5ssZsI64yc2T33D0GuFFT6ezpr91jUMhPlbOwzL9cWXp5ZMuQaLq6uqPqrqlRi/F5OTqI0IIeWaas7LcoI1eS4n5/LZSz/LkxWT1NoIN/XaN0JKctHhvV7Ybfi+9A7JRXhD8UunwbTUhlxg53g+0NUCK7pLuzTEN7pPbzv89lPa56nZkHf8eWPxps967CMbNIIUTUoFD8g+cAmmx/+HU7MLDo0gzzh1GAm6NTQNiDM5Hv4B)*

```python
import os
from openai import OpenAI

LOCAL_URL = "http://localhost:8001/v1"
LOCAL_MODEL = "qwen3.6"
CLOUD_MODEL = "gpt-4o"

def get_client_and_model():
    """Return (client, model) — prefer local, fall back to OpenAI cloud."""
    try:
        local = OpenAI(base_url=LOCAL_URL, api_key="none")
        local.models.list()  # quick probe
        return local, LOCAL_MODEL
    except Exception:
        return OpenAI(api_key=os.environ["OPENAI_API_KEY"]), CLOUD_MODEL

client, model = get_client_and_model()
response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Hello"}],
)
print(f"Using: {model}")
print(response.choices[0].message.content)
```
