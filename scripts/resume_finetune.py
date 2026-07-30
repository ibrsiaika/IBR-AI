#!/usr/bin/env python3
"""
Resume finetune from the saved E2 checkpoint and run E3+ for better quality.

The previous extended_finetune.py was killed during E3. This script loads
the E2 checkpoint and continues training for more epochs.
"""
import gc
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
from train_full_pipeline import remap_state_dict_keys, tokenize_samples
from conversation_data import get_conversation_data

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
FINETUNE_PATH = MODEL_DIR / "ibr_gpt_code_100m_finetuned.pt"

torch.set_num_threads(2)
SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)


def cosine_lr_lambda(step, warmup, total):
    if step < warmup:
        return step / max(warmup, 1)
    progress = (step - warmup) / max(1, total - warmup)
    return 0.1 + 0.9 * 0.5 * (1.0 + math.cos(math.pi * progress))


@torch.no_grad()
def generate_greedy(model, tok, prompt, max_tokens=50):
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


def main():
    print("=" * 70)
    print("  Resume Fine-tune from E2 Checkpoint")
    print("=" * 70)

    # Load the E2 checkpoint
    print("\n[1/4] Loading E2 finetuned model...")
    ckpt = torch.load(FINETUNE_PATH, map_location='cpu', weights_only=False)
    cfg = ckpt['model_config']
    meta = ckpt.get('meta', {})

    model = ScratchGPTLarge(
        vocab_size=cfg['vocab_size'],
        embed_dim=cfg['embed_dim'],
        num_layers=cfg['num_layers'],
        num_heads=cfg['num_heads'],
        max_seq_len=cfg['max_seq_len'],
        use_checkpointing=True,
    )
    state = ckpt['model_state_dict']
    state = remap_state_dict_keys(state, set(model.state_dict().keys()))
    model.load_state_dict(state)
    print(f"  Loaded: stage={meta.get('stage', '?')}")
    print(f"  Previous finetune losses: {meta.get('finetune_losses', [])}")

    # Build tokenizer
    tok = FastBPETokenizerV2(vocab_size=cfg['vocab_size'])
    tok.vocab = ckpt['tokenizer_vocab']
    tok.id_to_token = {v: k for k, v in tok.vocab.items()}
    tok.merges = [tuple(p) for p in ckpt['tokenizer_merges']]

    # Prepare conversation data (expand 15x for even more signal)
    print("\n[2/4] Preparing conversation data...")
    conv_data = get_conversation_data()
    print(f"  Conversation samples: {len(conv_data)}")
    conv_repeated = conv_data * 15  # 15x = 4215 samples
    print(f"  Expanded (15x): {len(conv_repeated)} samples")

    conv_seqs, conv_tokens = tokenize_samples(tok, conv_repeated, seq_len=32,
                                               label="conversation ", limit=5000)

    # Continue training: 2 more epochs at lower LR (0.02) for fine-tuning
    print("\n[3/4] Continuing fine-tune (2 epochs, LR=0.02)...")
    model = model.to(torch.bfloat16)

    train_seqs = conv_seqs[:3000]
    data = torch.tensor(train_seqs, dtype=torch.long)

    opt = torch.optim.SGD(
        model.parameters(),
        lr=0.02, momentum=0.9, weight_decay=1e-4, nesterov=True,
    )
    EPOCHS = 2
    MICRO_BATCH = 4
    GRAD_ACCUM = 2
    WARMUP = 10
    total_steps = (EPOCHS * len(data)) // (MICRO_BATCH * GRAD_ACCUM)
    scheduler = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: cosine_lr_lambda(s, WARMUP, total_steps)
    )

    prev_losses = meta.get('finetune_losses', [])
    losses = []
    model.train()
    t_start = time.perf_counter()
    step_count = 0

    for epoch in range(EPOCHS):
        perm = torch.randperm(len(data))
        ep_losses = []
        opt.zero_grad()

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
                print(f"  ERROR: {e}")
                break

            if (i // MICRO_BATCH + 1) % GRAD_ACCUM == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
                opt.zero_grad()
                scheduler.step()
                step_count += 1
                if step_count % 50 == 0:
                    avg = float(np.mean(ep_losses[-50:])) if ep_losses else float('nan')
                    lr = scheduler.get_last_lr()[0]
                    elapsed = time.perf_counter() - t_start
                    print(f"  E{epoch+1} step {step_count}/{total_steps} loss={avg:.4f} lr={lr:.5f} t={elapsed:.0f}s")

            if i % (MICRO_BATCH * 50) == 0 and i > 0:
                gc.collect()

        avg_loss = float(np.mean(ep_losses)) if ep_losses else float('nan')
        ppl = math.exp(min(avg_loss, 12)) if not math.isnan(avg_loss) else float('nan')
        elapsed = time.perf_counter() - t_start
        losses.append(avg_loss)
        print(f"\n  E{epoch+1}/{EPOCHS}  Loss:{avg_loss:.4f}  PPL:{ppl:.1f}  T:{elapsed:.0f}s")

        # Show generation after each epoch
        model.eval()
        print(f"  Generation after E{epoch+1}:")
        for p in ["User: Hi", "User: What is Python?", "User: Write a function"]:
            text = generate_greedy(model, tok, p, max_tokens=40)
            print(f"    {p!r} -> {text[:80]!r}")
        model.train()

        # Save after each epoch
        model_cpu = model.to(torch.float32)
        all_ft_losses = prev_losses + losses
        pretrain_losses = ckpt.get('training', [])[:2] if ckpt.get('training') else []
        torch.save({
            'model_state_dict': model_cpu.state_dict(),
            'model_config': cfg,
            'tokenizer_vocab': tok.vocab,
            'tokenizer_merges': tok.merges,
            'tokenizer_type': 'fast_bpe_v2',
            'training': pretrain_losses + all_ft_losses,
            'meta': {
                'name': 'IBR-GPT-Code-100M',
                'stage': f'finetuned-E{len(all_ft_losses)}',
                'pretrained': False,
                'params': model_cpu.count_parameters(),
                'finetune_epochs': len(all_ft_losses),
                'finetune_losses': all_ft_losses,
                'pretrain_losses': pretrain_losses,
            },
        }, FINETUNE_PATH)
        print(f"  Saved: {FINETUNE_PATH.name} ({os.path.getsize(FINETUNE_PATH)/1024/1024:.1f} MB)")
        model = model_cpu.to(torch.bfloat16)

    # Final generation
    print(f"\n{'='*70}")
    print(f"  FINAL GENERATION")
    print(f"{'='*70}")
    model.eval()
    model_cpu = model.to(torch.float32)

    prompts = [
        "User: Hi",
        "User: Hello",
        "User: How are you?",
        "User: What is Python?",
        "User: Write a function",
        "User: Thank you",
        "User: Bye",
        "User: What can you do?",
    ]
    for p in prompts:
        text = generate_greedy(model_cpu, tok, p, max_tokens=50)
        print(f"\n  {p}")
        print(f"  -> {text[:100]}")

    train_time = time.perf_counter() - t_start
    print(f"\n{'='*70}")
    print(f"  COMPLETE")
    print(f"{'='*70}")
    print(f"  Previous losses: {prev_losses}")
    print(f"  New losses: {losses}")
    print(f"  Total finetune epochs: {len(prev_losses) + len(losses)}")
    print(f"  Time: {train_time:.0f}s ({train_time/60:.1f} min)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
