"""Tests for From-Scratch AI (ScratchGPT — NO pre-trained weights)."""
from __future__ import annotations
import pytest
import torch


class TestBPETokenizer:
    def test_importable(self) -> None:
        from ibr_platform.models.scratch import BPETokenizer
        assert BPETokenizer is not None

    def test_train(self) -> None:
        from ibr_platform.models.scratch import BPETokenizer
        tok = BPETokenizer(vocab_size=100)
        tok.train(["hello world", "hello there", "world peace"])
        assert tok.vocab_size_actual > 10  # At least chars + some merges

    def test_encode_decode(self) -> None:
        from ibr_platform.models.scratch import BPETokenizer
        tok = BPETokenizer(vocab_size=100)
        tok.train(["hello world hello"])
        ids = tok.encode("hello")
        assert len(ids) > 0
        decoded = tok.decode(ids)
        assert "hello" in decoded or "h" in decoded  # At least partial decode


class TestScratchGPT:
    def test_importable(self) -> None:
        from ibr_platform.models.scratch import ScratchGPT
        assert ScratchGPT is not None

    def test_model_creation(self) -> None:
        from ibr_platform.models.scratch import ScratchGPT
        model = ScratchGPT(vocab_size=100, embed_dim=64, num_layers=2, num_heads=4, max_seq_len=32)
        assert model.count_parameters() > 0
        assert model.vocab_size == 100

    def test_forward_pass(self) -> None:
        from ibr_platform.models.scratch import ScratchGPT
        model = ScratchGPT(vocab_size=100, embed_dim=64, num_layers=2, num_heads=4, max_seq_len=32)
        x = torch.randint(0, 100, (2, 10))  # batch=2, seq=10
        logits, loss = model(x, targets=x)
        assert logits.shape == (2, 10, 100)
        assert loss is not None
        assert loss.item() > 0  # Random init should have positive loss

    def test_generate(self) -> None:
        from ibr_platform.models.scratch import ScratchGPT
        model = ScratchGPT(vocab_size=100, embed_dim=64, num_layers=2, num_heads=4, max_seq_len=32)
        idx = torch.tensor([[1, 2, 3]], dtype=torch.long)
        generated = model.generate(idx, max_new_tokens=5, temperature=0.5)
        assert generated.shape == (1, 8)  # 3 input + 5 generated

    def test_not_pretrained(self) -> None:
        """Model weights are randomly initialized (NOT pre-trained)."""
        from ibr_platform.models.scratch import ScratchGPT
        model1 = ScratchGPT(vocab_size=100, embed_dim=64, num_layers=2, num_heads=4, max_seq_len=32)
        model2 = ScratchGPT(vocab_size=100, embed_dim=64, num_layers=2, num_heads=4, max_seq_len=32)
        # Two randomly initialized models should have different weights
        w1 = model1.token_embedding.weight[0, 0].item()
        w2 = model2.token_embedding.weight[0, 0].item()
        assert w1 != w2  # Different random init


class TestScratchModelManager:
    def test_importable(self) -> None:
        from ibr_platform.models.scratch import ScratchModelManager
        assert ScratchModelManager is not None

    def test_instantiable(self) -> None:
        from ibr_platform.models.scratch import ScratchModelManager
        mgr = ScratchModelManager(embed_dim=64, num_layers=2, num_heads=4, max_seq_len=32, vocab_size=100)
        assert mgr is not None

    def test_pretrain_reduces_loss(self) -> None:
        from ibr_platform.models.scratch import ScratchModelManager
        mgr = ScratchModelManager(embed_dim=64, num_layers=2, num_heads=4, max_seq_len=32, vocab_size=100)
        texts = [
            "artificial intelligence is the future of technology",
            "machine learning models learn from data",
            "neural networks are inspired by the human brain",
            "deep learning uses multiple layers of neurons",
            "transformers use attention mechanisms for processing",
        ]
        result = mgr.pretrain(texts, epochs=3, learning_rate=3e-4, batch_size=4, seq_len=16)
        assert result["initial_loss"] > result["final_loss"]
        assert result["loss_reduction_pct"] > 0
        assert result["pretrained"] is False

    def test_fine_tune_reduces_loss(self) -> None:
        from ibr_platform.models.scratch import ScratchModelManager
        mgr = ScratchModelManager(embed_dim=64, num_layers=2, num_heads=4, max_seq_len=32, vocab_size=100)
        # Pre-train first
        mgr.pretrain(["hello world this is a test of the model"], epochs=2, seq_len=16)
        # Fine-tune
        ft_texts = ["the ibr platform is an autonomous ai system", "cpu first deployment enables accessible ai"]
        result = mgr.fine_tune(ft_texts, epochs=3, seq_len=16)
        assert result["initial_loss"] > result["final_loss"]

    def test_generate_returns_text(self) -> None:
        from ibr_platform.models.scratch import ScratchModelManager
        mgr = ScratchModelManager(embed_dim=64, num_layers=2, num_heads=4, max_seq_len=32, vocab_size=100)
        mgr.pretrain(["hello world this is a test"], epochs=2, seq_len=16)
        text = mgr.generate("hello", max_new_tokens=5)
        assert len(text) > 0

    def test_get_info(self) -> None:
        from ibr_platform.models.scratch import ScratchModelManager
        mgr = ScratchModelManager(embed_dim=64, num_layers=2, num_heads=4, max_seq_len=32, vocab_size=100)
        mgr.pretrain(["test data for model that is long enough to create sequences"], epochs=1, seq_len=8)
        info = mgr.get_info()
        assert info["architecture"] == "ScratchGPT"
        assert info["pretrained"] is False
        assert info["total_params"] > 0
        assert info["is_trained"] is True

    def test_save_model(self, tmp_path) -> None:
        from ibr_platform.models.scratch import ScratchModelManager
        mgr = ScratchModelManager(embed_dim=64, num_layers=2, num_heads=4, max_seq_len=32, vocab_size=100)
        mgr.pretrain(["test data"], epochs=1, seq_len=16)
        path = str(tmp_path / "test_model.pt")
        mgr.save(path)
        import os
        assert os.path.exists(path)
