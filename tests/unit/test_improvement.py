"""Tests for Section 40 — Self-Improvement Loop."""
from __future__ import annotations

import pytest


class TestSelfImprovementLoop:
    def test_importable(self) -> None:
        from ibr_platform.platform.improvement import SelfImprovementLoop
        assert SelfImprovementLoop is not None

    def test_report_failure(self) -> None:
        from ibr_platform.platform.improvement import FailureCategory, SelfImprovementLoop
        loop = SelfImprovementLoop()
        f = loop.report_failure(FailureCategory.KNOWLEDGE_GAP, "Model doesn't know X")
        assert f.category == FailureCategory.KNOWLEDGE_GAP
        assert f.description == "Model doesn't know X"

    def test_generate_hypothesis_auto(self) -> None:
        from ibr_platform.platform.improvement import FailureCategory, SelfImprovementLoop
        loop = SelfImprovementLoop()
        f = loop.report_failure(FailureCategory.REASONING_ERROR, "Wrong reasoning")
        h = loop.generate_hypothesis(f)
        assert h.failure_id == f.id
        assert len(h.root_cause) > 0
        assert len(h.proposed_fix) > 0

    def test_design_experiment(self) -> None:
        from ibr_platform.platform.improvement import (
            ExperimentStatus,
            FailureCategory,
            SelfImprovementLoop,
        )
        loop = SelfImprovementLoop()
        f = loop.report_failure(FailureCategory.KNOWLEDGE_GAP, "Missing info")
        h = loop.generate_hypothesis(f)
        exp = loop.design_experiment(h)
        assert exp.status == ExperimentStatus.PROPOSED
        assert exp.hypothesis_id == h.id

    def test_approve_experiment(self) -> None:
        from ibr_platform.platform.improvement import (
            ExperimentStatus,
            FailureCategory,
            SelfImprovementLoop,
        )
        loop = SelfImprovementLoop()
        f = loop.report_failure(FailureCategory.KNOWLEDGE_GAP, "test")
        h = loop.generate_hypothesis(f)
        exp = loop.design_experiment(h)
        assert loop.approve_experiment(exp.id, "admin") is True
        assert exp.status == ExperimentStatus.APPROVED

    def test_approve_nonexistent(self) -> None:
        from ibr_platform.platform.improvement import SelfImprovementLoop
        loop = SelfImprovementLoop()
        assert loop.approve_experiment("nonexistent", "admin") is False

    async def test_run_experiment_not_approved_raises(self) -> None:
        from ibr_platform.platform.improvement import FailureCategory, SelfImprovementLoop
        loop = SelfImprovementLoop()
        f = loop.report_failure(FailureCategory.KNOWLEDGE_GAP, "test")
        h = loop.generate_hypothesis(f)
        exp = loop.design_experiment(h)
        with pytest.raises(ValueError, match="approved"):
            await loop.run_experiment(exp.id)

    async def test_run_experiment_complete(self) -> None:
        from ibr_platform.platform.improvement import (
            ExperimentStatus,
            FailureCategory,
            SelfImprovementLoop,
        )
        loop = SelfImprovementLoop()
        f = loop.report_failure(FailureCategory.KNOWLEDGE_GAP, "test")
        h = loop.generate_hypothesis(f)
        exp = loop.design_experiment(h, success_criteria={"MMLU": 0.8})
        loop.approve_experiment(exp.id, "admin")
        result = await loop.run_experiment(exp.id)
        assert exp.status == ExperimentStatus.COMPLETE
        assert "recommendation" in result
        assert "candidate_model_id" in result

    async def test_run_experiment_promote(self) -> None:
        from ibr_platform.platform.improvement import (
            FailureCategory,
            Recommendation,
            SelfImprovementLoop,
        )
        loop = SelfImprovementLoop()
        f = loop.report_failure(FailureCategory.KNOWLEDGE_GAP, "test")
        h = loop.generate_hypothesis(f)
        exp = loop.design_experiment(h, success_criteria={"MMLU": 0.8})
        loop.approve_experiment(exp.id, "admin")
        result = await loop.run_experiment(exp.id)
        # Score is simulated at 0.87 which is >= 0.8
        assert result["recommendation"] == Recommendation.PROMOTE.value

    def test_get_failures(self) -> None:
        from ibr_platform.platform.improvement import FailureCategory, SelfImprovementLoop
        loop = SelfImprovementLoop()
        loop.report_failure(FailureCategory.KNOWLEDGE_GAP, "f1")
        loop.report_failure(FailureCategory.REASONING_ERROR, "f2")
        assert len(loop.get_failures()) == 2

    def test_get_experiments_by_status(self) -> None:
        from ibr_platform.platform.improvement import (
            ExperimentStatus,
            FailureCategory,
            SelfImprovementLoop,
        )
        loop = SelfImprovementLoop()
        f = loop.report_failure(FailureCategory.KNOWLEDGE_GAP, "test")
        h = loop.generate_hypothesis(f)
        experiments = [loop.design_experiment(h) for _ in range(2)]
        loop.approve_experiment(experiments[0].id, "admin")
        proposed = loop.get_experiments(ExperimentStatus.PROPOSED)
        approved = loop.get_experiments(ExperimentStatus.APPROVED)
        assert len(proposed) == 1
        assert len(approved) == 1
