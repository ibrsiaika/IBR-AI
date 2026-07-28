"""
High-Level Architecture — Layered Architecture (PRD Section 10).

The IBR Platform follows a layered architecture where each layer has a single
responsibility and depends only on layers below it. Upper layers may depend
on lower layers, but lower layers NEVER depend on upper layers. This
discipline enables swapping implementations without cascading changes.

The 10 layers (from top to bottom):
    1. User Layer — CLI, Dashboard, SDK, APIs
    2. Orchestration — Task Orchestrator (auth, quota, dispatch)
    3. Planning — Planner Agent (decompose into execution graphs)
    4. Execution — Specialist Agent Pool (25+ agents)
    5. Knowledge — Knowledge Graph + Vector DB
    6. Data — Dataset Generator
    7. Training — Model Training Pipeline
    8. Evaluation — Benchmarks + RLHF
    9. Registry — Model Registry (versioned artifacts)
   10. Deployment — Production Deployment (canary, A/B, rollback)

This module defines:
    - ArchitectureLayer enum (the 10 layers)
    - LayerBase abstract class (base for all layer implementations)
    - can_depend() function (dependency rule checker)
    - get_architecture_info() function (layer metadata)

References:
    - PRD Section 10 (High-Level Architecture)
    - PRD Section 10.1 (Layered Architecture)
    - PRD Section 10.3 (Key Architectural Decisions)
    - ADR-0001 (Technology Stack and Project Structure)
"""

from __future__ import annotations

import abc
from enum import IntEnum


class ArchitectureLayer(IntEnum):
    """The 10 architecture layers (PRD Section 10.1).

    Layers are numbered 1-10, where 1 is the topmost (User) and 10 is the
    bottommost (Deployment). Upper layers (lower numbers) may depend on
    lower layers (higher numbers), but NOT vice versa.

    Usage:
        layer = ArchitectureLayer.USER  # Layer 1
        assert layer.value == 1
    """

    USER = 1           # CLI, Dashboard, SDK, APIs
    ORCHESTRATION = 2  # Task Orchestrator
    PLANNING = 3       # Planner Agent
    EXECUTION = 4      # Specialist Agent Pool
    KNOWLEDGE = 5      # Knowledge Graph + Vector DB
    DATA = 6           # Dataset Generator
    TRAINING = 7       # Training Pipeline
    EVALUATION = 8     # Benchmarks + RLHF
    REGISTRY = 9       # Model Registry
    DEPLOYMENT = 10    # Production Deployment


# Layer metadata: name, component, responsibility (PRD Section 10.1, Table 10.1)
_LAYER_INFO: dict[ArchitectureLayer, dict[str, str]] = {
    ArchitectureLayer.USER: {
        "name": "User Layer",
        "component": "CLI / Dashboard / SDK",
        "responsibility": "Submit requests, view results, manage platform",
    },
    ArchitectureLayer.ORCHESTRATION: {
        "name": "Orchestration Layer",
        "component": "Task Orchestrator",
        "responsibility": "Authenticate, quota check, dispatch to Planner",
    },
    ArchitectureLayer.PLANNING: {
        "name": "Planning Layer",
        "component": "Planner Agent",
        "responsibility": "Decompose objective into execution graph",
    },
    ArchitectureLayer.EXECUTION: {
        "name": "Execution Layer",
        "component": "Specialist Agent Pool",
        "responsibility": "Execute plan nodes (research, verify, code, train)",
    },
    ArchitectureLayer.KNOWLEDGE: {
        "name": "Knowledge Layer",
        "component": "Knowledge Graph + Vector DB",
        "responsibility": "Store verified facts, entities, relationships",
    },
    ArchitectureLayer.DATA: {
        "name": "Data Layer",
        "component": "Dataset Generator",
        "responsibility": "Assemble training datasets with provenance",
    },
    ArchitectureLayer.TRAINING: {
        "name": "Training Layer",
        "component": "Training Pipeline",
        "responsibility": "Distributed training with checkpointing",
    },
    ArchitectureLayer.EVALUATION: {
        "name": "Evaluation Layer",
        "component": "Evaluation + RLHF Agent",
        "responsibility": "Run benchmarks, preference learning",
    },
    ArchitectureLayer.REGISTRY: {
        "name": "Registry Layer",
        "component": "Model Registry",
        "responsibility": "Versioned model artifacts with lineage",
    },
    ArchitectureLayer.DEPLOYMENT: {
        "name": "Deployment Layer",
        "component": "Production Deployment",
        "responsibility": "Canary, A/B, automatic rollback",
    },
}


class LayerBase(abc.ABC):
    """Abstract base class for all architecture layer implementations.

    Every layer component inherits from LayerBase and declares which layer
    it belongs to via the `layer` property. This enables the platform to
    enforce dependency rules at runtime.

    Usage:
        class UserAPI(LayerBase):
            @property
            def layer(self) -> ArchitectureLayer:
                return ArchitectureLayer.USER

            # ... implementation ...
    """

    @property
    @abc.abstractmethod
    def layer(self) -> ArchitectureLayer:
        """The architecture layer this component belongs to."""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(layer={self.layer.name})>"


def can_depend(upper: ArchitectureLayer, lower: ArchitectureLayer) -> bool:
    """Check if `upper` layer can depend on `lower` layer.

    Dependency rule (PRD Section 10.1): Upper layers (lower numbers) may
    depend on lower layers (higher numbers), but NOT vice versa.

    Args:
        upper: The layer that wants to depend on `lower`.
        lower: The layer being depended upon.

    Returns:
        True if `upper` can depend on `lower`, False otherwise.

    Examples:
        >>> can_depend(ArchitectureLayer.USER, ArchitectureLayer.ORCHESTRATION)
        True  # User (1) can depend on Orchestration (2)
        >>> can_depend(ArchitectureLayer.ORCHESTRATION, ArchitectureLayer.USER)
        False  # Orchestration (2) cannot depend on User (1)
        >>> can_depend(ArchitectureLayer.USER, ArchitectureLayer.USER)
        False  # A layer cannot depend on itself
    """
    if upper == lower:
        return False  # No self-dependencies (prevents circular)
    # Upper layers have LOWER numeric values; they can depend on layers
    # with HIGHER numeric values (which are "lower" in the stack)
    return upper.value < lower.value


def get_architecture_info(layer: ArchitectureLayer) -> dict[str, str]:
    """Get metadata about an architecture layer.

    Args:
        layer: The architecture layer to query.

    Returns:
        Dictionary with keys: name, component, responsibility.

    Raises:
        KeyError: If the layer is not recognized.
    """
    if layer not in _LAYER_INFO:
        raise KeyError(f"Unknown architecture layer: {layer}")
    return _LAYER_INFO[layer].copy()


def list_layers() -> list[ArchitectureLayer]:
    """List all architecture layers in order (top to bottom).

    Returns:
        List of ArchitectureLayer values, ordered USER to DEPLOYMENT.
    """
    return sorted(ArchitectureLayer, key=lambda layer: layer.value)


def validate_dependency_graph(dependencies: dict[ArchitectureLayer, list[ArchitectureLayer]]) -> list[str]:
    """Validate a dependency graph for rule violations.

    Args:
        dependencies: Mapping of layer to list of layers it depends on.

    Returns:
        List of violation messages (empty if valid).
    """
    violations: list[str] = []
    for src_layer, deps in dependencies.items():
        for dep in deps:
            if not can_depend(src_layer, dep):
                violations.append(
                    f"{src_layer.name} cannot depend on {dep.name} "
                    f"(dependency rule violation: upper layers only)"
                )
    return violations
