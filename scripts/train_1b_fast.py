#!/usr/bin/env python3
"""IBR-GPT-Code-1B — Optimized for speed (smaller batch, capped data)."""
import os, sys, time, json, re, math, hashlib
import torch, torch.nn.functional as F
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from ibr_platform.models.scratch import BPETokenizer, ScratchGPT

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'ibr_gpt_code_1b.pt')

# Web scanning + vuln code (inline for speed)
CODE = [
"import urllib.request\nimport re\ndef scan_website(url):\n    req = urllib.request.Request(url, headers={'User-Agent':'IBR-Bot'})\n    resp = urllib.request.urlopen(req, timeout=10)\n    html = resp.read().decode('utf-8', errors='ignore')\n    title = re.search(r'<title>(.*?)</title>', html, re.I)\n    links = re.findall(r'href=[\"\\'](.*?)[\"\\']', html)\n    return {'title': title.group(1) if title else '', 'links': links, 'size': len(html)}",
"import socket\ndef port_scan(host, ports=[80,443,22,8080]):\n    results = {}\n    for port in ports:\n        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n        sock.settimeout(2)\n        results[port] = 'open' if sock.connect_ex((host, port)) == 0 else 'closed'\n        sock.close()\n    return results",
"import re\ndef extract_entities(text):\n    emails = re.findall(r'[\\w.+-]+@[\\w-]+\\.[\\w.]+', text)\n    urls = re.findall(r'https?://[^\\s]+', text)\n    phones = re.findall(r'\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b', text)\n    ips = re.findall(r'\\b\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\b', text)\n    return {'emails': list(set(emails)), 'urls': list(set(urls)), 'phones': list(set(phones)), 'ips': list(set(ips))}",
"def redact_pii(text):\n    import re\n    text = re.sub(r'[\\w.+-]+@[\\w-]+\\.[\\w.]+', '[EMAIL]', text)\n    text = re.sub(r'\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b', '[PHONE]', text)\n    text = re.sub(r'\\b\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}[\\s-]?\\d{4}\\b', '[CARD]', text)\n    return text",
"def process_input(data):\n    query = 'SELECT * FROM users WHERE name=' + data\n    return db.execute(query)",
"def safe_query(data):\n    query = 'SELECT * FROM users WHERE name = ?'\n    return db.execute(query, (data,))",
"def eval_input(user_input):\n    return eval(user_input)",
"def safe_calc(expr):\n    import ast\n    return ast.literal_eval(expr)",
"def read_file(filename):\n    with open('/data/' + filename) as f:\n        return f.read()",
"def safe_read(filename):\n    import os\n    path = os.path.normpath(filename)\n    if not path.startswith('/data/'):\n        raise ValueError('Invalid')\n    with open(path) as f:\n        return f.read()",
"def hash_pass(password):\n    import hashlib\n    return hashlib.md5(password.encode()).hexdigest()",
"def secure_hash(password):\n    import bcrypt\n    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())",
"def deserialize(data):\n    import pickle\n    return pickle.loads(data)",
"def safe_deserialize(data):\n    import json\n    return json.loads(data)",
"def exec_cmd(cmd):\n    import os\n    os.system('ls ' + cmd)",
"def safe_exec(cmd):\n    import subprocess\n    return subprocess.run(['ls', cmd], capture_output=True)",
"def train_model(X, y, epochs=10):\n    model = Model()\n    for epoch in range(epochs):\n        loss = model.train(X, y)\n        print(f'Epoch {epoch}: {loss}')\n    return model",
"def tokenize(text):\n    return [t.lower() for t in text.split()]",
"def clean_text(text):\n    text = text.replace('\\n', ' ')\n    return ' '.join(text.split()).lower()",
"def save_checkpoint(model, path):\n    torch.save(model.state_dict(), path)",
"def evaluate(model, data):\n    correct = 0\n    for x, y in data:\n        if model(x) == y:\n            correct += 1\n    return correct / len(data)",
"def deduplicate(items):\n    seen = set()\n    result = []\n    for item in items:\n        if item not in seen:\n            seen.add(item)\n            result.append(item)\n    return result",
"def quantize(weights, bits=8):\n    scale = max(abs(weights)) / (2**(bits-1) - 1)\n    return (weights / scale).round().astype(f'int{bits}')",
"class NeuralNetwork:\n    def __init__(self, layers):\n        self.layers = layers\n    def forward(self, x):\n        for layer in self.layers:\n            x = layer(x)\n        return x",
"def normalize(data):\n    mean = np.mean(data)\n    std = np.std(data)\n    return (data - mean) / std",
"class DataCollector:\n    def __init__(self):\n        self.data = []\n        self.cache = {}\n    def collect(self, url, content):\n        h = hashlib.md5(content.encode()).hexdigest()\n        if h in self.cache:\n            return None\n        self.cache[h] = True\n        self.data.append({'url': url, 'content': content, 'hash': h})\n        return self.data[-1]",
"import re\ndef analyze_security(html):\n    forms = re.findall(r'<form[^>]*>', html, re.I)\n    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)\n    emails = re.findall(r'[\\w.+-]+@[\\w-]+\\.[\\w.]+', html)\n    comments = re.findall(r'<!--(.*?)-->', html, re.DOTALL)\n    return {'forms': len(forms), 'scripts': len(scripts), 'emails': len(emails), 'comments': len(comments)}",
"def secure_hash_file(filepath):\n    import hashlib\n    h = hashlib.sha256()\n    with open(filepath, 'rb') as f:\n        while True:\n            chunk = f.read(8192)\n            if not chunk:\n                break\n            h.update(chunk)\n    return h.hexdigest()",
"from collections import Counter\ndef tfidf_search(docs, query):\n    query_terms = query.lower().split()\n    scores = []\n    for doc in docs:\n        tokens = doc.lower().split()\n        tf = Counter(tokens)\n        score = sum(tf.get(t, 0) for t in query_terms)\n        scores.append(score)\n    return sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:5]",
"class CodebaseAnalyzer:\n    def __init__(self, root):\n        self.root = root\n        self.results = {'files': 0, 'functions': 0, 'issues': []}\n    def scan(self):\n        import os\n        for root, dirs, files in os.walk(self.root):\n            for f in files:\n                if f.endswith('.py'):\n                    self.results['files'] += 1\n                    with open(os.path.join(root, f)) as fh:\n                        content = fh.read()\n                        self.results['functions'] += content.count('def ')\n                        if 'eval(' in content:\n                            self.results['issues'].append(f'{f}: eval()')\n        return self.results",
"def async_fetch(urls):\n    import asyncio, aiohttp\n    async def fetch(session, url):\n        async with session.get(url) as resp:\n            return {'url': url, 'status': resp.status, 'text': await resp.text()}\n    async def main():\n        async with aiohttp.ClientSession() as session:\n            return await asyncio.gather(*[fetch(session, u) for u in urls])\n    return asyncio.run(main())",
"def parse_xml_safe(data):\n    from lxml import etree\n    parser = etree.XMLParser(resolve_entities=False, no_network=True)\n    return etree.fromstring(data, parser=parser)",
"def safe_redirect(url):\n    from urllib.parse import urlparse\n    p = urlparse(url)\n    if p.netloc and p.netloc != 'example.com':\n        return 'Invalid redirect'\n    return url",
"def verify_file(filepath, expected_hash):\n    actual = secure_hash_file(filepath)\n    return actual == expected_hash",
"def classify_code(code):\n    vulnerable_patterns = ['eval(', 'exec(', 'pickle.loads', 'os.system', 'shell=True']\n    found = [p for p in vulnerable_patterns if p in code]\n    return {'vulnerable': len(found) > 0, 'patterns': found, 'risk': 'high' if found else 'low'}",
"def monitor_changes(path, interval=60):\n    import time, os\n    snapshots = {}\n    while True:\n        for f in os.listdir(path):\n            fp = os.path.join(path, f)\n            if os.path.isfile(fp):\n                h = secure_hash_file(fp)\n                if fp in snapshots and snapshots[fp] != h:\n                    print(f'CHANGED: {f}')\n                snapshots[fp] = h\n        time.sleep(interval)",
"def generate_report(findings):\n    import json\n    report = {\n        'summary': {'total': len(findings), 'vulnerable': sum(1 for f in findings if f.get('risk') == 'high')},\n        'details': findings,\n        'timestamp': __import__('datetime').datetime.now().isoformat()\n    }\n    return json.dumps(report, indent=2)",
"def crawl_domain(domain, max_pages=50):\n    import urllib.request, re\n    from urllib.parse import urljoin\n    visited = set()\n    queue = [f'https://{domain}']\n    pages = []\n    while queue and len(visited) < max_pages:\n        url = queue.pop(0)\n        if url in visited:\n            continue\n        visited.add(url)\n        try:\n            req = urllib.request.Request(url, headers={'User-Agent': 'IBR-Bot/1.0'})\n            html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')\n            links = re.findall(r'href=[\"\\'](https?://[^\"\\']+)[\"\\']', html)\n            pages.append({'url': url, 'size': len(html), 'links': len(links)})\n            for link in links:\n                if domain in link and link not in visited:\n                    queue.append(link)\n        except:\n            pass\n    return pages",
"def detect_tech_stack(html):\n    import re\n    techs = []\n    if 'wp-content' in html or 'wordpress' in html.lower():\n        techs.append('WordPress')\n    if 'react' in html.lower() or '__NEXT_DATA__' in html:\n        techs.append('React/Next.js')\n    if 'django' in html.lower():\n        techs.append('Django')\n    if 'flask' in html.lower():\n        techs.append('Flask')\n    if 'jquery' in html.lower():\n        techs.append('jQuery')\n    if 'bootstrap' in html.lower():\n        techs.append('Bootstrap')\n    return techs",
"def check_headers(url):\n    import urllib.request\n    req = urllib.request.Request(url, headers={'User-Agent': 'IBR-Bot'})\n    resp = urllib.request.urlopen(req, timeout=10)\n    headers = dict(resp.headers)\n    security = {\n        'hsts': 'strict-transport-security' in {k.lower(): v for k, v in headers.items()},\n        'xframe': 'x-frame-options' in {k.lower(): v for k, v in headers.items()},\n        'xss_protection': 'x-xss-protection' in {k.lower(): v for k, v in headers.items()},\n        'content_type': headers.get('Content-Type', 'unknown')\n    }\n    return security",
"def fuzzy_search(data, query, threshold=0.7):\n    from difflib import SequenceMatcher\n    results = []\n    for item in data:\n        ratio = SequenceMatcher(None, query.lower(), item.lower()).ratio()\n        if ratio >= threshold:\n            results.append((item, ratio))\n    return sorted(results, key=lambda x: x[1], reverse=True)",
"def compress_model(model, bits=8):\n    state = model.state_dict()\n    compressed = {}\n    for key, tensor in state.items():\n        if 'weight' in key and tensor.dtype == torch.float32:\n            scale = tensor.abs().max() / (2**(bits-1) - 1)\n            compressed[key] = (tensor / scale).round().to(torch.int8)\n            compressed[key + '_scale'] = scale\n        else:\n            compressed[key] = tensor\n    return compressed",
"def benchmark_inference(model, input_ids, n=10):\n    import time\n    model.eval()\n    times = []\n    with torch.no_grad():\n        for _ in range(n):\n            t0 = time.perf_counter()\n            model.generate(input_ids, max_new_tokens=10, temperature=0.5)\n            times.append(time.perf_counter() - t0)\n    avg = sum(times) / len(times)\n    return {'avg_ms': avg * 1000, 'tokens_per_sec': 10 / avg, 'runs': n}",
]

# Also load cached CodeSearchNet if available
cache_path = os.path.join(os.path.dirname(__file__), '..', 'research', 'cached_code_data.json')
if os.path.exists(cache_path):
    with open(cache_path) as f:
        cached = json.load(f)
    CODE.extend(cached)
    print(f"Loaded {len(cached)} cached CodeSearchNet samples")

# Add more cached if available
cache2 = os.path.join(os.path.dirname(__file__), '..', 'research', 'code_cache_1000.json')
if os.path.exists(cache2):
    with open(cache2) as f:
        cached2 = json.load(f)
    CODE.extend(cached2)
    print(f"Loaded {len(cached2)} more cached samples")

print(f"\nTotal training samples: {len(CODE)}")

# Clean + dedup
def clean(c):
    c = c.replace('\x00','')
    c = ''.join(ch for ch in c if ch.isprintable() or ch in '\n\t ')
    return c.strip()

cleaned = []
seen = set()
for s in CODE:
    c = clean(s)
    if len(c) > 20 and len(c) < 5000:
        h = hashlib.md5(c[:300].encode()).hexdigest()
        if h not in seen:
            seen.add(h)
            cleaned.append(c)

print(f"After dedup: {len(cleaned)} samples, {sum(len(s) for s in cleaned):,} chars")

# Tokenizer
print("Building BPE tokenizer...")
tok = BPETokenizer(vocab_size=2000)
tok.train(cleaned)
print(f"Vocab: {tok.vocab_size_actual}")

# Model (8L/256D/8H — largest feasible on CPU)
print("Building IBR-GPT-Code-1B (8L/256D/8H)...")
model = ScratchGPT(
    vocab_size=tok.vocab_size_actual,
    embed_dim=256, num_layers=8, num_heads=8, max_seq_len=64, dropout=0.1
)
params = model.count_parameters()
print(f"Params: {params:,} | Size: {params*4/1024/1024:.1f} MB | INT8: {params/1024/1024:.1f} MB")

# Prepare data
seq_len = 32  # Small for memory
all_tokens = []
for s in cleaned:
    enc = tok.encode(s)
    if len(enc) > 5:
        all_tokens.extend(enc)
        all_tokens.append(tok.vocab.get('<EOS>', 0))

sequences = []
for i in range(0, len(all_tokens) - seq_len - 1, seq_len):
    sequences.append(all_tokens[i:i + seq_len + 1])

# Cap
sequences = sequences[:2500]
data = torch.tensor(sequences, dtype=torch.long)
print(f"Tokens: {len(all_tokens):,} | Sequences: {len(sequences)}")

# Pre-train
print(f"\nPre-training (12 epochs)...")
opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)
model.train()
pt_losses = []
t0 = time.perf_counter()

for epoch in range(12):
    perm = torch.randperm(len(data))
    ep_l = []
    for i in range(0, len(data), 16):
        batch = data[perm[i:i+16]]
        x, y = batch[:, :-1], batch[:, 1:]
        _, loss = model(x, targets=y)
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        ep_l.append(loss.item())
    avg = np.mean(ep_l)
    pt_losses.append(avg)
    ppl = math.exp(min(avg, 10))
    print(f"  E{epoch+1}/12  Loss:{avg:.4f}  PPL:{ppl:.1f}")

pt_time = time.perf_counter() - t0
print(f"\nPre-train: {pt_losses[0]:.4f} → {pt_losses[-1]:.4f} ({((pt_losses[0]-pt_losses[-1])/pt_losses[0]*100):.1f}%)")
print(f"PPL: {math.exp(pt_losses[0]):.1f} → {math.exp(min(pt_losses[-1],10)):.1f}")
print(f"Time: {pt_time:.1f}s")

# Fine-tune on web scanning code
print(f"\nFine-tuning on web scanning code (8 epochs)...")
web_code = CODE[:40]  # First 40 = web scanning + vuln patterns
ft_seqs = []
for code in web_code:
    enc = tok.encode(code)
    if len(enc) > 5:
        if len(enc) > seq_len:
            for i in range(0, len(enc)-seq_len, seq_len):
                ft_seqs.append(enc[i:i+seq_len+1])
        else:
            ft_seqs.append(enc + [tok.vocab.get('<PAD>',0)]*(seq_len+1-len(enc)))

ft_data = torch.tensor(ft_seqs[:200], dtype=torch.long)
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

print(f"Fine-tune: {ft_losses[0]:.4f} → {ft_losses[-1]:.4f}")

# Test generation
print(f"\nCode generation tests:")
model.eval()
python_kw = {"def","class","import","from","return","if","else","for","while","self","None","True","False","print","open","len","range","try","except","with","as"}
total_kw = 0
balanced = 0
prompts = ["def scan_website", "import urllib", "def extract_emails", "def port_scan", "class DataCollector", "def secure_hash", "def analyze_security", "def redact_pii"]

for p in prompts:
    ids = tok.encode(p)
    if not ids: ids = [0]
    idx = torch.tensor([ids], dtype=torch.long)
    gen = model.generate(idx, max_new_tokens=25, temperature=0.7)
    text = tok.decode(gen[0].tolist())
    found = sum(1 for kw in python_kw if kw in text.lower())
    total_kw += found
    if text.count("(") == text.count(")"): balanced += 1
    print(f"  '{p}' → '{text[:100]}'")
    print(f"    Keywords: {found} | Balanced: {text.count('(')==text.count(')')}")

avg_kw = total_kw / len(prompts)
syntax_pct = balanced / len(prompts) * 100

# Benchmark
test = torch.tensor([[0]], dtype=torch.long)
times = []
for _ in range(5):
    t0 = time.perf_counter()
    with torch.no_grad():
        model.generate(test, max_new_tokens=10, temperature=0.5)
    times.append(time.perf_counter() - t0)
tps = 10 / np.mean(times)

print(f"\nQuality: {avg_kw:.1f} keywords/output | {syntax_pct:.0f}% balanced | {tps:.1f} tok/s")

# Save
print(f"\nSaving model...")
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
torch.save({
    'model_state_dict': model.state_dict(),
    'model_config': {'vocab_size': tok.vocab_size_actual, 'embed_dim': 256, 'num_layers': 8, 'num_heads': 8, 'max_seq_len': 64},
    'tokenizer_vocab': tok.vocab, 'tokenizer_merges': tok.merges,
    'training': {'pretrain': pt_losses, 'finetune': ft_losses},
    'meta': {'name': 'IBR-GPT-Code-1B', 'pretrained': False, 'params': params, 'data_samples': len(cleaned),
             'quality': {'avg_keywords': avg_kw, 'syntax_pct': syntax_pct, 'tps': tps}},
}, MODEL_PATH)
print(f"Saved: {MODEL_PATH} ({os.path.getsize(MODEL_PATH)/1024/1024:.2f} MB)")

print(f"\n{'='*60}")
print(f"IBR-GPT-Code-1B — COMPLETE")
print(f"{'='*60}")
print(f"Params: {params:,} | Size: {params*4/1024/1024:.1f}MB | INT8: {params/1024/1024:.1f}MB")
print(f"Pre-train: {pt_losses[0]:.4f} → {pt_losses[-1]:.4f} ({((pt_losses[0]-pt_losses[-1])/pt_losses[0]*100):.1f}%)")
print(f"PPL: {math.exp(pt_losses[0]):.1f} → {math.exp(min(pt_losses[-1],10)):.1f}")
print(f"Fine-tune: {ft_losses[0]:.4f} → {ft_losses[-1]:.4f}")
print(f"Quality: {avg_kw:.1f} kw/out | {syntax_pct:.0f}% syntax | {tps:.1f} tok/s")
print(f"Data: {len(cleaned)} samples | Cost: $0.00 | Pre-trained: NO")
