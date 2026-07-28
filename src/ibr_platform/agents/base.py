"""
Agent Framework — Base Classes (PRD Section 33).

This module defines the abstract base classes for all IBR Platform agents.
Every agent inherits from AgentBase and implements the four lifecycle methods:
initialize, execute, health_check, shutdown.

The agent framework follows the patterns documented in:
- PRD Section 11 (Multi-Agent Architecture)
- PRD Section 33 (Agent Framework — Phase 3)
- PRD Section 61 (MCP integration)
- PRD Section 71 (Agent Memory — MemGPT pattern)

Communication between agents uses the JSON envelope defined in PRD Section 11.2.
"""

from __future__ import annotations

import abc
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum, StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AgentStatus(StrEnum):
    """Lifecycle status of an agent (PRD Section 11.3)."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"
    BLOCKED = "blocked"
    SHUTDOWN = "shutdown"


class Priority(IntEnum):
    """Task priority levels (PRD Section 32.3 — Scheduler)."""

    P0_CRITICAL = 0  # Interactive inference, preempts everything
    P1_HIGH = 1      # Research tasks
    P2_NORMAL = 2    # Training jobs
    P3_LOW = 3       # Background batch work


class MessageStatus(StrEnum):
    """Status of an inter-agent message (PRD Section 11.2)."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(slots=True)
class Task:
    """
    A task for an agent to execute (PRD Section 11.2).

    Attributes:
        id: Globally unique task identifier.
        parent_id: Parent task ID (for hierarchical plans).
        agent_target: Name of the agent that should execute this task.
        agent_source: Name of the agent that created this task.
        task: The work to be done (natural language or structured).
        priority: Task priority (P0-P3).
        dependencies: List of task IDs that must complete before this task.
        confidence: Confidence score (0.0-1.0) for fact-bearing messages.
        evidence: List of source artifact IDs supporting this task.
        memory_ids: List of memory entries referenced.
        artifacts: List of produced artifact IDs.
        timestamp: When the task was created.
        metadata: Additional task-specific metadata.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str | None = None
    agent_target: str = ""
    agent_source: str = ""
    task: str = ""
    priority: Priority = Priority.P2_NORMAL
    dependencies: list[str] = field(default_factory=list)
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)
    memory_ids: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AgentResult:
    """
    Result of an agent's execution (PRD Section 33.3).

    Attributes:
        success: Whether the execution succeeded.
        data: The result data (agent-specific).
        error: Error message if success is False.
        confidence: Confidence in the result (0.0-1.0).
        artifacts: List of artifact IDs produced.
        memory_writes: List of memory IDs written.
        logs: Structured log entries.
        next_tasks: List of follow-up tasks to schedule.
    """

    success: bool = True
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    confidence: float = 0.0
    artifacts: list[str] = field(default_factory=list)
    memory_writes: list[str] = field(default_factory=list)
    logs: list[dict[str, Any]] = field(default_factory=list)
    next_tasks: list[Task] = field(default_factory=list)


class HealthStatus(BaseModel):
    """Health check result (PRD Section 33.3)."""

    status: str = Field(description="healthy, degraded, or unhealthy")
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AgentBase(abc.ABC):
    """
    Abstract base class for all IBR Platform agents (PRD Section 33.4).

    Every agent must implement:
        - initialize(config): Set up the agent with configuration.
        - execute(task) -> AgentResult: Perform the agent's work.
        - health_check() -> HealthStatus: Verify the agent is healthy.
        - shutdown(): Clean up resources.

    Agents are stateless between tasks — all state lives in memory stores
    (PRD Section 10.3). This enables horizontal scaling, fault tolerance,
    and debugging.

    Agents communicate via structured JSON messages (PRD Section 11.2),
    never through shared mutable state.

    Usage:
        class MyAgent(AgentBase):
            async def initialize(self, config):
                self.config = config

            async def execute(self, task):
                # Do work
                return AgentResult(success=True, data={"result": "..."})

            async def health_check(self):
                return HealthStatus(status="healthy")

            async def shutdown(self):
                pass

        agent = MyAgent()
        await agent.initialize({"key": "value"})
        result = await agent.execute(Task(task="do something"))
    """

    def __init__(self, name: str | None = None) -> None:
        """Initialize the agent with an optional name.

        Args:
            name: Human-readable agent name. Defaults to the class name.
        """
        self.name: str = name or self.__class__.__name__
        self._status: AgentStatus = AgentStatus.PENDING
        self._initialized: bool = False

    @property
    def status(self) -> AgentStatus:
        """Current agent status."""
        return self._status

    @property
    def is_initialized(self) -> bool:
        """Whether the agent has been initialized."""
        return self._initialized

    @abc.abstractmethod
    async def initialize(self, config: dict[str, Any]) -> None:
        """
        Initialize the agent with configuration.

        Called once before the agent's first execute() call.
        Set up connections, load models, configure tools, etc.

        Args:
            config: Agent configuration dictionary.

        Raises:
            AgentInitializationError: If initialization fails.
        """
        ...

    @abc.abstractmethod
    async def execute(self, task: Task) -> AgentResult:
        """
        Execute a task and return the result.

        This is the main entry point for agent work. The agent receives
        a Task, performs its work, and returns an AgentResult.

        Args:
            task: The task to execute.

        Returns:
            AgentResult with success status, data, and metadata.
        """
        ...

    @abc.abstractmethod
    async def health_check(self) -> HealthStatus:
        """
        Check the agent's health.

        Returns:
            HealthStatus indicating whether the agent is healthy,
            degraded, or unhealthy.
        """
        ...

    @abc.abstractmethod
    async def shutdown(self) -> None:
        """
        Shut down the agent and release resources.

        Called when the agent is being decommissioned.
        Close connections, flush buffers, save state.
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r}, status={self._status.value})>"


class AgentInitializationError(Exception):
    """Raised when an agent fails to initialize."""


class AgentExecutionError(Exception):
    """Raised when an agent fails to execute a task."""


class AgentRegistry:
    """
    Registry of available agents (PRD Section 33).

    The registry maps agent names to agent classes, enabling the scheduler
    to look up and instantiate agents dynamically.

    Usage:
        registry = AgentRegistry()
        registry.register("planner", PlannerAgent)
        agent = registry.create("planner", name="planner-1")
    """

    def __init__(self) -> None:
        self._agents: dict[str, type[AgentBase]] = {}

    def register(self, name: str, agent_class: type[AgentBase]) -> None:
        """Register an agent class.

        Args:
            name: Agent name (used for lookup).
            agent_class: The agent class (must inherit from AgentBase).

        Raises:
            TypeError: If agent_class is not a subclass of AgentBase.
            ValueError: If name is already registered.
        """
        if not (isinstance(agent_class, type) and issubclass(agent_class, AgentBase)):
            raise TypeError(
                f"agent_class must be a subclass of AgentBase, got {agent_class}"
            )
        if name in self._agents:
            raise ValueError(f"Agent '{name}' is already registered")
        self._agents[name] = agent_class

    def create(self, name: str, **kwargs: Any) -> AgentBase:
        """Create an instance of a registered agent.

        Args:
            name: Registered agent name.
            **kwargs: Passed to the agent constructor.

        Returns:
            Agent instance (not yet initialized).

        Raises:
            KeyError: If name is not registered.
        """
        if name not in self._agents:
            raise KeyError(f"Agent '{name}' not registered. Available: {list(self._agents)}")
        return self._agents[name](**kwargs)

    def list_agents(self) -> list[str]:
        """List all registered agent names."""
        return list(self._agents.keys())

    def is_registered(self, name: str) -> bool:
        """Check if an agent is registered."""
        return name in self._agents


# Global agent registry instance
_registry = AgentRegistry()


def get_registry() -> AgentRegistry:
    """Get the global agent registry."""
    return _registry


def register_agent(name: str) -> Any:
    """Decorator to register an agent class.

    Usage:
        @register_agent("planner")
        class PlannerAgent(AgentBase):
            ...
    """

    def decorator(cls: type[AgentBase]) -> type[AgentBase]:
        _registry.register(name, cls)
        return cls

    return decorator
