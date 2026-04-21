---
bundle:
  name: local-llm-guides
  version: 0.1.0
  description: |
    Team knowledge bundle for running Qwen3.5, Qwen3.6, and Gemma 4 locally.

    Covers model selection, hardware requirements (CUDA / ROCm / MLX), and
    backend setup (llama.cpp, Ollama, vLLM, LM Studio) across Windows, Linux,
    and macOS. Includes the infographic-builder bundle for generating visual
    summaries, decision charts, and model comparison cards.

includes:
  - bundle: git+https://github.com/singh2/infographic-builder@main
---

@local-llm-guides:README.md

@local-llm-guides:models/qwen3.5.md
@local-llm-guides:models/qwen3.6.md
@local-llm-guides:models/gemma4.md

@local-llm-guides:backends/llama-cpp.md
@local-llm-guides:backends/ollama.md
@local-llm-guides:backends/vllm.md
@local-llm-guides:backends/lmstudio.md

@local-llm-guides:hardware/cuda.md
@local-llm-guides:hardware/rocm.md
@local-llm-guides:hardware/mlx.md

@local-llm-guides:agent-integration.md
