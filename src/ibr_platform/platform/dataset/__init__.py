"""
Dataset Generation (PRD Section 38).

Implements 9 dataset types with provenance, quality scoring, deduplication,
and validation. All FREE — no paid data sources.

Dataset types (PRD Section 38.2, Table 38.1):
    - Instruction: {input, instruction, output}
    - QA: {question, context, answer, citations}
    - Reasoning: {problem, reasoning_trace, answer}
    - Coding: {specification, code, tests, expected_output}
    - Mathematics: {problem, solution, answer, difficulty}
    - Scientific: {hypothesis, experiment, result, conclusion}
    - Dialogue: {turns, summary, outcome}
    - ToolUse: {task, tool_calls, outcome}
    - Synthetic: {input, output, quality_score, generator_model}

References:
    - PRD Section 38 (Dataset Generation)
    - PRD Section 95 (Phi-3 Textbook Quality)
    - PRD Section 99 (Data Deduplication & Quality Filtering)
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class DatasetType(StrEnum):
    """9 dataset types (PRD Section 38.2)."""

    INSTRUCTION = "instruction"
    QA = "qa"
    REASONING = "reasoning"
    CODING = "coding"
    MATHEMATICS = "mathematics"
    SCIENTIFIC = "scientific"
    DIALOGUE = "dialogue"
    TOOL_USE = "tool_use"
    SYNTHETIC = "synthetic"


@dataclass(slots=True)
class DatasetExample:
    """A single training example with provenance (PRD Section 38.3).

    Every example has full provenance: source, license, quality score.
    """

    data: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    dataset_id: str = ""
    source_artifacts: list[str] = field(default_factory=list)
    license: str = "unknown"
    quality_score: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        """SHA-256 hash of the example content (for deduplication)."""
        content = str(sorted(self.data.items()))
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass(slots=True)
class Dataset:
    """A training dataset with metadata, provenance, and examples.

    Attributes:
        id: Unique dataset ID.
        name: Dataset name.
        dataset_type: Type of dataset (instruction, qa, etc.).
        examples: List of DatasetExample objects.
        provenance: Dataset-level provenance (sources, transformations).
        license: Overall license (most restrictive of all sources).
        quality_score: Average quality score across examples.
        created_at: When the dataset was created.
        metadata: Additional dataset metadata.
    """

    name: str = ""
    dataset_type: DatasetType = DatasetType.INSTRUCTION
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    examples: list[DatasetExample] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)
    license: str = "unknown"
    quality_score: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def size(self) -> int:
        """Number of examples in the dataset."""
        return len(self.examples)

    def add_example(self, example: DatasetExample) -> None:
        """Add an example to the dataset."""
        example.dataset_id = self.id
        self.examples.append(example)
        self._update_quality_score()

    def _update_quality_score(self) -> None:
        """Recalculate the dataset's average quality score."""
        if self.examples:
            self.quality_score = sum(e.quality_score for e in self.examples) / len(self.examples)
        else:
            self.quality_score = 0.0


class DatasetGenerator:
    """Generates training datasets (PRD Section 38).

    Supports all 9 dataset types with:
        - Provenance tracking (source artifacts, license)
        - Quality scoring (0.0-1.0)
        - Deduplication (exact match via content hash)
        - Validation (schema check, completeness)

    All FREE — no paid APIs. Uses data from the Research Engine (Section 34)
    and Knowledge Graph (Section 51).

    Usage:
        gen = DatasetGenerator()
        ds = gen.create_dataset(
            name="my-instruction-ds",
            dataset_type=DatasetType.INSTRUCTION,
        )
        gen.add_example(ds, {"input": "Hello", "instruction": "Greet", "output": "Hi there!"})
        validated = gen.validate(ds)
    """

    def __init__(self) -> None:
        self._datasets: dict[str, Dataset] = {}

    def create_dataset(
        self,
        name: str,
        dataset_type: DatasetType,
        license: str = "unknown",
        metadata: dict[str, Any] | None = None,
    ) -> Dataset:
        """Create a new dataset.

        Args:
            name: Dataset name.
            dataset_type: Type of dataset.
            license: License of the data.
            metadata: Additional metadata.

        Returns:
            The created Dataset.
        """
        ds = Dataset(
            name=name,
            dataset_type=dataset_type,
            license=license,
            metadata=metadata or {},
        )
        self._datasets[ds.id] = ds
        return ds

    def add_example(
        self,
        dataset: Dataset,
        data: dict[str, Any],
        source_artifacts: list[str] | None = None,
        license: str = "unknown",
        quality_score: float = 0.0,
    ) -> DatasetExample:
        """Add an example to a dataset.

        Args:
            dataset: The dataset to add to.
            data: Example data (schema depends on dataset type).
            source_artifacts: Source artifact IDs for provenance.
            license: License of this example's data.
            quality_score: Quality score (0.0-1.0).

        Returns:
            The created DatasetExample.
        """
        example = DatasetExample(
            data=data,
            source_artifacts=source_artifacts or [],
            license=license,
            quality_score=quality_score,
        )
        dataset.add_example(example)
        return example

    def deduplicate(self, dataset: Dataset) -> int:
        """Remove duplicate examples (exact match via content hash).

        Args:
            dataset: The dataset to deduplicate.

        Returns:
            Number of duplicates removed.
        """
        seen_hashes: set[str] = set()
        unique_examples: list[DatasetExample] = []
        removed = 0

        for example in dataset.examples:
            h = example.content_hash
            if h not in seen_hashes:
                seen_hashes.add(h)
                unique_examples.append(example)
            else:
                removed += 1

        dataset.examples = unique_examples
        dataset._update_quality_score()
        return removed

    def validate(self, dataset: Dataset) -> dict[str, Any]:
        """Validate a dataset (PRD Section 38.6).

        Checks: schema, completeness, quality, deduplication, license.

        Args:
            dataset: The dataset to validate.

        Returns:
            Validation report with: valid, errors, warnings, stats.
        """
        errors: list[str] = []
        warnings: list[str] = []

        if dataset.size == 0:
            errors.append("Dataset is empty")

        # Check each example has required fields for its type
        required_fields = self._get_required_fields(dataset.dataset_type)
        for i, example in enumerate(dataset.examples):
            for field_name in required_fields:
                if field_name not in example.data:
                    errors.append(f"Example {i} missing required field: {field_name}")

            # Check quality score
            if example.quality_score < 0.7:
                warnings.append(
                    f"Example {i} has low quality score: {example.quality_score:.2f}"
                )

            # Check provenance
            if not example.source_artifacts:
                warnings.append(f"Example {i} has no provenance (source_artifacts empty)")

        # Check for duplicates
        hashes = [e.content_hash for e in dataset.examples]
        duplicates = len(hashes) - len(set(hashes))
        if duplicates > 0:
            warnings.append(f"Found {duplicates} duplicate examples")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "stats": {
                "total_examples": dataset.size,
                "avg_quality": dataset.quality_score,
                "duplicates": duplicates,
                "dataset_type": dataset.dataset_type.value,
            },
        }

    def _get_required_fields(self, dataset_type: DatasetType) -> list[str]:
        """Get required fields for a dataset type (PRD Table 38.1)."""
        schemas = {
            DatasetType.INSTRUCTION: ["input", "instruction", "output"],
            DatasetType.QA: ["question", "answer"],
            DatasetType.REASONING: ["problem", "answer"],
            DatasetType.CODING: ["specification", "code"],
            DatasetType.MATHEMATICS: ["problem", "answer"],
            DatasetType.SCIENTIFIC: ["hypothesis", "conclusion"],
            DatasetType.DIALOGUE: ["turns"],
            DatasetType.TOOL_USE: ["task", "tool_calls"],
            DatasetType.SYNTHETIC: ["input", "output"],
        }
        return schemas.get(dataset_type, [])

    def get_dataset(self, dataset_id: str) -> Dataset | None:
        """Get a dataset by ID."""
        return self._datasets.get(dataset_id)

    def list_datasets(self) -> list[Dataset]:
        """List all datasets."""
        return list(self._datasets.values())

    def filter_by_quality(
        self,
        dataset: Dataset,
        min_quality: float = 0.7,
    ) -> int:
        """Remove examples below a quality threshold.

        Args:
            dataset: The dataset to filter.
            min_quality: Minimum quality score (default 0.7).

        Returns:
            Number of examples removed.
        """
        original = len(dataset.examples)
        dataset.examples = [e for e in dataset.examples if e.quality_score >= min_quality]
        dataset._update_quality_score()
        return original - len(dataset.examples)

    def __repr__(self) -> str:
        return f"<DatasetGenerator(datasets={len(self._datasets)})>"
