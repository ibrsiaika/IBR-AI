#!/usr/bin/env python3
"""
IBR-GPT-Code Inference Engine — Load trained model and generate Python code.

Features:
- Load fp32, INT8, or INT4 model variants
- Greedy decoding (deterministic, for "exact" answers)
- Top-k / Top-p (nucleus) sampling
- Beam search (best-of-N)
- Batch generation (multiple prompts at once)
- REPL mode (interactive prompt)

Usage:
    python scripts/inference.py --model 100m --prompt "def scan_url" --mode greedy
    python scripts/inference.py --model compact_int4 --prompt "import urllib" --mode beam --beams 4
    python scripts/inference.py --model 100m --repl
"""
import argparse
import json
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
from int4_quantizer import dequantize_int4

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
torch.set_num_threads(2)

MODEL_FILES = {
    '100m': MODELS_DIR / "ibr_gpt_code_100m.pt",
    '100m_int8': MODELS_DIR / "ibr_gpt_code_100m_int8.pt",
    'compact': MODELS_DIR / "ibr_gpt_code_compact.pt",
    'compact_int4': MODELS_DIR / "ibr_gpt_code_compact_int4.pt",
}


def load_model(model_key: str):
    """Load a model + tokenizer from checkpoint."""
    if model_key not in MODEL_FILES:
        raise ValueError(f"Unknown model: {model_key}. Available: {list(MODEL_FILES.keys())}")
    path = MODEL_FILES[model_key]
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}\nRun training first: python scripts/train_100m_v2.py")
    
    ckpt = torch.load(path, map_location='cpu', weights_only=False)
    cfg = ckpt['model_config']
    
    m = ScratchGPTLarge(
        vocab_size=cfg['vocab_size'],
        embed_dim=cfg['embed_dim'],
        num_layers=cfg['num_layers'],
        num_heads=cfg['num_heads'],
        max_seq_len=cfg['max_seq_len'],
        use_checkpointing=False,
    )
    
    # Load weights (handle different formats)
    if 'quantized_state' in ckpt:
        # INT4 or INT8 quantized model
        print(f"  Loading quantized ({ckpt['meta'].get('quantization', '?')}) model...", file=sys.stderr)
        quant = ckpt['quantized_state']
        new_state = {}
        for name in m.state_dict().keys():
            packed = quant['packed'].get(name)
            scales = quant['scales'].get(name)
            shape = quant['shapes'].get(name)
            
            if packed is None:
                # Try with .block. prefix (saved with checkpointing)
                m_match = re.match(r'(blocks\.\d+)\.(.+)', name)
                if m_match:
                    alt_name = f"{m_match.group(1)}.block.{m_match.group(2)}"
                    packed = quant['packed'].get(alt_name)
                    scales = quant['scales'].get(alt_name)
                    shape = quant['shapes'].get(alt_name)
            
            if packed is None:
                continue
            
            if scales is None:
                new_state[name] = torch.from_numpy(np.asarray(packed)).float() if hasattr(packed, 'dtype') else torch.tensor(packed).float()
            else:
                new_state[name] = dequantize_int4(packed, scales, shape).float()
        
        m.load_state_dict(new_state, strict=False)
    else:
        # fp32 model
        state = ckpt['model_state_dict']
        # Handle checkpointed key naming
        if any('.block.' in k for k in state.keys()):
            new_state = {}
            for k, v in state.items():
                new_state[k.replace('.block.', '.')] = v
            state = new_state
        m.load_state_dict(state)
    
    m.eval()
    
    # Build tokenizer
    tok = FastBPETokenizerV2(vocab_size=cfg['vocab_size'])
    tok.vocab = ckpt['tokenizer_vocab']
    tok.id_to_token = {v: k for k, v in tok.vocab.items()}
    tok.merges = [tuple(p) for p in ckpt['tokenizer_merges']]
    
    meta = ckpt.get('meta', {})
    print(f"  Loaded: {meta.get('name', model_key)} | {meta.get('params', 0):,} params", file=sys.stderr)
    return m, tok, cfg, meta


@torch.no_grad()
def generate_greedy(model, tokenizer, prompt: str, max_tokens: int = 50) -> str:
    """Greedy decoding — pick the most likely token each step. Deterministic."""
    ids = tokenizer.encode(prompt)
    if not ids:
        ids = [0]
    idx = torch.tensor([ids], dtype=torch.long)
    
    for _ in range(max_tokens):
        idx_cond = idx if idx.size(1) <= model.max_seq_len else idx[:, -model.max_seq_len:]
        logits, _ = model(idx_cond)
        # Greedy: argmax of last position
        next_id = logits[:, -1, :].argmax(dim=-1, keepdim=True)
        idx = torch.cat([idx, next_id], dim=1)
        # Stop on EOS
        if next_id.item() == tokenizer.vocab.get("<EOS>", -1):
            break
    
    return tokenizer.decode(idx[0].tolist())


@torch.no_grad()
def generate_top_k(model, tokenizer, prompt: str, max_tokens: int = 50,
                   temperature: float = 0.7, top_k: int = 10) -> str:
    """Top-k sampling."""
    ids = tokenizer.encode(prompt)
    if not ids:
        ids = [0]
    idx = torch.tensor([ids], dtype=torch.long)
    
    for _ in range(max_tokens):
        idx_cond = idx if idx.size(1) <= model.max_seq_len else idx[:, -model.max_seq_len:]
        logits, _ = model(idx_cond)
        logits = logits[:, -1, :] / max(temperature, 1e-5)
        # Top-k filter
        v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
        logits[logits < v[:, [-1]]] = float('-inf')
        probs = F.softmax(logits, dim=-1)
        next_id = torch.multinomial(probs, num_samples=1)
        idx = torch.cat([idx, next_id], dim=1)
        if next_id.item() == tokenizer.vocab.get("<EOS>", -1):
            break
    
    return tokenizer.decode(idx[0].tolist())


@torch.no_grad()
def generate_beam(model, tokenizer, prompt: str, max_tokens: int = 50,
                  num_beams: int = 4, length_penalty: float = 0.6) -> str:
    """Beam search — keeps top-N hypotheses, returns best."""
    ids = tokenizer.encode(prompt)
    if not ids:
        ids = [0]
    
    # Initialize beams
    beams = [(0.0, ids[:])]  # (log_prob, token_ids)
    finished = []
    eos_id = tokenizer.vocab.get("<EOS>", -1)
    
    for step in range(max_tokens):
        if not beams:
            break
        candidates = []
        for log_prob, beam_ids in beams:
            idx = torch.tensor([beam_ids], dtype=torch.long)
            idx_cond = idx if idx.size(1) <= model.max_seq_len else idx[:, -model.max_seq_len:]
            logits, _ = model(idx_cond)
            log_probs = F.log_softmax(logits[:, -1, :], dim=-1)[0]
            # Top-K candidates per beam
            top_log_probs, top_ids = log_probs.topk(num_beams)
            for k in range(num_beams):
                next_id = top_ids[k].item()
                new_lp = log_prob + top_log_probs[k].item()
                new_ids = beam_ids + [next_id]
                if next_id == eos_id:
                    finished.append((new_lp, new_ids))
                else:
                    candidates.append((new_lp, new_ids))
        
        # Keep top-N beams (with length penalty)
        candidates.sort(key=lambda x: x[0] / ((len(x[1]) ** length_penalty) + 1e-8), reverse=True)
        beams = candidates[:num_beams]
    
    # Add unfinished beams to finished
    finished.extend(beams)
    if not finished:
        return tokenizer.decode(ids)
    
    # Return best (highest avg log prob)
    finished.sort(key=lambda x: x[0] / max(len(x[1]), 1), reverse=True)
    best = finished[0][1]
    return tokenizer.decode(best)


def generate_batch(model, tokenizer, prompts: list[str], max_tokens: int = 40,
                   mode: str = "greedy", temperature: float = 0.7, top_k: int = 10) -> list[str]:
    """Generate for multiple prompts."""
    results = []
    for p in prompts:
        if mode == "greedy":
            r = generate_greedy(model, tokenizer, p, max_tokens)
        elif mode == "beam":
            r = generate_beam(model, tokenizer, p, max_tokens)
        else:
            r = generate_top_k(model, tokenizer, p, max_tokens, temperature, top_k)
        results.append(r)
    return results


def repl_mode(model, tokenizer, cfg):
    """Interactive REPL."""
    print(f"\nIBR-GPT-Code Interactive REPL")
    print(f"Type 'exit' or 'quit' to leave. 'mode X' to switch (greedy/topk/beam).")
    print(f"Max seq len: {cfg['max_seq_len']}")
    mode = "greedy"
    while True:
        try:
            prompt = input(f"\n[{mode}] > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not prompt:
            continue
        if prompt.lower() in ('exit', 'quit'):
            break
        if prompt.lower().startswith('mode '):
            mode = prompt[5:].strip().lower()
            if mode not in ('greedy', 'topk', 'beam'):
                mode = 'greedy'
            print(f"Switched to {mode} mode")
            continue
        if prompt.lower() == 'info':
            print(f"Mode: {mode}, Max seq: {cfg['max_seq_len']}, Vocab: {cfg['vocab_size']}")
            continue
        
        t0 = time.perf_counter()
        if mode == "greedy":
            text = generate_greedy(model, tokenizer, prompt, max_tokens=40)
        elif mode == "beam":
            text = generate_beam(model, tokenizer, prompt, max_tokens=40, num_beams=4)
        else:
            text = generate_top_k(model, tokenizer, prompt, max_tokens=40, temperature=0.5, top_k=10)
        elapsed = time.perf_counter() - t0
        n_new = len(tokenizer.encode(text)) - len(tokenizer.encode(prompt))
        tps = n_new / elapsed if elapsed > 0 else 0
        print(f"\n{text}")
        print(f"\n[{n_new} tokens in {elapsed:.2f}s = {tps:.1f} tok/s]")


def main():
    p = argparse.ArgumentParser(description="IBR-GPT-Code Inference Engine")
    p.add_argument('--model', default='100m', choices=list(MODEL_FILES.keys()),
                   help='Model variant to use')
    p.add_argument('--prompt', help='Prompt for code generation')
    p.add_argument('--mode', default='greedy', choices=['greedy', 'topk', 'beam'],
                   help='Decoding mode')
    p.add_argument('--max-tokens', type=int, default=50, help='Max tokens to generate')
    p.add_argument('--temperature', type=float, default=0.7)
    p.add_argument('--top-k', type=int, default=10)
    p.add_argument('--beams', type=int, default=4)
    p.add_argument('--repl', action='store_true', help='Interactive REPL mode')
    p.add_argument('--benchmark', action='store_true', help='Run speed benchmark')
    p.add_argument('--list', action='store_true', help='List available models')
    args = p.parse_args()
    
    if args.list:
        print("Available models:")
        for k, v in MODEL_FILES.items():
            exists = "✓" if v.exists() else "✗"
            sz = f"{os.path.getsize(v)/1024/1024:.1f} MB" if v.exists() else "not trained"
            print(f"  {exists} {k:15s} {sz}  ({v.name})")
        return
    
    print(f"Loading model '{args.model}'...", file=sys.stderr)
    m, tok, cfg, meta = load_model(args.model)
    params = meta.get('params', 0)
    print(f"  Params: {params:,} ({params/1e6:.2f}M)", file=sys.stderr)
    print(f"  Vocab: {cfg['vocab_size']}, Max seq: {cfg['max_seq_len']}", file=sys.stderr)
    
    if args.benchmark:
        print("\nBenchmark (greedy, 50 tokens)...", file=sys.stderr)
        t0 = time.perf_counter()
        text = generate_greedy(m, tok, "def ", max_tokens=50)
        elapsed = time.perf_counter() - t0
        n_tok = len(tok.encode(text))
        print(f"  Generated {n_tok} tokens in {elapsed:.2f}s = {n_tok/elapsed:.1f} tok/s")
        return
    
    if args.repl:
        repl_mode(m, tok, cfg)
        return
    
    if not args.prompt:
        # Default demo prompts
        prompts = [
            "def scan",
            "import urllib",
            "def fetch",
            "class Scanner",
            "def parse",
        ]
        print(f"\nNo prompt given. Running demo with {len(prompts)} prompts:\n")
        for p in prompts:
            t0 = time.perf_counter()
            if args.mode == "greedy":
                text = generate_greedy(m, tok, p, max_tokens=args.max_tokens)
            elif args.mode == "beam":
                text = generate_beam(m, tok, p, max_tokens=args.max_tokens, num_beams=args.beams)
            else:
                text = generate_top_k(m, tok, p, max_tokens=args.max_tokens,
                                      temperature=args.temperature, top_k=args.top_k)
            elapsed = time.perf_counter() - t0
            print(f"  Prompt: {p!r}")
            print(f"  Output: {text[:120]}")
            print(f"  [{elapsed:.2f}s]")
            print()
    else:
        t0 = time.perf_counter()
        if args.mode == "greedy":
            text = generate_greedy(m, tok, args.prompt, max_tokens=args.max_tokens)
        elif args.mode == "beam":
            text = generate_beam(m, tok, args.prompt, max_tokens=args.max_tokens, num_beams=args.beams)
        else:
            text = generate_top_k(m, tok, args.prompt, max_tokens=args.max_tokens,
                                  temperature=args.temperature, top_k=args.top_k)
        elapsed = time.perf_counter() - t0
        print(text)
        print(f"\n[{elapsed:.2f}s, mode={args.mode}]", file=sys.stderr)


if __name__ == "__main__":
    main()
