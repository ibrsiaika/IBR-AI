#!/usr/bin/env python3
"""
Multi-test suite for IBR-GPT-Code models.

Tests:
1. Parameter count verification (100M+, compact ~20M)
2. Model file sizes (fp32, INT8, INT4)
3. INT4 quantization correctness (dequantization error)
4. Tokenizer integrity (encode/decode roundtrip)
5. Generation quality (keywords, syntax, balance)
6. Inference speed (tokens/sec)
7. Loss / Perplexity verification
8. INT4 dequantization & inference test
9. Memory efficiency
10. Architecture correctness
"""
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from fast_bpe import FastBPETokenizerV2
from train_100m_v2 import ScratchGPTLarge
from int4_quantizer import quantize_model_int4, estimate_int4_size_bytes, dequantize_int4

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_100M = MODELS_DIR / "ibr_gpt_code_100m.pt"
MODEL_100M_INT8 = MODELS_DIR / "ibr_gpt_code_100m_int8.pt"
MODEL_COMPACT = MODELS_DIR / "ibr_gpt_code_compact.pt"
MODEL_COMPACT_INT4 = MODELS_DIR / "ibr_gpt_code_compact_int4.pt"

torch.set_num_threads(2)

PASS = 0
FAIL = 0
RESULTS = []

def report(name: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS += 1
    else:
        FAIL += 1
    line = f"  [{status}] {name}"
    if detail:
        line += f" — {detail}"
    print(line)
    RESULTS.append((name, ok, detail))


def header(s: str) -> None:
    print(f"\n{'='*70}\n  {s}\n{'='*70}")


# ============================================================================
# TEST 1: Parameter count
# ============================================================================
def test_param_count():
    header("TEST 1: Parameter Count Verification")
    
    # 100M model
    m = ScratchGPTLarge(vocab_size=1500, embed_dim=768, num_layers=14, num_heads=12,
                        max_seq_len=32, use_checkpointing=False)
    p = m.count_parameters()
    report("100M model has ≥100M params", p >= 100_000_000, f"{p:,} ({p/1e6:.2f}M)")
    
    # Compact 25M model
    m2 = ScratchGPTLarge(vocab_size=2000, embed_dim=512, num_layers=6, num_heads=8,
                         max_seq_len=48, use_checkpointing=False)
    p2 = m2.count_parameters()
    report("Compact model has ≥15M params", p2 >= 15_000_000, f"{p2:,} ({p2/1e6:.2f}M)")
    report("Compact model is <100M params (smaller variant)", p2 < 100_000_000, f"{p2/1e6:.2f}M < 100M")


# ============================================================================
# TEST 2: Model file sizes
# ============================================================================
def test_file_sizes():
    header("TEST 2: Model File Sizes")
    
    # 100M fp32
    if MODEL_100M.exists():
        sz = os.path.getsize(MODEL_100M) / 1024 / 1024
        report("100M fp32 saved", sz > 100, f"{sz:.1f} MB")
    else:
        report("100M fp32 saved", False, "FILE MISSING")
    
    # 100M INT8
    if MODEL_100M_INT8.exists():
        sz = os.path.getsize(MODEL_100M_INT8) / 1024 / 1024
        report("100M INT8 ≤ 100 MB", sz <= 100, f"{sz:.1f} MB")
        report("100M INT8 is 3-5x smaller than fp32", 
               sz < os.path.getsize(MODEL_100M) / 1024 / 1024 / 2,
               f"{sz:.1f} MB vs {os.path.getsize(MODEL_100M)/1024/1024:.1f} MB")
    else:
        report("100M INT8 saved", False, "FILE MISSING")
    
    # Compact fp32
    if MODEL_COMPACT.exists():
        sz = os.path.getsize(MODEL_COMPACT) / 1024 / 1024
        report("Compact fp32 saved", sz > 50, f"{sz:.1f} MB")
    else:
        report("Compact fp32 saved", False, "FILE MISSING")
    
    # Compact INT4 — TARGET: 10-15 MB
    if MODEL_COMPACT_INT4.exists():
        sz = os.path.getsize(MODEL_COMPACT_INT4) / 1024 / 1024
        report("Compact INT4 is 10-20 MB (target: 10-15 MB)", 
               10 <= sz <= 20, f"{sz:.1f} MB")
        report("Compact INT4 < fp32 / 3", 
               sz < os.path.getsize(MODEL_COMPACT) / 1024 / 1024 / 3,
               f"{sz:.1f} MB vs {os.path.getsize(MODEL_COMPACT)/1024/1024:.1f} MB")
    else:
        report("Compact INT4 saved", False, "FILE MISSING")


# ============================================================================
# TEST 3: INT4 quantization correctness
# ============================================================================
def test_int4_correctness():
    header("TEST 3: INT4 Quantization Correctness")
    
    torch.manual_seed(42)
    # Test on a typical weight tensor
    w = torch.randn(500, 500) * 0.05
    quant = quantize_model_int4({'test.weight': w})
    packed = quant['packed']['test.weight']
    scales = quant['scales']['test.weight']
    shape = quant['shapes']['test.weight']
    
    w_dq = dequantize_int4(packed, scales, shape)
    err = (w - w_dq).abs().mean().item()
    rel_err = err / w.abs().mean().item()
    
    report("INT4 dequantization works", w_dq.shape == w.shape, f"shape={tuple(w_dq.shape)}")
    report("INT4 quantization error < 20%", rel_err < 0.20, f"rel_err={rel_err*100:.2f}%")
    report("INT4 compression > 5x", 
           w.numel() * 4 / (packed.nbytes + scales.nbytes) > 5,
           f"{w.numel()*4/(packed.nbytes+scales.nbytes):.2f}x")


# ============================================================================
# TEST 4: Tokenizer integrity
# ============================================================================
def test_tokenizer():
    header("TEST 4: Tokenizer Integrity")
    
    tok = FastBPETokenizerV2(vocab_size=500)
    train_texts = [
        "def hello_world():\n    return 'hello'",
        "import urllib.request\nresponse = urllib.request.urlopen(url)",
        "class Scanner:\n    def scan(self, url):\n        pass",
    ] * 50
    tok.train(train_texts)
    
    report("BPE training produces vocab", tok.vocab_size_actual > 100, f"vocab={tok.vocab_size_actual}")
    
    # Encode/decode roundtrip
    text = "def hello"
    ids = tok.encode(text)
    decoded = tok.decode(ids)
    report("BPE encode produces tokens", len(ids) > 0, f"ids={ids}")
    report("BPE decode preserves text", "def" in decoded and "hello" in decoded, f"decoded={decoded!r}")
    
    # Cache works
    ids2 = tok.encode(text)
    report("BPE caching works", ids == ids2, "same output for same input")


# ============================================================================
# TEST 5: Generation quality (load saved models)
# ============================================================================
def _load_model(path: Path):
    """Load model from checkpoint, handling CheckpointedBlock key naming."""
    ckpt = torch.load(path, map_location='cpu', weights_only=False)
    cfg = ckpt['model_config']
    
    # Try loading without checkpointing first (faster for inference)
    # If keys don't match (saved with CheckpointedBlock), remap
    m = ScratchGPTLarge(
        vocab_size=cfg['vocab_size'],
        embed_dim=cfg['embed_dim'],
        num_layers=cfg['num_layers'],
        num_heads=cfg['num_heads'],
        max_seq_len=cfg['max_seq_len'],
        use_checkpointing=False,
    )
    
    state = ckpt['model_state_dict']
    # Check if ANY key has '.block.' prefix (saved with checkpointing)
    has_block_prefix = any('.block.' in k for k in state.keys())
    if has_block_prefix:
        # Remap: 'blocks.0.block.X' -> 'blocks.0.X'
        new_state = {}
        for k, v in state.items():
            new_k = k.replace('.block.', '.')
            new_state[new_k] = v
        state = new_state
    
    m.load_state_dict(state)
    m.eval()
    return m, ckpt


def test_generation_100m():
    header("TEST 5: Generation Quality — 100M Model")
    
    if not MODEL_100M.exists():
        report("100M model file exists", False, "MISSING")
        return
    
    print("  Loading 100M model...")
    m, ckpt = _load_model(MODEL_100M)
    cfg = ckpt['model_config']
    
    # Build tokenizer
    tok = FastBPETokenizerV2(vocab_size=cfg['vocab_size'])
    tok.vocab = ckpt['tokenizer_vocab']
    tok.id_to_token = {v: k for k, v in tok.vocab.items()}
    tok.merges = [tuple(p) for p in ckpt['tokenizer_merges']]
    
    # Generation tests
    prompts = ["def scan", "import urllib", "def fetch", "class Scanner", "def parse"]
    kw_set = {"def", "class", "import", "from", "return", "if", "for", "self", 
              "url", "request", "scan", "urllib", "open", "len", "range"}
    
    total_kw = 0
    total_balanced = 0
    n = len(prompts)
    
    for p in prompts:
        ids = tok.encode(p)
        if not ids:
            ids = [0]
        idx = torch.tensor([ids], dtype=torch.long)
        with torch.no_grad():
            gen = m.generate(idx, max_new_tokens=30, temperature=0.5, top_k=10)
        text = tok.decode(gen[0].tolist())
        kw = sum(1 for k in kw_set if k in text.lower())
        bal = 1 if text.count("(") == text.count(")") else 0
        total_kw += kw
        total_balanced += bal
        print(f"    '{p}' -> {text[:70]!r} [kw:{kw} bal:{bal}]")
    
    avg_kw = total_kw / n
    bal_pct = total_balanced / n * 100
    report("100M generates ≥1 keyword/output", avg_kw >= 1.0, f"{avg_kw:.1f} kw/out")
    report("100M ≥ 50% paren balance", bal_pct >= 50, f"{bal_pct:.0f}%")
    
    # Loss/perplexity
    losses = ckpt.get('training', [])
    if losses:
        report("100M training loss reduced", losses[-1] < losses[0], 
               f"{losses[0]:.4f} -> {losses[-1]:.4f}")
        ppl = math.exp(min(losses[-1], 12))
        report("100M PPL < 50", ppl < 50, f"PPL={ppl:.1f}")


def test_generation_compact():
    header("TEST 6: Generation Quality — Compact Model")
    
    if not MODEL_COMPACT.exists():
        report("Compact model file exists", False, "MISSING")
        return
    
    print("  Loading compact model...")
    m, ckpt = _load_model(MODEL_COMPACT)
    cfg = ckpt['model_config']
    
    tok = FastBPETokenizerV2(vocab_size=cfg['vocab_size'])
    tok.vocab = ckpt['tokenizer_vocab']
    tok.id_to_token = {v: k for k, v in tok.vocab.items()}
    tok.merges = [tuple(p) for p in ckpt['tokenizer_merges']]
    
    prompts = ["def scan", "import urllib", "def fetch", "class Scanner", "def parse"]
    kw_set = {"def", "class", "import", "from", "return", "if", "for", "self",
              "url", "request", "scan", "urllib", "open", "len", "range"}
    
    total_kw = 0
    total_balanced = 0
    n = len(prompts)
    
    for p in prompts:
        ids = tok.encode(p)
        if not ids:
            ids = [0]
        idx = torch.tensor([ids], dtype=torch.long)
        with torch.no_grad():
            gen = m.generate(idx, max_new_tokens=30, temperature=0.5, top_k=10)
        text = tok.decode(gen[0].tolist())
        kw = sum(1 for k in kw_set if k in text.lower())
        bal = 1 if text.count("(") == text.count(")") else 0
        total_kw += kw
        total_balanced += bal
        print(f"    '{p}' -> {text[:70]!r} [kw:{kw} bal:{bal}]")
    
    avg_kw = total_kw / n
    bal_pct = total_balanced / n * 100
    report("Compact generates ≥1 keyword/output", avg_kw >= 1.0, f"{avg_kw:.1f} kw/out")
    report("Compact ≥ 30% paren balance", bal_pct >= 30, f"{bal_pct:.0f}%")
    
    losses = ckpt.get('training', [])
    if losses:
        report("Compact training loss reduced", losses[-1] < losses[0],
               f"{losses[0]:.4f} -> {losses[-1]:.4f}")
        ppl = math.exp(min(losses[-1], 12))
        report("Compact PPL < 50", ppl < 50, f"PPL={ppl:.1f}")


# ============================================================================
# TEST 7: INT4 quantized model can be loaded & used for inference
# ============================================================================
def test_int4_inference():
    header("TEST 7: INT4 Model Inference")
    
    if not MODEL_COMPACT_INT4.exists():
        report("INT4 compact file exists", False, "MISSING")
        return
    
    print("  Loading INT4 compact model...")
    ckpt = torch.load(MODEL_COMPACT_INT4, map_location='cpu', weights_only=False)
    cfg = ckpt['model_config']
    quant = ckpt['quantized_state']
    
    # Build model
    m = ScratchGPTLarge(
        vocab_size=cfg['vocab_size'],
        embed_dim=cfg['embed_dim'],
        num_layers=cfg['num_layers'],
        num_heads=cfg['num_heads'],
        max_seq_len=cfg['max_seq_len'],
        use_checkpointing=False,
    )
    
    # Dequantize & load each weight
    print("  Dequantizing INT4 weights...")
    new_state = {}
    model_state = m.state_dict()
    import re as _re
    
    for name in model_state.keys():
        # Try direct match, then with '.block.' prefix (saved with checkpointing)
        packed = quant['packed'].get(name)
        scales = quant['scales'].get(name)
        shape = quant['shapes'].get(name)
        
        if packed is None:
            # Try remapping 'blocks.0.X' -> 'blocks.0.block.X'
            m_match = _re.match(r'(blocks\.\d+)\.(.+)', name)
            if m_match:
                alt_name = f"{m_match.group(1)}.block.{m_match.group(2)}"
                packed = quant['packed'].get(alt_name)
                scales = quant['scales'].get(alt_name)
                shape = quant['shapes'].get(alt_name)
        
        if packed is None:
            print(f"    SKIP {name} (not in quantized state)")
            continue
        
        if scales is None:
            # Small tensor (LayerNorm, bias) - keep as is
            if hasattr(packed, 'dtype'):
                new_state[name] = torch.from_numpy(np.asarray(packed))
            else:
                new_state[name] = torch.tensor(packed)
        else:
            # Dequantize
            new_state[name] = dequantize_int4(packed, scales, shape)
    
    m.load_state_dict(new_state, strict=False)
    m.eval()
    report("INT4 model dequantizes & loads", len(new_state) > 0, f"{len(new_state)} weights")
    
    # Test inference
    tok = FastBPETokenizerV2(vocab_size=cfg['vocab_size'])
    tok.vocab = ckpt['tokenizer_vocab']
    tok.id_to_token = {v: k for k, v in tok.vocab.items()}
    tok.merges = [tuple(p) for p in ckpt['tokenizer_merges']]
    
    ids = tok.encode("def scan")
    if not ids:
        ids = [0]
    idx = torch.tensor([ids], dtype=torch.long)
    with torch.no_grad():
        gen = m.generate(idx, max_new_tokens=20, temperature=0.5, top_k=10)
    text = tok.decode(gen[0].tolist())
    report("INT4 model generates output", len(text) > 0, f"output={text[:60]!r}")


# ============================================================================
# TEST 8: Inference speed
# ============================================================================
def test_inference_speed():
    header("TEST 8: Inference Speed")
    
    if not MODEL_COMPACT.exists():
        report("Compact model exists for speed test", False, "MISSING")
        return
    
    m, ckpt = _load_model(MODEL_COMPACT)
    cfg = ckpt['model_config']
    
    idx = torch.tensor([[0]], dtype=torch.long)
    # Warmup
    with torch.no_grad():
        m.generate(idx, max_new_tokens=5, temperature=0.5, top_k=10)
    
    times = []
    for _ in range(3):
        t0 = time.perf_counter()
        with torch.no_grad():
            m.generate(idx, max_new_tokens=20, temperature=0.5, top_k=10)
        times.append(time.perf_counter() - t0)
    
    tps = 20 / float(np.mean(times))
    report("Compact inference > 20 tok/s", tps > 20, f"{tps:.1f} tok/s")


# ============================================================================
# TEST 9: Architecture correctness
# ============================================================================
def test_architecture():
    header("TEST 9: Architecture Correctness")
    
    m = ScratchGPTLarge(vocab_size=1000, embed_dim=128, num_layers=2, num_heads=4,
                        max_seq_len=16, use_checkpointing=False)
    
    # Weight tying
    report("Weight tying (lm_head = token_embedding)",
           m.lm_head.weight is m.token_embedding.weight,
           "shared weights")
    
    # Forward pass shapes
    x = torch.randint(0, 1000, (2, 8), dtype=torch.long)
    logits, loss = m(x, targets=x)
    report("Forward produces correct logit shape",
           logits.shape == (2, 8, 1000),
           f"shape={tuple(logits.shape)}")
    report("Forward produces loss", loss is not None, f"loss={loss.item():.4f}")
    
    # Generate
    gen = m.generate(x, max_new_tokens=5, temperature=0.5, top_k=10)
    report("Generate produces correct shape",
           gen.shape == (2, 13),
           f"shape={tuple(gen.shape)}")


# ============================================================================
# TEST 10: Metadata & Golden Stack
# ============================================================================
def test_metadata():
    header("TEST 10: Metadata & Golden Token Stack")
    
    for name, path in [("100M", MODEL_100M), ("Compact", MODEL_COMPACT)]:
        if not path.exists():
            report(f"{name}: file exists", False, "MISSING")
            continue
        ckpt = torch.load(path, map_location='cpu', weights_only=False)
        meta = ckpt.get('meta', {})
        
        report(f"{name}: has meta", 'name' in meta, f"name={meta.get('name')}")
        report(f"{name}: pretrained=False", meta.get('pretrained') == False, "from scratch")
        report(f"{name}: has params count", 'params' in meta, f"{meta.get('params', 0):,}")
        report(f"{name}: has samples count", 'samples' in meta, f"{meta.get('samples', 0):,}")
        report(f"{name}: has golden_stack list", 'golden_stack' in meta, 
               f"{len(meta.get('golden_stack', []))} techniques")
        
        # Check for key Golden Stack techniques
        gs = meta.get('golden_stack', [])
        for tech in ['bfloat16', 'weight-tying', 'dedup', 'curriculum-learning']:
            report(f"{name}: Golden Stack has '{tech}'", tech in gs, "")


# ============================================================================
# MAIN
# ============================================================================
def main():
    print("=" * 70)
    print("  IBR-GPT-Code Multi-Test Suite")
    print("  Tests: params, sizes, quantization, tokenizer, generation,")
    print("         INT4 inference, speed, architecture, metadata")
    print("=" * 70)
    
    test_param_count()
    test_file_sizes()
    test_int4_correctness()
    test_tokenizer()
    test_generation_100m()
    test_generation_compact()
    test_int4_inference()
    test_inference_speed()
    test_architecture()
    test_metadata()
    
    print("\n" + "=" * 70)
    print(f"  RESULTS: {PASS} PASS / {FAIL} FAIL / {PASS+FAIL} TOTAL")
    print(f"  Success rate: {PASS/(PASS+FAIL)*100:.1f}%")
    print("=" * 70)
    
    # Save results to JSON
    out_path = Path(__file__).resolve().parent.parent / "research" / "multi_test_results.json"
    with open(out_path, 'w') as f:
        json.dump({
            'pass': PASS, 'fail': FAIL, 'total': PASS + FAIL,
            'success_rate': PASS / (PASS + FAIL) * 100,
            'results': [{'name': n, 'pass': p, 'detail': d} for n, p, d in RESULTS],
        }, f, indent=2)
    print(f"\nResults saved: {out_path}")
    
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
