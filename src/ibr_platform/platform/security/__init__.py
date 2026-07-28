"""
Security package — Security & Safety Requirements (PRD Section 22).

Contains:
    - rbac: Role-Based Access Control (4 roles, permission matrix)
    - audit: Immutable, hash-chained audit log (tamper-evident)
    - approval: Human approval gate for high-impact actions
    - sandbox: Agent sandbox configuration (container isolation)
"""

from ibr_platform.platform.security.approval import (
    ApprovalGate,
    ApprovalRequest,
    ApprovalStatus,
    RiskLevel,
)
from ibr_platform.platform.security.audit import AuditEntry, AuditLog
from ibr_platform.platform.security.rbac import RBACManager, Role
from ibr_platform.platform.security.sandbox import SandboxConfig

__all__ = [
    # RBAC
    "RBACManager",
    "Role",
    # Audit
    "AuditEntry",
    "AuditLog",
    # Approval
    "ApprovalGate",
    "ApprovalRequest",
    "ApprovalStatus",
    "RiskLevel",
    # Sandbox
    "SandboxConfig",
]
