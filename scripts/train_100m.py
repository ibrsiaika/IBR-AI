#!/usr/bin/env python3
"""
IBR-GPT-Code 100M — Trained on 5200+ real code samples
92.8M parameters (12L/768D/12H) — GPT-2 small architecture
"""
import os, sys, time, json, re, math, hashlib
import torch, torch.nn as nn, torch.nn.functional as F
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from ibr_platform.models.scratch import BPETokenizer, ScratchGPT

MODEL_NAME = "IBR-GPT-Code-100M"
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'ibr_gpt_code_100m.pt')

print("=" * 60)
print(f"  {MODEL_NAME} — 92.8M params, 5200+ code samples")
print("=" * 60)

# Step 1: Load data
print("\n[1/6] Loading 5200+ code samples...")
with open(os.path.join(os.path.dirname(__file__), '..', 'research', 'large_code_dataset.json')) as f:
    code_samples = json.load(f)
print(f"  Loaded: {len(code_samples)} samples, {sum(len(s) for s in code_samples):,} chars")

# Step 2: BPE Tokenizer (4000 vocab)
print("\n[2/6] Building BPE tokenizer (4000 vocab)...")
tokenizer = BPETokenizer(vocab_size=4000)
tokenizer.train(code_samples)
print(f"  Vocab: {tokenizer.vocab_size_actual}, Merges: {len(tokenizer.merges)}")

# Step 3: Build 100M model
print("\n[3/6] Building 100M model (12L/768D/12H)...")
model = ScratchGPT(
    vocab_size=tokenizer.vocab_size_actual,
    embed_dim=768,
    num_layers=12,
    num_heads=12,
    max_seq_len=64,
    dropout=0.1,
)
params = model.count_parameters()
print(f"  Params: {params:,} ({params/1e6:.1f}M)")
print(f"  FP32: {params*4/1024/1024:.1f} MB | INT8: {params/1024/1024:.1f} MB")

# Step 4: Prepare training data
print("\n[4/6] Preparing training data...")
seq_len = 32  # Small for CPU memory
all_tokens = []
for s in code_samples:
    enc = tokenizer.encode(s)
    if len(enc) > 5:
        all_tokens.extend(enc)
        all_tokens.append(tokenizer.vocab.get("<EOS>", 0))

sequences = []
for i in range(0, len(all_tokens) - seq_len - 1, seq_len):
    sequences.append(all_tokens[i:i + seq_len + 1])

# Cap at 3000 for CPU memory (each epoch processes 3000 sequences)
sequences = sequences[:3000]
data = torch.tensor(sequences, dtype=torch.long)
print(f"  Tokens: {len(all_tokens):,} | Sequences: {len(sequences)} | Seq len: {seq_len}")

# Step 5: Pre-train (8 epochs — CPU optimized)
print("\n[5/6] Pre-training (8 epochs on CPU)...")
optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)
batch_size = 8  # Small batch for 100M model on CPU
model.train()
pt_losses = []
t0 = time.perf_counter()

for epoch in range(8):
    perm = torch.randperm(len(data))
    ep_losses = []
    for i in range(0, len(data), batch_size):
        batch = data[perm[i:i+batch_size]]
        x, y = batch[:, :-1], batch[:, 1:]
        _, loss = model(x, targets=y)
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        ep_losses.append(loss.item())
    avg = np.mean(ep_losses)
    pt_losses.append(avg)
    ppl = math.exp(min(avg, 10))
    elapsed = time.perf_counter() - t0
    print(f"  E{epoch+1}/8  Loss:{avg:.4f}  PPL:{ppl:.1f}  Time:{elapsed:.0f}s")

pt_time = time.perf_counter() - t0
print(f"\n  Pre-train: {pt_losses[0]:.4f} -> {pt_losses[-1]:.4f} ({((pt_losses[0]-pt_losses[-1])/pt_losses[0]*100):.1f}%)")
print(f"  PPL: {math.exp(pt_losses[0]):.1f} -> {math.exp(min(pt_losses[-1],10)):.1f}")
print(f"  Time: {pt_time:.0f}s ({pt_time/60:.1f} min)")

# Step 6: Test code generation
print("\n[6/6] Testing code generation...")
model.eval()

python_keywords = {"def","class","import","from","return","if","else","for","while",
                   "self","None","True","False","print","open","len","range","try",
                   "except","with","as","raise","yield","lambda","async","await"}

prompts = [
    "def scan_website",
    "def extract_emails",
    "def port_scan",
    "def secure_hash",
    "def process_data",
    "def analyze_code",
    "class DataCollector",
    "import os",
]

total_kw = 0
balanced = 0

for prompt in prompts:
    ids = tokenizer.encode(prompt)
    if not ids:
        ids = [0]
    idx = torch.tensor([ids], dtype=torch.long)
    gen = model.generate(idx, max_new_tokens=25, temperature=0.7)
    text = tokenizer.decode(gen[0].tolist())
    found = sum(1 for kw in python_keywords if kw in text.lower())
    total_kw += found
    if text.count("(") == text.count(")"):
        balanced += 1
    print(f"\n  '{prompt}'")
    print(f"  -> '{text[:120]}'")
    print(f"     Keywords: {found} | Balanced: {text.count('(')==text.count(')')}")

avg_kw = total_kw / len(prompts)
syntax_pct = balanced / len(prompts) * 100

# Benchmark
test = torch.tensor([[0]], dtype=torch.long)
times = []
for _ in range(3):
    t0 = time.perf_counter()
    with torch.no_grad():
        model.generate(test, max_new_tokens=10, temperature=0.5)
    times.append(time.perf_counter() - t0)
tps = 10 / np.mean(times)

print(f"\n  Quality: {avg_kw:.1f} kw/out | {syntax_pct:.0f}% balanced | {tps:.1f} tok/s")

# Save
print(f"\n  Saving {MODEL_NAME}...")
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
torch.save({
    'model_state_dict': model.state_dict(),
    'model_config': {
        'vocab_size': tokenizer.vocab_size_actual,
        'embed_dim': 768, 'num_layers': 12, 'num_heads': 12, 'max_seq_len': 64,
    },
    'tokenizer_vocab': tokenizer.vocab,
    'tokenizer_merges': tokenizer.merges,
    'training': {'pretrain': pt_losses},
    'meta': {
        'name': MODEL_NAME,
        'pretrained': False,
        'params': params,
        'data_samples': len(code_samples),
        'quality': {'avg_keywords': avg_kw, 'syntax_pct': syntax_pct, 'tps': tps},
    },
}, MODEL_PATH)
sz = os.path.getsize(MODEL_PATH) / 1024 / 1024
print(f"  Saved: {MODEL_PATH} ({sz:.1f} MB)")

print(f"\n{'='*60}")
print(f"  {MODEL_NAME} — COMPLETE")
print(f"{'='*60}")
print(f"""
  Model: {MODEL_NAME} (12L/768D/12H)
  Params: {params:,} ({params/1e6:.1f}M)
  Size: {params*4/1024/1024:.1f} MB (FP32) | {params/1024/1024:.1f} MB (INT8)
  
  Data: {len(code_samples)} code samples ({sum(len(s) for s in code_samples):,} chars)
  Pre-train: {pt_losses[0]:.4f} -> {pt_losses[-1]:.4f} ({((pt_losses[0]-pt_losses[-1])/pt_losses[0]*100):.1f}%)
  PPL: {math.exp(pt_losses[0]):.1f} -> {math.exp(min(pt_losses[-1],10)):.1f}
  Quality: {avg_kw:.1f} kw/out | {syntax_pct:.0f}% balanced | {tps:.1f} tok/s
  Time: {pt_time/60:.1f} min on CPU
  Cost: $0.00 | Pre-trained: NO
""")
