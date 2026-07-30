"""
Tests for Real Model Manager — uses REAL distilgpt2 model.

These tests download actual model weights from HuggingFace (FREE) and
perform real inference and fine-tuning. NOT simulations.

Run: pytest tests/unit/test_real_model.py -v --timeout=120

Note: First run downloads the model (~313MB) and caches it.
Subsequent runs use the cached version.

These tests require the optional `transformers` and `torch` packages.
Install with: pip install 'ibr-platform[ml]'
If transformers is not installed, all tests in this module are skipped.
"""
from __future__ import annotations

import pytest

# Skip entire module if transformers is not installed
transformers = pytest.importorskip("transformers")
torch = pytest.importorskip("torch")


class TestRealModelManager:
    """Test the RealModelManager with actual distilgpt2 model."""

    @pytest.fixture(scope="class")
    def model_mgr(self):
        """Load the real model (downloads once, cached for all tests)."""
        from ibr_platform.models import RealModelManager
        return RealModelManager("distilgpt2")

    def test_model_loaded(self, model_mgr) -> None:
        """Model is loaded with correct parameters."""
        assert model_mgr.model_name == "distilgpt2"
        assert model_mgr.total_params > 80_000_000  # ~85M params
        assert model_mgr.model_size_mb > 300  # ~313MB

    def test_model_info(self, model_mgr) -> None:
        """get_model_info returns correct information."""
        info = model_mgr.get_model_info()
        assert info["model_name"] == "distilgpt2"
        assert info["total_params"] > 80_000_000
        assert info["device"] == "cpu"
        assert "torch_version" in info

    def test_generate_returns_text(self, model_mgr) -> None:
        """generate() returns real generated text."""
        result = model_mgr.generate("Hello", max_new_tokens=10, temperature=0.0)
        assert len(result.text) > 0
        assert "Hello" in result.text
        assert result.tokens_generated == 10
        assert result.tokens_per_second > 0

    def test_generate_different_prompts(self, model_mgr) -> None:
        """Different prompts produce different outputs."""
        r1 = model_mgr.generate("The sky is", max_new_tokens=10, temperature=0.7)
        r2 = model_mgr.generate("The ocean is", max_new_tokens=10, temperature=0.7)
        assert r1.text != r2.text

    def test_fine_tune_reduces_loss(self, model_mgr) -> None:
        """Fine-tuning actually reduces the loss."""
        training_texts = [
            "The IBR Platform is an autonomous AI research system.",
            "Machine learning models learn patterns from data.",
            "Python is a versatile programming language.",
            "Transformers are powerful neural network architectures.",
        ]
        result = model_mgr.fine_tune(training_texts, epochs=2, learning_rate=5e-5)
        assert result.initial_loss > result.final_loss
        assert result.loss_reduction_pct > 0
        assert result.epochs == 2
        assert result.training_examples == 4

    def test_benchmark(self, model_mgr) -> None:
        """benchmark() returns performance metrics."""
        bench = model_mgr.benchmark("Test prompt", num_runs=3)
        assert bench["avg_ms"] > 0
        assert bench["p99_ms"] >= bench["avg_ms"]
        assert bench["tokens_per_sec"] > 0
        assert bench["num_runs"] == 3

    def test_inference_is_real(self, model_mgr) -> None:
        """Inference produces actual readable text (not empty or garbage)."""
        result = model_mgr.generate("Once upon a time", max_new_tokens=20, temperature=0.5)
        # Should contain actual words
        words = result.text.split()
        assert len(words) > 3
        # Should be mostly alphabetic
        alpha_ratio = sum(c.isalpha() or c.isspace() for c in result.text) / len(result.text)
        assert alpha_ratio > 0.7
