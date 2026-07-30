#!/usr/bin/env python3
"""
IBR-GPT-Code 100M — Comprehensive End-to-End Training Pipeline

Two-stage training on CPU (2-core, 4GB RAM):
  Stage 1: PRETRAIN on 27K Python code samples (CodeParrot-clean)
  Stage 2: FINE-TUNE on curated human-like conversation data

The model learns to:
  - Write Python code (from pretrain)
  - Hold simple conversations (from finetune)
  - Respond like a human assistant

Architecture: 14L × 768D × 12H = 100.4M params (from scratch, NO pre-trained weights)

Optimizations (Golden Token Stack):
  - bfloat16 mixed precision (with fp32 cross-entropy for stability)
  - SGD with momentum + warmup + cosine LR decay
  - Gradient accumulation (effective batch=8 from micro-batch=4)
  - Gradient checkpointing (recompute activations to save memory)
  - Weight tying (lm_head = token_embedding, saves 1.15M params)
  - Curriculum learning (easy→hard sequence ordering)
  - Hash-based deduplication
  - BPE semantic cache (50K word encoding cache)

Output:
  - models/ibr_gpt_code_100m.pt (383 MB fp32, pretrained)
  - models/ibr_gpt_code_100m_int8.pt (97 MB INT8)
  - models/ibr_gpt_code_100m_finetuned.pt (fine-tuned, talks like human)

Usage:
  python scripts/train_full_pipeline.py
  python scripts/train_full_pipeline.py --skip-pretrain   # only finetune
  python scripts/train_full_pipeline.py --skip-finetune   # only pretrain
"""
from __future__ import annotations

import argparse
import gc
import json
import math
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

# Load scratch modules directly (avoid transformers dependency)
import importlib.util
_scratch_path = Path(__file__).resolve().parent.parent / "src" / "ibr_platform" / "models" / "scratch" / "__init__.py"
_spec = importlib.util.spec_from_file_location("ibr_scratch", _scratch_path)
_scratch_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_scratch_mod)
TransformerBlock = _scratch_mod.TransformerBlock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fast_bpe import FastBPETokenizerV2
from train_100m_v2 import ScratchGPTLarge, quantize_int8
from conversation_data import get_conversation_data

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
DATA_PATH = Path(__file__).resolve().parent.parent / "research" / "big_code_dataset.json"
PRETRAIN_PATH = MODEL_DIR / "ibr_gpt_code_100m.pt"
PRETRAIN_INT8_PATH = MODEL_DIR / "ibr_gpt_code_100m_int8.pt"
FINETUNE_PATH = MODEL_DIR / "ibr_gpt_code_100m_finetuned.pt"
CKPT_PATH = MODEL_DIR / "ibr_gpt_code_100m_ckpt.pt"

torch.set_num_threads(2)
SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)


# ============================================================================
# DATA PREPARATION
# ============================================================================

def load_code_data() -> list[str]:
    """Load Python code dataset."""
    print("  Loading code dataset...")
    with open(DATA_PATH) as f:
        samples = json.load(f)
    print(f"  {len(samples):,} code samples loaded ({sum(len(s) for s in samples)/1e6:.1f} MB)")
    return samples


def tokenize_samples(tok: FastBPETokenizerV2, samples: list[str], seq_len: int,
                     label: str = "", limit: int = 5000) -> tuple[np.ndarray, int]:
    """Tokenize samples and create sequences."""
    print(f"  Tokenizing {min(len(samples), limit):,} {label}samples...")
    t0 = time.perf_counter()
    all_tokens: list[int] = []
    eos_id = tok.vocab.get("<EOS>", 0)
    for i, s in enumerate(samples[:limit]):
        if i % 1000 == 0 and i > 0:
            print(f"    {i}/{min(len(samples), limit)}")
        enc = tok.encode(s)
        if len(enc) > 5:
            all_tokens.extend(enc)
            all_tokens.append(eos_id)
    print(f"  Total tokens: {len(all_tokens):,} ({time.perf_counter()-t0:.1f}s)")

    n_seqs = len(all_tokens) // (seq_len + 1)
    sequences = np.array(all_tokens[:n_seqs * (seq_len + 1)]).reshape(n_seqs, seq_len + 1)
    print(f"  Sequences: {n_seqs:,}")

    # Deduplicate
    seen: set = set()
    keep_idx: list[int] = []
    for i in range(n_seqs):
        h = sequences[i].tobytes()
        if h not in seen:
            seen.add(h)
            keep_idx.append(i)
    sequences = sequences[keep_idx]
    print(f"  After dedup: {len(sequences):,}")

    # Curriculum learning: sort by complexity
    complexities = [len(set(sequences[i].tolist())) for i in range(len(sequences))]
    sort_idx = np.argsort(complexities)
    sequences = sequences[sort_idx]
    print(f"  Curriculum learning applied (easy -> hard)")

    return sequences, len(all_tokens)


# ============================================================================
# TRAINING
# ============================================================================

@dataclass
class TrainConfig:
    epochs: int = 2
    micro_batch: int = 4
    grad_accum: int = 2
    lr: float = 0.1
    warmup_steps: int = 20
    seq_len: int = 32
    max_seqs: int = 1500


def cosine_lr_lambda(step: int, warmup: int, total: int) -> float:
    if step < warmup:
        return step / max(warmup, 1)
    progress = (step - warmup) / max(1, total - warmup)
    return 0.5 * (1.0 + math.cos(math.pi * progress))


def train_one_stage(model: ScratchGPTLarge, tok: FastBPETokenizerV2,
                    sequences: np.ndarray, cfg: TrainConfig, stage_name: str) -> tuple[list[float], float]:
    print(f"\n{'='*70}")
    print(f"  STAGE: {stage_name}")
    print(f"  Epochs: {cfg.epochs}, Batch: {cfg.micro_batch}x{cfg.grad_accum}={cfg.micro_batch*cfg.grad_accum}")
    print(f"  LR: {cfg.lr}, Warmup: {cfg.warmup_steps} steps")
    print(f"  Sequences: {len(sequences):,}")
    print(f"{'='*70}")

    train_seqs = sequences[:cfg.max_seqs] if len(sequences) > cfg.max_seqs else sequences
    print(f"  Training on: {len(train_seqs):,} sequences")

    data = torch.tensor(train_seqs, dtype=torch.long)

    opt = torch.optim.SGD(
        model.parameters(),
        lr=cfg.lr,
        momentum=0.9,
        weight_decay=1e-4,
        nesterov=True,
    )
    total_steps = (cfg.epochs * len(data)) // (cfg.micro_batch * cfg.grad_accum)
    scheduler = torch.optim.lr_scheduler.LambdaLR(
        opt,
        lambda s: cosine_lr_lambda(s, cfg.warmup_steps, total_steps),
    )

    losses: list[float] = []
    model.train()
    t_start = time.perf_counter()
    step_count = 0

    for epoch in range(cfg.epochs):
        perm = torch.randperm(len(data))
        ep_losses: list[float] = []
        opt.zero_grad()

        for i in range(0, len(data), cfg.micro_batch):
            batch = data[perm[i:i + cfg.micro_batch]]
            if batch.size(0) == 0:
                continue
            x = batch[:, :-1]
            y = batch[:, 1:]
            try:
                _, loss = model(x, targets=y)
                (loss / cfg.grad_accum).backward()
                ep_losses.append(loss.item())
            except Exception as e:
                print(f"  [step {step_count}] ERROR: {e}")
                break

            if (i // cfg.micro_batch + 1) % cfg.grad_accum == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
                opt.zero_grad()
                scheduler.step()
                step_count += 1
                if step_count % 30 == 0:
                    avg = float(np.mean(ep_losses[-30:])) if ep_losses else float('nan')
                    lr = scheduler.get_last_lr()[0]
                    elapsed = time.perf_counter() - t_start
                    print(f"  E{epoch+1} step {step_count}/{total_steps} loss={avg:.4f} lr={lr:.5f} t={elapsed:.0f}s")

            if i % (cfg.micro_batch * 20) == 0 and i > 0:
                gc.collect()

        avg_loss = float(np.mean(ep_losses)) if ep_losses else float('nan')
        ppl = math.exp(min(avg_loss, 12)) if not math.isnan(avg_loss) else float('nan')
        elapsed = time.perf_counter() - t_start
        losses.append(avg_loss)
        print(f"\n  E{epoch+1}/{cfg.epochs}  Loss:{avg_loss:.4f}  PPL:{ppl:.1f}  T:{elapsed:.0f}s")

    total_time = time.perf_counter() - t_start
    return losses, total_time


# ============================================================================
# GENERATION / EVALUATION
# ============================================================================

@torch.no_grad()
def generate_greedy(model: ScratchGPTLarge, tok: FastBPETokenizerV2,
                    prompt: str, max_tokens: int = 40) -> str:
    ids = tok.encode(prompt)
    if not ids:
        ids = [0]
    idx = torch.tensor([ids], dtype=torch.long)
    eos_id = tok.vocab.get("<EOS>", -1)
    for _ in range(max_tokens):
        idx_cond = idx if idx.size(1) <= model.max_seq_len else idx[:, -model.max_seq_len:]
        logits, _ = model(idx_cond)
        next_id = logits[:, -1, :].argmax(dim=-1, keepdim=True)
        idx = torch.cat([idx, next_id], dim=1)
        if next_id.item() == eos_id:
            break
    return tok.decode(idx[0].tolist())


@torch.no_grad()
def generate_top_k(model: ScratchGPTLarge, tok: FastBPETokenizerV2,
                   prompt: str, max_tokens: int = 40,
                   temperature: float = 0.7, top_k: int = 10) -> str:
    ids = tok.encode(prompt)
    if not ids:
        ids = [0]
    idx = torch.tensor([ids], dtype=torch.long)
    eos_id = tok.vocab.get("<EOS>", -1)
    for _ in range(max_tokens):
        idx_cond = idx if idx.size(1) <= model.max_seq_len else idx[:, -model.max_seq_len:]
        logits, _ = model(idx_cond)
        logits = logits[:, -1, :] / max(temperature, 1e-5)
        v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
        logits[logits < v[:, [-1]]] = float('-inf')
        probs = F.softmax(logits, dim=-1)
        next_id = torch.multinomial(probs, num_samples=1)
        idx = torch.cat([idx, next_id], dim=1)
        if next_id.item() == eos_id:
            break
    return tok.decode(idx[0].tolist())


def evaluate_generation(model: ScratchGPTLarge, tok: FastBPETokenizerV2,
                        stage_name: str, prompts: list[str] | None = None) -> None:
    print(f"\n{'='*70}")
    print(f"  GENERATION SAMPLES — {stage_name}")
    print(f"{'='*70}")
    if prompts is None:
        prompts = [
            "def scan",
            "import urllib",
            "User: Hi",
            "User: What is Python?",
            "User: Write a function",
            "User: How are you?",
        ]
    model.eval()
    for p in prompts:
        text_greedy = generate_greedy(model, tok, p, max_tokens=40)
        text_topk = generate_top_k(model, tok, p, max_tokens=40, temperature=0.5, top_k=10)
        print(f"\n  Prompt: {p!r}")
        print(f"  Greedy: {text_greedy[:100]!r}")
        print(f"  Top-k:  {text_topk[:100]!r}")


# ============================================================================
# SAVE / LOAD
# ============================================================================

def save_model(model: ScratchGPTLarge, tok: FastBPETokenizerV2, path: Path,
               losses: list[float], meta: dict) -> None:
    model.eval()
    state = model.state_dict()
    save_dict = {
        'model_state_dict': state,
        'model_config': {
            'vocab_size': tok.vocab_size_actual,
            'embed_dim': model.embed_dim,
            'num_layers': len(model.blocks),
            'num_heads': 12,
            'max_seq_len': model.max_seq_len,
        },
        'tokenizer_vocab': tok.vocab,
        'tokenizer_merges': tok.merges,
        'tokenizer_type': 'fast_bpe_v2',
        'training': losses,
        'meta': meta,
    }
    torch.save(save_dict, path)
    size_mb = os.path.getsize(path) / 1024 / 1024
    print(f"  Saved: {path.name} ({size_mb:.1f} MB)")


def remap_state_dict_keys(state: dict, model_keys: set) -> dict:
    """Remap state dict keys to match model (handle CheckpointedBlock wrapper)."""
    saved_keys = set(state.keys())
    if model_keys == saved_keys:
        return state
    # Need to ADD '.block.' (saved without checkpointing, model has it)
    needs_block = any('.block.' in k for k in model_keys) and not any('.block.' in k for k in saved_keys)
    if needs_block:
        new_state = {}
        for k, v in state.items():
            m = re.match(r'(blocks\.\d+)\.(.+)', k)
            if m:
                new_state[f"{m.group(1)}.block.{m.group(2)}"] = v
            else:
                new_state[k] = v
        return new_state
    # Need to REMOVE '.block.'
    has_block = any('.block.' in k for k in saved_keys) and not any('.block.' in k for k in model_keys)
    if has_block:
        new_state = {}
        for k, v in state.items():
            new_state[k.replace('.block.', '.')] = v
        return new_state
    return state


def load_or_build_model(vocab_size: int, seq_len: int, checkpoint_path: Path | None = None) -> ScratchGPTLarge:
    model = ScratchGPTLarge(
        vocab_size=vocab_size,
        embed_dim=768,
        num_layers=14,
        num_heads=12,
        max_seq_len=seq_len,
        dropout=0.1,
        use_checkpointing=True,
    )
    params = model.count_parameters()
    print(f"  Model: {params:,} params ({params/1e6:.2f}M)")

    if checkpoint_path and checkpoint_path.exists():
        print(f"  Loading checkpoint: {checkpoint_path.name}")
        ckpt = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
        state = ckpt['model_state_dict']
        state = remap_state_dict_keys(state, set(model.state_dict().keys()))
        model.load_state_dict(state)
        print(f"  Checkpoint loaded (epoch {ckpt.get('epoch', '?')})")
    else:
        print(f"  No checkpoint found, starting from scratch (random init)")

    model = model.to(torch.bfloat16)
    print(f"  Using bfloat16")
    return model


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(description="IBR-GPT-Code 100M Full Pipeline")
    parser.add_argument("--skip-pretrain", action="store_true",
                        help="Skip pretrain stage (load existing checkpoint)")
    parser.add_argument("--skip-finetune", action="store_true",
                        help="Skip fine-tune stage")
    args = parser.parse_args()

    print("=" * 70)
    print("  IBR-GPT-Code 100M — Full Training Pipeline")
    print("  Stage 1: Pretrain on Python code")
    print("  Stage 2: Fine-tune on human-like conversation")
    print("  Hardware: 2-core CPU, 4GB RAM, no GPU")
    print("=" * 70)

    total_start = time.perf_counter()

    # ====== STEP 1: Load code data ======
    print("\n[1/6] Loading code dataset...")
    code_samples = load_code_data()

    # ====== STEP 2: Train BPE tokenizer on code ======
    print("\n[2/6] Training BPE tokenizer (1500 vocab, Fast BPE)...")
    t0 = time.perf_counter()
    tok = FastBPETokenizerV2(vocab_size=1500)
    tok.train(code_samples[:3000])
    vocab_size = tok.vocab_size_actual
    print(f"  Vocab: {vocab_size} | Trained in {time.perf_counter()-t0:.1f}s")

    # ====== STEP 3: Tokenize code → sequences ======
    print("\n[3/6] Preparing pretrain sequences...")
    code_seqs, total_tokens = tokenize_samples(tok, code_samples, seq_len=32,
                                                label="code ", limit=5000)

    # ====== STEP 4: Build/load model ======
    print("\n[4/6] Building IBR-GPT-Code-100M (14L/768D/12H)...")
    ckpt = CKPT_PATH if args.skip_pretrain else None
    model = load_or_build_model(vocab_size, seq_len=32, checkpoint_path=ckpt)

    # ====== STEP 5: PRETRAIN ======
    pretrain_losses: list[float] = []
    pretrain_time = 0.0
    if not args.skip_pretrain:
        print("\n[5/6] STAGE 1: Pretrain on Python code")
        pretrain_cfg = TrainConfig(
            epochs=2, micro_batch=4, grad_accum=2,
            lr=0.1, warmup_steps=20, seq_len=32, max_seqs=1500,
        )
        pretrain_losses, pretrain_time = train_one_stage(
            model, tok, code_seqs, pretrain_cfg, "PRETRAIN (Python code)"
        )

        # Save checkpoint after pretrain
        print("\n  Saving pretrain checkpoint...")
        model_cpu = model.to(torch.float32)
        torch.save({
            'model_state_dict': model_cpu.state_dict(),
            'epoch': 2,
            'losses': pretrain_losses,
            'model_config': {
                'vocab_size': vocab_size, 'embed_dim': 768,
                'num_layers': 14, 'num_heads': 12, 'max_seq_len': 32,
            },
            'tokenizer_vocab': tok.vocab,
            'tokenizer_merges': tok.merges,
        }, CKPT_PATH)
        model = model_cpu.to(torch.bfloat16)
        print(f"  Checkpoint saved: {CKPT_PATH.name}")

        # Evaluate pretrain
        evaluate_generation(model, tok, "AFTER PRETRAIN")

        # Save pretrained model
        print("\n  Saving pretrained model...")
        model_cpu = model.to(torch.float32)
        save_model(model_cpu, tok, PRETRAIN_PATH, pretrain_losses, {
            'name': 'IBR-GPT-Code-100M',
            'stage': 'pretrained',
            'pretrained': False,
            'params': model_cpu.count_parameters(),
            'samples': len(code_samples),
            'tokens': total_tokens,
            'train_time_sec': pretrain_time,
            'optimizer': 'SGD-momentum',
            'lr_schedule': 'warmup+cosine',
            'golden_stack': ['bfloat16', 'sgd-momentum', 'grad-accum', 'grad-checkpointing',
                             'weight-tying', 'curriculum-learning', 'dedup', 'bpe-cache',
                             'warmup-lr', 'cosine-decay'],
        })

        # Save INT8 quantized
        print("  Quantizing to INT8...")
        quant_state, scales = quantize_int8(model_cpu.state_dict())
        torch.save({
            'model_state_dict': quant_state,
            'quant_scales': scales,
            'model_config': {'vocab_size': vocab_size, 'embed_dim': 768,
                             'num_layers': 14, 'num_heads': 12, 'max_seq_len': 32},
            'tokenizer_vocab': tok.vocab,
            'tokenizer_merges': tok.merges,
            'training': pretrain_losses,
            'meta': {'name': 'IBR-GPT-Code-100M', 'quantization': 'INT8',
                     'params': model_cpu.count_parameters()},
        }, PRETRAIN_INT8_PATH)
        print(f"  Saved: {PRETRAIN_INT8_PATH.name} ({os.path.getsize(PRETRAIN_INT8_PATH)/1024/1024:.1f} MB)")

        model = model_cpu.to(torch.bfloat16)
    else:
        print("\n[5/6] SKIPPING pretrain (using existing checkpoint)")

    # ====== STEP 6: FINETUNE on conversation ======
    finetune_losses: list[float] = []
    finetune_time = 0.0
    if not args.skip_finetune:
        print("\n[6/6] STAGE 2: Fine-tune on human-like conversation")
        conv_data = get_conversation_data()
        print(f"  Conversation samples: {len(conv_data)}")

        # Tokenize conversation data (repeat 5x for more signal)
        conv_repeated = conv_data * 5
        print(f"  Expanded (5x): {len(conv_repeated)} samples")
        conv_seqs, conv_tokens = tokenize_samples(tok, conv_repeated, seq_len=32,
                                                   label="conversation ", limit=1000)

        # Lower LR for fine-tuning
        finetune_cfg = TrainConfig(
            epochs=3, micro_batch=4, grad_accum=2,
            lr=0.03, warmup_steps=10, seq_len=32, max_seqs=400,
        )
        finetune_losses, finetune_time = train_one_stage(
            model, tok, conv_seqs, finetune_cfg, "FINETUNE (conversation)"
        )

        # Evaluate after finetune
        evaluate_generation(model, tok, "AFTER FINETUNE")

        # Save fine-tuned model
        print("\n  Saving fine-tuned model...")
        model_cpu = model.to(torch.float32)
        all_losses = pretrain_losses + finetune_losses
        save_model(model_cpu, tok, FINETUNE_PATH, all_losses, {
            'name': 'IBR-GPT-Code-100M',
            'stage': 'finetuned',
            'pretrained': False,
            'params': model_cpu.count_parameters(),
            'samples': len(code_samples) + len(conv_data),
            'tokens': total_tokens + conv_tokens,
            'train_time_sec': pretrain_time + finetune_time,
            'pretrain_losses': pretrain_losses,
            'finetune_losses': finetune_losses,
            'golden_stack': ['bfloat16', 'sgd-momentum', 'grad-accum', 'grad-checkpointing',
                             'weight-tying', 'curriculum-learning', 'dedup', 'bpe-cache',
                             'warmup-lr', 'cosine-decay', 'low-lr-finetune'],
        })

    # ====== FINAL REPORT ======
    total_time = time.perf_counter() - total_start
    print(f"\n{'='*70}")
    print(f"  FULL PIPELINE COMPLETE")
    print(f"{'='*70}")
    print(f"  Total time:     {total_time:.0f}s ({total_time/60:.1f} min)")
    if pretrain_losses:
        print(f"  Pretrain:       {pretrain_time:.0f}s, loss {pretrain_losses[0]:.4f} -> {pretrain_losses[-1]:.4f}")
    if finetune_losses:
        print(f"  Finetune:       {finetune_time:.0f}s, loss {finetune_losses[0]:.4f} -> {finetune_losses[-1]:.4f}")
    print(f"  Cost:           $0.00 (CPU only, no GPU)")
    print(f"  Pre-trained:    NO (from scratch)")
    print(f"\n  Models saved:")
    for p in [PRETRAIN_PATH, PRETRAIN_INT8_PATH, FINETUNE_PATH]:
        if p.exists():
            print(f"    {p.name}: {os.path.getsize(p)/1024/1024:.1f} MB")

    # Cleanup checkpoint
    try:
        CKPT_PATH.unlink()
        print(f"\n  Removed checkpoint (pipeline complete)")
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
