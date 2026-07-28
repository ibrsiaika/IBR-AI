"""
Tests for Section 10 — High-Level Architecture (Layered Architecture).

Verifies the 10-layer architecture from PRD Section 10, dependency rules
(upper layers depend on lower, never reverse), and the TaskOrchestrator.

Run: pytest tests/unit/test_architecture.py -v
"""
from __future__ import annotations

import pytest


class TestLayerDefinitions:
    """Test that all 10 architecture layers are defined (PRD Section 10.1)."""

    def test_layer_enum_exists(self) -> None:
        """The ArchitectureLayer enum is importable."""
        from ibr_platform.platform.architecture import ArchitectureLayer
        assert ArchitectureLayer is not None

    @pytest.mark.parametrize(
        "layer_name",
        [
            "USER",
            "ORCHESTRATION",
            "PLANNING",
            "EXECUTION",
            "KNOWLEDGE",
            "DATA",
            "TRAINING",
            "EVALUATION",
            "REGISTRY",
            "DEPLOYMENT",
        ],
    )
    def test_layer_defined(self, layer_name: str) -> None:
        """Each of the 10 layers is defined in the enum."""
        from ibr_platform.platform.architecture import ArchitectureLayer
        assert hasattr(ArchitectureLayer, layer_name), f"Layer {layer_name} not defined"

    def test_layer_count(self) -> None:
        """Exactly 10 layers are defined."""
        from ibr_platform.platform.architecture import ArchitectureLayer
        layers = [layer for layer in ArchitectureLayer if layer.name != "_"]  # exclude any sentinel
        assert len(layers) == 10, f"Expected 10 layers, got {len(layers)}"

    @pytest.mark.parametrize(
        "layer_name,expected_value",
        [
            ("USER", 1),
            ("ORCHESTRATION", 2),
            ("PLANNING", 3),
            ("EXECUTION", 4),
            ("KNOWLEDGE", 5),
            ("DATA", 6),
            ("TRAINING", 7),
            ("EVALUATION", 8),
            ("REGISTRY", 9),
            ("DEPLOYMENT", 10),
        ],
    )
    def test_layer_ordering(self, layer_name: str, expected_value: int) -> None:
        """Layers are numbered 1-10 in order (User=1, Deployment=10)."""
        from ibr_platform.platform.architecture import ArchitectureLayer
        layer = getattr(ArchitectureLayer, layer_name)
        assert layer.value == expected_value


class TestLayerBase:
    """Test the LayerBase abstract class (PRD Section 10.3)."""

    def test_layer_base_importable(self) -> None:
        """LayerBase is importable."""
        from ibr_platform.platform.architecture import LayerBase
        assert LayerBase is not None

    def test_layer_base_is_abstract(self) -> None:
        """LayerBase cannot be instantiated directly."""
        from ibr_platform.platform.architecture import LayerBase
        with pytest.raises(TypeError):
            LayerBase()

    def test_layer_base_has_layer_property(self) -> None:
        """LayerBase subclasses have a layer property."""
        from ibr_platform.platform.architecture import ArchitectureLayer, LayerBase

        class TestLayer(LayerBase):
            @property
            def layer(self) -> ArchitectureLayer:
                return ArchitectureLayer.USER

        layer = TestLayer()
        assert layer.layer == ArchitectureLayer.USER

    def test_concrete_layer_can_be_instantiated(self) -> None:
        """A concrete LayerBase subclass can be instantiated."""
        from ibr_platform.platform.architecture import ArchitectureLayer, LayerBase

        class UserLayer(LayerBase):
            @property
            def layer(self) -> ArchitectureLayer:
                return ArchitectureLayer.USER

        user_layer = UserLayer()
        assert user_layer is not None
        assert user_layer.layer == ArchitectureLayer.USER


class TestDependencyRules:
    """Test the dependency direction rules (PRD Section 10.1).

    Upper layers may depend on lower layers, but lower layers never
    depend on upper layers.
    """

    def test_dependency_checker_exists(self) -> None:
        """The dependency checker function exists."""
        from ibr_platform.platform.architecture import can_depend
        assert callable(can_depend)

    @pytest.mark.parametrize(
        "upper,lower",
        [
            ("ORCHESTRATION", "PLANNING"),
            ("PLANNING", "EXECUTION"),
            ("EXECUTION", "KNOWLEDGE"),
            ("REGISTRY", "DEPLOYMENT"),  # Registry (9) can depend on Deployment (10)
            ("USER", "DEPLOYMENT"),  # Top can depend on bottom
        ],
    )
    def test_upper_can_depend_on_lower(self, upper: str, lower: str) -> None:
        """Upper layers can depend on lower layers."""
        from ibr_platform.platform.architecture import ArchitectureLayer, can_depend
        assert can_depend(getattr(ArchitectureLayer, upper), getattr(ArchitectureLayer, lower))

    @pytest.mark.parametrize(
        "lower,upper",
        [
            ("PLANNING", "ORCHESTRATION"),
            ("EXECUTION", "PLANNING"),
            ("KNOWLEDGE", "EXECUTION"),
            ("DEPLOYMENT", "REGISTRY"),  # Deployment (10) cannot depend on Registry (9)
            ("DEPLOYMENT", "USER"),
        ],
    )
    def test_lower_cannot_depend_on_upper(self, lower: str, upper: str) -> None:
        """Lower layers cannot depend on upper layers."""
        from ibr_platform.platform.architecture import ArchitectureLayer, can_depend
        assert not can_depend(getattr(ArchitectureLayer, lower), getattr(ArchitectureLayer, upper))

    def test_same_layer_cannot_depend(self) -> None:
        """A layer cannot depend on itself (no circular dependencies)."""
        from ibr_platform.platform.architecture import ArchitectureLayer, can_depend
        assert not can_depend(ArchitectureLayer.USER, ArchitectureLayer.USER)


class TestTaskOrchestrator:
    """Test the TaskOrchestrator (PRD Section 10, Layer 2)."""

    def test_orchestrator_importable(self) -> None:
        """TaskOrchestrator is importable."""
        from ibr_platform.platform.orchestrator import TaskOrchestrator
        assert TaskOrchestrator is not None

    def test_orchestrator_can_be_instantiated(self) -> None:
        """TaskOrchestrator can be instantiated."""
        from ibr_platform.platform.orchestrator import TaskOrchestrator
        orchestrator = TaskOrchestrator()
        assert orchestrator is not None

    def test_orchestrator_has_submit_method(self) -> None:
        """TaskOrchestrator has a submit_request method."""
        from ibr_platform.platform.orchestrator import TaskOrchestrator
        orch = TaskOrchestrator()
        assert hasattr(orch, "submit_request")

    def test_orchestrator_has_get_result_method(self) -> None:
        """TaskOrchestrator has a get_result method."""
        from ibr_platform.platform.orchestrator import TaskOrchestrator
        orch = TaskOrchestrator()
        assert hasattr(orch, "get_result")

    def test_orchestrator_has_health_check(self) -> None:
        """TaskOrchestrator has a health_check method."""
        from ibr_platform.platform.orchestrator import TaskOrchestrator
        orch = TaskOrchestrator()
        assert hasattr(orch, "health_check")

    async def test_orchestrator_submit_returns_request_id(self) -> None:
        """submit_request returns a unique request ID."""
        from ibr_platform.platform.orchestrator import TaskOrchestrator
        orch = TaskOrchestrator()
        request_id = await orch.submit_request("What is the capital of France?")
        assert request_id is not None
        assert isinstance(request_id, str)
        assert len(request_id) > 0

    async def test_orchestrator_submit_two_requests_different_ids(self) -> None:
        """Two requests get different IDs."""
        from ibr_platform.platform.orchestrator import TaskOrchestrator
        orch = TaskOrchestrator()
        id1 = await orch.submit_request("Question 1")
        id2 = await orch.submit_request("Question 2")
        assert id1 != id2

    async def test_orchestrator_get_result_unknown_id(self) -> None:
        """get_result for unknown ID raises or returns None."""
        from ibr_platform.platform.orchestrator import TaskOrchestrator
        orch = TaskOrchestrator()
        result = await orch.get_result("nonexistent-id")
        assert result is None or result.status == "not_found"


class TestArchitectureRegistry:
    """Test the layer registry that tracks all layers."""

    def test_registry_exists(self) -> None:
        """The architecture registry is importable."""
        from ibr_platform.platform.architecture import get_architecture_info
        assert callable(get_architecture_info)

    @pytest.mark.parametrize(
        "layer_name",
        ["USER", "ORCHESTRATION", "PLANNING", "EXECUTION", "KNOWLEDGE",
         "DATA", "TRAINING", "EVALUATION", "REGISTRY", "DEPLOYMENT"],
    )
    def test_registry_has_layer_info(self, layer_name: str) -> None:
        """Each layer has info in the registry."""
        from ibr_platform.platform.architecture import ArchitectureLayer, get_architecture_info
        layer = getattr(ArchitectureLayer, layer_name)
        info = get_architecture_info(layer)
        assert info is not None
        assert "name" in info or "component" in info or "responsibility" in info

    def test_registry_info_has_responsibility(self) -> None:
        """Layer info includes a responsibility description."""
        from ibr_platform.platform.architecture import ArchitectureLayer, get_architecture_info
        info = get_architecture_info(ArchitectureLayer.USER)
        assert "responsibility" in info or "description" in info
