"""
Agent Communication Protocol — JSON Message Envelope (PRD Section 11.2).

All inter-agent communication uses a structured JSON envelope. This module
defines the AgentMessage dataclass with all required fields from the PRD,
plus serialization (to_dict, to_json, from_dict, from_json).

The envelope fields (PRD Section 11.2):
    - task_id: Globally unique identifier
    - parent_task_id: For hierarchical plans
    - agent_source: Sending agent
    - agent_target: Receiving agent
    - task: The work to be done
    - priority: P0-P2
    - dependencies: List of task IDs that must complete first
    - confidence: 0.0-1.0 for fact-bearing messages
    - evidence: List of source artifact IDs
    - status: pending/in_progress/complete/failed/blocked
    - memory_ids: List of memory entries referenced
    - logs: List of structured log entries
    - artifacts: List of produced artifact IDs
    - timestamp: When the message was created
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ibr_platform.agents.base import MessageStatus, Priority


@dataclass(slots=True)
class AgentMessage:
    """Inter-agent communication envelope (PRD Section 11.2).

    All agents communicate via this structured envelope — never through
    shared mutable state. This enables: audit logging, debugging,
    serialization for network transport, and replay for testing.

    Attributes:
        task_id: Globally unique task identifier (auto-generated).
        parent_task_id: Parent task ID (for hierarchical plans).
        agent_source: Name of the sending agent.
        agent_target: Name of the receiving agent.
        task: The work to be done (natural language or structured).
        priority: Task priority (P0-CRITICAL, P1-HIGH, P2-NORMAL, P3-LOW).
        dependencies: List of task IDs that must complete before this task.
        confidence: Confidence score (0.0-1.0) for fact-bearing messages.
        evidence: List of source artifact IDs supporting this task.
        status: Current status (pending/in_progress/complete/failed/blocked).
        memory_ids: List of memory entries referenced.
        logs: List of structured log entries.
        artifacts: List of produced artifact IDs.
        timestamp: When the message was created.
        metadata: Additional message-specific metadata.
    """

    task: str = ""
    agent_source: str = ""
    agent_target: str = ""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_task_id: str | None = None
    priority: Priority = Priority.P2_NORMAL
    dependencies: list[str] = field(default_factory=list)
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)
    status: MessageStatus = MessageStatus.PENDING
    memory_ids: list[str] = field(default_factory=list)
    logs: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dictionary (suitable for JSON).

        Returns:
            Dictionary representation with all fields.
        """
        return {
            "task_id": self.task_id,
            "parent_task_id": self.parent_task_id,
            "agent_source": self.agent_source,
            "agent_target": self.agent_target,
            "task": self.task,
            "priority": self.priority.name,
            "dependencies": list(self.dependencies),
            "confidence": self.confidence,
            "evidence": list(self.evidence),
            "status": self.status.value,
            "memory_ids": list(self.memory_ids),
            "logs": list(self.logs),
            "artifacts": list(self.artifacts),
            "timestamp": self.timestamp.isoformat(),
            "metadata": dict(self.metadata),
        }

    def to_json(self, indent: int | None = None) -> str:
        """Serialize to a JSON string.

        Args:
            indent: If provided, pretty-print with this indent level.

        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentMessage:
        """Deserialize from a dictionary.

        Args:
            data: Dictionary with message fields.

        Returns:
            AgentMessage instance.
        """
        # Parse priority (accept name or value)
        priority_raw = data.get("priority", "P2_NORMAL")
        if isinstance(priority_raw, str):
            try:
                priority = Priority[priority_raw]
            except KeyError:
                try:
                    priority = Priority(int(priority_raw))
                except (ValueError, TypeError):
                    priority = Priority.P2_NORMAL
        elif isinstance(priority_raw, int):
            priority = Priority(priority_raw)
        else:
            priority = Priority.P2_NORMAL

        # Parse status (accept name or value)
        status_raw = data.get("status", "pending")
        if isinstance(status_raw, str):
            try:
                status = MessageStatus(status_raw)
            except ValueError:
                status = MessageStatus.PENDING
        else:
            status = MessageStatus.PENDING

        # Parse timestamp
        timestamp_raw = data.get("timestamp")
        if isinstance(timestamp_raw, str):
            try:
                timestamp = datetime.fromisoformat(timestamp_raw)
            except ValueError:
                timestamp = datetime.now(UTC)
        elif isinstance(timestamp_raw, datetime):
            timestamp = timestamp_raw
        else:
            timestamp = datetime.now(UTC)

        return cls(
            task=data.get("task", ""),
            agent_source=data.get("agent_source", ""),
            agent_target=data.get("agent_target", ""),
            task_id=data.get("task_id", str(uuid.uuid4())),
            parent_task_id=data.get("parent_task_id"),
            priority=priority,
            dependencies=list(data.get("dependencies", [])),
            confidence=float(data.get("confidence", 0.0)),
            evidence=list(data.get("evidence", [])),
            status=status,
            memory_ids=list(data.get("memory_ids", [])),
            logs=list(data.get("logs", [])),
            artifacts=list(data.get("artifacts", [])),
            timestamp=timestamp,
            metadata=dict(data.get("metadata", {})),
        )

    @classmethod
    def from_json(cls, json_str: str) -> AgentMessage:
        """Deserialize from a JSON string.

        Args:
            json_str: JSON string representation.

        Returns:
            AgentMessage instance.
        """
        return cls.from_dict(json.loads(json_str))

    def __repr__(self) -> str:
        return (
            f"<AgentMessage(task_id={self.task_id[:8]}..., "
            f"source={self.agent_source}, target={self.agent_target}, "
            f"status={self.status.value})>"
        )
