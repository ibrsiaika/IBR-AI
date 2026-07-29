"""Tests for Section 39 — Model Training Pipeline."""
from __future__ import annotations

import pytest


class TestTrainingConfig:
    def test_config_importable(self) -> None:
        from ibr_platform.platform.training import TrainingConfig
        assert TrainingConfig is not None

    def test_config_validate_valid(self) -> None:
        from ibr_platform.platform.training import TrainingConfig, TrainingTechnique
        config = TrainingConfig(
            technique=TrainingTechnique.SFT,
            base_model="llama-3.2-1b",
            dataset_id="ds_123",
        )
        errors = config.validate()
        assert len(errors) == 0

    def test_config_validate_missing_model(self) -> None:
        from ibr_platform.platform.training import TrainingConfig
        config = TrainingConfig(dataset_id="ds_123")
        errors = config.validate()
        assert any("base_model" in e for e in errors)

    def test_config_validate_qlora_needs_quantization(self) -> None:
        from ibr_platform.platform.training import TrainingConfig, TrainingTechnique
        config = TrainingConfig(
            technique=TrainingTechnique.QLORA,
            base_model="llama-3.2-1b",
            dataset_id="ds_123",
        )
        errors = config.validate()
        assert any("quantization" in e for e in errors)

    def test_techniques_defined(self) -> None:
        from ibr_platform.platform.training import TrainingTechnique
        assert hasattr(TrainingTechnique, "SFT")
        assert hasattr(TrainingTechnique, "LORA")
        assert hasattr(TrainingTechnique, "QLORA")
        assert hasattr(TrainingTechnique, "GRPO")
        assert hasattr(TrainingTechnique, "DPO")


class TestCheckpointManager:
    def test_checkpoint_mgr_importable(self) -> None:
        from ibr_platform.platform.training import CheckpointManager
        assert CheckpointManager is not None

    def test_save_and_load(self) -> None:
        from ibr_platform.platform.training import CheckpointManager
        mgr = CheckpointManager()
        cp = mgr.save(step=100, path="/tmp/cp_100.pt")
        loaded = mgr.load(cp.id)
        assert loaded is not None
        assert loaded.step == 100

    def test_get_latest(self) -> None:
        from ibr_platform.platform.training import CheckpointManager
        mgr = CheckpointManager()
        mgr.save(step=100, path="/tmp/cp1")
        mgr.save(step=500, path="/tmp/cp2")
        mgr.save(step=300, path="/tmp/cp3")
        latest = mgr.get_latest()
        assert latest.step == 500

    def test_list_checkpoints(self) -> None:
        from ibr_platform.platform.training import CheckpointManager
        mgr = CheckpointManager()
        mgr.save(step=100, path="/cp1")
        mgr.save(step=200, path="/cp2")
        cps = mgr.list_checkpoints()
        assert len(cps) == 2
        assert cps[0].step <= cps[1].step

    def test_delete(self) -> None:
        from ibr_platform.platform.training import CheckpointManager
        mgr = CheckpointManager()
        cp = mgr.save(step=100, path="/cp1")
        assert mgr.delete(cp.id) is True
        assert mgr.load(cp.id) is None


class TestTrainingPipeline:
    def test_pipeline_importable(self) -> None:
        from ibr_platform.platform.training import TrainingPipeline
        assert TrainingPipeline is not None

    def test_pipeline_instantiable(self) -> None:
        from ibr_platform.platform.training import TrainingPipeline
        pipeline = TrainingPipeline()
        assert pipeline is not None

    async def test_pipeline_run_sft(self) -> None:
        from ibr_platform.platform.training import (
            TrainingConfig,
            TrainingPipeline,
            TrainingStatus,
            TrainingTechnique,
        )
        config = TrainingConfig(
            technique=TrainingTechnique.SFT,
            base_model="test-model",
            dataset_id="ds_1",
            epochs=1,
            save_steps=50,
        )
        pipeline = TrainingPipeline()
        result = await pipeline.run(config)
        assert result["status"] == TrainingStatus.COMPLETE.value
        assert "model_artifact_id" in result
        assert result["technique"] == "sft"

    async def test_pipeline_run_lora(self) -> None:
        from ibr_platform.platform.training import (
            TrainingConfig,
            TrainingPipeline,
            TrainingTechnique,
        )
        config = TrainingConfig(
            technique=TrainingTechnique.LORA,
            base_model="test-model",
            dataset_id="ds_1",
            epochs=1,
            lora_rank=8,
            save_steps=50,
        )
        pipeline = TrainingPipeline()
        result = await pipeline.run(config)
        assert result["technique"] == "lora"

    async def test_pipeline_invalid_config_raises(self) -> None:
        from ibr_platform.platform.training import TrainingConfig, TrainingPipeline
        config = TrainingConfig()  # Missing required fields
        pipeline = TrainingPipeline()
        with pytest.raises(ValueError):
            await pipeline.run(config)

    async def test_pipeline_creates_checkpoints(self) -> None:
        from ibr_platform.platform.training import (
            TrainingConfig,
            TrainingPipeline,
            TrainingTechnique,
        )
        config = TrainingConfig(
            technique=TrainingTechnique.SFT,
            base_model="test-model",
            dataset_id="ds_1",
            epochs=1,
            save_steps=50,
        )
        pipeline = TrainingPipeline()
        await pipeline.run(config)
        assert pipeline.checkpoint_manager.count > 0

    async def test_pipeline_metrics_history(self) -> None:
        from ibr_platform.platform.training import (
            TrainingConfig,
            TrainingPipeline,
            TrainingTechnique,
        )
        config = TrainingConfig(
            technique=TrainingTechnique.SFT,
            base_model="test-model",
            dataset_id="ds_1",
            epochs=1,
            save_steps=100,
        )
        pipeline = TrainingPipeline()
        await pipeline.run(config)
        history = pipeline.get_metrics_history()
        assert len(history) > 0
        # Loss should decrease
        assert history[-1].loss < history[0].loss
