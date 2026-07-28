"""
Immutable Audit Log — PRD Section 22.1.

Implements an append-only, cryptographically hash-chained audit log.
Each entry's hash includes the previous entry's hash, making tampering
mathematically detectable (changing any entry invalidates all subsequent
hashes).

The audit log records every state-changing action: actor, action,
resource, before-state, after-state, timestamp. This is required for
SOC 2, GDPR, and EU AI Act compliance (PRD Section 28).

References:
    - PRD Section 22.1 (Security — Audit Logging)
    - PRD Section 28 (Compliance — 7-year retention)
    - Hash Chains: https://en.wikipedia.org/wiki/Hash_chain
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True, frozen=True)
class AuditEntry:
    """A single audit log entry (immutable, hash-chained).

    Attributes:
        id: Unique entry ID.
        timestamp: When the action occurred (UTC).
        actor: Who performed the action (user ID or agent name).
        action: What action was performed (e.g., "read", "write", "deploy").
        resource: What resource was affected (e.g., "model-v1", "doc-123").
        details: Additional action-specific metadata.
        previous_hash: Hash of the previous entry (None for the first entry).
        hash: This entry's hash (SHA-256 of all fields including previous_hash).
    """

    id: str
    timestamp: str  # ISO 8601 string (for immutability)
    actor: str
    action: str
    resource: str
    details: str  # JSON string (for immutability)
    previous_hash: str | None
    hash: str

    @classmethod
    def create(
        cls,
        actor: str,
        action: str,
        resource: str,
        details: dict[str, Any] | None = None,
        previous_hash: str | None = None,
    ) -> AuditEntry:
        """Create a new audit entry with computed hash.

        Args:
            actor: Who performed the action.
            action: What action was performed.
            resource: What resource was affected.
            details: Additional metadata.
            previous_hash: Hash of the previous entry (None for first).

        Returns:
            A new AuditEntry with computed hash.
        """
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).isoformat()
        details_str = json.dumps(details or {}, sort_keys=True, default=str)

        # Compute hash: SHA-256 of all fields
        hash_input = f"{entry_id}|{timestamp}|{actor}|{action}|{resource}|{details_str}|{previous_hash or ''}"
        entry_hash = hashlib.sha256(hash_input.encode()).hexdigest()

        return cls(
            id=entry_id,
            timestamp=timestamp,
            actor=actor,
            action=action,
            resource=resource,
            details=details_str,
            previous_hash=previous_hash,
            hash=entry_hash,
        )

    def verify(self, previous_hash: str | None) -> bool:
        """Verify this entry's hash is correct given the previous hash.

        Args:
            previous_hash: The hash of the previous entry (None for first).

        Returns:
            True if the hash is valid, False if tampered.
        """
        hash_input = f"{self.id}|{self.timestamp}|{self.actor}|{self.action}|{self.resource}|{self.details}|{previous_hash or ''}"
        expected = hashlib.sha256(hash_input.encode()).hexdigest()
        return expected == self.hash


class AuditLog:
    """Immutable, hash-chained audit log (PRD Section 22.1).

    The log is append-only — entries cannot be modified or deleted.
    Each entry's hash includes the previous entry's hash, creating a
    cryptographic chain. Tampering with any entry invalidates all
    subsequent entries.

    Usage:
        log = AuditLog()
        entry_id = await log.append(actor="user1", action="read", resource="doc1")
        entries = log.get_entries()
        assert log.verify_integrity() is True
    """

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    async def append(
        self,
        actor: str,
        action: str,
        resource: str,
        details: dict[str, Any] | None = None,
    ) -> str:
        """Append a new entry to the audit log.

        Args:
            actor: Who performed the action.
            action: What action was performed.
            resource: What resource was affected.
            details: Additional metadata.

        Returns:
            The entry ID.
        """
        previous_hash = self._entries[-1].hash if self._entries else None
        entry = AuditEntry.create(
            actor=actor,
            action=action,
            resource=resource,
            details=details,
            previous_hash=previous_hash,
        )
        self._entries.append(entry)
        return entry.id

    def get_entries(self) -> list[AuditEntry]:
        """Get all audit log entries.

        Returns:
            List of all AuditEntry objects (in order).
        """
        return list(self._entries)

    def get_entry(self, entry_id: str) -> AuditEntry | None:
        """Get a specific entry by ID.

        Args:
            entry_id: The entry ID to retrieve.

        Returns:
            The AuditEntry, or None if not found.
        """
        for entry in self._entries:
            if entry.id == entry_id:
                return entry
        return None

    def query(
        self,
        actor: str | None = None,
        action: str | None = None,
        resource: str | None = None,
    ) -> list[AuditEntry]:
        """Query audit log entries with optional filters.

        Args:
            actor: If provided, filter by actor.
            action: If provided, filter by action.
            resource: If provided, filter by resource.

        Returns:
            List of matching AuditEntry objects.
        """
        results = self._entries
        if actor is not None:
            results = [e for e in results if e.actor == actor]
        if action is not None:
            results = [e for e in results if e.action == action]
        if resource is not None:
            results = [e for e in results if e.resource == resource]
        return list(results)

    def verify_integrity(self) -> bool:
        """Verify the integrity of the entire audit log.

        Checks that every entry's hash is correct and that the hash
        chain is unbroken.

        Returns:
            True if the log is intact, False if any entry was tampered.
        """
        previous_hash: str | None = None
        for entry in self._entries:
            if not entry.verify(previous_hash):
                return False
            if entry.previous_hash != previous_hash:
                return False
            previous_hash = entry.hash
        return True

    def count(self) -> int:
        """Get the total number of entries."""
        return len(self._entries)

    def __repr__(self) -> str:
        return f"<AuditLog(entries={len(self._entries)})>"
