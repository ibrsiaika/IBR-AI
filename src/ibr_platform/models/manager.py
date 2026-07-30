"""
Real Model Manager — Downloads, loads, fine-tunes, and runs inference
with REAL pre-trained models from HuggingFace (FREE, open source).

This is NOT a simulation — actual model weights are downloaded and
actual PyTorch training occurs with real loss computation.

Supported models (all FREE, all CPU-compatible):
    - distilgpt2 (85M params, ~313MB, Apache 2.0) — DEFAULT
    - gpt2 (124M params, ~499MB, MIT) — larger but still CPU-feasible
    - sshleifer/tiny-gpt2 (smallest, for testing)

References:
    - PRD Section 39 (Model Training)
    - PRD Section 46 (Model Compression)
    - PRD Section 89 (CPU-First Deep Dive)
    - PRD Section 100 (Low-Resource Inference)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import torch

# BUG M-1 FIX: Lazy import of transformers — only required when RealModelManager
# is actually instantiated. This allows the package to be imported without the
# heavy `transformers` dependency (it's an optional [ml] extra).
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    _HAS_TRANSFORMERS = True
except ImportError:
    AutoModelForCausalLM = None  # type: ignore[assignment,misc]
    AutoTokenizer = None  # type: ignore[assignment,misc]
    _HAS_TRANSFORMERS = False


@dataclass(slots=True)
class InferenceResult:
    """Result of a real model inference.

    Attributes:
        text: Generated text.
        prompt: Input prompt.
        tokens_generated: Number of tokens generated.
        inference_time_seconds: Wall-clock time.
        tokens_per_second: Throughput.
        model_name: Model used.
    """

    text: str = ""
    prompt: str = ""
    tokens_generated: int = 0
    inference_time_seconds: float = 0.0
    tokens_per_second: float = 0.0
    model_name: str = ""


@dataclass(slots=True)
class FineTuningResult:
    """Result of a real fine-tuning run.

    Attributes:
        initial_loss: Loss at epoch 1.
        final_loss: Loss at final epoch.
        loss_reduction_pct: Percentage reduction in loss.
        epochs: Number of epochs trained.
        training_examples: Number of training examples.
        training_time_seconds: Wall-clock training time.
        model_name: Model fine-tuned.
    """

    initial_loss: float = 0.0
    final_loss: float = 0.0
    loss_reduction_pct: float = 0.0
    epochs: int = 0
    training_examples: int = 0
    training_time_seconds: float = 0.0
    model_name: str = ""


class RealModelManager:
    """Manages real pre-trained models (FREE, from HuggingFace).

    Downloads actual model weights, runs real inference, and performs
    real fine-tuning with PyTorch. All on CPU — no GPU required.

    Usage:
        mgr = RealModelManager()  # Downloads distilgpt2
        result = mgr.generate("Hello, world!")
        ft_result = mgr.fine_tune(["Training text 1", "Training text 2"])
    """

    def __init__(self, model_name: str = "distilgpt2") -> None:
        """Initialize and download the model.

        Args:
            model_name: HuggingFace model name (default: distilgpt2).

        Raises:
            ImportError: If the `transformers` package is not installed.
                Install with: pip install 'ibr-platform[ml]'
        """
        if not _HAS_TRANSFORMERS:
            raise ImportError(
                "RealModelManager requires the 'transformers' package. "
                "Install it with: pip install 'ibr-platform[ml]' "
                "or: pip install transformers torch"
            )
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self._total_params = sum(p.numel() for p in self.model.parameters())

    @property
    def total_params(self) -> int:
        """Total number of model parameters."""
        return self._total_params

    @property
    def model_size_mb(self) -> float:
        """Model size in MB (FP32)."""
        return self._total_params * 4 / 1024 / 1024

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 30,
        temperature: float = 0.7,
    ) -> InferenceResult:
        """Generate text using the real model.

        Args:
            prompt: Input prompt.
            max_new_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (0=greedy, 1=creative).

        Returns:
            InferenceResult with generated text and metrics.
        """
        self.model.eval()
        inputs = self.tokenizer(prompt, return_tensors="pt")

        t0 = time.perf_counter()
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id,
            )
        elapsed = time.perf_counter() - t0

        text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        tokens_generated = len(outputs[0]) - len(inputs["input_ids"][0])

        return InferenceResult(
            text=text,
            prompt=prompt,
            tokens_generated=tokens_generated,
            inference_time_seconds=elapsed,
            tokens_per_second=tokens_generated / elapsed if elapsed > 0 else 0,
            model_name=self.model_name,
        )

    def fine_tune(
        self,
        training_texts: list[str],
        epochs: int = 3,
        learning_rate: float = 5e-5,
        batch_size: int = 4,
        max_length: int = 64,
    ) -> FineTuningResult:
        """Fine-tune the model with real PyTorch training.

        Performs Supervised Fine-Tuning (SFT) with AdamW optimizer.
        Real loss computation, real backpropagation, real weight updates.

        Args:
            training_texts: List of training text strings.
            epochs: Number of training epochs.
            learning_rate: Learning rate.
            batch_size: Mini-batch size.
            max_length: Maximum sequence length.

        Returns:
            FineTuningResult with training metrics.
        """
        import numpy as np

        self.model.train()
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate)

        all_losses: list[float] = []
        t0 = time.perf_counter()

        for epoch in range(epochs):
            epoch_losses: list[float] = []

            for i in range(0, len(training_texts), batch_size):
                batch = training_texts[i:i + batch_size]
                encodings = self.tokenizer(
                    batch,
                    truncation=True,
                    padding=True,
                    max_length=max_length,
                    return_tensors="pt",
                )

                outputs = self.model(**encodings, labels=encodings["input_ids"])
                loss = outputs.loss

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                epoch_losses.append(loss.item())

            avg_loss = float(np.mean(epoch_losses))
            all_losses.append(avg_loss)

        training_time = time.perf_counter() - t0
        initial = all_losses[0] if all_losses else 0.0
        final = all_losses[-1] if all_losses else 0.0
        reduction = ((initial - final) / initial * 100) if initial > 0 else 0.0

        return FineTuningResult(
            initial_loss=initial,
            final_loss=final,
            loss_reduction_pct=reduction,
            epochs=epochs,
            training_examples=len(training_texts),
            training_time_seconds=training_time,
            model_name=self.model_name,
        )

    def benchmark(self, prompt: str = "Test", num_runs: int = 5) -> dict[str, float]:
        """Benchmark inference performance.

        Args:
            prompt: Test prompt.
            num_runs: Number of benchmark runs.

        Returns:
            Dictionary with avg_ms, p99_ms, tokens_per_sec.
        """
        import numpy as np

        self.model.eval()
        inputs = self.tokenizer(prompt, return_tensors="pt")
        times: list[float] = []

        for _ in range(num_runs):
            t0 = time.perf_counter()
            with torch.no_grad():
                _ = self.model.generate(
                    **inputs,
                    max_new_tokens=10,
                    do_sample=False,
                    pad_token_id=self.tokenizer.pad_token_id,
                )
            times.append(time.perf_counter() - t0)

        avg = float(np.mean(times))
        p99 = float(np.percentile(times, 99))

        return {
            "avg_ms": avg * 1000,
            "p99_ms": p99 * 1000,
            "tokens_per_sec": 10 / avg if avg > 0 else 0,
            "num_runs": num_runs,
        }

    def get_model_info(self) -> dict[str, Any]:
        """Get model information.

        Returns:
            Dictionary with model name, params, size, etc.
        """
        return {
            "model_name": self.model_name,
            "total_params": self._total_params,
            "model_size_mb": round(self.model_size_mb, 2),
            "device": "cpu",
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
        }

    def __repr__(self) -> str:
        return f"<RealModelManager(model={self.model_name}, params={self._total_params:,})>"
