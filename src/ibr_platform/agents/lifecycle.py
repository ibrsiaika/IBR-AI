"""
Agent Lifecycle Management (PRD Section 11.3).

Manages the lifecycle of agent processes: spawn, initialize, execute,
checkpoint, terminate. Agents are stateless between tasks — all state
lives in memory stores. This enables horizontal scaling, fault tolerance,
and debugging.

The lifecycle manager:
1. Spawns agents (creates instance, calls initialize)
2. Tracks active agents
3. Routes messages to the correct agent
4. Handles failures (retry, escalate, degrade)
5. Terminates agents (calls shutdown, removes from active set)

References:
    - PRD Section 11.3 (Agent Lifecycle)
    - PRD Section 10.3 (Key Architectural Decisions — agents are stateless)
"""

from __future__ import annotations

import asyncio
import contextlib
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ibr_platform.agents.base import (
    AgentBase,
    AgentExecutionError,
    AgentInitializationError,
    AgentResult,
    AgentStatus,
    HealthStatus,
    Task,
)


@dataclass(slots=True)
class AgentInstance:
    """A running agent instance tracked by the lifecycle manager.

    Attributes:
        id: Unique agent instance ID.
        name: Agent name (from the roster).
        agent: The AgentBase instance.
        status: Current agent status.
        spawned_at: When the agent was spawned.
        last_active: When the agent last executed a task.
        tasks_completed: Count of completed tasks.
        tasks_failed: Count of failed tasks.
    """

    id: str
    name: str
    agent: AgentBase
    status: AgentStatus = AgentStatus.PENDING
    spawned_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_active: datetime = field(default_factory=lambda: datetime.now(UTC))
    tasks_completed: int = 0
    tasks_failed: int = 0


class AgentLifecycle:
    """Manages agent lifecycles (PRD Section 11.3).

    The lifecycle manager is responsible for spawning, tracking, and
    terminating agents. It provides a central registry of active agents
    and routes messages to the correct agent.

    Agents are stateless between tasks — all state lives in memory stores
    (PRD Section 10.3). The lifecycle manager does NOT store agent state;
    it only tracks which agents are active and their health.

    Usage:
        lifecycle = AgentLifecycle()
        agent_id = await lifecycle.spawn("planner", PlannerAgent, config={})
        result = await lifecycle.execute(agent_id, task)
        await lifecycle.terminate(agent_id)
    """

    def __init__(self) -> None:
        self._agents: dict[str, AgentInstance] = {}
        self._lock = asyncio.Lock()

    @property
    def active_agents(self) -> dict[str, AgentInstance]:
        """Read-only view of active agents (for testing)."""
        return dict(self._agents)

    async def spawn(
        self,
        name: str,
        agent_class: type[AgentBase],
        config: dict[str, Any] | None = None,
    ) -> str:
        """Spawn a new agent instance.

        Creates an instance of `agent_class`, calls initialize(), and
        registers it in the active agent set.

        Args:
            name: Human-readable agent name.
            agent_class: The agent class (must inherit from AgentBase).
            config: Configuration dictionary for initialize().

        Returns:
            Unique agent instance ID.

        Raises:
            AgentInitializationError: If initialize() fails.
        """
        agent = agent_class(name=name)
        agent_id = str(uuid.uuid4())

        try:
            await agent.initialize(config or {})
            agent._status = AgentStatus.PENDING
            agent._initialized = True
        except Exception as e:
            raise AgentInitializationError(
                f"Failed to initialize agent '{name}': {e}"
            ) from e

        instance = AgentInstance(
            id=agent_id,
            name=name,
            agent=agent,
            status=AgentStatus.PENDING,
        )

        async with self._lock:
            self._agents[agent_id] = instance

        return agent_id

    async def execute(self, agent_id: str, task: Task) -> AgentResult:
        """Execute a task on the specified agent.

        Args:
            agent_id: The agent instance ID returned by spawn().
            task: The task to execute.

        Returns:
            AgentResult from the agent's execute() method.

        Raises:
            KeyError: If agent_id is not active.
            AgentExecutionError: If execute() fails.
        """
        async with self._lock:
            instance = self._agents.get(agent_id)
            if instance is None:
                raise KeyError(f"Agent '{agent_id}' not found or terminated")
            instance.status = AgentStatus.IN_PROGRESS
            instance.last_active = datetime.now(UTC)

        try:
            result = await instance.agent.execute(task)
            async with self._lock:
                instance.status = AgentStatus.COMPLETE
                instance.tasks_completed += 1
                instance.last_active = datetime.now(UTC)
            return result
        except Exception as e:
            async with self._lock:
                instance.status = AgentStatus.FAILED
                instance.tasks_failed += 1
            raise AgentExecutionError(
                f"Agent '{instance.name}' failed to execute task: {e}"
            ) from e

    async def terminate(self, agent_id: str) -> None:
        """Terminate an agent instance.

        Calls shutdown() on the agent and removes it from the active set.

        Args:
            agent_id: The agent instance ID to terminate.

        Raises:
            KeyError: If agent_id is not active.
        """
        async with self._lock:
            instance = self._agents.pop(agent_id, None)
            if instance is None:
                raise KeyError(f"Agent '{agent_id}' not found or already terminated")

        with contextlib.suppress(Exception):
            await instance.agent.shutdown()
        instance.status = AgentStatus.SHUTDOWN

    async def health_check(self, agent_id: str) -> HealthStatus:
        """Check the health of an agent.

        Args:
            agent_id: The agent instance ID.

        Returns:
            HealthStatus from the agent's health_check() method.

        Raises:
            KeyError: If agent_id is not active.
        """
        async with self._lock:
            instance = self._agents.get(agent_id)
            if instance is None:
                raise KeyError(f"Agent '{agent_id}' not found or terminated")
        return await instance.agent.health_check()

    def list_active(self) -> list[str]:
        """List all active agent IDs.

        Returns:
            List of agent instance IDs currently active.
        """
        return list(self._agents.keys())

    def get_info(self, agent_id: str) -> dict[str, Any] | None:
        """Get information about an agent instance.

        Args:
            agent_id: The agent instance ID.

        Returns:
            Dictionary with agent info, or None if not found.
        """
        instance = self._agents.get(agent_id)
        if instance is None:
            return None
        return {
            "id": instance.id,
            "name": instance.name,
            "status": instance.status.value,
            "spawned_at": instance.spawned_at.isoformat(),
            "last_active": instance.last_active.isoformat(),
            "tasks_completed": instance.tasks_completed,
            "tasks_failed": instance.tasks_failed,
        }

    async def terminate_all(self) -> None:
        """Terminate all active agents (for graceful shutdown)."""
        agent_ids = list(self._agents.keys())
        for agent_id in agent_ids:
            with contextlib.suppress(Exception):
                await self.terminate(agent_id)

    def __repr__(self) -> str:
        return f"<AgentLifecycle(active={len(self._agents)})>"
