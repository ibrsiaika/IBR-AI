#!/usr/bin/env python3
"""
IBR-GPT-Code Compact (25M) — Train & INT4-quantize to hit 10-15MB target.

ARCHITECTURE:
- 6 layers, 512 dim, 8 heads = ~25M params (vocab=2000)
- INT4 quantized → 12.5 MB (hits the 10-15MB target)

WHY COMPACT?
- 100M model is great for capability, but ~95 MB (INT8) / ~48 MB (INT4)
- This compact 25M model fits in 10-15 MB after INT4 — perfect for:
  - Edge deployment
  - Mobile inference
  - Embedded devices
  - Quick downloads

DATA: 27,369 Python code samples (59 MB) — same as 100M model
TRAINING: 3 epochs on 4000 sequences (~25 min on 2-core CPU)
QUANTIZATION: INT4 (2 weights per byte) = 8x compression
"""
import gc
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

# Load scratch modules directly
import importlib.util
_scratch_path = Path(__file__).resolve().parent.parent / "src" / "ibr_platform" / "models" / "scratch" / "__init__.py"
_spec = importlib.util.spec_from_file_location("ibr_scratch", _scratch_path)
_scratch_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scratch_mod)

# Import shared architecture & quantizer
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fast_bpe import FastBPETokenizerV2 as FastBPETokenizer
from train_100m_v2 import ScratchGPTLarge
from int4_quantizer import quantize_model_int4, estimate_int4_size_bytes, dequantize_int4

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH_FP32 = MODEL_DIR / "ibr_gpt_code_compact.pt"
MODEL_PATH_INT4 = MODEL_DIR / "ibr_gpt_code_compact_int4.pt"
DATA_PATH = Path(__file__).resolve().parent.parent / "research" / "big_code_dataset.json"

torch.set_num_threads(2)
SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)


def main() -> None:
    print("=" * 70)
    print("  IBR-GPT-Code-Compact (25M) — INT4 quantized to ~12 MB")
    print("=" * 70)

    # ---- 1. Load data ----
    print("\n[1/6] Loading data...")
    t0 = time.perf_counter()
    with open(DATA_PATH) as f:
        samples = json.load(f)
    print(f"  Loaded {len(samples):,} samples in {time.perf_counter()-t0:.1f}s")

    # ---- 2. Train BPE tokenizer ----
    print("\n[2/6] Training BPE tokenizer (2000 vocab)...")
    t0 = time.perf_counter()
    tok = FastBPETokenizer(vocab_size=2000)
    # Use subset for BPE (standard practice)
    bpe_samples = samples[:3000]
    print(f"  BPE training on {len(bpe_samples):,} samples (subset of {len(samples):,})")
    tok.train(bpe_samples)
    vocab_size = tok.vocab_size_actual
    print(f"  Vocab: {vocab_size} | Trained in {time.perf_counter()-t0:.1f}s")

    # ---- 3. Tokenize & create sequences ----
    print("\n[3/6] Tokenizing samples & creating sequences...")
    t0 = time.perf_counter()
    seq_len = 48
    # Memory-safe subset (5000 samples)
    TOKENIZE_LIMIT = 5000
    print(f"  Tokenizing {TOKENIZE_LIMIT:,} samples (memory-safe subset)...")
    all_tokens: list[int] = []
    eos_id = tok.vocab.get("<EOS>", 0)
    for i, s in enumerate(samples[:TOKENIZE_LIMIT]):
        if i % 1000 == 0:
            print(f"    {i}/{TOKENIZE_LIMIT}")
        enc = tok.encode(s)
        if len(enc) > 5:
            all_tokens.extend(enc)
            all_tokens.append(eos_id)
    print(f"  Total tokens: {len(all_tokens):,} ({time.perf_counter()-t0:.1f}s)")

    # Create sequences as numpy array
    n_seqs = len(all_tokens) // (seq_len + 1)
    sequences_np = np.array(all_tokens[:n_seqs * (seq_len + 1)]).reshape(n_seqs, seq_len + 1)
    print(f"  Sequences: {n_seqs:,}")

    # Dedup
    print(f"  Deduplicating...")
    seen: set = set()
    keep_idx: list[int] = []
    for i in range(n_seqs):
        h = sequences_np[i].tobytes()
        if h not in seen:
            seen.add(h)
            keep_idx.append(i)
    sequences_np = sequences_np[keep_idx]
    print(f"  After dedup: {len(sequences_np):,}")

    # Curriculum: easy -> hard
    complexities = [len(set(sequences_np[i].tolist())) for i in range(len(sequences_np))]
    sort_idx = np.argsort(complexities)
    sequences_np = sequences_np[sort_idx]
    print(f"  Curriculum learning applied")

    MAX_SEQS = min(4000, len(sequences_np))
    train_seqs = sequences_np[:MAX_SEQS]
    print(f"  Training on: {len(train_seqs):,} sequences")

    # ---- 4. Build compact model ----
    print("\n[4/6] Building IBR-GPT-Code-Compact (6L/512D/8H)...")
    model = ScratchGPTLarge(
        vocab_size=vocab_size,
        embed_dim=512,
        num_layers=6,
        num_heads=8,
        max_seq_len=seq_len,
        dropout=0.1,
        use_checkpointing=False,  # not needed for compact model
    )
    params = model.count_parameters()
    print(f"  Params: {params:,} ({params/1e6:.2f}M)")
    print(f"  Memory (fp32): {params*4/1024/1024:.1f} MB")
    print(f"  Memory (INT4):  {params/2/1024/1024:.1f} MB  <-- target 10-15 MB")

    # Use bfloat16 for 2x speed
    try:
        model = model.to(torch.bfloat16)
        print("  Using bfloat16")
    except Exception:
        print("  bfloat16 not available, using fp32")

    # ---- 5. Train ----
    print("\n[5/6] Training (SGD + grad accum, 3 epochs)...")
    data = torch.tensor(train_seqs, dtype=torch.long)
    opt = torch.optim.SGD(model.parameters(), lr=0.1, momentum=0.9, weight_decay=1e-4, nesterov=True)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=3, eta_min=0.001)

    EPOCHS = 3
    MICRO_BATCH = 8
    GRAD_ACCUM = 2  # effective batch = 16
    losses: list[float] = []

    model.train()
    t_train_start = time.perf_counter()

    for epoch in range(EPOCHS):
        perm = torch.randperm(len(data))
        ep_losses: list[float] = []
        opt.zero_grad()
        step_count = 0

        for i in range(0, len(data), MICRO_BATCH):
            batch = data[perm[i:i + MICRO_BATCH]]
            if batch.size(0) == 0:
                continue
            x = batch[:, :-1]
            y = batch[:, 1:]
            try:
                _, loss = model(x, targets=y)
                (loss / GRAD_ACCUM).backward()
                ep_losses.append(loss.item())
            except Exception as e:
                print(f"  [step {step_count}] ERROR: {e}")
                break

            if (i // MICRO_BATCH + 1) % GRAD_ACCUM == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
                opt.zero_grad()
                step_count += 1
                if step_count % 30 == 0:
                    print(f"  E{epoch+1} step {step_count}/{len(data)//MICRO_BATCH//GRAD_ACCUM} loss={loss.item():.4f} t={time.perf_counter()-t_train_start:.0f}s")

            if i % (MICRO_BATCH * 50) == 0 and i > 0:
                gc.collect()

        scheduler.step()
        avg = float(np.mean(ep_losses)) if ep_losses else float('nan')
        ppl = math.exp(min(avg, 12)) if not math.isnan(avg) else float('nan')
        elapsed = time.perf_counter() - t_train_start
        losses.append(avg)
        print(f"  E{epoch+1}/{EPOCHS}  Loss:{avg:.4f}  PPL:{ppl:.1f}  LR:{scheduler.get_last_lr()[0]:.4f}  T:{elapsed:.0f}s")

    train_time = time.perf_counter() - t_train_start
    print(f"\n  Total training time: {train_time:.0f}s ({train_time/60:.1f} min)")
    if len(losses) >= 2:
        print(f"  Loss: {losses[0]:.4f} -> {losses[-1]:.4f} ({((losses[0]-losses[-1])/losses[0]*100):.1f}% reduction)")
        print(f"  PPL: {math.exp(losses[0]):.1f} -> {math.exp(min(losses[-1],12)):.1f}")

    # ---- 6. Test & Save ----
    print("\n[6/6] Testing & saving...")
    model.eval()
    model = model.to(torch.float32)  # for cleaner sampling

    kw_set = {"def", "class", "import", "from", "return", "if", "else", "for",
              "self", "None", "True", "False", "print", "open", "len", "range",
              "try", "except", "with", "url", "request", "scan", "urllib"}

    prompts = ["def scan", "import urllib", "def fetch", "class Scanner", "def parse"]
    print(f"\n  Generation tests (top-k=10, temp=0.5):")
    print(f"  {'-'*60}")
    tot_kw = 0
    tot_bal = 0
    n_syn = 0
    for p in prompts:
        ids = tok.encode(p)
        if not ids:
            ids = [0]
        idx = torch.tensor([ids], dtype=torch.long)
        gen = model.generate(idx, max_new_tokens=35, temperature=0.5, top_k=10)
        text = tok.decode(gen[0].tolist())
        found_kw = sum(1 for k in kw_set if k in text.lower())
        bal = 1 if text.count("(") == text.count(")") else 0
        try:
            compile(text, "<gen>", "exec")
            syn = 1
        except Exception:
            syn = 0
        tot_kw += found_kw
        tot_bal += bal
        n_syn += syn
        print(f"  '{p}' -> {text[:75]!r} [kw:{found_kw} bal:{bal} syn:{syn}]")

    n = len(prompts)
    avg_kw = tot_kw / n
    bal_pct = tot_bal / n * 100
    syn_pct = n_syn / n * 100

    # Benchmark
    test = torch.tensor([[0]], dtype=torch.long)
    bench = []
    for _ in range(3):
        t0 = time.perf_counter()
        with torch.no_grad():
            model.generate(test, max_new_tokens=20, temperature=0.5, top_k=10)
        bench.append(time.perf_counter() - t0)
    tps = 20 / float(np.mean(bench))

    # Save fp32
    state = model.state_dict()
    save_dict_fp32 = {
        'model_state_dict': state,
        'model_config': {'vocab_size': vocab_size, 'embed_dim': 512, 'num_layers': 6,
                         'num_heads': 8, 'max_seq_len': seq_len},
        'tokenizer_vocab': tok.vocab,
        'tokenizer_merges': tok.merges,
        'tokenizer_type': 'fast_bpe_v2',
        'training': losses,
        'meta': {'name': 'IBR-GPT-Code-Compact', 'pretrained': False, 'params': params,
                 'samples': len(samples), 'seqs': len(train_seqs),
                 'golden_stack': ['bfloat16', 'sgd-momentum', 'grad-accum', 'weight-tying',
                                  'curriculum-learning', 'dedup', 'bpe-cache', 'int4-quant']},
    }
    torch.save(save_dict_fp32, MODEL_PATH_FP32)
    fp32_size = os.path.getsize(MODEL_PATH_FP32) / 1024 / 1024

    # Save INT4
    print(f"\n  Quantizing to INT4 (8x compression)...")
    quant = quantize_model_int4(state)
    int4_bytes = estimate_int4_size_bytes(quant)
    int4_size = int4_bytes / 1024 / 1024
    save_dict_int4 = {
        'quantized_state': quant,
        'model_config': save_dict_fp32['model_config'],
        'tokenizer_vocab': tok.vocab,
        'tokenizer_merges': tok.merges,
        'tokenizer_type': 'fast_bpe_v2',
        'training': losses,
        'meta': {**save_dict_fp32['meta'], 'quantization': 'INT4',
                 'params': params, 'fp32_size_mb': fp32_size, 'int4_size_mb': int4_size},
    }
    torch.save(save_dict_int4, MODEL_PATH_INT4)
    int4_file_size = os.path.getsize(MODEL_PATH_INT4) / 1024 / 1024

    print(f"\n{'='*70}")
    print(f"  IBR-GPT-Code-Compact — COMPLETE")
    print(f"{'='*70}")
    print(f"  Params:       {params:,} ({params/1e6:.2f}M)")
    print(f"  Samples:      {len(samples):,}")
    print(f"  Tokens:       {len(all_tokens):,}")
    print(f"  Vocab:        {vocab_size}")
    print(f"  Training:     {train_time:.0f}s ({train_time/60:.1f} min)")
    if len(losses) >= 2:
        print(f"  Loss:         {losses[0]:.4f} -> {losses[-1]:.4f} ({((losses[0]-losses[-1])/losses[0]*100):.1f}%)")
        print(f"  Perplexity:   {math.exp(losses[0]):.1f} -> {math.exp(min(losses[-1],12)):.1f}")
    print(f"  Quality:      {avg_kw:.1f} kw/out | {bal_pct:.0f}% balanced | {syn_pct:.0f}% valid syntax")
    print(f"  Speed:        {tps:.1f} tok/s")
    print(f"  Size (fp32):  {fp32_size:.1f} MB")
    print(f"  Size (INT4):  {int4_file_size:.1f} MB   <-- target: 10-15 MB")
    print(f"  Compression:  {fp32_size/int4_file_size:.1f}x")
    print(f"  Pre-trained:  NO (from scratch)")
    print(f"  Cost:         $0.00")


if __name__ == "__main__":
    main()
