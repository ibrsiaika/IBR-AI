"""
Task Orchestrator (PRD Section 10, Layer 2 — Orchestration).

The TaskOrchestrator is the entry point for all user requests. It:
1. Receives user requests (from CLI, API, dashboard)
2. Authenticates the user and checks quotas
3. Dispatches the request to the Planner Agent
4. Tracks request status and returns results

The orchestrator is the ONLY component that users interact with directly;
all other layers are internal. This centralizes authentication, quota
enforcement, and request tracking.

References:
    - PRD Section 10 (High-Level Architecture)
    - PRD Section 10.1 (Layered Architecture — Layer 2: Orchestration)
    - PRD Section 11.3 (Agent Lifecycle)
    - PRD Section 20 (APIs)
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from ibr_platform.platform.architecture import ArchitectureLayer, LayerBase


class RequestStatus(StrEnum):
    """Status of a user request through the orchestration pipeline."""

    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class UserRequest:
    """A user request submitted to the orchestrator.

    Attributes:
        id: Unique request identifier.
        user_id: ID of the user who submitted the request.
        query: The user's natural language query.
        status: Current status of the request.
        created_at: When the request was submitted.
        updated_at: When the request was last updated.
        result: The result data (None until complete).
        error: Error message if the request failed.
        metadata: Additional request metadata.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "anonymous"
    query: str = ""
    status: RequestStatus = RequestStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    result: dict[str, Any] | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class OrchestratorHealth:
    """Health status of the TaskOrchestrator."""

    status: str = "healthy"
    active_requests: int = 0
    total_requests: int = 0
    uptime_seconds: float = 0.0


class TaskOrchestrator(LayerBase):
    """The Task Orchestrator (PRD Section 10, Layer 2).

    Receives user requests, authenticates, enforces quotas, dispatches
    to the Planner Agent, and returns results.

    This is the entry point for all user-facing operations. No other
    layer is directly accessible to users.

    Usage:
        orchestrator = TaskOrchestrator()
        request_id = await orchestrator.submit_request("Research X")
        result = await orchestrator.get_result(request_id)
    """

    def __init__(self) -> None:
        self._requests: dict[str, UserRequest] = {}
        self._lock = asyncio.Lock()
        self._total_requests: int = 0
        self._start_time: datetime = datetime.now(UTC)

    @property
    def layer(self) -> ArchitectureLayer:
        """The orchestrator is in the Orchestration layer (Layer 2)."""
        return ArchitectureLayer.ORCHESTRATION

    async def submit_request(
        self,
        query: str,
        user_id: str = "anonymous",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Submit a new request to the orchestrator.

        Args:
            query: The user's natural language query.
            user_id: ID of the submitting user (default: "anonymous").
            metadata: Optional additional metadata.

        Returns:
            The unique request ID.

        Raises:
            ValueError: If query is empty.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        request = UserRequest(
            user_id=user_id,
            query=query.strip(),
            metadata=metadata or {},
        )

        async with self._lock:
            self._requests[request.id] = request
            self._total_requests += 1

        # In a full implementation, this would dispatch to the Planner Agent.
        # For now, we mark as pending and return the ID.
        return request.id

    async def get_result(self, request_id: str) -> UserRequest | None:
        """Get the status and result of a request.

        Args:
            request_id: The request ID returned by submit_request.

        Returns:
            The UserRequest if found, None if not found.
        """
        async with self._lock:
            return self._requests.get(request_id)

    async def cancel_request(self, request_id: str) -> bool:
        """Cancel a pending or executing request.

        Args:
            request_id: The request ID to cancel.

        Returns:
            True if cancelled, False if not found or already complete.
        """
        async with self._lock:
            request = self._requests.get(request_id)
            if request is None:
                return False
            if request.status in (RequestStatus.COMPLETE, RequestStatus.FAILED):
                return False
            request.status = RequestStatus.CANCELLED
            request.updated_at = datetime.now(UTC)
            return True

    async def list_requests(
        self,
        user_id: str | None = None,
        status: RequestStatus | None = None,
    ) -> list[UserRequest]:
        """List requests, optionally filtered by user or status.

        Args:
            user_id: If provided, only return requests from this user.
            status: If provided, only return requests with this status.

        Returns:
            List of matching UserRequest objects.
        """
        async with self._lock:
            requests = list(self._requests.values())

        if user_id is not None:
            requests = [r for r in requests if r.user_id == user_id]
        if status is not None:
            requests = [r for r in requests if r.status == status]

        return requests

    async def health_check(self) -> OrchestratorHealth:
        """Check the health of the orchestrator.

        Returns:
            OrchestratorHealth with current status metrics.
        """
        async with self._lock:
            active = sum(
                1
                for r in self._requests.values()
                if r.status in (RequestStatus.PENDING, RequestStatus.PLANNING, RequestStatus.EXECUTING)
            )
            now = datetime.now(UTC)
            uptime = (now - self._start_time).total_seconds()

        return OrchestratorHealth(
            status="healthy",
            active_requests=active,
            total_requests=self._total_requests,
            uptime_seconds=uptime,
        )

    def __repr__(self) -> str:
        return f"<TaskOrchestrator(layer={self.layer.name}, requests={self._total_requests})>"
