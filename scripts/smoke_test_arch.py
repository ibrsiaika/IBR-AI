#!/usr/bin/env python3
"""Quick smoke test — verify architecture & param count."""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import torch
torch.set_num_threads(2)

# Import the new architecture from train_100m_v2
from train_100m_v2 import ScratchGPTLarge, FastBPETokenizer, quantize_int8

print("=" * 60)
print("  Architecture smoke test")
print("=" * 60)

# Test 100M model (14L/768D/12H)
m = ScratchGPTLarge(vocab_size=1500, embed_dim=768, num_layers=14, num_heads=12,
                    max_seq_len=64, use_checkpointing=False)
p = m.count_parameters()
print(f"\n100M model (14L/768D/12H):")
print(f"  Params: {p:,} ({p/1e6:.2f}M)")
print(f"  fp32:   {p*4/1024/1024:.1f} MB")
print(f"  bf16:   {p*2/1024/1024:.1f} MB")
print(f"  INT8:   {p/1024/1024:.1f} MB")
print(f"  INT4:   {p/2/1024/1024:.1f} MB")

# Test forward pass
x = torch.randint(0, 1500, (2, 32), dtype=torch.long)
y = torch.randint(0, 1500, (2, 32), dtype=torch.long)
logits, loss = m(x, targets=y)
print(f"  Forward OK: logits={tuple(logits.shape)} loss={loss.item():.4f}")

# Test 40M model (12L/512D/8H)
m40 = ScratchGPTLarge(vocab_size=1500, embed_dim=512, num_layers=12, num_heads=8,
                     max_seq_len=64, use_checkpointing=False)
p40 = m40.count_parameters()
print(f"\n40M model (12L/512D/8H):")
print(f"  Params: {p40:,} ({p40/1e6:.2f}M)")
print(f"  fp32:   {p40*4/1024/1024:.1f} MB")
print(f"  bf16:   {p40*2/1024/1024:.1f} MB")
print(f"  INT8:   {p40/1024/1024:.1f} MB")
print(f"  INT4:   {p40/2/1024/1024:.1f} MB  <-- target: 10-15 MB")

# Test INT8 quantization
print(f"\nINT8 quantization test:")
state = m40.state_dict()
qs, scales = quantize_int8(state)
total_orig = sum(v.numel() * v.element_size() for v in state.values())
total_quant = sum(v.numel() * v.element_size() for v in qs.values())
print(f"  Original: {total_orig/1024/1024:.1f} MB")
print(f"  INT8:     {total_quant/1024/1024:.1f} MB")
print(f"  Ratio:    {total_orig/total_quant:.2f}x smaller")

# BPE tokenizer test
print(f"\nBPE tokenizer test:")
tok = FastBPETokenizer(vocab_size=500)
tok.train(["def hello():\n    return 'world'", "import os\nprint(os.getcwd())"])
print(f"  Vocab: {tok.vocab_size_actual}")
ids = tok.encode("def hello")
print(f"  'def hello' -> {ids}")
text = tok.decode(ids)
print(f"  decode: {text!r}")

print("\nSmoke test PASSED.")
