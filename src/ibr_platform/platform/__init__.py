"""
Platform package — Core platform code (PRD Section 32.2).

Contains:
    - architecture: Layered architecture definitions (10 layers, dependency rules)
    - orchestrator: Task Orchestrator (entry point for user requests)
    - memory: 12-tier memory system (working, short-term, long-term, etc.)
    - security: RBAC, audit log, approval gate, sandbox
    - runtime: IBR runtime (process management, lifecycle, health checks)
    - kernel: Resource management, sandboxing, IPC
    - scheduler: Task scheduler (plan execution, dependency resolution)
"""

from ibr_platform.platform.architecture import (
    ArchitectureLayer,
    LayerBase,
    can_depend,
    get_architecture_info,
    list_layers,
    validate_dependency_graph,
)
from ibr_platform.platform.memory import MemoryEntry, MemoryManager, MemoryTier
from ibr_platform.platform.orchestrator import (
    OrchestratorHealth,
    RequestStatus,
    TaskOrchestrator,
    UserRequest,
)

__all__ = [
    # Architecture
    "ArchitectureLayer",
    "LayerBase",
    "can_depend",
    "get_architecture_info",
    "list_layers",
    "validate_dependency_graph",
    # Memory
    "MemoryEntry",
    "MemoryManager",
    "MemoryTier",
    # Orchestrator
    "OrchestratorHealth",
    "RequestStatus",
    "TaskOrchestrator",
    "UserRequest",
]
