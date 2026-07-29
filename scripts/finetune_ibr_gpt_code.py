#!/usr/bin/env python3
"""
IBR-GPT-Code — Fine-tuning Script
Pre-trained model → Fine-tune on your data → Test

Usage:
  python scripts/finetune_ibr_gpt_code.py --mode pretrain --data your_code.txt
  python scripts/finetune_ibr_gpt_code.py --mode finetune --data vuln_code.txt
  python scripts/finetune_ibr_gpt_code.py --mode generate --prompt "def hello"
  python scripts/finetune_ibr_gpt_code.py --mode info
"""
import argparse, os, sys, json, re, math, time
import torch, numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from ibr_platform.models.scratch import BPETokenizer, ScratchGPT

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'ibr_gpt_code.pt')

def load_model(path):
    if not os.path.exists(path):
        print(f"Model not found at {path}")
        print("Run pretrain first: python scripts/finetune_ibr_gpt_code.py --mode pretrain --data your_code.txt")
        sys.exit(1)
    ckpt = torch.load(path, weights_only=False)
    cfg = ckpt['model_config']
    model = ScratchGPT(
        vocab_size=cfg['vocab_size'], embed_dim=cfg['embed_dim'],
        num_layers=cfg['num_layers'], num_heads=cfg['num_heads'],
        max_seq_len=cfg['max_seq_len']
    )
    model.load_state_dict(ckpt['model_state_dict'])
    tok = BPETokenizer(vocab_size=cfg['vocab_size'])
    tok.vocab = ckpt['tokenizer_vocab']
    tok.id_to_token = {v: k for k, v in tok.vocab.items()}
    tok.merges = ckpt['tokenizer_merges']
    return model, tok, ckpt

def save_model(path, model, tok, training, meta):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save({
        'model_state_dict': model.state_dict(),
        'model_config': {
            'vocab_size': tok.vocab_size_actual,
            'embed_dim': model.embed_dim,
            'num_layers': len(model.blocks),
            'num_heads': model.blocks[0].attn.num_heads,
            'max_seq_len': model.max_seq_len,
        },
        'tokenizer_vocab': tok.vocab,
        'tokenizer_merges': tok.merges,
        'training': training,
        'meta': meta,
    }, path)

def load_data(path):
    with open(path) as f:
        return [line.strip() for line in f if line.strip() and len(line.strip()) > 20]

def clean_code(code):
    code = code.replace('\x00', '')
    code = re.sub(r'\n{4,}', '\n\n\n', code)
    code = ''.join(c for c in code if c.isprintable() or c in '\n\t ')
    return code.strip()

def main():
    parser = argparse.ArgumentParser(description='IBR-GPT-Code Fine-tuning')
    parser.add_argument('--mode', choices=['pretrain', 'finetune', 'generate', 'info'], required=True)
    parser.add_argument('--data', type=str, help='Path to training data file (one code sample per line)')
    parser.add_argument('--prompt', type=str, help='Prompt for generation')
    parser.add_argument('--epochs', type=int, default=10)
    parser.add_argument('--lr', type=float, default=3e-4)
    parser.add_argument('--max-tokens', type=int, default=25)
    parser.add_argument('--temp', type=float, default=0.7)
    args = parser.parse_args()

    if args.mode == 'info':
        model, tok, ckpt = load_model(MODEL_PATH)
        meta = ckpt.get('meta', {})
        print(f"Model: {meta.get('name', 'IBR-GPT-Code')}")
        print(f"Params: {model.count_parameters():,}")
        print(f"Vocab: {tok.vocab_size_actual}")
        print(f"Pre-trained: {meta.get('pretrained', 'NO')}")
        print(f"Data sources: {meta.get('data_sources', 'N/A')}")
        return

    if args.mode == 'generate':
        model, tok, _ = load_model(MODEL_PATH)
        model.eval()
        ids = tok.encode(args.prompt or "def hello")
        if not ids: ids = [0]
        idx = torch.tensor([ids], dtype=torch.long)
        gen = model.generate(idx, max_new_tokens=args.max_tokens, temperature=args.temp)
        print(tok.decode(gen[0].tolist()))
        return

    if args.mode == 'pretrain':
        texts = load_data(args.data)
        texts = [clean_code(t) for t in texts if len(t) > 20]
        print(f"Training on {len(texts)} samples...")
        tok = BPETokenizer(vocab_size=2000)
        tok.train(texts)
        model = ScratchGPT(
            vocab_size=tok.vocab_size_actual,
            embed_dim=256, num_layers=8, num_heads=8, max_seq_len=128, dropout=0.1
        )
        print(f"Params: {model.count_parameters():,}")
    else:  # finetune
        model, tok, _ = load_model(MODEL_PATH)
        texts = load_data(args.data)
        texts = [clean_code(t) for t in texts if len(t) > 20]
        print(f"Fine-tuning on {len(texts)} samples...")

    # Prepare data
    seq_len = 64
    all_tokens = []
    for t in texts:
        enc = tok.encode(t)
        if len(enc) > 5:
            all_tokens.extend(enc)
            all_tokens.append(tok.vocab.get('<EOS>', 0))

    sequences = []
    for i in range(0, len(all_tokens) - seq_len - 1, seq_len // 2):
        sequences.append(all_tokens[i:i + seq_len + 1])

    if not sequences:
        print("Not enough data for training")
        return

    data = torch.tensor(sequences[:3000], dtype=torch.long)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    model.train()
    losses = []

    for epoch in range(args.epochs):
        perm = torch.randperm(len(data))
        ep_losses = []
        for i in range(0, len(data), 16):
            batch = data[perm[i:i+16]]
            x, y = batch[:, :-1], batch[:, 1:]
            _, loss = model(x, targets=y)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            ep_losses.append(loss.item())
        avg = np.mean(ep_losses)
        losses.append(avg)
        ppl = math.exp(min(avg, 10))
        print(f"  E{epoch+1}/{args.epochs} Loss:{avg:.4f} PPL:{ppl:.1f}")

    print(f"\nLoss: {losses[0]:.4f} → {losses[-1]:.4f} ({((losses[0]-losses[-1])/losses[0]*100):.1f}%)")

    save_model(MODEL_PATH, model, tok, losses, {
        'name': 'IBR-GPT-Code',
        'pretrained': False,
        'params': model.count_parameters(),
        'mode': args.mode,
        'samples': len(texts),
    })
    print(f"Saved to {MODEL_PATH}")

if __name__ == '__main__':
    main()
