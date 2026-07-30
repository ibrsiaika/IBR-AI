# IBR-GPT-Code

> **Private Property — All Rights Reserved.**
> Not for sale, redistribution, or unauthorized use.
> Copyright © 2025 ibrsiaika. All rights reserved.

## What This Is

IBR-GPT-Code is a from-scratch GPT-style Transformer trained on Python code
and human-like conversation data. No pre-trained weights are used — the model
is randomly initialized and trained end-to-end on CPU.

The goal: a **100M-parameter model** that can talk like a human, write Python
code, and run on low-resource hardware (2-core CPU, 4GB RAM, no GPU).

## Training Pipeline — 100M Parameter Model

Two-stage training on a 2-core CPU:

### Stage 1: Pretrain (on Python code)
- Architecture: 14 layers × 768 dim × 12 heads = **100.4M params**
- Data: 27,369 Python code samples (59 MB, CodeParrot-clean)
- BPE tokenizer: 1,500 vocab (trained from scratch, Fast BPE)
- Optimizer: SGD with momentum + warmup + cosine LR decay
- Mixed precision: bfloat16 (with fp32 cross-entropy for stability)
- Gradient checkpointing: recompute activations to save memory
- Curriculum learning: easy→hard sequence ordering
- Hash-based deduplication

```bash
python scripts/train_full_pipeline.py
# → models/ibr_gpt_code_100m.pt (383 MB fp32)
# → models/ibr_gpt_code_100m_int8.pt (97 MB INT8)
```

### Stage 2: Fine-tune (on human-like conversation)
- Same architecture, continued training
- Data: 90 curated conversational patterns (greetings, Q&A, explanations)
- Lower learning rate (0.03 vs 0.1 pretrain)
- 3 epochs, ~3 min on 2-core CPU
- Preserves code knowledge while learning to talk like a human

```bash
python scripts/train_full_pipeline.py --skip-pretrain
# → models/ibr_gpt_code_100m_finetuned.pt
```

## Quick Start

```bash
# Clone
git clone https://github.com/ibrsiaika/IBR-AI.git
cd IBR-AI

# Install (CPU-only, no GPU needed)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e .

# Download 27K Python code samples (FREE, HuggingFace)
python scripts/download_more_data.py

# Run the full pretrain + finetune pipeline (~10 min on 2-core CPU)
python scripts/train_full_pipeline.py

# Generate from the trained model
python scripts/inference.py --model 100m --prompt "def scan" --mode greedy

# Or use the CLI
ibr train --data code.txt --epochs 10 --output model.pt
ibr generate --model model.pt --prompt "def hello"
ibr info --model model.pt
ibr serve --port 8000
```

## Architecture

```
ScratchGPT (100.41M params, from scratch — NO pre-trained weights)
├── Token Embedding (1500 vocab × 768 dim, random init std=0.02)
├── Position Embedding (32 positions × 768 dim)
├── 14 × Transformer Blocks (with gradient checkpointing)
│   ├── Pre-LayerNorm
│   ├── Multi-Head Self-Attention (12 heads × 64 dim/head)
│   ├── Residual Connection
│   ├── Pre-LayerNorm
│   ├── MLP (768 → 3072 → 768, GELU)
│   └── Residual Connection
├── Final LayerNorm
└── LM Head (weight-tied with token embedding — saves 1.15M params)

Fast BPE Tokenizer (from scratch, 50x faster than naive BPE)
├── Word frequency table (top 8000 words)
├── Incremental pair counting
├── 1,500 token vocabulary
└── Semantic cache (50K word encoding cache)
```

## Golden Token Stack — Optimizations Applied

| Optimization | What it does | Effect |
|--------------|--------------|--------|
| bfloat16 | Half-precision training | 2x speed, 2x memory savings |
| SGD + momentum | No Adam state (4 bytes/param) | 800 MB memory saved vs AdamW |
| Gradient accumulation | Effective batch=8 from micro-batch=4 | Stable gradients on small batches |
| Gradient checkpointing | Recompute activations in backward | 60% activation memory saved |
| Weight tying | lm_head = token_embedding | 1.15M params saved |
| Curriculum learning | Sort seqs by complexity (easy→hard) | Faster convergence |
| Deduplication | Hash-based seq dedup | 3% data removed |
| BPE semantic cache | Cache word→token IDs | 5x encode speedup |
| Warmup + cosine LR | Stable training, better convergence | Lower final loss |
| INT8 quantization | Post-training 4x compression | 383 MB → 97 MB |
| Low-LR finetune | 0.03 LR for finetune (vs 0.1 pretrain) | Preserves code, learns conversation |

## Training Results

### Stage 1: Pretrain (Python code)

| Metric | Value |
|--------|-------|
| Parameters | 100,408,320 (100.41M) |
| Architecture | 14L × 768D × 12H |
| Training data | 27,369 Python samples (59 MB) |
| Total tokens | 4,461,832 |
| Tokenizer vocab | 1,500 (Fast BPE) |
| Pre-train loss | 3.69 → 2.76 (25.2% reduction) |
| Perplexity | 40.1 → 15.8 |
| Training time | ~7 min on 2-core CPU |
| Size (fp32) | 383.2 MB |
| Size (INT8) | 97.0 MB |
| Inference speed | ~14 tok/s (greedy) |
| Training cost | $0.00 (CPU only, no GPU) |
| Pre-trained weights | None (from scratch) |

### Stage 2: Fine-tune (human conversation)

| Metric | Value |
|--------|-------|
| Conversation samples | 90 (expanded 5x = 450) |
| Fine-tune loss | 5.37 → ~2.5 (over 3 epochs) |
| Conversation patterns learned | Greetings, Q&A, code requests |
| Fine-tune time | ~3 min on 2-core CPU |
| Final model | `ibr_gpt_code_100m_finetuned.pt` |

## API Endpoints

```bash
# Start server
ibr serve --port 8000

# Health check
curl http://localhost:8000/health

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

- **CodeParrot Clean** (HuggingFace, cleaned GitHub Python, Apache 2.0)
- **CodeSearchNet** (HuggingFace, 457K Python functions, Apache 2.0)
- **Curated conversation patterns** (hand-written, for fine-tuning)

No paid APIs. No API keys. All data is publicly available.

## License

**Private Property — All Rights Reserved.**

This software and associated documentation files are the exclusive property
of the author. No license is granted for use, copying, modification,
merging, publication, distribution, sublicensing, or sale of this software.
Unauthorized use is prohibited.

For inquiries, contact the author via GitHub.
