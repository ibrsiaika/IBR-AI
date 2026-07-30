# IBR-GPT-Code

> **Status: Alpha — a from-scratch Transformer that trains on CPU.**
> The model trains and generates text, but is **not competitive** with
> Pythia-70M, SmolLM2-135M, or any production small model.
> This repo is a learning exercise, not a production system.

## What This Is

IBR-GPT-Code is a small, from-scratch GPT-style Transformer trained on
Python code. No pre-trained weights are used — the model is randomly
initialized and trained end-to-end on CPU.

The goal is to demonstrate the full training loop (tokenizer → model →
training → generation) in a minimal, honest codebase. It is **not** a
competitive model. For real work, use a pre-trained base model
(Pythia-70M, SmolLM2-135M, Qwen2.5-0.5B, GPT-OSS 20B) and fine-tune.

## What Works (verified)

```bash
# 1. Model imports and runs a smoke test
python -m ibr_platform.models.scratch
# → prints params, loss, generated text

# 2. Full test suite passes (474 tests)
pytest tests/ -q
# → 474 passed, 1 skipped

# 3. CLI works end-to-end
pip install -e .
ibr train --data code.txt --epochs 10 --output model.pt
ibr generate --model model.pt --prompt "def hello"
ibr info --model model.pt
ibr serve --port 8000

# 4. API server starts
python -m ibr_platform.api.server
# → uvicorn on http://0.0.0.0:8000
```

## Quick Start

```bash
# Clone
git clone https://github.com/ibrsiaika/IBR-AI.git
cd IBR-AI

# Install (minimal — no transformers, no GPU)
pip install -e .
# For full ML extras (transformers, distilgpt2 tests):
pip install -e ".[ml,api,dev]"

# Run the model smoke test
python -m ibr_platform.models.scratch

# Run tests
pytest tests/ -q

# Train a tiny model from scratch
ibr train --data your_code.txt --epochs 10 --output model.pt

# Generate from the trained model
ibr generate --model model.pt --prompt "def scan" --max-tokens 30

# Start the API server
ibr serve --port 8000
# Then: curl http://localhost:8000/health
```

## Architecture

```
ScratchGPT (from scratch, NO pre-trained weights)
├── Token Embedding (random init, std=0.02)
├── Positional Embedding (learned, not RoPE)
├── N × Transformer Blocks (pre-LayerNorm residuals)
│   ├── LayerNorm → Multi-Head Self-Attention → Residual
│   └── LayerNorm → MLP (4x expansion, GELU) → Residual
├── Final LayerNorm
└── LM Head (weight-tied with token embedding)

BPE Tokenizer (from scratch)
├── Character-level init
├── Greedy merge based on frequency
└── Custom vocab (default 1000)
```

**Honest comparison to nanoGPT (Karpathy):**
- nanoGPT uses `F.scaled_dot_product_attention` (Flash Attention).
  This repo uses manual `torch.triu` masks. Slower, more memory.
- nanoGPT uses `tiktoken` (GPT-2 BPE, 50,257 vocab, 3 lines).
  This repo has a custom BPE from scratch (~200 lines). Reinvents the wheel.
- nanoGPT uses `torch.autocast("cpu", dtype=torch.bfloat16)` for AMP.
  This repo uses `model.to(torch.bfloat16)`. Breaks numerically on cross-entropy.
- nanoGPT has a proper train/val split and eval loop.
  This repo has no eval loop — only training loss.

## Training Results

The model trains and reduces loss. The numbers below are from a tiny
demo run (800 samples, 5 epochs, ~100K params, 15 seconds on CPU):

| Metric | Value |
|--------|-------|
| Parameters | ~100K (demo) |
| Vocab size | 1,000 |
| Initial loss | 4.92 |
| Final loss | 0.79 |
| Loss reduction | 84.0% |
| Training time | 15 seconds (CPU) |
| Pre-trained weights | None |

For larger models (6.7M, 25M, 100M params), see the `scripts/` directory.
Those scripts require more memory and time than a fresh clone provides,
and the resulting model files are not committed to the repo (they are
in `.gitignore`). Run the scripts to reproduce.

## Limitations

- **Small vocab** (1,000–2,000 tokens). Production models use 32K–200K.
- **Learned positional embeddings** (2018-era). Modern models use RoPE.
- **Manual attention masks**. Slower than Flash Attention.
- **No evaluation on standard benchmarks** (HumanEval, MBPP).
  The model has not been evaluated on any code-generation benchmark.
- **CPU-only training** limits model size. A 100M-param model takes
  ~7 minutes per epoch on a 2-core CPU.
- **No published weights.** Model files are not committed to the repo
  and are not uploaded to HuggingFace.
- **Not competitive with production small models.** Pythia-70M,
  SmolLM2-135M, and Qwen2.5-0.5B are all better, faster, and smaller.

## API Endpoints

```bash
# Start server
ibr serve --port 8000

# Health check
curl http://localhost:8000/health
# → {"status": "healthy", "version": "0.1.0", ...}

# Train model
curl -X POST http://localhost:8000/api/v1/model/train \
  -H "Content-Type: application/json" \
  -d '{"texts": ["def hello(): pass"], "epochs": 5, "mode": "pretrain"}'

# Generate
curl -X POST http://localhost:8000/api/v1/model/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "def ", "max_new_tokens": 20}'

# Model info
curl http://localhost:8000/api/v1/model/info
```

## CLI Commands

```
ibr train      --data PATH --epochs N --output PATH [--mode pretrain|finetune]
ibr generate   --model PATH --prompt TEXT [--max-tokens N] [--temperature F] [--top-k K]
ibr info       --model PATH
ibr serve      [--host H] [--port P]
ibr version
```

## Testing

```bash
# Run all tests (474 pass, 1 skipped)
pytest tests/ -q

# Run only the model tests
pytest tests/unit/test_scratch_model.py -v

# Run only the API tests
pytest tests/unit/test_model_api.py -v

# Smoke test the model
python -m ibr_platform.models.scratch
```

## Data Sources (all FREE)

- **CodeSearchNet** (HuggingFace, 457K Python functions, Apache 2.0)
- **CodeParrot Clean** (HuggingFace, cleaned GitHub Python, Apache 2.0)
- **Wikipedia API** (free, no auth)
- **arXiv API** (free, no auth)

No paid APIs. No API keys. All data is publicly available.

## License

Apache License 2.0. See [LICENSE](LICENSE).

## References

If you want to actually build a small GPT, study these (in order):

1. **nanoGPT** — https://github.com/karpathy/nanoGPT (~300 lines, MIT)
   The gold standard for a minimal, working GPT.
2. **minGPT** — https://github.com/karpathy/minGPT (~300 lines, MIT)
   Even simpler than nanoGPT.
3. **llm.c** — https://github.com/karpathy/llm.c (~1k lines C/CUDA)
   GPT-2 124M in pure CUDA.
4. **GPT-OSS** — https://github.com/openai/gpt-oss (Apache 2.0)
   OpenAI's open small model (July 2025).
5. **tiktoken** — https://github.com/openai/tiktoken
   Don't reinvent BPE. Use this.

This repo exists to learn from. It is not a substitute for any of the
above.
