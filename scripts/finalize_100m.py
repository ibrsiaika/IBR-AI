#!/usr/bin/env python3
"""
Convert training checkpoint to final model + INT8.
Also test generation quality.
"""
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fast_bpe import FastBPETokenizerV2
from train_100m_v2 import ScratchGPTLarge, quantize_int8

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
CKPT_PATH = MODELS_DIR / "ibr_gpt_code_100m_ckpt.pt"
MODEL_PATH = MODELS_DIR / "ibr_gpt_code_100m.pt"
INT8_PATH = MODELS_DIR / "ibr_gpt_code_100m_int8.pt"

torch.set_num_threads(2)


def main():
    print("=" * 70)
    print("  Convert checkpoint to final model + test generation")
    print("=" * 70)

    if not CKPT_PATH.exists():
        print(f"ERROR: Checkpoint not found: {CKPT_PATH}")
        return 1

    print(f"\n[1/4] Loading checkpoint...")
    ckpt = torch.load(CKPT_PATH, map_location='cpu', weights_only=False)
    cfg = ckpt['model_config']
    epoch = ckpt.get('epoch', 0)
    losses = ckpt.get('losses', [])
    print(f"  Epoch: {epoch}, Losses: {losses}")

    print(f"\n[2/4] Building model...")
    m = ScratchGPTLarge(
        vocab_size=cfg['vocab_size'],
        embed_dim=cfg['embed_dim'],
        num_layers=cfg['num_layers'],
        num_heads=cfg['num_heads'],
        max_seq_len=cfg['max_seq_len'],
        use_checkpointing=False,
    )
    
    state = ckpt['model_state_dict']
    # Handle checkpointed key naming
    if any('.block.' in k for k in state.keys()):
        new_state = {}
        for k, v in state.items():
            new_state[k.replace('.block.', '.')] = v
        state = new_state
    m.load_state_dict(state)
    m.eval()
    params = m.count_parameters()
    print(f"  Loaded: {params:,} params ({params/1e6:.2f}M)")

    # Build tokenizer
    tok = FastBPETokenizerV2(vocab_size=cfg['vocab_size'])
    tok.vocab = ckpt['tokenizer_vocab']
    tok.id_to_token = {v: k for k, v in tok.vocab.items()}
    tok.merges = [tuple(p) for p in ckpt['tokenizer_merges']]

    print(f"\n[3/4] Testing generation quality...")
    kw_set = {"def", "class", "import", "from", "return", "if", "else", "for",
              "self", "None", "True", "False", "print", "open", "len", "range",
              "try", "except", "with", "url", "request", "scan", "urllib"}

    prompts = ["def scan", "import urllib", "def fetch", "class Scanner",
               "def parse", "def check", "def secure", "def extract"]
    
    print(f"\n  Generation tests (greedy decoding):")
    print(f"  {'-'*68}")
    tot_kw = 0
    tot_bal = 0
    n_syn = 0
    
    for p in prompts:
        ids = tok.encode(p)
        if not ids:
            ids = [0]
        idx = torch.tensor([ids], dtype=torch.long)
        # Greedy decode
        for _ in range(40):
            idx_cond = idx if idx.size(1) <= m.max_seq_len else idx[:, -m.max_seq_len:]
            with torch.no_grad():
                logits, _ = m(idx_cond)
            next_id = logits[:, -1, :].argmax(dim=-1, keepdim=True)
            idx = torch.cat([idx, next_id], dim=1)
            if next_id.item() == tok.vocab.get("<EOS>", -1):
                break
        text = tok.decode(idx[0].tolist())
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
        print(f"  '{p}' -> {text[:80]!r} [kw:{found_kw} bal:{bal} syn:{syn}]")

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
            for _ in range(20):
                idx_cond = test if test.size(1) <= m.max_seq_len else test[:, -m.max_seq_len:]
                logits, _ = m(idx_cond)
                test = torch.cat([test, logits[:, -1, :].argmax(dim=-1, keepdim=True)], dim=1)
        bench.append(time.perf_counter() - t0)
    tps = 20 / float(np.mean(bench))

    print(f"\n[4/4] Saving final model...")
    state = m.state_dict()
    save_dict = {
        'model_state_dict': state,
        'model_config': cfg,
        'tokenizer_vocab': tok.vocab,
        'tokenizer_merges': tok.merges,
        'tokenizer_type': 'fast_bpe_v2',
        'training': losses,
        'meta': {
            'name': 'IBR-GPT-Code-100M',
            'version': 'v3',
            'pretrained': False,
            'params': params,
            'samples': 27369,
            'tokens': 4461832,
            'seqs': 2000,
            'epochs_trained': epoch,
            'optimizer': 'SGD-momentum',
            'lr_schedule': 'warmup+cosine',
            'golden_stack': ['bfloat16', 'sgd-momentum', 'grad-accum', 'grad-checkpointing',
                             'weight-tying', 'curriculum-learning', 'dedup', 'bpe-cache',
                             'warmup-lr', 'cosine-decay', 'int8-quant'],
        },
    }
    torch.save(save_dict, MODEL_PATH)
    fp32_size = os.path.getsize(MODEL_PATH) / 1024 / 1024
    print(f"  {MODEL_PATH.name}: {fp32_size:.1f} MB")

    # INT8
    print(f"  Quantizing to INT8...")
    quant_state, scales = quantize_int8(state)
    int8_save = {
        'model_state_dict': quant_state,
        'quant_scales': scales,
        'model_config': cfg,
        'tokenizer_vocab': tok.vocab,
        'tokenizer_merges': tok.merges,
        'tokenizer_type': 'fast_bpe_v2',
        'training': losses,
        'meta': {**save_dict['meta'], 'quantization': 'INT8'},
    }
    torch.save(int8_save, INT8_PATH)
    int8_size = os.path.getsize(INT8_PATH) / 1024 / 1024
    print(f"  {INT8_PATH.name}: {int8_size:.1f} MB")

    # Cleanup checkpoint
    try:
        CKPT_PATH.unlink()
        print(f"  Removed checkpoint")
    except Exception:
        pass

    print(f"\n{'='*70}")
    print(f"  IBR-GPT-Code-100M v3 — FINAL")
    print(f"{'='*70}")
    print(f"  Params:       {params:,} ({params/1e6:.2f}M)")
    print(f"  Epochs:       {epoch}")
    if losses:
        print(f"  Loss:         {losses[0]:.4f} -> {losses[-1]:.4f}")
        print(f"  PPL:          {math.exp(losses[0]):.1f} -> {math.exp(min(losses[-1],12)):.1f}")
    print(f"  Quality:      {avg_kw:.1f} kw/out | {bal_pct:.0f}% balanced | {syn_pct:.0f}% valid syntax")
    print(f"  Speed:        {tps:.1f} tok/s (greedy)")
    print(f"  Size (fp32):  {fp32_size:.1f} MB")
    print(f"  Size (INT8):  {int8_size:.1f} MB")
    print(f"  Cost:         $0.00")
    return 0


if __name__ == "__main__":
    sys.exit(main())
