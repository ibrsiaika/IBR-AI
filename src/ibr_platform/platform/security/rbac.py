"""
Role-Based Access Control (RBAC) — PRD Section 22.1.

Implements the 4-role RBAC system: admin, engineer, researcher, viewer.
Each role has a set of permissions. The RBACManager assigns roles to users
and checks permissions.

Permissions matrix:
    read:   All roles
    write:  admin, engineer, researcher
    deploy: admin, engineer
    delete: admin only

References:
    - PRD Section 22.1 (Security Requirements — Authorization)
    - PRD Section 23 (Human-in-the-Loop — Governance)
"""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    """User roles (PRD Section 22.1 — at least 4 roles)."""

    ADMIN = "admin"        # Full access, including delete and config
    ENGINEER = "engineer"  # Deploy, write, read (no delete)
    RESEARCHER = "researcher"  # Write, read (no deploy, no delete)
    VIEWER = "viewer"      # Read only


# Permission matrix: role -> set of permissions
_ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {"read", "write", "deploy", "delete", "manage_users", "config"},
    Role.ENGINEER: {"read", "write", "deploy"},
    Role.RESEARCHER: {"read", "write"},
    Role.VIEWER: {"read"},
}


class RBACManager:
    """Manages role assignments and permission checks (PRD Section 22.1).

    Usage:
        rbac = RBACManager()
        rbac.assign_role("user1", Role.ADMIN)
        assert rbac.has_permission("user1", "deploy")
    """

    def __init__(self) -> None:
        self._user_roles: dict[str, Role] = {}

    def assign_role(self, user_id: str, role: Role) -> None:
        """Assign a role to a user.

        Args:
            user_id: Unique user identifier.
            role: The Role to assign.
        """
        self._user_roles[user_id] = role

    def revoke_role(self, user_id: str) -> None:
        """Revoke a user's role.

        Args:
            user_id: The user whose role to revoke.
        """
        self._user_roles.pop(user_id, None)

    def get_role(self, user_id: str) -> Role | None:
        """Get the role assigned to a user.

        Args:
            user_id: The user to query.

        Returns:
            The user's Role, or None if not assigned.
        """
        return self._user_roles.get(user_id)

    def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if a user has a specific permission.

        Args:
            user_id: The user to check.
            permission: The permission string (e.g., "read", "deploy").

        Returns:
            True if the user has the permission, False otherwise.
        """
        role = self._user_roles.get(user_id)
        if role is None:
            return False
        permissions = _ROLE_PERMISSIONS.get(role, set())
        return permission in permissions

    def get_permissions(self, user_id: str) -> set[str]:
        """Get all permissions for a user.

        Args:
            user_id: The user to query.

        Returns:
            Set of permission strings (empty if user has no role).
        """
        role = self._user_roles.get(user_id)
        if role is None:
            return set()
        return _ROLE_PERMISSIONS.get(role, set()).copy()

    def list_users(self) -> dict[str, Role]:
        """List all users and their roles.

        Returns:
            Dictionary mapping user_id to Role.
        """
        return dict(self._user_roles)

    def __repr__(self) -> str:
        return f"<RBACManager(users={len(self._user_roles)})>"
