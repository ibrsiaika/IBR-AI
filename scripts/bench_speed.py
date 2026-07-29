#!/usr/bin/env python3
"""Benchmark training speed to plan training time."""
import os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import torch
torch.set_num_threads(2)

from train_100m_v2 import ScratchGPTLarge

# Test 100M model speed
print("=" * 60)
print("  Benchmark: 100M model training speed")
print("=" * 60)

m = ScratchGPTLarge(vocab_size=1500, embed_dim=768, num_layers=14, num_heads=12,
                    max_seq_len=64, use_checkpointing=True, dropout=0.0)
m.train()
p = m.count_parameters()
print(f"Params: {p/1e6:.2f}M")

# Convert to bfloat16
m = m.to(torch.bfloat16)

opt = torch.optim.SGD(m.parameters(), lr=0.01, momentum=0.9)

# Benchmark with batch=4, seq=32
for batch_size, seq_len in [(4, 32), (8, 32), (4, 48)]:
    print(f"\nbatch={batch_size}, seq={seq_len}:")
    x = torch.randint(0, 1500, (batch_size, seq_len), dtype=torch.long)
    y = torch.randint(0, 1500, (batch_size, seq_len), dtype=torch.long)
    
    # Warmup
    for _ in range(2):
        opt.zero_grad()
        _, loss = m(x, targets=y)
        loss.backward()
        opt.step()
    
    # Benchmark
    times = []
    for _ in range(5):
        t0 = time.perf_counter()
        opt.zero_grad()
        _, loss = m(x, targets=y)
        loss.backward()
        opt.step()
        times.append(time.perf_counter() - t0)
    
    avg = sum(times) / len(times)
    tps = batch_size * seq_len / avg
    print(f"  avg/step: {avg*1000:.0f} ms | {tps:.0f} tok/s")
    print(f"  est 1000 seqs @ 2 epochs: {2000 * avg / 60:.1f} min")

# Also test compact 25M model
print("\n" + "=" * 60)
print("  Benchmark: Compact 25M model")
print("=" * 60)

m2 = ScratchGPTLarge(vocab_size=1500, embed_dim=512, num_layers=6, num_heads=8,
                     max_seq_len=64, use_checkpointing=False, dropout=0.0)
m2.train()
p2 = m2.count_parameters()
print(f"Params: {p2/1e6:.2f}M")
m2 = m2.to(torch.bfloat16)
opt2 = torch.optim.SGD(m2.parameters(), lr=0.01, momentum=0.9)

batch_size, seq_len = 8, 48
x = torch.randint(0, 1500, (batch_size, seq_len), dtype=torch.long)
y = torch.randint(0, 1500, (batch_size, seq_len), dtype=torch.long)

# Warmup
for _ in range(2):
    opt2.zero_grad()
    _, loss = m2(x, targets=y)
    loss.backward()
    opt2.step()

times = []
for _ in range(5):
    t0 = time.perf_counter()
    opt2.zero_grad()
    _, loss = m2(x, targets=y)
    loss.backward()
    opt2.step()
    times.append(time.perf_counter() - t0)

avg = sum(times) / len(times)
tps = batch_size * seq_len / avg
print(f"  batch={batch_size}, seq={seq_len}")
print(f"  avg/step: {avg*1000:.0f} ms | {tps:.0f} tok/s")
print(f"  est 4000 seqs @ 3 epochs: {12000 * avg / 60:.1f} min")
print(f"  INT4 size: {p2/2/1024/1024:.1f} MB")
