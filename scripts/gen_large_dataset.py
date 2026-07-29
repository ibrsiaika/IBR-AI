#!/usr/bin/env python3
"""Generate large code dataset (5000+ samples) for 100M model training."""
import json, os, re, hashlib, random

# Load cached
all_code = []
for cf in ['research/cached_code_data.json', 'research/code_cache_1000.json']:
    if os.path.exists(cf):
        with open(cf) as f:
            all_code.extend(json.load(f))
print(f"Cached: {len(all_code)} samples")

# Generate diverse Python code
random.seed(42)
generated = []

names = ['process','analyze','transform','validate','compute','parse','format','search','filter','sort','merge','split','clean','normalize','tokenize','encode','decode','encrypt','decrypt','hash','verify','authenticate','scan','crawl','fetch','extract','classify','predict','train','evaluate','optimize','compress','serialize','cache','monitor','log','report','render','export','import','backup','migrate','deploy']
args = ['data','text','url','filename','model','config','request','response','query','params','options','items','values','key','value','name','path','content','message']
modules = ['os','sys','json','re','hashlib','collections','itertools','functools','datetime','pathlib','urllib','socket','threading','asyncio','logging','csv','sqlite3','subprocess','math','random','base64','uuid']

for i in range(5000):
    n = random.choice(names)
    a = random.choice(args)
    m = random.choice(modules)
    pattern = random.randint(0, 7)

    if pattern == 0:
        code = f"def {n}_{random.choice(names)}({a}, {random.choice(args)}):\n    \"\"\"Process {a}.\"\"\"\n    result = {n}({a})\n    if result:\n        return result\n    return None"
    elif pattern == 1:
        code = f"class {n.title()}{random.choice(names).title()}:\n    def __init__(self, {a}):\n        self.{a} = {a}\n    def process(self):\n        return self.{a}"
    elif pattern == 2:
        code = f"import {m}\n\ndef {n}({a}):\n    \"\"\"{n} using {m}.\"\"\"\n    return {m}.{random.choice(['dumps','loads','parse','read','write','get','post','open','exists','listdir','walk','join','split','find','match','search','sub','compile'])}({a})"
    elif pattern == 3:
        code = f"def {n}({a}):\n    try:\n        result = {a}.process()\n        return result\n    except Exception as e:\n        print(f'Error: {{e}}')\n        return None"
    elif pattern == 4:
        code = f"def {n}({a}):\n    results = []\n    for item in {a}:\n        if item:\n            results.append(item)\n    return results"
    elif pattern == 5:
        code = f"async def {n}({a}):\n    \"\"\"Async {n}.\"\"\"\n    data = await fetch({a})\n    return data"
    elif pattern == 6:
        code = f"def {n}({a}):\n    \"\"\"{n} with validation.\"\"\"\n    if not {a}:\n        raise ValueError('Invalid input')\n    return {a}.strip().lower()"
    else:
        code = f"def {n}({a}, {random.choice(args)}=None):\n    \"\"\"{n} function.\"\"\"\n    if {random.choice(args)} is None:\n        {random.choice(args)} = []\n    for i in range(len({a})):\n        {random.choice(args)}.append({a}[i])\n    return {random.choice(args)}"

    generated.append(code)

all_code.extend(generated)
print(f"After generation: {len(all_code)} total")

# Clean + dedup
cleaned = []
seen = set()
for s in all_code:
    s = s.replace('\x00', '')
    s = ''.join(c for c in s if c.isprintable() or c in '\n\t ')
    if len(s) > 20 and len(s) < 5000:
        h = hashlib.md5(s[:300].encode()).hexdigest()
        if h not in seen:
            seen.add(h)
            cleaned.append(s)

total_chars = sum(len(s) for s in cleaned)
print(f"After clean+dedup: {len(cleaned)} samples, {total_chars:,} chars ({total_chars/1024/1024:.1f} MB)")

os.makedirs('research', exist_ok=True)
with open('research/large_code_dataset.json', 'w') as f:
    json.dump(cleaned, f)
print("Saved to research/large_code_dataset.json")
