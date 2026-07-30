"""
From-Scratch AI — Transformer built from zero (NO pre-trained weights).

This module contains:
    - BPETokenizer: Tokenizer trained from scratch on real data
    - MultiHeadSelfAttention: Attention mechanism from scratch
    - TransformerBlock: Attention + MLP with residual connections
    - ScratchGPT: Complete GPT-style language model from scratch
    - ScratchModelManager: Manages the from-scratch model lifecycle

All weights are randomly initialized. No pre-trained model is used.
The model is pre-trained and fine-tuned on data scraped from FREE sources.

References:
    - "Attention is All You Need" (Vaswani et al., 2017)
    - GPT-2 (Radford et al., 2019)
    - nanoGPT (Karpathy)
    - PRD Section 89 (CPU-First Deep Dive)
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F


class BPETokenizer:
    """Byte Pair Encoding tokenizer built from scratch.

    Trains on the provided text data. No pre-trained vocabulary.
    Starts with character-level tokens and merges most frequent pairs.
    """

    def __init__(self, vocab_size: int = 1000) -> None:
        self.vocab_size = vocab_size
        self.merges: list[tuple[str, str]] = []
        self.vocab: dict[str, int] = {}
        self.id_to_token: dict[int, str] = {}

    def train(self, texts: list[str]) -> None:
        """Train BPE on texts."""
        word_freq: Counter = Counter()
        for text in texts:
            # BUG S-3 FIX: match whitespace too so decode preserves word boundaries
            words = re.findall(r'\w+|\s+|[^\w\s]', text.lower())
            word_freq.update(words)

        word_splits: dict[str, list[str]] = {}
        for word in word_freq:
            word_splits[word] = list(word)

        char_set: set[str] = set()
        for word in word_splits:
            char_set.update(word_splits[word])

        self.vocab = {char: idx for idx, char in enumerate(sorted(char_set))}
        self.vocab["<PAD>"] = len(self.vocab)
        self.vocab["<UNK>"] = len(self.vocab)
        self.vocab["<BOS>"] = len(self.vocab)
        self.vocab["<EOS>"] = len(self.vocab)

        num_merges = self.vocab_size - len(self.vocab)
        for _ in range(num_merges):
            pair_counts: Counter = Counter()
            for word, freq in word_freq.items():
                splits = word_splits[word]
                for i in range(len(splits) - 1):
                    pair_counts[(splits[i], splits[i + 1])] += freq
            if not pair_counts:
                break
            best_pair = pair_counts.most_common(1)[0][0]
            self.merges.append(best_pair)
            new_token = best_pair[0] + best_pair[1]
            self.vocab[new_token] = len(self.vocab)
            for word in word_splits:
                splits = word_splits[word]
                new_splits = []
                i = 0
                while i < len(splits):
                    if i < len(splits) - 1 and (splits[i], splits[i + 1]) == best_pair:
                        new_splits.append(new_token)
                        i += 2
                    else:
                        new_splits.append(splits[i])
                        i += 1
                word_splits[word] = new_splits

        self.id_to_token = {idx: token for token, idx in self.vocab.items()}

    def encode(self, text: str) -> list[int]:
        """Encode text to token IDs.

        BUG S-3 FIX: Include whitespace in the token regex so that
        decode() can reconstruct word boundaries. Previously the regex
        r'\\w+|[^\\w\\s]' dropped all whitespace, causing decode to
        concatenate words with no separator ('helloworld' instead of
        'hello world').
        """
        # Match words, whitespace runs, or single non-word non-space chars
        words = re.findall(r'\w+|\s+|[^\w\s]', text.lower())
        ids: list[int] = []
        for word in words:
            splits = list(word)
            for merge_pair in self.merges:
                new_splits = []
                i = 0
                while i < len(splits):
                    if i < len(splits) - 1 and (splits[i], splits[i + 1]) == merge_pair:
                        new_splits.append(splits[i] + splits[i + 1])
                        i += 2
                    else:
                        new_splits.append(splits[i])
                        i += 1
                splits = new_splits
            for token in splits:
                ids.append(self.vocab.get(token, self.vocab["<UNK>"]))
        return ids

    def decode(self, ids: list[int]) -> str:
        """Decode token IDs to text."""
        tokens = [self.id_to_token.get(idx, "<UNK>") for idx in ids]
        text = ""
        for token in tokens:
            if token not in ("<PAD>", "<BOS>", "<EOS>"):
                text += token
        return text

    @property
    def vocab_size_actual(self) -> int:
        return len(self.vocab)


class MultiHeadSelfAttention(nn.Module):
    """Multi-head self-attention from scratch.

    Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V
    """

    def __init__(self, embed_dim: int, num_heads: int, dropout: float = 0.1) -> None:
        super().__init__()
        # BUG S-4 FIX: descriptive error instead of bare assert
        if embed_dim % num_heads != 0:
            raise ValueError(
                f"embed_dim ({embed_dim}) must be divisible by num_heads ({num_heads}). "
                f"Got remainder {embed_dim % num_heads}."
            )
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.q_proj = nn.Linear(embed_dim, embed_dim)
        self.k_proj = nn.Linear(embed_dim, embed_dim)
        self.v_proj = nn.Linear(embed_dim, embed_dim)
        self.out_proj = nn.Linear(embed_dim, embed_dim)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, mask: torch.Tensor | None = None) -> torch.Tensor:
        B, T, C = x.shape
        q = self.q_proj(x).view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(B, T, self.num_heads, self.head_dim).transpose(1, 2)
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        if mask is None:
            mask = torch.triu(torch.ones(T, T, device=x.device), diagonal=1).bool()
            mask = mask.unsqueeze(0).unsqueeze(0)
        scores = scores.masked_fill(mask, float('-inf'))
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)
        out = torch.matmul(attn_weights, v)
        out = out.transpose(1, 2).contiguous().view(B, T, C)
        return self.out_proj(out)


class TransformerBlock(nn.Module):
    """Transformer block: Pre-LayerNorm Attention + MLP with residuals."""

    def __init__(self, embed_dim: int, num_heads: int, mlp_ratio: int = 4, dropout: float = 0.1) -> None:
        super().__init__()
        self.ln1 = nn.LayerNorm(embed_dim)
        self.attn = MultiHeadSelfAttention(embed_dim, num_heads, dropout)
        self.ln2 = nn.LayerNorm(embed_dim)
        self.mlp = nn.Sequential(
            nn.Linear(embed_dim, embed_dim * mlp_ratio),
            nn.GELU(),
            nn.Linear(embed_dim * mlp_ratio, embed_dim),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor, mask: torch.Tensor | None = None) -> torch.Tensor:
        x = x + self.attn(self.ln1(x), mask)
        x = x + self.mlp(self.ln2(x))
        return x


class ScratchGPT(nn.Module):
    """GPT-style language model built from scratch (NO pre-trained weights).

    Architecture: Token embedding + Position embedding + Transformer blocks + LM head.
    All weights randomly initialized using GPT-2 style initialization.
    """

    def __init__(
        self,
        vocab_size: int,
        embed_dim: int = 128,
        num_layers: int = 4,
        num_heads: int = 4,
        max_seq_len: int = 128,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.max_seq_len = max_seq_len
        self.token_embedding = nn.Embedding(vocab_size, embed_dim)
        self.position_embedding = nn.Embedding(max_seq_len, embed_dim)
        self.blocks = nn.ModuleList([
            TransformerBlock(embed_dim, num_heads, dropout=dropout)
            for _ in range(num_layers)
        ])
        self.ln_f = nn.LayerNorm(embed_dim)
        self.lm_head = nn.Linear(embed_dim, vocab_size, bias=False)
        self.lm_head.weight = self.token_embedding.weight
        self.dropout = nn.Dropout(dropout)
        self.apply(self._init_weights)

    def _init_weights(self, module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, idx: torch.Tensor, targets: torch.Tensor | None = None) -> tuple[torch.Tensor, torch.Tensor | None]:
        B, T = idx.shape
        # BUG S-4 FIX: replaced bare assert with descriptive ValueError
        if T > self.max_seq_len:
            raise ValueError(
                f"Sequence length {T} exceeds max_seq_len {self.max_seq_len}. "
                f"Truncate input to <= {self.max_seq_len} tokens."
            )
        pos = torch.arange(0, T, device=idx.device).unsqueeze(0)
        x = self.dropout(self.token_embedding(idx) + self.position_embedding(pos))
        mask = torch.triu(torch.ones(T, T, device=idx.device), diagonal=1).bool().unsqueeze(0).unsqueeze(0)
        for block in self.blocks:
            x = block(x, mask)
        x = self.ln_f(x)
        logits = self.lm_head(x)
        loss = None
        if targets is not None:
            loss = F.cross_entropy(
                logits.reshape(-1, self.vocab_size),
                targets.reshape(-1),
                ignore_index=-1,
            )
        return logits, loss

    @torch.no_grad()
    def generate(self, idx: torch.Tensor, max_new_tokens: int, temperature: float = 0.8,
                 top_k: int | None = None) -> torch.Tensor:
        """Generate tokens autoregressively.

        Args:
            idx: Input token IDs of shape (batch, seq_len).
            max_new_tokens: Number of tokens to generate.
            temperature: Sampling temperature. If <= 0, uses greedy decoding (argmax).
            top_k: If set, restrict sampling to top-K tokens.

        Returns:
            Tensor of shape (batch, seq_len + max_new_tokens).
        """
        self.eval()
        for _ in range(max_new_tokens):
            idx_cond = idx if idx.size(1) <= self.max_seq_len else idx[:, -self.max_seq_len:]
            logits, _ = self.forward(idx_cond)
            logits = logits[:, -1, :]  # (batch, vocab)

            # BUG S-1 FIX: temperature=0 means greedy decoding (no division by zero)
            if temperature <= 0:
                idx_next = logits.argmax(dim=-1, keepdim=True)
            else:
                logits = logits / temperature
                # BUG S-2 FIX: top_k sampling support
                if top_k is not None and top_k > 0:
                    v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                    logits[logits < v[:, [-1]]] = float('-inf')
                probs = F.softmax(logits, dim=-1)
                idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat([idx, idx_next], dim=1)
        return idx

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


class ScratchModelManager:
    """Manages a from-scratch AI model (NO pre-trained weights).

    Builds a BPE tokenizer and Transformer from scratch, pre-trains on
    provided data, fine-tunes on domain-specific data, and runs inference.

    Usage:
        mgr = ScratchModelManager()
        mgr.pretrain(training_texts, epochs=10)
        mgr.fine_tune(domain_texts, epochs=5)
        text = mgr.generate("artificial intelligence")
    """

    def __init__(
        self,
        embed_dim: int = 128,
        num_layers: int = 4,
        num_heads: int = 4,
        max_seq_len: int = 128,
        vocab_size: int = 800,
    ) -> None:
        self.embed_dim = embed_dim
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.max_seq_len = max_seq_len
        self.tokenizer = BPETokenizer(vocab_size=vocab_size)
        self.model: ScratchGPT | None = None
        self._is_trained = False

    def build_tokenizer(self, texts: list[str]) -> None:
        """Build BPE tokenizer from scratch on the given texts."""
        self.tokenizer.train(texts)

    def build_model(self) -> ScratchGPT:
        """Build the Transformer model from scratch (random init)."""
        self.model = ScratchGPT(
            vocab_size=self.tokenizer.vocab_size_actual,
            embed_dim=self.embed_dim,
            num_layers=self.num_layers,
            num_heads=self.num_heads,
            max_seq_len=self.max_seq_len,
        )
        return self.model

    def pretrain(
        self,
        texts: list[str],
        epochs: int = 10,
        learning_rate: float = 3e-4,
        batch_size: int = 16,
        seq_len: int = 64,
    ) -> dict[str, Any]:
        """Pre-train the model from scratch.

        Args:
            texts: Training text data.
            epochs: Number of training epochs.
            learning_rate: Learning rate.
            batch_size: Mini-batch size.
            seq_len: Sequence length.

        Returns:
            Training metrics dictionary.
        """
        import numpy as np

        if self.model is None:
            self.build_tokenizer(texts)
            self.build_model()

        # Encode all text
        all_tokens: list[int] = []
        for text in texts:
            enc = self.tokenizer.encode(text)
            if len(enc) > 10:
                all_tokens.extend(enc)
                all_tokens.append(self.tokenizer.vocab["<EOS>"])

        if not all_tokens:
            return {"error": "No training data"}

        # Create sequences
        # BUG S-5 FIX: guard against seq_len < 2 (range() requires step > 0)
        if seq_len < 2:
            return {"error": f"seq_len must be >= 2, got {seq_len}"}
        sequences: list[list[int]] = []
        step = max(1, seq_len // 2)  # ensure step > 0
        for i in range(0, len(all_tokens) - seq_len - 1, step):
            sequences.append(all_tokens[i:i + seq_len + 1])

        if not sequences:
            return {"error": "No sequences generated"}

        data = torch.tensor(sequences, dtype=torch.long)
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate, weight_decay=0.01)

        self.model.train()
        all_losses: list[float] = []
        import time
        t0 = time.perf_counter()

        for epoch in range(epochs):
            perm = torch.randperm(len(data))
            epoch_losses: list[float] = []
            for i in range(0, len(data), batch_size):
                batch = data[perm[i:i + batch_size]]
                x, y = batch[:, :-1], batch[:, 1:]
                _, loss = self.model(x, targets=y)
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                epoch_losses.append(loss.item())
            avg_loss = float(np.mean(epoch_losses))
            all_losses.append(avg_loss)

        training_time = time.perf_counter() - t0
        self._is_trained = True

        return {
            "initial_loss": all_losses[0],
            "final_loss": all_losses[-1],
            "loss_reduction_pct": ((all_losses[0] - all_losses[-1]) / all_losses[0] * 100) if all_losses[0] > 0 else 0,
            "epochs": epochs,
            "training_time_seconds": training_time,
            "total_params": self.model.count_parameters(),
            "vocab_size": self.tokenizer.vocab_size_actual,
            "sequences": len(sequences),
            "pretrained": False,
        }

    def fine_tune(
        self,
        texts: list[str],
        epochs: int = 5,
        learning_rate: float = 1e-4,
        batch_size: int = 8,
        seq_len: int = 64,
    ) -> dict[str, Any]:
        """Fine-tune the pre-trained model on domain-specific data."""
        import numpy as np
        import time

        if self.model is None:
            return {"error": "Model not built. Call pretrain() first."}

        domain_encoded: list[list[int]] = []
        for text in texts:
            enc = self.tokenizer.encode(text)
            if len(enc) > 5:
                domain_encoded.append(enc)

        sequences: list[list[int]] = []
        pad_id = self.tokenizer.vocab["<PAD>"]
        for enc in domain_encoded:
            if len(enc) > seq_len:
                for i in range(0, len(enc) - seq_len, seq_len // 2):
                    sequences.append(enc[i:i + seq_len + 1])
            else:
                sequences.append(enc + [pad_id] * (seq_len + 1 - len(enc)))

        if not sequences:
            return {"error": "No sequences generated"}

        data = torch.tensor(sequences, dtype=torch.long)
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate, weight_decay=0.01)

        self.model.train()
        all_losses: list[float] = []
        t0 = time.perf_counter()

        for epoch in range(epochs):
            perm = torch.randperm(len(data))
            epoch_losses: list[float] = []
            for i in range(0, len(data), batch_size):
                batch = data[perm[i:i + batch_size]]
                x, y = batch[:, :-1], batch[:, 1:]
                _, loss = self.model(x, targets=y)
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                epoch_losses.append(loss.item())
            all_losses.append(float(np.mean(epoch_losses)))

        return {
            "initial_loss": all_losses[0],
            "final_loss": all_losses[-1],
            "loss_reduction_pct": ((all_losses[0] - all_losses[-1]) / all_losses[0] * 100) if all_losses[0] > 0 else 0,
            "epochs": epochs,
            "training_time_seconds": time.perf_counter() - t0,
        }

    def generate(self, prompt: str, max_new_tokens: int = 20, temperature: float = 0.7) -> str:
        """Generate text using the from-scratch model."""
        if self.model is None:
            return "Model not trained"
        prompt_ids = self.tokenizer.encode(prompt)
        if not prompt_ids:
            prompt_ids = [self.tokenizer.vocab.get(prompt[0] if prompt else " ", self.tokenizer.vocab["<UNK>"])]
        idx = torch.tensor([prompt_ids], dtype=torch.long)
        generated = self.model.generate(idx, max_new_tokens, temperature)
        return self.tokenizer.decode(generated[0].tolist())

    def save(self, path: str) -> None:
        """Save the model and tokenizer."""
        torch.save({
            "model_state_dict": self.model.state_dict() if self.model else None,
            "model_config": {
                "vocab_size": self.tokenizer.vocab_size_actual,
                "embed_dim": self.embed_dim,
                "num_layers": self.num_layers,
                "num_heads": self.num_heads,
                "max_seq_len": self.max_seq_len,
            },
            "tokenizer_vocab": self.tokenizer.vocab,
            "tokenizer_merges": self.tokenizer.merges,
            "pretrained": False,
        }, path)

    def load(self, path: str) -> None:
        """Load a saved model and tokenizer from disk.

        BUG S-7 FIX: Added the missing load() method to mirror save().

        Args:
            path: Path to a .pt file saved by ``save()``.
        """
        ckpt = torch.load(path, map_location="cpu", weights_only=False)
        cfg = ckpt.get("model_config", {})
        # Restore tokenizer state
        self.tokenizer.vocab = ckpt.get("tokenizer_vocab", {})
        self.tokenizer.merges = ckpt.get("tokenizer_merges", [])
        self.tokenizer.id_to_token = {idx: tok for tok, idx in self.tokenizer.vocab.items()}
        # Restore model config
        self.embed_dim = cfg.get("embed_dim", self.embed_dim)
        self.num_layers = cfg.get("num_layers", self.num_layers)
        self.num_heads = cfg.get("num_heads", self.num_heads)
        self.max_seq_len = cfg.get("max_seq_len", self.max_seq_len)
        # Rebuild model and load weights
        self.build_model()
        if ckpt.get("model_state_dict") is not None:
            self.model.load_state_dict(ckpt["model_state_dict"])
        self._is_trained = True

    def get_info(self) -> dict[str, Any]:
        """Get model information."""
        return {
            "architecture": "ScratchGPT",
            "pretrained": False,
            "total_params": self.model.count_parameters() if self.model else 0,
            "vocab_size": self.tokenizer.vocab_size_actual,
            "embed_dim": self.embed_dim,
            "num_layers": self.num_layers,
            "num_heads": self.num_heads,
            "max_seq_len": self.max_seq_len,
            "is_trained": self._is_trained,
            "device": "cpu",
        }
