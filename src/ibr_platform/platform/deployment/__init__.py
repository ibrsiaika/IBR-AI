"""
CPU Optimization & Deployment Modes (PRD Section 17).

Implements 4 deployment modes with CPU-first optimization:
    - TINY: Laptop (4-8 GB RAM), 125M-1B model, llama.cpp
    - COMPACT: Workstation (16-32 GB RAM), 1B-3B model, llama.cpp/vLLM
    - PROFESSIONAL: Server (64-128 GB RAM), 7B-13B model, vLLM
    - ENTERPRISE: Cluster (256+ GB RAM), 70B+ model, vLLM+TensorParallel

All FREE — no paid deployment tools, no paid cloud services required.

References:
    - PRD Section 17 (CPU Optimization & Deployment Modes)
    - PRD Section 89 (CPU-First Deep Dive)
    - PRD Section 100 (Low-Resource Inference — llama.cpp, MLC-LLM, PowerInfer)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class DeploymentMode(StrEnum):
    """4 deployment modes (PRD Section 17.1)."""

    TINY = "tiny"
    COMPACT = "compact"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass(slots=True)
class ModeConfig:
    """Configuration for a deployment mode (PRD Section 17.1, Table 17.1).

    Attributes:
        mode: The deployment mode.
        ram_budget_mb: Maximum RAM budget in MB.
        max_concurrent_agents: Maximum concurrent agent workers.
        model_size_range: Recommended model size range.
        inference_engine: Recommended inference engine (free).
        gpu_enabled: Whether GPU is available/enabled.
        training_enabled: Whether training is supported.
        distributed: Whether distributed mode is enabled.
        quantization: Default quantization for this mode.
        target_hardware: Target hardware description.
        max_concurrency: Maximum concurrent users.
    """

    mode: DeploymentMode = DeploymentMode.TINY
    ram_budget_mb: int = 2048
    max_concurrent_agents: int = 1
    model_size_range: str = "125M-1B"
    inference_engine: str = "llama.cpp"
    gpu_enabled: bool = False
    training_enabled: bool = False
    distributed: bool = False
    quantization: str = "q4_k_m"
    target_hardware: str = "Laptop (4-8 GB RAM)"
    max_concurrency: str = "1 user"


@dataclass(slots=True)
class CPUOptimizationConfig:
    """CPU optimization settings (PRD Section 17.2).

    Attributes:
        simd_enabled: Use AVX2/AVX-512/NEON SIMD instructions.
        lazy_loading: Load components on first use, not at startup.
        incremental_computation: Update aggregations incrementally.
        cache_layers: Number of cache layers (L1 in-process, L2 Redis, L3 disk).
        background_processing: Yield to foreground work.
        disk_io_streaming: Use streaming for disk-bound operations.
        default_quantization: Default quantization format.
        max_cpu_percent: Maximum CPU usage before throttling.
        startup_timeout_seconds: Cold-start timeout.
    """

    simd_enabled: bool = True
    lazy_loading: bool = True
    incremental_computation: bool = True
    cache_layers: int = 3
    background_processing: bool = True
    disk_io_streaming: bool = True
    default_quantization: str = "q4_k_m"
    max_cpu_percent: int = 80
    startup_timeout_seconds: int = 30


# Mode configurations (PRD Section 17.1, Table 17.1)
_MODE_CONFIGS: dict[DeploymentMode, ModeConfig] = {
    DeploymentMode.TINY: ModeConfig(
        mode=DeploymentMode.TINY,
        ram_budget_mb=2048,
        max_concurrent_agents=1,
        model_size_range="125M-1B",
        inference_engine="llama.cpp",
        gpu_enabled=False,
        training_enabled=False,
        distributed=False,
        quantization="q4_k_m",
        target_hardware="Laptop (4-8 GB RAM)",
        max_concurrency="1 user",
    ),
    DeploymentMode.COMPACT: ModeConfig(
        mode=DeploymentMode.COMPACT,
        ram_budget_mb=8192,
        max_concurrent_agents=5,
        model_size_range="1B-3B",
        inference_engine="llama.cpp",
        gpu_enabled=False,
        training_enabled=True,
        distributed=False,
        quantization="q4_k_m",
        target_hardware="Workstation (16-32 GB RAM)",
        max_concurrency="5 users",
    ),
    DeploymentMode.PROFESSIONAL: ModeConfig(
        mode=DeploymentMode.PROFESSIONAL,
        ram_budget_mb=32768,
        max_concurrent_agents=20,
        model_size_range="7B-13B",
        inference_engine="vllm",
        gpu_enabled=True,
        training_enabled=True,
        distributed=False,
        quantization="int8",
        target_hardware="Server (64-128 GB RAM)",
        max_concurrency="50 users",
    ),
    DeploymentMode.ENTERPRISE: ModeConfig(
        mode=DeploymentMode.ENTERPRISE,
        ram_budget_mb=131072,
        max_concurrent_agents=100,
        model_size_range="70B+",
        inference_engine="vllm",
        gpu_enabled=True,
        training_enabled=True,
        distributed=True,
        quantization="int8",
        target_hardware="Cluster (256+ GB RAM, multi-GPU)",
        max_concurrency="500+ users",
    ),
}


def get_mode_config(mode: DeploymentMode) -> ModeConfig:
    """Get configuration for a deployment mode.

    Args:
        mode: The deployment mode.

    Returns:
        ModeConfig for the requested mode.
    """
    return _MODE_CONFIGS[mode]


class DeploymentManager:
    """Manages deployment configuration and validation (PRD Section 17).

    Usage:
        mgr = DeploymentManager(DeploymentMode.TINY)
        if mgr.check_ram_budget(1024):
            # Model fits in RAM budget
            ...
        model_size = mgr.get_recommended_model_size()
    """

    def __init__(self, mode: DeploymentMode = DeploymentMode.TINY) -> None:
        self._mode = mode
        self._config = get_mode_config(mode)
        self._cpu_config = CPUOptimizationConfig()

    @property
    def mode(self) -> DeploymentMode:
        return self._mode

    @property
    def config(self) -> ModeConfig:
        return self._config

    @property
    def cpu_config(self) -> CPUOptimizationConfig:
        return self._cpu_config

    def check_ram_budget(self, required_mb: int) -> bool:
        """Check if a model fits within the RAM budget.

        Args:
            required_mb: Required memory in MB.

        Returns:
            True if the model fits, False otherwise.
        """
        return required_mb <= self._config.ram_budget_mb

    def get_recommended_model_size(self) -> str:
        """Get the recommended model size range for this mode.

        Returns:
            Model size range string (e.g., "125M-1B").
        """
        return self._config.model_size_range

    def get_recommended_engine(self) -> str:
        """Get the recommended inference engine for this mode.

        Returns:
            Engine name (e.g., "llama.cpp", "vllm").
        """
        return self._config.inference_engine

    def supports_gpu(self) -> bool:
        """Check if this mode supports GPU acceleration.

        Returns:
            True if GPU is enabled for this mode.
        """
        return self._config.gpu_enabled

    def supports_training(self) -> bool:
        """Check if this mode supports model training.

        Returns:
            True if training is enabled for this mode.
        """
        return self._config.training_enabled

    def health_check(self) -> dict[str, Any]:
        """Get deployment health status.

        Returns:
            Dictionary with: status, mode, ram_budget, engine, gpu, training.
        """
        return {
            "status": "healthy",
            "mode": self._mode.value,
            "ram_budget_mb": self._config.ram_budget_mb,
            "inference_engine": self._config.inference_engine,
            "gpu_enabled": self._config.gpu_enabled,
            "training_enabled": self._config.training_enabled,
            "model_size_range": self._config.model_size_range,
            "max_concurrent_agents": self._config.max_concurrent_agents,
            "quantization": self._config.quantization,
        }

    def __repr__(self) -> str:
        return (
            f"<DeploymentManager(mode={self._mode.value}, "
            f"ram={self._config.ram_budget_mb}MB, engine={self._config.inference_engine})>"
        )
