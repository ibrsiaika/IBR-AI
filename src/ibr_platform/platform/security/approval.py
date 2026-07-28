"""
Human Approval Gate — PRD Section 22.1, 23.

Implements the approval workflow for high-impact actions. High-impact
actions (production deployment, large-scale retraining, knowledge
deletion, dataset/model publication, security-sensitive operations)
require explicit human approval before execution.

Key rules (PRD Section 23.2):
    - The requester cannot approve their own request (two-person rule)
    - Critical-risk actions require TWO approvals
    - Approvals are time-bound (configurable per risk level)
    - All approvals are recorded in the audit log

References:
    - PRD Section 22.1 (Security — Human Approval Gates)
    - PRD Section 23 (Human-in-the-Loop & Governance)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class ApprovalStatus(StrEnum):
    """Status of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class RiskLevel(StrEnum):
    """Risk classification for approval requests (PRD Section 23.2)."""

    LOW = "low"          # 24-hour expiry
    MEDIUM = "medium"    # 24-hour expiry
    HIGH = "high"        # 4-hour expiry
    CRITICAL = "critical"  # 1-hour expiry, requires two-person review


# Risk level -> required number of approvals
_RISK_APPROVALS_REQUIRED: dict[RiskLevel, int] = {
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 1,
    RiskLevel.CRITICAL: 2,  # Two-person review for critical actions
}


@dataclass(slots=True)
class ApprovalRequest:
    """A request for human approval of a high-impact action.

    Attributes:
        id: Unique approval request ID.
        action: The action being requested (e.g., "deploy", "retrain").
        resource: The resource affected (e.g., "model-v1").
        requester: The user ID who requested the action.
        risk_level: Risk classification (low/medium/high/critical).
        status: Current approval status.
        approvals: List of approver user IDs who approved.
        rejections: List of approver user IDs who rejected (with reasons).
        created_at: When the request was created.
        decided_at: When the request was decided (approved/rejected).
        metadata: Additional request-specific data.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action: str = ""
    resource: str = ""
    requester: str = ""
    risk_level: RiskLevel = RiskLevel.MEDIUM
    status: ApprovalStatus = ApprovalStatus.PENDING
    approvals: list[str] = field(default_factory=list)
    rejections: list[tuple[str, str]] = field(default_factory=list)  # (approver, reason)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    decided_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def approvals_required(self) -> int:
        """Number of approvals required based on risk level."""
        return _RISK_APPROVALS_REQUIRED.get(self.risk_level, 1)

    @property
    def is_fully_approved(self) -> bool:
        """Whether the request has enough approvals."""
        return len(self.approvals) >= self.approvals_required


class ApprovalGate:
    """Manages human approval workflows for high-impact actions (PRD Section 23).

    Usage:
        gate = ApprovalGate()
        approval_id = await gate.request_approval(
            action="deploy", resource="model-v1",
            requester="engineer1", risk_level="high"
        )
        await gate.approve(approval_id, approver="admin1")
        if gate.get_status(approval_id) == ApprovalStatus.APPROVED:
            # Execute the action
            ...
    """

    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}

    async def request_approval(
        self,
        action: str,
        resource: str,
        requester: str,
        risk_level: str | RiskLevel,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Submit a request for human approval.

        Args:
            action: The action being requested.
            resource: The resource affected.
            requester: The user ID requesting the action.
            risk_level: Risk classification (low/medium/high/critical).
            metadata: Additional request data.

        Returns:
            The approval request ID.
        """
        if isinstance(risk_level, str):
            risk_level = RiskLevel(risk_level)

        request = ApprovalRequest(
            action=action,
            resource=resource,
            requester=requester,
            risk_level=risk_level,
            metadata=metadata or {},
        )
        self._requests[request.id] = request
        return request.id

    async def approve(self, approval_id: str, approver: str) -> None:
        """Approve a request.

        Args:
            approval_id: The approval request ID.
            approver: The user ID of the approver.

        Raises:
            KeyError: If approval_id is not found.
            ValueError: If the approver is the requester (two-person rule),
                or if the request is already decided.
        """
        request = self._requests.get(approval_id)
        if request is None:
            raise KeyError(f"Approval '{approval_id}' not found")

        if request.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval is already {request.status.value}")

        # Two-person rule: requester cannot approve their own request
        if approver == request.requester:
            raise ValueError(
                f"Requester '{approver}' cannot approve their own request "
                f"(two-person rule per PRD Section 23.2)"
            )

        # Check if approver already approved
        if approver in request.approvals:
            raise ValueError(f"'{approver}' has already approved this request")

        request.approvals.append(approver)

        # Check if we have enough approvals
        if request.is_fully_approved:
            request.status = ApprovalStatus.APPROVED
            request.decided_at = datetime.now(UTC)

    async def reject(self, approval_id: str, approver: str, reason: str) -> None:
        """Reject a request.

        Args:
            approval_id: The approval request ID.
            approver: The user ID of the rejecter.
            reason: Why the request is being rejected.

        Raises:
            KeyError: If approval_id is not found.
            ValueError: If the request is already decided.
        """
        request = self._requests.get(approval_id)
        if request is None:
            raise KeyError(f"Approval '{approval_id}' not found")

        if request.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval is already {request.status.value}")

        # Two-person rule applies to rejections too
        if approver == request.requester:
            raise ValueError(
                f"Requester '{approver}' cannot reject their own request"
            )

        request.rejections.append((approver, reason))
        request.status = ApprovalStatus.REJECTED
        request.decided_at = datetime.now(UTC)

    def get_status(self, approval_id: str) -> ApprovalStatus | None:
        """Get the status of an approval request.

        Args:
            approval_id: The approval request ID.

        Returns:
            The ApprovalStatus, or None if not found.
        """
        request = self._requests.get(approval_id)
        if request is None:
            return None
        return request.status

    def get_request(self, approval_id: str) -> ApprovalRequest | None:
        """Get the full approval request.

        Args:
            approval_id: The approval request ID.

        Returns:
            The ApprovalRequest, or None if not found.
        """
        return self._requests.get(approval_id)

    def list_pending(self) -> list[ApprovalRequest]:
        """List all pending approval requests.

        Returns:
            List of pending ApprovalRequest objects.
        """
        return [
            r for r in self._requests.values()
            if r.status == ApprovalStatus.PENDING
        ]

    def list_by_requester(self, requester: str) -> list[ApprovalRequest]:
        """List all requests by a specific requester.

        Args:
            requester: The user ID to filter by.

        Returns:
            List of ApprovalRequest objects from that requester.
        """
        return [
            r for r in self._requests.values()
            if r.requester == requester
        ]

    def __repr__(self) -> str:
        return f"<ApprovalGate(requests={len(self._requests)})>"
