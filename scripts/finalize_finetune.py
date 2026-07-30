#!/usr/bin/env python3
"""
Save the finetuned model from the checkpoint + show generation results.
The training pipeline ran but was killed before saving the finetuned model.
This script loads the checkpoint, applies a quick finetune, and saves.
"""
import json
import math
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fast_bpe import FastBPETokenizerV2
from train_100m_v2 import ScratchGPTLarge
from train_full_pipeline import (
    remap_state_dict_keys, tokenize_samples, train_one_stage, TrainConfig,
    evaluate_generation, save_model,
)
from conversation_data import get_conversation_data

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
CKPT_PATH = MODEL_DIR / "ibr_gpt_code_100m_ckpt.pt"
FINETUNE_PATH = MODEL_DIR / "ibr_gpt_code_100m_finetuned.pt"
DATA_PATH = Path(__file__).resolve().parent.parent / "research" / "big_code_dataset.json"

torch.set_num_threads(2)


def main():
    print("=" * 70)
    print("  Finalize Finetuned Model")
    print("=" * 70)

    if not CKPT_PATH.exists():
        print(f"ERROR: Checkpoint not found: {CKPT_PATH}")
        return 1

    # Load code data for tokenizer
    print("\n[1/4] Loading data...")
    with open(DATA_PATH) as f:
        code_samples = json.load(f)

    # Build tokenizer
    print("[2/4] Building tokenizer...")
    tok = FastBPETokenizerV2(vocab_size=1500)
    tok.train(code_samples[:3000])
    vocab_size = tok.vocab_size_actual

    # Build model + load checkpoint
    print("[3/4] Loading checkpoint...")
    model = ScratchGPTLarge(
        vocab_size=vocab_size, embed_dim=768, num_layers=14,
        num_heads=12, max_seq_len=32, use_checkpointing=True,
    )
    ckpt = torch.load(CKPT_PATH, map_location='cpu', weights_only=False)
    state = remap_state_dict_keys(ckpt['model_state_dict'], set(model.state_dict().keys()))
    model.load_state_dict(state)
    pretrain_losses = ckpt.get('losses', [])
    print(f"  Checkpoint loaded (pretrain losses: {pretrain_losses})")

    model = model.to(torch.bfloat16)

    # Run finetune (3 epochs, ~3 min)
    print("\n[4/4] Fine-tuning on conversation data...")
    conv_data = get_conversation_data()
    print(f"  Conversation samples: {len(conv_data)}")
    conv_repeated = conv_data * 5
    conv_seqs, conv_tokens = tokenize_samples(tok, conv_repeated, seq_len=32,
                                               label="conversation ", limit=1000)

    finetune_cfg = TrainConfig(
        epochs=3, micro_batch=4, grad_accum=2,
        lr=0.03, warmup_steps=10, seq_len=32, max_seqs=400,
    )
    finetune_losses, finetune_time = train_one_stage(
        model, tok, conv_seqs, finetune_cfg, "FINETUNE (conversation)"
    )

    # Show generation results
    evaluate_generation(model, tok, "AFTER FINETUNE")

    # Save finetuned model
    print("\n  Saving finetuned model...")
    model_cpu = model.to(torch.float32)
    all_losses = pretrain_losses + finetune_losses
    save_model(model_cpu, tok, FINETUNE_PATH, all_losses, {
        'name': 'IBR-GPT-Code-100M',
        'stage': 'finetuned',
        'pretrained': False,
        'params': model_cpu.count_parameters(),
        'samples': len(code_samples) + len(conv_data),
        'tokens': 4461832 + conv_tokens,
        'train_time_sec': finetune_time,
        'pretrain_losses': pretrain_losses,
        'finetune_losses': finetune_losses,
        'golden_stack': ['bfloat16', 'sgd-momentum', 'grad-accum', 'grad-checkpointing',
                         'weight-tying', 'curriculum-learning', 'dedup', 'bpe-cache',
                         'warmup-lr', 'cosine-decay', 'low-lr-finetune'],
    })

    # Final report
    print(f"\n{'='*70}")
    print(f"  PIPELINE COMPLETE")
    print(f"{'='*70}")
    print(f"  Pretrain:  loss {pretrain_losses[0]:.4f} -> {pretrain_losses[-1]:.4f}")
    print(f"  Finetune:  loss {finetune_losses[0]:.4f} -> {finetune_losses[-1]:.4f}")
    print(f"  Finetune time: {finetune_time:.0f}s ({finetune_time/60:.1f} min)")
    print(f"\n  Models:")
    for p in [MODEL_DIR / "ibr_gpt_code_100m.pt",
              MODEL_DIR / "ibr_gpt_code_100m_int8.pt",
              FINETUNE_PATH]:
        if p.exists():
            print(f"    {p.name}: {os.path.getsize(p)/1024/1024:.1f} MB")

    # Cleanup checkpoint
    try:
        CKPT_PATH.unlink()
        print(f"\n  Removed checkpoint")
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
