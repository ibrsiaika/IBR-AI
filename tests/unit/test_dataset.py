"""Tests for Section 38 — Dataset Generation."""
from __future__ import annotations

import pytest


class TestDatasetTypes:
    def test_all_9_types(self) -> None:
        from ibr_platform.platform.dataset import DatasetType
        assert len(list(DatasetType)) == 9

    @pytest.mark.parametrize("t", [
        "INSTRUCTION", "QA", "REASONING", "CODING", "MATHEMATICS",
        "SCIENTIFIC", "DIALOGUE", "TOOL_USE", "SYNTHETIC"
    ])
    def test_type_defined(self, t: str) -> None:
        from ibr_platform.platform.dataset import DatasetType
        assert hasattr(DatasetType, t)


class TestDatasetExample:
    def test_example_has_provenance(self) -> None:
        from ibr_platform.platform.dataset import DatasetExample
        e = DatasetExample(data={"input": "test"}, source_artifacts=["art1"], license="MIT")
        assert e.source_artifacts == ["art1"]
        assert e.license == "MIT"

    def test_content_hash(self) -> None:
        from ibr_platform.platform.dataset import DatasetExample
        e1 = DatasetExample(data={"input": "test"})
        e2 = DatasetExample(data={"input": "test"})
        e3 = DatasetExample(data={"input": "different"})
        assert e1.content_hash == e2.content_hash
        assert e1.content_hash != e3.content_hash


class TestDatasetGenerator:
    def test_generator_importable(self) -> None:
        from ibr_platform.platform.dataset import DatasetGenerator
        assert DatasetGenerator is not None

    def test_create_dataset(self) -> None:
        from ibr_platform.platform.dataset import DatasetGenerator, DatasetType
        gen = DatasetGenerator()
        ds = gen.create_dataset(name="test", dataset_type=DatasetType.INSTRUCTION)
        assert ds.name == "test"
        assert ds.size == 0

    def test_add_example(self) -> None:
        from ibr_platform.platform.dataset import DatasetGenerator, DatasetType
        gen = DatasetGenerator()
        ds = gen.create_dataset(name="test", dataset_type=DatasetType.INSTRUCTION)
        gen.add_example(ds, {"input": "hi", "instruction": "greet", "output": "hello"},
                       quality_score=0.9)
        assert ds.size == 1

    def test_deduplicate(self) -> None:
        from ibr_platform.platform.dataset import DatasetGenerator, DatasetType
        gen = DatasetGenerator()
        ds = gen.create_dataset(name="test", dataset_type=DatasetType.INSTRUCTION)
        gen.add_example(ds, {"input": "a", "instruction": "b", "output": "c"})
        gen.add_example(ds, {"input": "a", "instruction": "b", "output": "c"})  # duplicate
        gen.add_example(ds, {"input": "x", "instruction": "y", "output": "z"})
        removed = gen.deduplicate(ds)
        assert removed == 1
        assert ds.size == 2

    def test_validate_valid(self) -> None:
        from ibr_platform.platform.dataset import DatasetGenerator, DatasetType
        gen = DatasetGenerator()
        ds = gen.create_dataset(name="test", dataset_type=DatasetType.INSTRUCTION)
        gen.add_example(ds, {"input": "a", "instruction": "b", "output": "c"},
                       source_artifacts=["art1"], quality_score=0.9)
        report = gen.validate(ds)
        assert report["valid"] is True

    def test_validate_missing_fields(self) -> None:
        from ibr_platform.platform.dataset import DatasetGenerator, DatasetType
        gen = DatasetGenerator()
        ds = gen.create_dataset(name="test", dataset_type=DatasetType.INSTRUCTION)
        gen.add_example(ds, {"input": "a"}, quality_score=0.9)  # Missing instruction, output
        report = gen.validate(ds)
        assert report["valid"] is False
        assert any("instruction" in e for e in report["errors"])

    def test_validate_empty_dataset(self) -> None:
        from ibr_platform.platform.dataset import DatasetGenerator, DatasetType
        gen = DatasetGenerator()
        ds = gen.create_dataset(name="test", dataset_type=DatasetType.INSTRUCTION)
        report = gen.validate(ds)
        assert report["valid"] is False

    def test_filter_by_quality(self) -> None:
        from ibr_platform.platform.dataset import DatasetGenerator, DatasetType
        gen = DatasetGenerator()
        ds = gen.create_dataset(name="test", dataset_type=DatasetType.INSTRUCTION)
        gen.add_example(ds, {"input": "a", "instruction": "b", "output": "c"}, quality_score=0.9)
        gen.add_example(ds, {"input": "d", "instruction": "e", "output": "f"}, quality_score=0.5)
        removed = gen.filter_by_quality(ds, min_quality=0.7)
        assert removed == 1
        assert ds.size == 1

    def test_quality_score_updates(self) -> None:
        from ibr_platform.platform.dataset import DatasetGenerator, DatasetType
        gen = DatasetGenerator()
        ds = gen.create_dataset(name="test", dataset_type=DatasetType.INSTRUCTION)
        gen.add_example(ds, {"input": "a", "instruction": "b", "output": "c"}, quality_score=0.8)
        gen.add_example(ds, {"input": "d", "instruction": "e", "output": "f"}, quality_score=0.6)
        assert ds.quality_score == 0.7  # Average

    def test_list_datasets(self) -> None:
        from ibr_platform.platform.dataset import DatasetGenerator, DatasetType
        gen = DatasetGenerator()
        gen.create_dataset(name="ds1", dataset_type=DatasetType.INSTRUCTION)
        gen.create_dataset(name="ds2", dataset_type=DatasetType.QA)
        assert len(gen.list_datasets()) == 2
