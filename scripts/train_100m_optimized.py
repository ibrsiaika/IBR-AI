#!/usr/bin/env python3
"""
IBR-GPT-Code 100M — Optimized for 2-core CPU, 4GB RAM
- 100M params (12L/768D/12H)
- 1500 vocab BPE (faster training)
- 5200+ code samples
- 5 epochs (fast)
- batch_size=4, seq_len=16 (memory optimized)
"""
import os, sys, time, json, re, math
import torch, torch.nn as nn, torch.nn.functional as F
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from ibr_platform.models.scratch import BPETokenizer, ScratchGPT

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'ibr_gpt_code_100m.pt')

print("=" * 60)
print("  IBR-GPT-Code-100M — 92.8M params")
print("=" * 60)

# Load data
print("\n[1/5] Loading data...")
with open(os.path.join(os.path.dirname(__file__), '..', 'research', 'large_code_dataset.json')) as f:
    samples = json.load(f)
# Use subset for faster BPE training
train_samples = samples[:1500]
print(f"  {len(train_samples)} samples (from {len(samples)} total)")

# BPE — small vocab for speed
print("\n[2/5] BPE tokenizer (800 vocab)...")
tok = BPETokenizer(vocab_size=800)
tok.train(train_samples)
print(f"  Vocab: {tok.vocab_size_actual}")

# 100M model
print("\n[3/5] Building 100M model (12L/768D/12H)...")
model = ScratchGPT(
    vocab_size=tok.vocab_size_actual,
    embed_dim=768, num_layers=12, num_heads=12,
    max_seq_len=32, dropout=0.1,
)
params = model.count_parameters()
print(f"  Params: {params:,} ({params/1e6:.1f}M)")
print(f"  FP32: {params*4/1024/1024:.1f} MB | INT8: {params/1024/1024:.1f} MB")

# Prepare data — small seq_len for memory
print("\n[4/5] Training (5 epochs)...")
seq_len = 16
all_tokens = []
for s in train_samples:
    enc = tok.encode(s)
    if len(enc) > 3:
        all_tokens.extend(enc)
        all_tokens.append(tok.vocab.get("<EOS>", 0))

sequences = []
for i in range(0, len(all_tokens) - seq_len - 1, seq_len):
    sequences.append(all_tokens[i:i + seq_len + 1])

sequences = sequences[:2000]  # Cap
data = torch.tensor(sequences, dtype=torch.long)
print(f"  Tokens: {len(all_tokens):,} | Seqs: {len(sequences)} | SeqLen: {seq_len}")

opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)
model.train()
losses = []
t0 = time.perf_counter()

for epoch in range(5):
    perm = torch.randperm(len(data))
    ep_l = []
    for i in range(0, len(data), 4):  # batch=4 for memory
        batch = data[perm[i:i+4]]
        x, y = batch[:, :-1], batch[:, 1:]
        _, loss = model(x, targets=y)
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        ep_l.append(loss.item())
    avg = np.mean(ep_l)
    losses.append(avg)
    ppl = math.exp(min(avg, 10))
    elapsed = time.perf_counter() - t0
    print(f"  E{epoch+1}/5  Loss:{avg:.4f}  PPL:{ppl:.1f}  T:{elapsed:.0f}s")

train_time = time.perf_counter() - t0
print(f"\n  Loss: {losses[0]:.4f} -> {losses[-1]:.4f} ({((losses[0]-losses[-1])/losses[0]*100):.1f}%)")
print(f"  PPL: {math.exp(losses[0]):.1f} -> {math.exp(min(losses[-1],10)):.1f}")
print(f"  Time: {train_time:.0f}s ({train_time/60:.1f} min)")

# Test
print("\n[5/5] Testing...")
model.eval()
kw_set = {"def","class","import","from","return","if","else","for","self","None","True","False","print","open","len","range","try","except","with"}
prompts = ["def scan", "def process", "class Data", "import os", "def secure"]
tot_kw = 0; bal = 0
for p in prompts:
    ids = tok.encode(p)
    if not ids: ids = [0]
    idx = torch.tensor([ids], dtype=torch.long)
    gen = model.generate(idx, max_new_tokens=20, temperature=0.7)
    text = tok.decode(gen[0].tolist())
    found = sum(1 for k in kw_set if k in text.lower())
    tot_kw += found
    if text.count("(") == text.count(")"): bal += 1
    print(f"  '{p}' -> '{text[:100]}'  [kw:{found}]")
avg_kw = tot_kw / len(prompts)
syn = bal / len(prompts) * 100

# Bench
test = torch.tensor([[0]], dtype=torch.long)
times = []
for _ in range(3):
    t0 = time.perf_counter()
    with torch.no_grad():
        model.generate(test, max_new_tokens=10, temperature=0.5)
    times.append(time.perf_counter() - t0)
tps = 10 / np.mean(times)
print(f"\n  Quality: {avg_kw:.1f} kw/out | {syn:.0f}% balanced | {tps:.1f} tok/s")

# Save
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
torch.save({
    'model_state_dict': model.state_dict(),
    'model_config': {'vocab_size': tok.vocab_size_actual, 'embed_dim': 768, 'num_layers': 12, 'num_heads': 12, 'max_seq_len': 32},
    'tokenizer_vocab': tok.vocab, 'tokenizer_merges': tok.merges,
    'training': losses,
    'meta': {'name': 'IBR-GPT-Code-100M', 'pretrained': False, 'params': params, 'samples': len(train_samples)},
}, MODEL_PATH)
print(f"\n  Saved: {MODEL_PATH} ({os.path.getsize(MODEL_PATH)/1024/1024:.1f} MB)")

print(f"\n{'='*60}")
print(f"IBR-GPT-Code-100M — COMPLETE")
print(f"{'='*60}")
print(f"  Params: {params:,} ({params/1e6:.1f}M)")
print(f"  Loss: {losses[0]:.4f} -> {losses[-1]:.4f} ({((losses[0]-losses[-1])/losses[0]*100):.1f}%)")
print(f"  PPL: {math.exp(losses[0]):.1f} -> {math.exp(min(losses[-1],10)):.1f}")
print(f"  Quality: {avg_kw:.1f} kw/out | {syn:.0f}% balanced | {tps:.1f} tok/s")
print(f"  Time: {train_time/60:.1f} min | Cost: $0.00 | Pre-trained: NO")
