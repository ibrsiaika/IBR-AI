"""
Self-Improvement Loop (PRD Section 40).

Implements the closed-loop system that monitors production failures,
generates hypotheses, designs experiments, trains candidates, benchmarks,
and recommends deployment — all gated by human approval.

Loop stages (PRD Section 40.1):
    1. Failure Analysis: triage failures (knowledge gap, reasoning error, etc.)
    2. Hypothesis Generation: propose fixes
    3. Experiment Design: training config, dataset, eval plan
    4. Candidate Training: run training job
    5. Benchmark Comparison: compare candidate vs production
    6. Deployment Recommendation: promote / don't promote / more experiments
    7. Human Approval: required before any production change

References:
    - PRD Section 40 (Self-Improvement Loop)
    - PRD Section 23 (Human-in-the-Loop & Governance)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class FailureCategory(StrEnum):
    """Categories of production failures (PRD Section 40.2)."""

    KNOWLEDGE_GAP = "knowledge_gap"
    REASONING_ERROR = "reasoning_error"
    CALIBRATION_ERROR = "calibration_error"
    CAPABILITY_GAP = "capability_gap"


class Recommendation(StrEnum):
    """Deployment recommendations (PRD Section 40.4)."""

    PROMOTE = "promote"
    DO_NOT_PROMOTE = "do_not_promote"
    MORE_EXPERIMENTS = "more_experiments"


class ExperimentStatus(StrEnum):
    """Status of a self-improvement experiment."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    RUNNING = "running"
    COMPLETE = "complete"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass(slots=True)
class Failure:
    """A production failure to be analyzed.

    Attributes:
        id: Unique failure ID.
        category: Failure category (knowledge gap, reasoning error, etc.).
        description: What went wrong.
        user_feedback: User's feedback (if any).
        timestamp: When the failure occurred.
        metadata: Additional failure data.
    """

    category: FailureCategory = FailureCategory.KNOWLEDGE_GAP
    description: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_feedback: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Hypothesis:
    """A hypothesis for fixing a failure (PRD Section 40.3).

    Attributes:
        id: Unique hypothesis ID.
        failure_id: The failure this hypothesis addresses.
        root_cause: Hypothesized root cause.
        proposed_fix: Proposed fix (e.g., "ingest sources X, retrain on dataset Y").
        expected_improvement: Quantitative prediction.
        evaluation_plan: How to measure improvement.
        confidence: Confidence in the hypothesis (0.0-1.0).
    """

    failure_id: str = ""
    root_cause: str = ""
    proposed_fix: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    expected_improvement: str = ""
    evaluation_plan: str = ""
    confidence: float = 0.5


@dataclass(slots=True)
class Experiment:
    """A self-improvement experiment (PRD Section 40.3).

    Attributes:
        id: Unique experiment ID.
        hypothesis_id: The hypothesis being tested.
        training_config: Training configuration.
        dataset_id: Dataset for training.
        benchmarks: List of benchmarks to evaluate.
        success_criteria: Quantitative criteria for success.
        status: Current experiment status.
        candidate_model_id: ID of the trained candidate model.
        results: Benchmark results.
        recommendation: Deployment recommendation.
        created_at: When the experiment was created.
    """

    hypothesis_id: str = ""
    training_config: dict[str, Any] = field(default_factory=dict)
    dataset_id: str = ""
    benchmarks: list[str] = field(default_factory=list)
    success_criteria: dict[str, float] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: ExperimentStatus = ExperimentStatus.PROPOSED
    candidate_model_id: str = ""
    results: dict[str, Any] = field(default_factory=dict)
    recommendation: Recommendation | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class SelfImprovementLoop:
    """The self-improvement loop coordinator (PRD Section 40).

    Coordinates: failure analysis → hypothesis → experiment → training →
    benchmarking → recommendation → human approval.

    HUMAN APPROVAL IS REQUIRED before any production deployment.
    The loop proposes; humans dispose (PRD Section 40.5).

    Usage:
        loop = SelfImprovementLoop()
        failure = loop.report_failure(FailureCategory.KNOWLEDGE_GAP, "Model doesn't know X")
        hypothesis = loop.generate_hypothesis(failure)
        experiment = loop.design_experiment(hypothesis)
        # Human approves experiment
        loop.approve_experiment(experiment.id, approver="admin")
        # Run experiment (trains candidate, benchmarks)
        result = await loop.run_experiment(experiment.id)
        # Human approves deployment
        if result["recommendation"] == Recommendation.PROMOTE:
            await loop.request_deployment_approval(experiment.id)
    """

    def __init__(self) -> None:
        self._failures: dict[str, Failure] = {}
        self._hypotheses: dict[str, Hypothesis] = {}
        self._experiments: dict[str, Experiment] = {}

    def report_failure(
        self,
        category: FailureCategory,
        description: str,
        user_feedback: str = "",
    ) -> Failure:
        """Report a production failure (PRD Section 40.2).

        Args:
            category: Failure category.
            description: What went wrong.
            user_feedback: User's feedback (if any).

        Returns:
            The created Failure.
        """
        failure = Failure(
            category=category,
            description=description,
            user_feedback=user_feedback,
        )
        self._failures[failure.id] = failure
        return failure

    def generate_hypothesis(
        self,
        failure: Failure,
        root_cause: str = "",
        proposed_fix: str = "",
    ) -> Hypothesis:
        """Generate a hypothesis for fixing a failure (PRD Section 40.3).

        In production, this uses an LLM to analyze the failure and propose fixes.

        Args:
            failure: The failure to address.
            root_cause: Hypothesized root cause (auto-generated if empty).
            proposed_fix: Proposed fix (auto-generated if empty).

        Returns:
            The created Hypothesis.
        """
        if not root_cause:
            root_cause = self._auto_root_cause(failure)
        if not proposed_fix:
            proposed_fix = self._auto_proposed_fix(failure, root_cause)

        hypothesis = Hypothesis(
            failure_id=failure.id,
            root_cause=root_cause,
            proposed_fix=proposed_fix,
            expected_improvement="MMLU score +1 point",
            evaluation_plan="Run MMLU and custom benchmarks",
            confidence=0.6,
        )
        self._hypotheses[hypothesis.id] = hypothesis
        return hypothesis

    def _auto_root_cause(self, failure: Failure) -> str:
        """Auto-generate root cause based on failure category."""
        causes = {
            FailureCategory.KNOWLEDGE_GAP: "Model lacks information about the topic",
            FailureCategory.REASONING_ERROR: "Model has information but reasons incorrectly",
            FailureCategory.CALIBRATION_ERROR: "Model is overconfident or underconfident",
            FailureCategory.CAPABILITY_GAP: "Model lacks a required skill",
        }
        return causes.get(failure.category, "Unknown root cause")

    def _auto_proposed_fix(self, failure: Failure, root_cause: str) -> str:
        """Auto-generate proposed fix based on failure category."""
        fixes = {
            FailureCategory.KNOWLEDGE_GAP: "Ingest additional sources and create a dataset for fine-tuning",
            FailureCategory.REASONING_ERROR: "Create reasoning traces and fine-tune with GRPO",
            FailureCategory.CALIBRATION_ERROR: "Apply preference optimization (DPO) to calibrate confidence",
            FailureCategory.CAPABILITY_GAP: "Distill capability from a larger teacher model",
        }
        return fixes.get(failure.category, "Investigate and apply appropriate fix")

    def design_experiment(
        self,
        hypothesis: Hypothesis,
        training_config: dict[str, Any] | None = None,
        dataset_id: str = "",
        benchmarks: list[str] | None = None,
        success_criteria: dict[str, float] | None = None,
    ) -> Experiment:
        """Design an experiment to test a hypothesis (PRD Section 40.3).

        Args:
            hypothesis: The hypothesis to test.
            training_config: Training configuration.
            dataset_id: Dataset for training.
            benchmarks: Benchmarks to evaluate.
            success_criteria: Quantitative success criteria.

        Returns:
            The created Experiment (status: PROPOSED).
        """
        experiment = Experiment(
            hypothesis_id=hypothesis.id,
            training_config=training_config or {"technique": "sft"},
            dataset_id=dataset_id,
            benchmarks=benchmarks or ["MMLU", "HumanEval"],
            success_criteria=success_criteria or {"MMLU": 0.85},
        )
        self._experiments[experiment.id] = experiment
        return experiment

    def approve_experiment(self, experiment_id: str, approver: str) -> bool:
        """Approve an experiment for execution (human approval gate).

        Args:
            experiment_id: The experiment to approve.
            approver: The user approving.

        Returns:
            True if approved, False if not found or already decided.
        """
        exp = self._experiments.get(experiment_id)
        if exp is None or exp.status != ExperimentStatus.PROPOSED:
            return False
        exp.status = ExperimentStatus.APPROVED
        return True

    async def run_experiment(self, experiment_id: str) -> dict[str, Any]:
        """Run an approved experiment (PRD Section 40.4).

        Trains a candidate model, runs benchmarks, and generates a recommendation.

        Args:
            experiment_id: The experiment to run.

        Returns:
            Dictionary with: recommendation, results, candidate_model_id.

        Raises:
            ValueError: If experiment is not approved.
        """
        exp = self._experiments.get(experiment_id)
        if exp is None:
            raise ValueError(f"Experiment '{experiment_id}' not found")
        if exp.status != ExperimentStatus.APPROVED:
            raise ValueError(f"Experiment must be approved before running (current: {exp.status})")

        exp.status = ExperimentStatus.RUNNING

        # Simulate training (production: uses TrainingPipeline)
        exp.candidate_model_id = f"candidate_{uuid.uuid4().hex[:8]}"

        # Simulate benchmarking (production: uses EvaluationAgent)
        results: dict[str, float] = {}
        all_criteria_met = True
        for benchmark in exp.benchmarks:
            score = 0.87  # Simulated score
            results[benchmark] = score
            target = exp.success_criteria.get(benchmark, 0.0)
            if score < target:
                all_criteria_met = False

        exp.results = {
            "scores": results,
            "candidate_model_id": exp.candidate_model_id,
            "benchmarks_run": len(exp.benchmarks),
        }

        # Generate recommendation (PRD Section 40.4)
        if all_criteria_met:
            exp.recommendation = Recommendation.PROMOTE
        elif sum(1 for s in results.values() if s >= 0.5) > len(results) / 2:
            exp.recommendation = Recommendation.MORE_EXPERIMENTS
        else:
            exp.recommendation = Recommendation.DO_NOT_PROMOTE

        exp.status = ExperimentStatus.COMPLETE

        return {
            "experiment_id": exp.id,
            "recommendation": exp.recommendation.value,
            "results": exp.results,
            "candidate_model_id": exp.candidate_model_id,
            "all_criteria_met": all_criteria_met,
        }

    def get_failures(self) -> list[Failure]:
        """List all reported failures."""
        return list(self._failures.values())

    def get_experiments(self, status: ExperimentStatus | None = None) -> list[Experiment]:
        """List experiments, optionally filtered by status."""
        if status is None:
            return list(self._experiments.values())
        return [e for e in self._experiments.values() if e.status == status]

    def __repr__(self) -> str:
        return (
            f"<SelfImprovementLoop(failures={len(self._failures)}, "
            f"experiments={len(self._experiments)})>"
        )
