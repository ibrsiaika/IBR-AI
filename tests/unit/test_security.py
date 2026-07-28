"""
Tests for Section 22 — Security & Safety Requirements.

Verifies RBAC (roles, permissions), audit logging (immutable, hash-chained),
approval gates (human approval for high-impact actions), and sandboxing.

Run: pytest tests/unit/test_security.py -v
"""
from __future__ import annotations

import pytest


class TestRBAC:
    """Test Role-Based Access Control (PRD Section 22.1)."""

    def test_rbac_importable(self) -> None:
        """RBAC module is importable."""
        from ibr_platform.platform.security.rbac import RBACManager, Role
        assert RBACManager is not None
        assert Role is not None

    def test_roles_defined(self) -> None:
        """All 4 roles are defined (admin, engineer, researcher, viewer)."""
        from ibr_platform.platform.security.rbac import Role
        assert hasattr(Role, "ADMIN")
        assert hasattr(Role, "ENGINEER")
        assert hasattr(Role, "RESEARCHER")
        assert hasattr(Role, "VIEWER")

    def test_rbac_can_be_instantiated(self) -> None:
        """RBACManager can be instantiated."""
        from ibr_platform.platform.security.rbac import RBACManager
        rbac = RBACManager()
        assert rbac is not None

    def test_rbac_assign_role(self) -> None:
        """RBACManager can assign a role to a user."""
        from ibr_platform.platform.security.rbac import RBACManager, Role
        rbac = RBACManager()
        rbac.assign_role("user1", Role.ADMIN)
        assert rbac.get_role("user1") == Role.ADMIN

    def test_rbac_check_permission_admin(self) -> None:
        """Admin role has all permissions."""
        from ibr_platform.platform.security.rbac import RBACManager, Role
        rbac = RBACManager()
        rbac.assign_role("admin1", Role.ADMIN)
        assert rbac.has_permission("admin1", "deploy")
        assert rbac.has_permission("admin1", "delete")
        assert rbac.has_permission("admin1", "read")
        assert rbac.has_permission("admin1", "write")

    def test_rbac_check_permission_viewer(self) -> None:
        """Viewer role has only read permission."""
        from ibr_platform.platform.security.rbac import RBACManager, Role
        rbac = RBACManager()
        rbac.assign_role("viewer1", Role.VIEWER)
        assert rbac.has_permission("viewer1", "read")
        assert not rbac.has_permission("viewer1", "write")
        assert not rbac.has_permission("viewer1", "deploy")
        assert not rbac.has_permission("viewer1", "delete")

    def test_rbac_check_permission_researcher(self) -> None:
        """Researcher role has read + write but not deploy/delete."""
        from ibr_platform.platform.security.rbac import RBACManager, Role
        rbac = RBACManager()
        rbac.assign_role("res1", Role.RESEARCHER)
        assert rbac.has_permission("res1", "read")
        assert rbac.has_permission("res1", "write")
        assert not rbac.has_permission("res1", "deploy")
        assert not rbac.has_permission("res1", "delete")

    def test_rbac_user_without_role(self) -> None:
        """User without role has no permissions."""
        from ibr_platform.platform.security.rbac import RBACManager
        rbac = RBACManager()
        assert not rbac.has_permission("unknown", "read")

    def test_rbac_revoke_role(self) -> None:
        """RBACManager can revoke a role."""
        from ibr_platform.platform.security.rbac import RBACManager, Role
        rbac = RBACManager()
        rbac.assign_role("user1", Role.ADMIN)
        rbac.revoke_role("user1")
        assert rbac.get_role("user1") is None


class TestAuditLog:
    """Test the immutable audit log (PRD Section 22.1)."""

    def test_audit_log_importable(self) -> None:
        """AuditLog is importable."""
        from ibr_platform.platform.security.audit import AuditLog
        assert AuditLog is not None

    def test_audit_log_can_be_instantiated(self) -> None:
        """AuditLog can be instantiated."""
        from ibr_platform.platform.security.audit import AuditLog
        log = AuditLog()
        assert log is not None

    async def test_audit_log_append(self) -> None:
        """AuditLog can append entries."""
        from ibr_platform.platform.security.audit import AuditLog
        log = AuditLog()
        entry_id = await log.append(
            actor="user1",
            action="read",
            resource="doc1",
            details={"query": "test"},
        )
        assert entry_id is not None
        assert isinstance(entry_id, str)

    async def test_audit_log_entries_have_hash_chain(self) -> None:
        """Audit log entries are hash-chained (tamper-evident)."""
        from ibr_platform.platform.security.audit import AuditLog
        log = AuditLog()
        await log.append(actor="u1", action="read", resource="r1")
        await log.append(actor="u2", action="write", resource="r2")
        entries = log.get_entries()
        assert len(entries) == 2
        # Each entry has a hash field
        assert hasattr(entries[0], "hash")
        assert hasattr(entries[1], "hash")
        # Second entry's hash includes the first entry's hash (chaining)
        assert entries[1].previous_hash == entries[0].hash

    async def test_audit_log_verify_integrity(self) -> None:
        """Audit log integrity can be verified."""
        from ibr_platform.platform.security.audit import AuditLog
        log = AuditLog()
        await log.append(actor="u1", action="read", resource="r1")
        await log.append(actor="u2", action="write", resource="r2")
        assert log.verify_integrity() is True

    async def test_audit_log_query_by_actor(self) -> None:
        """Audit log can be queried by actor."""
        from ibr_platform.platform.security.audit import AuditLog
        log = AuditLog()
        await log.append(actor="alice", action="read", resource="r1")
        await log.append(actor="bob", action="write", resource="r2")
        await log.append(actor="alice", action="delete", resource="r3")
        alice_entries = log.query(actor="alice")
        assert len(alice_entries) == 2
        assert all(e.actor == "alice" for e in alice_entries)


class TestApprovalGate:
    """Test the human approval gate (PRD Section 22.1, 23)."""

    def test_approval_gate_importable(self) -> None:
        """ApprovalGate is importable."""
        from ibr_platform.platform.security.approval import ApprovalGate
        assert ApprovalGate is not None

    def test_approval_gate_can_be_instantiated(self) -> None:
        """ApprovalGate can be instantiated."""
        from ibr_platform.platform.security.approval import ApprovalGate
        gate = ApprovalGate()
        assert gate is not None

    async def test_request_approval_returns_id(self) -> None:
        """Requesting approval returns a unique approval ID."""
        from ibr_platform.platform.security.approval import ApprovalGate
        gate = ApprovalGate()
        approval_id = await gate.request_approval(
            action="deploy",
            resource="model-v1",
            requester="engineer1",
            risk_level="high",
        )
        assert approval_id is not None
        assert isinstance(approval_id, str)

    async def test_approval_pending_status(self) -> None:
        """New approval request has 'pending' status."""
        from ibr_platform.platform.security.approval import ApprovalGate, ApprovalStatus
        gate = ApprovalGate()
        approval_id = await gate.request_approval(
            action="deploy", resource="m1", requester="e1", risk_level="high"
        )
        status = gate.get_status(approval_id)
        assert status == ApprovalStatus.PENDING

    async def test_approval_approve(self) -> None:
        """Approval can be granted."""
        from ibr_platform.platform.security.approval import ApprovalGate, ApprovalStatus
        gate = ApprovalGate()
        approval_id = await gate.request_approval(
            action="deploy", resource="m1", requester="e1", risk_level="high"
        )
        await gate.approve(approval_id, approver="admin1")
        assert gate.get_status(approval_id) == ApprovalStatus.APPROVED

    async def test_approval_reject(self) -> None:
        """Approval can be rejected."""
        from ibr_platform.platform.security.approval import ApprovalGate, ApprovalStatus
        gate = ApprovalGate()
        approval_id = await gate.request_approval(
            action="deploy", resource="m1", requester="e1", risk_level="high"
        )
        await gate.reject(approval_id, approver="admin1", reason="Not ready")
        assert gate.get_status(approval_id) == ApprovalStatus.REJECTED

    async def test_approval_two_person_review(self) -> None:
        """High-impact actions require two-person review."""
        from ibr_platform.platform.security.approval import ApprovalGate, ApprovalStatus
        gate = ApprovalGate()
        approval_id = await gate.request_approval(
            action="deploy", resource="m1", requester="e1", risk_level="critical"
        )
        # First approval
        await gate.approve(approval_id, approver="admin1")
        # Critical actions need two approvals
        assert gate.get_status(approval_id) == ApprovalStatus.PENDING
        # Second approval
        await gate.approve(approval_id, approver="admin2")
        assert gate.get_status(approval_id) == ApprovalStatus.APPROVED

    async def test_approval_requester_cannot_approve(self) -> None:
        """The requester cannot approve their own request (two-person rule)."""
        from ibr_platform.platform.security.approval import ApprovalGate
        gate = ApprovalGate()
        approval_id = await gate.request_approval(
            action="deploy", resource="m1", requester="e1", risk_level="high"
        )
        with pytest.raises(ValueError, match="cannot approve"):
            await gate.approve(approval_id, approver="e1")


class TestSandbox:
    """Test the agent sandbox configuration (PRD Section 22.1)."""

    def test_sandbox_importable(self) -> None:
        """SandboxConfig is importable."""
        from ibr_platform.platform.security.sandbox import SandboxConfig
        assert SandboxConfig is not None

    def test_sandbox_default_config(self) -> None:
        """SandboxConfig has secure defaults."""
        from ibr_platform.platform.security.sandbox import SandboxConfig
        config = SandboxConfig()
        assert config.network_egress is False  # No network by default
        assert config.filesystem_readonly is True  # Read-only FS by default
        assert config.max_memory_mb > 0
        assert config.timeout_seconds > 0

    def test_sandbox_runtime_class(self) -> None:
        """SandboxConfig supports gVisor runtime class (ADR-0015)."""
        from ibr_platform.platform.security.sandbox import SandboxConfig
        config = SandboxConfig(runtime_class="gvisor")
        assert config.runtime_class == "gvisor"

    def test_sandbox_allowlist(self) -> None:
        """SandboxConfig supports network allowlist."""
        from ibr_platform.platform.security.sandbox import SandboxConfig
        config = SandboxConfig(
            network_egress=True,
            network_allowlist=["api.openai.com", "api.anthropic.com"],
        )
        assert config.network_egress is True
        assert len(config.network_allowlist) == 2
