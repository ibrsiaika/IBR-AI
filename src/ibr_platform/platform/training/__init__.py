"""
Model Training Pipeline (PRD Section 39).

Implements training configuration, pipeline orchestration, checkpointing,
and metrics tracking. All FREE — uses PyTorch (open source) when available
but the framework itself requires no paid APIs.

Supported techniques (PRD Section 39.2, Table 39.1):
    - Continued Pretraining
    - SFT (Supervised Fine-Tuning)
    - LoRA (Low-Rank Adaptation)
    - QLoRA (Quantized LoRA)
    - Knowledge Distillation
    - DPO (Direct Preference Optimization)
    - ORPO (Odds Ratio Preference Optimization)
    - PPO (Proximal Policy Optimization)
    - GRPO (Group Relative Policy Optimization)

References:
    - PRD Section 39 (Model Training)
    - PRD Section 52 (GRPO and DeepSeek-R1)
    - PRD Section 46 (Quantization — QLoRA)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class TrainingTechnique(StrEnum):
    """Supported training techniques (PRD Section 39.2)."""

    CONTINUED_PRETRAINING = "continued_pretraining"
    SFT = "sft"
    LORA = "lora"
    QLORA = "qlora"
    DISTILLATION = "distillation"
    DPO = "dpo"
    ORPO = "orpo"
    PPO = "ppo"
    GRPO = "grpo"


class TrainingStatus(StrEnum):
    """Status of a training job."""

    PENDING = "pending"
    RUNNING = "running"
    CHECKPOINTED = "checkpointed"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class TrainingConfig:
    """Configuration for a training job (PRD Section 39).

    Attributes:
        technique: Training technique (SFT, LoRA, QLoRA, GRPO, etc.).
        base_model: Base model ID or path.
        dataset_id: Dataset ID for training.
        output_model_name: Name for the output model.
        hyperparameters: Training hyperparameters.
        epochs: Number of training epochs.
        batch_size: Batch size.
        learning_rate: Learning rate.
        lora_rank: LoRA rank (for LoRA/QLoRA).
        lora_alpha: LoRA alpha.
        quantization: Quantization for QLoRA ("4bit", "8bit", None).
        max_seq_length: Maximum sequence length.
        gradient_accumulation_steps: Gradient accumulation steps.
        warmup_steps: Warmup steps.
        save_steps: Checkpoint interval (steps).
        eval_steps: Evaluation interval (steps).
        seed: Random seed for reproducibility.
        distributed: Whether to use distributed training.
        num_gpus: Number of GPUs (0 = CPU).
    """

    technique: TrainingTechnique = TrainingTechnique.SFT
    base_model: str = ""
    dataset_id: str = ""
    output_model_name: str = ""
    hyperparameters: dict[str, Any] = field(default_factory=dict)
    epochs: int = 3
    batch_size: int = 8
    learning_rate: float = 2e-5
    lora_rank: int = 16
    lora_alpha: int = 32
    quantization: str | None = None
    max_seq_length: int = 2048
    gradient_accumulation_steps: int = 1
    warmup_steps: int = 100
    save_steps: int = 500
    eval_steps: int = 500
    seed: int = 42
    distributed: bool = False
    num_gpus: int = 0

    def validate(self) -> list[str]:
        """Validate the config. Returns list of errors (empty = valid)."""
        errors: list[str] = []
        if not self.base_model:
            errors.append("base_model is required")
        if not self.dataset_id:
            errors.append("dataset_id is required")
        if self.technique in (TrainingTechnique.LORA, TrainingTechnique.QLORA) and self.lora_rank <= 0:
            errors.append("lora_rank must be positive for LoRA/QLoRA")
        if self.technique == TrainingTechnique.QLORA and self.quantization is None:
            errors.append("quantization is required for QLoRA (use '4bit')")
        if self.epochs <= 0:
            errors.append("epochs must be positive")
        if self.batch_size <= 0:
            errors.append("batch_size must be positive")
        return errors


@dataclass(slots=True)
class TrainingMetrics:
    """Metrics from a training run.

    Attributes:
        step: Current training step.
        epoch: Current epoch.
        loss: Current training loss.
        learning_rate: Current learning rate.
        eval_loss: Evaluation loss (if evaluated).
        eval_accuracy: Evaluation accuracy (if evaluated).
        grad_norm: Gradient norm.
        tokens_per_second: Training throughput.
        gpu_memory_used_mb: GPU memory usage.
    """

    step: int = 0
    epoch: float = 0.0
    loss: float = 0.0
    learning_rate: float = 0.0
    eval_loss: float | None = None
    eval_accuracy: float | None = None
    grad_norm: float = 0.0
    tokens_per_second: float = 0.0
    gpu_memory_used_mb: float = 0.0


@dataclass(slots=True)
class Checkpoint:
    """A training checkpoint (PRD Section 39.3).

    Attributes:
        id: Unique checkpoint ID.
        step: Training step when checkpoint was saved.
        path: Filesystem path to checkpoint.
        metrics: Metrics at checkpoint time.
        timestamp: When the checkpoint was created.
    """

    step: int = 0
    path: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metrics: TrainingMetrics = field(default_factory=TrainingMetrics)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class CheckpointManager:
    """Manages training checkpoints (PRD Section 39.3).

    Supports: save, load, list, delete checkpoints.
    Enables: preemption (save + terminate), resumption (load + continue).

    Usage:
        mgr = CheckpointManager(checkpoint_dir="/checkpoints")
        cp = mgr.save(step=500, path="/checkpoints/step_500.pt", metrics=metrics)
        loaded = mgr.load(cp.id)
        all_cps = mgr.list_checkpoints()
    """

    def __init__(self, checkpoint_dir: str = "./checkpoints") -> None:
        self._checkpoint_dir = checkpoint_dir
        self._checkpoints: dict[str, Checkpoint] = {}

    def save(
        self,
        step: int,
        path: str,
        metrics: TrainingMetrics | None = None,
    ) -> Checkpoint:
        """Save a checkpoint.

        Args:
            step: Training step.
            path: Filesystem path to checkpoint.
            metrics: Metrics at this step.

        Returns:
            The created Checkpoint.
        """
        cp = Checkpoint(
            step=step,
            path=path,
            metrics=metrics or TrainingMetrics(),
        )
        self._checkpoints[cp.id] = cp
        return cp

    def load(self, checkpoint_id: str) -> Checkpoint | None:
        """Load a checkpoint by ID.

        Args:
            checkpoint_id: The checkpoint ID.

        Returns:
            The Checkpoint, or None if not found.
        """
        return self._checkpoints.get(checkpoint_id)

    def get_latest(self) -> Checkpoint | None:
        """Get the most recent checkpoint.

        Returns:
            The latest Checkpoint, or None if no checkpoints exist.
        """
        if not self._checkpoints:
            return None
        return max(self._checkpoints.values(), key=lambda cp: cp.step)

    def list_checkpoints(self) -> list[Checkpoint]:
        """List all checkpoints, ordered by step.

        Returns:
            List of Checkpoints (ascending by step).
        """
        return sorted(self._checkpoints.values(), key=lambda cp: cp.step)

    def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint.

        Args:
            checkpoint_id: The checkpoint ID.

        Returns:
            True if deleted, False if not found.
        """
        if checkpoint_id in self._checkpoints:
            del self._checkpoints[checkpoint_id]
            return True
        return False

    @property
    def count(self) -> int:
        """Number of checkpoints."""
        return len(self._checkpoints)


class TrainingPipeline:
    """Orchestrates model training (PRD Section 39).

    Coordinates: config validation, training execution, checkpointing,
    metrics collection, and model artifact registration.

    In production, this uses PyTorch + DeepSpeed for actual training.
    The framework itself is FREE — no paid APIs.

    Usage:
        config = TrainingConfig(
            technique=TrainingTechnique.LORA,
            base_model="llama-3.2-1b",
            dataset_id="ds_123",
            lora_rank=16,
        )
        pipeline = TrainingPipeline()
        result = await pipeline.run(config)
    """

    def __init__(self) -> None:
        self._checkpoint_mgr = CheckpointManager()
        self._current_status: TrainingStatus = TrainingStatus.PENDING
        self._metrics_history: list[TrainingMetrics] = []

    @property
    def status(self) -> TrainingStatus:
        return self._current_status

    @property
    def checkpoint_manager(self) -> CheckpointManager:
        return self._checkpoint_mgr

    async def run(self, config: TrainingConfig) -> dict[str, Any]:
        """Run a training job.

        Validates config, simulates training (in production: PyTorch),
        creates checkpoints, and returns metrics.

        Args:
            config: Training configuration.

        Returns:
            Dictionary with: model_artifact_id, metrics, checkpoints, status.

        Raises:
            ValueError: If config validation fails.
        """
        # Validate config
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid training config: {errors}")

        self._current_status = TrainingStatus.RUNNING

        # Simulate training (production: PyTorch + DeepSpeed)
        total_steps = config.epochs * 100  # Simplified
        for step in range(1, total_steps + 1):
            metrics = TrainingMetrics(
                step=step,
                epoch=step / 100,
                loss=max(0.01, 2.0 * (0.95 ** step)),  # Simulated loss decay
                learning_rate=config.learning_rate,
                grad_norm=1.0,
            )
            self._metrics_history.append(metrics)

            # Save checkpoint at save_steps interval
            if step % config.save_steps == 0:
                self._checkpoint_mgr.save(
                    step=step,
                    path=f"{self._checkpoint_mgr._checkpoint_dir}/step_{step}.pt",
                    metrics=metrics,
                )

        self._current_status = TrainingStatus.COMPLETE

        # Generate model artifact ID
        model_artifact_id = f"model_{config.technique.value}_{uuid.uuid4().hex[:8]}"

        return {
            "model_artifact_id": model_artifact_id,
            "technique": config.technique.value,
            "base_model": config.base_model,
            "dataset_id": config.dataset_id,
            "status": self._current_status.value,
            "final_loss": self._metrics_history[-1].loss if self._metrics_history else 0,
            "total_steps": total_steps,
            "checkpoints": self._checkpoint_mgr.count,
            "seed": config.seed,
        }

    async def cancel(self) -> None:
        """Cancel the current training job."""
        self._current_status = TrainingStatus.CANCELLED

    def get_metrics_history(self) -> list[TrainingMetrics]:
        """Get the full metrics history.

        Returns:
            List of TrainingMetrics from all training steps.
        """
        return list(self._metrics_history)

    def __repr__(self) -> str:
        return f"<TrainingPipeline(status={self._current_status.value})>"
