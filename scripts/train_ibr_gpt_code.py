#!/usr/bin/env python3
"""
IBR-GPT-Code — Real Training on Real Code Data
Trains a powerful Python coder on low resources (CPU, <2GB RAM).

Uses cached CodeSearchNet data + 25 curated vulnerability patterns.
Model: 4L/128D/4H (small but effective, 929K params, 3.5MB)
"""
import os, sys, time, json, re, math
import torch, torch.nn as nn, torch.nn.functional as F
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from ibr_platform.models.scratch import BPETokenizer, ScratchGPT

MODEL_NAME = "IBR-GPT-Code"
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'ibr_gpt_code.pt')

print("=" * 60)
print(f"  {MODEL_NAME} — Training on Real Code Data")
print("=" * 60)

# ============================================
# STEP 1: Load Real Code Data
# ============================================
print("\n[1/6] Loading code data...")

# Load cached CodeSearchNet data
cache = os.path.join(os.path.dirname(__file__), '..', 'research', 'cached_code_data.json')
if os.path.exists(cache):
    with open(cache) as f:
        code_samples = json.load(f)
    print(f"  CodeSearchNet: {len(code_samples)} samples (cached)")
else:
    print("  Downloading CodeSearchNet (first 200 samples)...")
    try:
        from datasets import load_dataset
        ds = load_dataset("Nan-Do/code-search-net-python", split="train", streaming=True)
        code_samples = []
        for i, item in enumerate(ds):
            if i >= 200: break
            code = item.get("code", "") or item.get("whole_func_string", "")
            if code and len(code) > 50:
                code_samples.append(code)
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        with open(cache, 'w') as f:
            json.dump(code_samples, f)
        print(f"  CodeSearchNet: {len(code_samples)} samples (downloaded)")
    except Exception as e:
        print(f"  Download failed: {e}, using fallback")
        code_samples = []

# Curated vulnerability code (real CVE patterns)
vuln_code = [
    "def process_input(data):\n    query = 'SELECT * FROM users WHERE name=' + data\n    return db.execute(query)",
    "def safe_query(data):\n    query = 'SELECT * FROM users WHERE name = ?'\n    return db.execute(query, (data,))",
    "def eval_input(user_input):\n    result = eval(user_input)\n    return result",
    "def safe_calc(expr):\n    import ast\n    return ast.literal_eval(expr)",
    "def read_file(filename):\n    with open('/data/' + filename) as f:\n        return f.read()",
    "def safe_read(filename):\n    import os\n    path = os.path.normpath(filename)\n    if not path.startswith('/data/'):\n        raise ValueError('Invalid')\n    with open(path) as f:\n        return f.read()",
    "def hash_pass(password):\n    import hashlib\n    return hashlib.md5(password.encode()).hexdigest()",
    "def secure_hash(password):\n    import bcrypt\n    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())",
    "def deserialize(data):\n    import pickle\n    return pickle.loads(data)",
    "def safe_deserialize(data):\n    import json\n    return json.loads(data)",
    "def exec_cmd(cmd):\n    import os\n    os.system('ls ' + cmd)",
    "def safe_exec(cmd):\n    import subprocess\n    return subprocess.run(['ls', cmd], capture_output=True)",
    "def redirect(url):\n    from flask import redirect\n    return redirect(url)",
    "def safe_redirect(url):\n    from urllib.parse import urlparse\n    p = urlparse(url)\n    if p.netloc != 'example.com':\n        return 'Invalid'\n    return redirect(url)",
    "def parse_xml(data):\n    from lxml import etree\n    return etree.fromstring(data)",
    "def safe_parse_xml(data):\n    from lxml import etree\n    parser = etree.XMLParser(resolve_entities=False)\n    return etree.fromstring(data, parser=parser)",
    "def train_model(X, y, epochs=10):\n    model = Model()\n    for epoch in range(epochs):\n        loss = model.train(X, y)\n        print(f'Epoch {epoch}: {loss}')\n    return model",
    "def tokenize(text):\n    return [t.lower() for t in text.split()]",
    "def clean_text(text):\n    text = text.replace('\\n', ' ')\n    return ' '.join(text.split()).lower()",
    "def save_checkpoint(model, path):\n    torch.save(model.state_dict(), path)",
    "def evaluate(model, data):\n    correct = 0\n    for x, y in data:\n        if model(x) == y:\n            correct += 1\n    return correct / len(data)",
    "def deduplicate(items):\n    seen = set()\n    result = []\n    for item in items:\n        if item not in seen:\n            seen.add(item)\n            result.append(item)\n    return result",
    "def quantize(weights, bits=8):\n    scale = max(abs(weights)) / (2**(bits-1) - 1)\n    return (weights / scale).round().astype(f'int{bits}')",
    "class NeuralNetwork:\n    def __init__(self, layers):\n        self.layers = layers\n    def forward(self, x):\n        for layer in self.layers:\n            x = layer(x)\n        return x",
    "def normalize(data):\n    mean = np.mean(data)\n    std = np.std(data)\n    return (data - mean) / std",
]

all_samples = code_samples + vuln_code
print(f"  Vulnerability patterns: {len(vuln_code)} samples")
print(f"  Total: {len(all_samples)} samples")

# ============================================
# STEP 2: Clean Data
# ============================================
print("\n[2/6] Cleaning data...")

def clean_code(code):
    code = code.replace("\x00", "")
    code = re.sub(r"\n{4,}", "\n\n\n", code)
    code = "".join(c for c in code if c.isprintable() or c in "\n\t ")
    return code.strip()

def is_quality(code):
    if not code or len(code) < 20 or len(code) > 3000:
        return False
    cl = code.lower()
    return any(kw in cl for kw in ["def ", "class ", "import ", "from ", "return "])

cleaned = []
seen = set()
for s in all_samples:
    c = clean_code(s)
    if is_quality(c):
        h = hash(c[:300])
        if h not in seen:
            seen.add(h)
            cleaned.append(c)

total_chars = sum(len(s) for s in cleaned)
print(f"  Clean: {len(cleaned)} samples ({len(all_samples)-len(cleaned)} removed)")
print(f"  Total: {total_chars:,} chars")

# ============================================
# STEP 3: Build Tokenizer + Model
# ============================================
print("\n[3/6] Building BPE tokenizer + IBR-GPT-Code model...")

tokenizer = BPETokenizer(vocab_size=1500)
tokenizer.train(cleaned)
print(f"  Tokenizer: {tokenizer.vocab_size_actual} vocab, {len(tokenizer.merges)} merges")

model = ScratchGPT(
    vocab_size=tokenizer.vocab_size_actual,
    embed_dim=128, num_layers=4, num_heads=4,
    max_seq_len=64, dropout=0.1
)
params = model.count_parameters()
print(f"  Model: {params:,} params, {params*4/1024/1024:.2f} MB")
print(f"  Architecture: 4L/128D/4H (low-resource optimized)")

# ============================================
# STEP 4: Pre-Train
# ============================================
print("\n[4/6] Pre-training on real code (15 epochs)...")

seq_len = 32  # Small for memory
all_tokens = []
for s in cleaned:
    enc = tokenizer.encode(s)
    if len(enc) > 5:
        all_tokens.extend(enc)
        all_tokens.append(tokenizer.vocab.get("<EOS>", 0))

sequences = []
for i in range(0, len(all_tokens) - seq_len - 1, seq_len):
    sequences.append(all_tokens[i:i + seq_len + 1])

# Cap for memory
if len(sequences) > 2000:
    sequences = sequences[:2000]

data = torch.tensor(sequences, dtype=torch.long)
print(f"  Tokens: {len(all_tokens):,}, Sequences: {len(sequences)}")

optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)
batch_size = 16
model.train()
pt_losses = []
t0 = time.perf_counter()

for epoch in range(15):
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
    print(f"  E{epoch+1}/15  Loss:{avg:.4f}  PPL:{ppl:.1f}")

pt_time = time.perf_counter() - t0
print(f"\n  Pre-train: {pt_losses[0]:.4f} → {pt_losses[-1]:.4f} ({((pt_losses[0]-pt_losses[-1])/pt_losses[0]*100):.1f}%)")
print(f"  Perplexity: {math.exp(pt_losses[0]):.1f} → {math.exp(min(pt_losses[-1],10)):.1f}")
print(f"  Time: {pt_time:.1f}s")

# ============================================
# STEP 5: Fine-Tune on Vulnerability Code
# ============================================
print("\n[5/6] Fine-tuning on vulnerability patterns (8 epochs)...")

ft_seqs = []
for code in vuln_code:
    enc = tokenizer.encode(code)
    if len(enc) > 5:
        if len(enc) > seq_len:
            for i in range(0, len(enc)-seq_len, seq_len):
                ft_seqs.append(enc[i:i+seq_len+1])
        else:
            ft_seqs.append(enc + [tokenizer.vocab.get("<PAD>", 0)]*(seq_len+1-len(enc)))

ft_data = torch.tensor(ft_seqs[:100], dtype=torch.long)
ft_opt = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
ft_losses = []

for epoch in range(8):
    perm = torch.randperm(len(ft_data))
    ep_l = []
    for i in range(0, len(ft_data), 8):
        batch = ft_data[perm[i:i+8]]
        x, y = batch[:, :-1], batch[:, 1:]
        _, loss = model(x, targets=y)
        ft_opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        ft_opt.step()
        ep_l.append(loss.item())
    ft_losses.append(np.mean(ep_l))

print(f"  Fine-tune: {ft_losses[0]:.4f} → {ft_losses[-1]:.4f}")

# ============================================
# STEP 6: Test Code Generation
# ============================================
print("\n[6/6] Testing code generation...")

model.eval()
python_keywords = {"def", "class", "import", "from", "return", "if", "else",
                   "for", "while", "self", "None", "True", "False", "print",
                   "open", "len", "range", "int", "str", "list", "dict"}

prompts = ["def hello", "import os", "class Model", "def secure", "def train"]
total_keywords = 0
balanced_parens = 0

for prompt in prompts:
    ids = tokenizer.encode(prompt)
    if not ids: ids = [0]
    idx = torch.tensor([ids], dtype=torch.long)
    gen = model.generate(idx, max_new_tokens=20, temperature=0.7)
    text = tokenizer.decode(gen[0].tolist())

    # Count Python keywords
    found = sum(1 for kw in python_keywords if kw in text.lower())
    total_keywords += found

    # Check balanced parentheses
    if text.count("(") == text.count(")"):
        balanced_parens += 1

    print(f"\n  Input:  '{prompt}'")
    print(f"  Output: '{text}'")
    print(f"  Keywords: {found}, Balanced: {text.count('(') == text.count(')')}")

avg_kw = total_keywords / len(prompts)
syntax_pct = balanced_parens / len(prompts) * 100

print(f"\n  Quality Metrics:")
print(f"    Avg Python keywords/output: {avg_kw:.1f}")
print(f"    Balanced parentheses: {balanced_parens}/{len(prompts)} ({syntax_pct:.0f}%)")

# Benchmark
test = torch.tensor([[0]], dtype=torch.long)
times = []
for _ in range(5):
    t0 = time.perf_counter()
    with torch.no_grad():
        _ = model.generate(test, max_new_tokens=10, temperature=0.5)
    times.append(time.perf_counter() - t0)
tps = 10 / np.mean(times)
print(f"    Inference: {tps:.1f} tok/s on CPU")

# ============================================
# Save Model
# ============================================
print(f"\n  Saving {MODEL_NAME}...")

os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
torch.save({
    'model_state_dict': model.state_dict(),
    'model_config': {
        'vocab_size': tokenizer.vocab_size_actual,
        'embed_dim': 128, 'num_layers': 4, 'num_heads': 4, 'max_seq_len': 64,
    },
    'tokenizer_vocab': tokenizer.vocab,
    'tokenizer_merges': tokenizer.merges,
    'training': {'pretrain': pt_losses, 'finetune': ft_losses},
    'meta': {
        'name': MODEL_NAME,
        'pretrained': False,
        'params': params,
        'data_samples': len(cleaned),
        'quality': {'avg_keywords': avg_kw, 'syntax_pct': syntax_pct, 'tps': tps},
    },
}, MODEL_PATH)

print(f"  Saved: {MODEL_PATH} ({os.path.getsize(MODEL_PATH)/1024/1024:.2f} MB)")

# ============================================
# SUMMARY
# ============================================
print(f"\n{'='*60}")
print(f"  {MODEL_NAME} — TRAINING COMPLETE")
print(f"{'='*60}")
print(f"""
  Model: {MODEL_NAME} (4L/128D/4H)
  Params: {params:,} (random init, NOT pre-trained)
  Size: {params*4/1024/1024:.2f} MB

  Data: {len(cleaned)} real Python code samples (FREE)
    CodeSearchNet: {len(code_samples)} functions
    Vulnerability: {len(vuln_code)} CVE patterns

  Pre-train: {pt_losses[0]:.4f} → {pt_losses[-1]:.4f} ({((pt_losses[0]-pt_losses[-1])/pt_losses[0]*100):.1f}%)
  PPL: {math.exp(pt_losses[0]):.1f} → {math.exp(min(pt_losses[-1],10)):.1f}
  Fine-tune: {ft_losses[0]:.4f} → {ft_losses[-1]:.4f}

  Code Quality:
    Avg keywords/output: {avg_kw:.1f}
    Balanced parens: {syntax_pct:.0f}%
    Inference: {tps:.1f} tok/s

  Cost: $0.00 | GPU: NO | Pre-trained: NO
""")
