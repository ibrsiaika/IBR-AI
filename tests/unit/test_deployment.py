"""Tests for Section 17 — CPU Optimization & Deployment Modes."""
from __future__ import annotations
import pytest


class TestDeploymentModes:
    """Test 4 deployment modes (PRD Section 17.1)."""

    @pytest.mark.parametrize("mode", ["TINY", "COMPACT", "PROFESSIONAL", "ENTERPRISE"])
    def test_mode_defined(self, mode: str) -> None:
        from ibr_platform.platform.deployment import DeploymentMode
        assert hasattr(DeploymentMode, mode)

    def test_mode_count(self) -> None:
        from ibr_platform.platform.deployment import DeploymentMode
        assert len(list(DeploymentMode)) == 4

    @pytest.mark.parametrize("mode,ram,max_agents", [
        ("TINY", 2048, 1),
        ("COMPACT", 8192, 5),
        ("PROFESSIONAL", 32768, 20),
        ("ENTERPRISE", 131072, 100),
    ])
    def test_mode_defaults(self, mode: str, ram: int, max_agents: int) -> None:
        from ibr_platform.platform.deployment import DeploymentMode, get_mode_config
        cfg = get_mode_config(DeploymentMode[mode])
        assert cfg.ram_budget_mb == ram
        assert cfg.max_concurrent_agents == max_agents

    @pytest.mark.parametrize("mode,model_size", [
        ("TINY", "125M-1B"),
        ("COMPACT", "1B-3B"),
        ("PROFESSIONAL", "7B-13B"),
        ("ENTERPRISE", "70B+"),
    ])
    def test_mode_model_size(self, mode: str, model_size: str) -> None:
        from ibr_platform.platform.deployment import DeploymentMode, get_mode_config
        cfg = get_mode_config(DeploymentMode[mode])
        assert cfg.model_size_range == model_size

    @pytest.mark.parametrize("mode,engine", [
        ("TINY", "llama.cpp"),
        ("COMPACT", "llama.cpp"),
        ("PROFESSIONAL", "vllm"),
        ("ENTERPRISE", "vllm"),
    ])
    def test_mode_inference_engine(self, mode: str, engine: str) -> None:
        from ibr_platform.platform.deployment import DeploymentMode, get_mode_config
        cfg = get_mode_config(DeploymentMode[mode])
        assert cfg.inference_engine == engine

    def test_tiny_mode_gpu_disabled(self) -> None:
        from ibr_platform.platform.deployment import DeploymentMode, get_mode_config
        cfg = get_mode_config(DeploymentMode.TINY)
        assert cfg.gpu_enabled is False

    def test_enterprise_mode_gpu_enabled(self) -> None:
        from ibr_platform.platform.deployment import DeploymentMode, get_mode_config
        cfg = get_mode_config(DeploymentMode.ENTERPRISE)
        assert cfg.gpu_enabled is True

    def test_tiny_mode_training_disabled(self) -> None:
        from ibr_platform.platform.deployment import DeploymentMode, get_mode_config
        cfg = get_mode_config(DeploymentMode.TINY)
        assert cfg.training_enabled is False

    def test_enterprise_mode_training_enabled(self) -> None:
        from ibr_platform.platform.deployment import DeploymentMode, get_mode_config
        cfg = get_mode_config(DeploymentMode.ENTERPRISE)
        assert cfg.training_enabled is True


class TestCPUOptimization:
    """Test CPU optimization settings (PRD Section 17.2)."""

    def test_cpu_config_importable(self) -> None:
        from ibr_platform.platform.deployment import CPUOptimizationConfig
        assert CPUOptimizationConfig is not None

    def test_cpu_config_defaults(self) -> None:
        from ibr_platform.platform.deployment import CPUOptimizationConfig
        cfg = CPUOptimizationConfig()
        assert cfg.simd_enabled is True  # AVX2/AVX-512
        assert cfg.lazy_loading is True
        assert cfg.incremental_computation is True
        assert cfg.cache_layers >= 1

    def test_cpu_config_quantization_default(self) -> None:
        from ibr_platform.platform.deployment import CPUOptimizationConfig
        cfg = CPUOptimizationConfig()
        assert cfg.default_quantization in ("int4", "int8", "q4_k_m")


class TestDeploymentManager:
    """Test the DeploymentManager."""

    def test_manager_importable(self) -> None:
        from ibr_platform.platform.deployment import DeploymentManager
        assert DeploymentManager is not None

    def test_manager_instantiable(self) -> None:
        from ibr_platform.platform.deployment import DeploymentManager
        mgr = DeploymentManager()
        assert mgr is not None

    def test_manager_get_config(self) -> None:
        from ibr_platform.platform.deployment import DeploymentManager, DeploymentMode
        mgr = DeploymentManager(DeploymentMode.TINY)
        cfg = mgr.config
        assert cfg.ram_budget_mb == 2048

    def test_manager_check_ram_budget(self) -> None:
        from ibr_platform.platform.deployment import DeploymentManager, DeploymentMode
        mgr = DeploymentManager(DeploymentMode.TINY)
        # 1GB model fits in 2GB budget
        assert mgr.check_ram_budget(1024) is True
        # 3GB model exceeds 2GB budget
        assert mgr.check_ram_budget(3072) is False

    def test_manager_recommended_model_size(self) -> None:
        from ibr_platform.platform.deployment import DeploymentManager, DeploymentMode
        mgr = DeploymentManager(DeploymentMode.TINY)
        size = mgr.get_recommended_model_size()
        assert "125M" in size or "1B" in size

    def test_manager_health_check(self) -> None:
        from ibr_platform.platform.deployment import DeploymentManager, DeploymentMode
        mgr = DeploymentManager(DeploymentMode.TINY)
        health = mgr.health_check()
        assert "status" in health
        assert "mode" in health
