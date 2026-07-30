#!/usr/bin/env python3
"""
Interactive chat demo — talk to the finetuned IBR-GPT-Code model.

Usage:
    python scripts/chat_demo.py
    python scripts/chat_demo.py --model 100m_ft
    python scripts/chat_demo.py --prompt "User: Hi"

The model was fine-tuned on 281 conversation patterns. It responds to
greetings, simple questions, code requests, and polite exchanges.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fast_bpe import FastBPETokenizerV2
from train_100m_v2 import ScratchGPTLarge
from train_full_pipeline import remap_state_dict_keys

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
torch.set_num_threads(2)


def load_finetuned_model(model_path: Path):
    """Load the finetuned model + tokenizer."""
    print(f"Loading model: {model_path.name}", file=sys.stderr)
    ckpt = torch.load(model_path, map_location='cpu', weights_only=False)
    cfg = ckpt['model_config']

    model = ScratchGPTLarge(
        vocab_size=cfg['vocab_size'],
        embed_dim=cfg['embed_dim'],
        num_layers=cfg['num_layers'],
        num_heads=cfg['num_heads'],
        max_seq_len=cfg['max_seq_len'],
        use_checkpointing=False,
    )
    state = ckpt['model_state_dict']
    state = remap_state_dict_keys(state, set(model.state_dict().keys()))
    model.load_state_dict(state)
    model.eval()

    tok = FastBPETokenizerV2(vocab_size=cfg['vocab_size'])
    tok.vocab = ckpt['tokenizer_vocab']
    tok.id_to_token = {v: k for k, v in tok.vocab.items()}
    tok.merges = [tuple(p) for p in ckpt['tokenizer_merges']]

    meta = ckpt.get('meta', {})
    print(f"  Params: {model.count_parameters():,}", file=sys.stderr)
    print(f"  Stage: {meta.get('stage', 'unknown')}", file=sys.stderr)
    print(f"  Vocab: {cfg['vocab_size']}, Max seq: {cfg['max_seq_len']}", file=sys.stderr)
    return model, tok, cfg, meta


@torch.no_grad()
def generate_response(model, tok, prompt: str, max_tokens: int = 60,
                      temperature: float = 0.7, top_k: int = 8) -> str:
    """Generate a response to the prompt."""
    # Format as conversation: "User: <prompt>\nAssistant:"
    if not prompt.startswith("User:"):
        formatted = f"User: {prompt}\nAssistant:"
    else:
        formatted = prompt

    ids = tok.encode(formatted)
    if not ids:
        ids = [0]
    idx = torch.tensor([ids], dtype=torch.long)
    eos_id = tok.vocab.get("<EOS>", -1)

    for _ in range(max_tokens):
        idx_cond = idx if idx.size(1) <= model.max_seq_len else idx[:, -model.max_seq_len:]
        logits, _ = model(idx_cond)
        logits = logits[:, -1, :] / max(temperature, 1e-5)
        if top_k > 0:
            v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
            logits[logits < v[:, [-1]]] = float('-inf')
        probs = F.softmax(logits, dim=-1)
        next_id = torch.multinomial(probs, num_samples=1)
        idx = torch.cat([idx, next_id], dim=1)
        if next_id.item() == eos_id:
            break

    full_text = tok.decode(idx[0].tolist())

    # Extract just the assistant's response (after the LAST "Assistant:")
    # The prompt already ends with "Assistant:", so take everything after it
    # Split on "assistant" (case-insensitive) and take the last part
    parts = re.split(r'assistant\s*:', full_text, flags=re.IGNORECASE)
    if len(parts) > 1:
        response = parts[-1].strip()
        # Stop at next "User:" if present (end of assistant turn)
        if "user:" in response.lower() or "user :" in response.lower():
            response = re.split(r'user\s*:', response, flags=re.IGNORECASE)[0].strip()
        # Clean up whitespace
        response = re.sub(r'\s+', ' ', response).strip()
        return response
    return full_text


def run_demo(model, tok, prompts: list[str] | None = None) -> None:
    """Run a demo of conversation samples."""
    if prompts is None:
        prompts = [
            "Hi",
            "Hello",
            "How are you?",
            "What is your name?",
            "What can you do?",
            "Can you help me?",
            "Write a function",
            "Thank you",
            "Bye",
        ]

    print(f"\n{'='*60}")
    print(f"  IBR-GPT-Code Chat Demo")
    print(f"{'='*60}")
    for p in prompts:
        t0 = time.perf_counter()
        response = generate_response(model, tok, p, max_tokens=50)
        elapsed = time.perf_counter() - t0
        print(f"\n  You: {p}")
        print(f"  AI:  {response[:100]}")
        print(f"  [{elapsed:.2f}s]")


def run_interactive(model, tok) -> None:
    """Run interactive REPL."""
    print(f"\n{'='*60}")
    print(f"  IBR-GPT-Code Interactive Chat")
    print(f"  Type 'quit' or 'exit' to leave.")
    print(f"{'='*60}")
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input:
            continue
        if user_input.lower() in ('quit', 'exit', 'bye'):
            print("AI: Goodbye!")
            break
        t0 = time.perf_counter()
        response = generate_response(model, tok, user_input, max_tokens=60)
        elapsed = time.perf_counter() - t0
        print(f"AI:  {response[:150]}")
        print(f"     [{elapsed:.2f}s]")


def main():
    parser = argparse.ArgumentParser(description="IBR-GPT-Code Chat Demo")
    parser.add_argument('--model', default='100m_ft',
                        help='Model key or path (default: 100m_ft)')
    parser.add_argument('--prompt', help='Single prompt (non-interactive)')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Interactive REPL mode')
    parser.add_argument('--max-tokens', type=int, default=60)
    parser.add_argument('--temperature', type=float, default=0.7)
    parser.add_argument('--top-k', type=int, default=8)
    args = parser.parse_args()

    # Resolve model path
    model_keys = {
        '100m_ft': MODELS_DIR / "ibr_gpt_code_100m_finetuned.pt",
        '100m': MODELS_DIR / "ibr_gpt_code_100m.pt",
    }
    if args.model in model_keys:
        model_path = model_keys[args.model]
    else:
        model_path = Path(args.model)

    if not model_path.exists():
        print(f"ERROR: Model not found: {model_path}", file=sys.stderr)
        print(f"Run: python scripts/extended_finetune.py", file=sys.stderr)
        return 1

    model, tok, cfg, meta = load_finetuned_model(model_path)

    if args.prompt:
        response = generate_response(model, tok, args.prompt,
                                     max_tokens=args.max_tokens,
                                     temperature=args.temperature,
                                     top_k=args.top_k)
        print(f"You: {args.prompt}")
        print(f"AI:  {response}")
    elif args.interactive:
        run_interactive(model, tok)
    else:
        run_demo(model, tok)

    return 0


if __name__ == "__main__":
    sys.exit(main())
