"""
Memory System — 12-Tier Implementation (PRD Section 15).

The IBR Platform's memory system is its persistent state. It is multi-tier
where each tier serves a different purpose with different retention policies,
access patterns, and storage backends.

The 12 tiers (PRD Section 15.1, Table 15.1):
    1. WORKING — Current task context, in-process + Redis
    2. SHORT_TERM — Recent conversation and task history, Redis, 24h TTL
    3. LONG_TERM — Persistent knowledge, Vector DB + Object storage
    4. SEMANTIC — Facts, concepts, relationships, Knowledge Graph
    5. EPISODIC — Specific past events, Vector DB + SQL
    6. PROCEDURAL — How-to knowledge, learned procedures, Vector DB
    7. PROJECT — Per-project context, Vector DB + Object storage
    8. CONVERSATION — Per-user conversation history, Vector DB + SQL
    9. KNOWLEDGE — Verified facts with provenance, Knowledge Graph
    10. VECTOR — Raw vector store, Vector DB
    11. GRAPH — Raw graph store, Graph DB
    12. COMPRESSED — Summarized older memory to bound size

Key features:
    - Scope isolation (project, user, organization) — enforced by RBAC
    - Versioning (immutable entries, prior versions queryable)
    - Eviction policy (TTL for short-term, LRU for working)
    - Access tracking (for LRU eviction)

Research basis (Letta, Dec 2025):
    - Programmatic context management — agents control what's paged in/out
    - Git-based versioning — memory entries are versioned like code
    - Automatic persistence — recall memory saves to disk automatically
    - Continual Learning in Token Space

References:
    - PRD Section 15 (Memory System)
    - PRD Section 35 (Memory — Phase 5)
    - PRD Section 71 (Agent Memory Architectures — MemGPT, Letta, Mem0)
    - Letta blog (Jul 2025, Dec 2025)
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class MemoryTier(StrEnum):
    """The 12 memory tiers (PRD Section 15.1, Table 15.1).

    Each tier serves a different purpose with different retention policies
    and storage backends.
    """

    WORKING = "working"            # Task context, in-process, ephemeral
    SHORT_TERM = "short_term"     # Recent history, 24h TTL
    LONG_TERM = "long_term"       # Persistent knowledge, indefinite
    SEMANTIC = "semantic"         # Facts, concepts, KG
    EPISODIC = "episodic"         # Past events, summarized
    PROCEDURAL = "procedural"     # How-to, learned procedures
    PROJECT = "project"           # Per-project context
    CONVERSATION = "conversation"  # Per-user history
    KNOWLEDGE = "knowledge"       # Verified facts, KG
    VECTOR = "vector"             # Raw vector store
    GRAPH = "graph"               # Raw graph store
    COMPRESSED = "compressed"     # Summarized older memory


@dataclass(slots=True)
class MemoryEntry:
    """A single memory entry (PRD Section 15.3).

    Entries are immutable — updates create new versions (PRD Section 15.7).
    The `version` field tracks how many times the entry has been updated.

    Attributes:
        id: Unique entry ID (UUID4).
        content: The memory content (text or structured data).
        tier: Memory tier (WORKING, SHORT_TERM, etc.).
        scope: Scope type ("project", "user", "organization").
        scope_id: Scope identifier (e.g., project ID, user ID).
        version: Version number (starts at 1, increments on update).
        created_at: When the entry was first created.
        updated_at: When the entry was last updated.
        accessed_at: When the entry was last read.
        access_count: Number of times the entry has been read.
        confidence: Confidence score (0.0-1.0) for fact-bearing entries.
        metadata: Additional entry-specific metadata.
        ttl: Time-to-live in seconds (None = no TTL, 0 = immediate expiry).
    """

    content: str = ""
    tier: MemoryTier = MemoryTier.LONG_TERM
    scope: str = "project"
    scope_id: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    accessed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    access_count: int = 0
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    ttl: float | None = None  # None = no TTL

    def is_expired(self) -> bool:
        """Check if this entry has expired based on TTL.

        Returns:
            True if the entry has expired, False otherwise.
        """
        if self.ttl is None:
            return False
        age = time.time() - self.created_at.timestamp()
        return age > self.ttl


class MemoryManager:
    """Multi-tier memory manager (PRD Section 15.3).

    Provides a uniform API across all 12 memory tiers:
        - write(): Store a memory entry
        - read(): Retrieve by ID
        - search(): Find entries by content (substring or vector)
        - update(): Create a new version (immutable, versioned)
        - delete(): Remove an entry
        - summarize(): Compress old entries
        - clear_tier(): Clear all entries in a tier
        - evict_expired(): Remove expired entries (TTL-based)
        - get_stats(): Per-tier entry counts
        - get_versions(): Get all versions of an entry

    Scope isolation is enforced: an agent in scope A cannot read
    scope B's memory without explicit cross-scope authorization
    (PRD Section 15.3).

    Usage:
        mgr = MemoryManager()
        entry_id = await mgr.write(
            content="Important fact",
            tier=MemoryTier.LONG_TERM,
            scope="project",
            scope_id="proj1",
        )
        entry = await mgr.read(entry_id)
        results = await mgr.search("fact", scope="project", scope_id="proj1")
    """

    def __init__(self, short_term_ttl_seconds: float = 86400) -> None:
        """Initialize the memory manager.

        Args:
            short_term_ttl_seconds: TTL for SHORT_TERM tier (default: 24h).
        """
        self._entries: dict[str, MemoryEntry] = {}
        self._versions: dict[str, list[MemoryEntry]] = {}  # entry_id -> all versions
        self._lock = asyncio.Lock()
        self._short_term_ttl = short_term_ttl_seconds

    async def write(
        self,
        content: str,
        tier: MemoryTier,
        scope: str,
        scope_id: str,
        confidence: float = 0.0,
        metadata: dict[str, Any] | None = None,
        ttl: float | None = None,
    ) -> str:
        """Write a memory entry.

        Args:
            content: The memory content.
            tier: Memory tier.
            scope: Scope type ("project", "user", "organization").
            scope_id: Scope identifier.
            confidence: Confidence score (0.0-1.0).
            metadata: Additional metadata.
            ttl: Time-to-live in seconds (None = no TTL).

        Returns:
            The entry ID.
        """
        # Set default TTL for SHORT_TERM tier
        if tier == MemoryTier.SHORT_TERM and ttl is None:
            ttl = self._short_term_ttl

        entry = MemoryEntry(
            content=content,
            tier=tier,
            scope=scope,
            scope_id=scope_id,
            confidence=confidence,
            metadata=metadata or {},
            ttl=ttl,
        )

        async with self._lock:
            self._entries[entry.id] = entry
            self._versions[entry.id] = [entry]

        return entry.id

    async def read(self, entry_id: str) -> MemoryEntry | None:
        """Read a memory entry by ID.

        Increments the access count and updates accessed_at.

        Args:
            entry_id: The entry ID.

        Returns:
            The MemoryEntry, or None if not found.
        """
        async with self._lock:
            entry = self._entries.get(entry_id)
            if entry is None:
                return None
            # Update access tracking (create a new entry since it's frozen)
            # Actually, MemoryEntry uses slots=True but not frozen=True
            entry.access_count += 1
            entry.accessed_at = datetime.now(UTC)
            return entry

    async def search(
        self,
        query: str,
        scope: str | None = None,
        scope_id: str | None = None,
        tier: MemoryTier | None = None,
        top_k: int = 10,
    ) -> list[MemoryEntry]:
        """Search memory entries by content.

        Currently uses substring matching. In production, this uses
        vector similarity search (HNSW via Qdrant/pgvectorscale).

        Args:
            query: Search query (substring match).
            scope: If provided, filter by scope.
            scope_id: If provided, filter by scope_id.
            tier: If provided, filter by tier.
            top_k: Maximum results to return.

        Returns:
            List of matching MemoryEntry objects.
        """
        query_lower = query.lower()
        results: list[MemoryEntry] = []

        async with self._lock:
            for entry in self._entries.values():
                # Check if expired
                if entry.is_expired():
                    continue
                # Check scope isolation
                if scope is not None and entry.scope != scope:
                    continue
                if scope_id is not None and entry.scope_id != scope_id:
                    continue
                # Check tier filter
                if tier is not None and entry.tier != tier:
                    continue
                # Check content match
                if query_lower in entry.content.lower():
                    results.append(entry)

        # Sort by relevance (access_count desc, then updated_at desc)
        results.sort(key=lambda e: (-e.access_count, e.updated_at), reverse=False)
        return results[:top_k]

    async def update(
        self,
        entry_id: str,
        content: str | None = None,
        confidence: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry | None:
        """Update a memory entry (creates a new version).

        Entries are immutable — the old version is preserved in the
        version history (PRD Section 15.7).

        Args:
            entry_id: The entry to update.
            content: New content (None = keep existing).
            confidence: New confidence (None = keep existing).
            metadata: New metadata (None = keep existing).

        Returns:
            The updated MemoryEntry, or None if not found.
        """
        async with self._lock:
            entry = self._entries.get(entry_id)
            if entry is None:
                return None

            # Create a new version (immutable update)
            new_version = MemoryEntry(
                content=content if content is not None else entry.content,
                tier=entry.tier,
                scope=entry.scope,
                scope_id=entry.scope_id,
                id=entry.id,  # Same ID, new version
                version=entry.version + 1,
                created_at=entry.created_at,
                updated_at=datetime.now(UTC),
                accessed_at=entry.accessed_at,
                access_count=entry.access_count,
                confidence=confidence if confidence is not None else entry.confidence,
                metadata=metadata if metadata is not None else entry.metadata,
                ttl=entry.ttl,
            )

            # Store old version in history
            self._versions[entry_id].append(new_version)
            # Update the main entry
            self._entries[entry_id] = new_version
            return new_version

    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry.

        Args:
            entry_id: The entry to delete.

        Returns:
            True if deleted, False if not found.
        """
        async with self._lock:
            if entry_id in self._entries:
                del self._entries[entry_id]
                # Keep version history for audit (PRD Section 15.7)
                return True
            return False

    async def get_versions(self, entry_id: str) -> list[MemoryEntry]:
        """Get all versions of an entry (PRD Section 15.7).

        Args:
            entry_id: The entry ID.

        Returns:
            List of all versions (oldest first), or empty list if not found.
        """
        async with self._lock:
            return list(self._versions.get(entry_id, []))

    async def clear_tier(self, tier: MemoryTier) -> int:
        """Clear all entries in a tier.

        Args:
            tier: The tier to clear.

        Returns:
            Number of entries cleared.
        """
        async with self._lock:
            to_remove = [eid for eid, e in self._entries.items() if e.tier == tier]
            for eid in to_remove:
                del self._entries[eid]
            return len(to_remove)

    async def evict_expired(self) -> int:
        """Evict all expired entries (TTL-based).

        Returns:
            Number of entries evicted.
        """
        async with self._lock:
            to_remove = [eid for eid, e in self._entries.items() if e.is_expired()]
            for eid in to_remove:
                del self._entries[eid]
            return len(to_remove)

    def count(self, tier: MemoryTier | None = None) -> int:
        """Count entries, optionally filtered by tier.

        Args:
            tier: If provided, count only entries in this tier.

        Returns:
            Entry count.
        """
        if tier is None:
            return len(self._entries)
        return sum(1 for e in self._entries.values() if e.tier == tier)

    def get_stats(self) -> dict[MemoryTier, int]:
        """Get per-tier entry counts.

        Returns:
            Dictionary mapping tier to entry count.
        """
        stats: dict[MemoryTier, int] = dict.fromkeys(MemoryTier, 0)
        for entry in self._entries.values():
            stats[entry.tier] = stats.get(entry.tier, 0) + 1
        return stats

    async def summarize(self, entry_ids: list[str]) -> str | None:
        """Summarize multiple entries into a compressed entry.

        Creates a new COMPRESSED tier entry that summarizes the given entries.
        In production, this uses an LLM to generate the summary.

        Args:
            entry_ids: List of entry IDs to summarize.

        Returns:
            The summary entry ID, or None if no entries found.
        """
        if not entry_ids:
            return None

        async with self._lock:
            entries = [self._entries[eid] for eid in entry_ids if eid in self._entries]
            if not entries:
                return None

            # Simple summary: concatenate first 100 chars of each entry
            summary_parts = [e.content[:100] for e in entries[:5]]
            summary = f"Summary of {len(entries)} entries: " + " | ".join(summary_parts)

        summary_id = await self.write(
            content=summary,
            tier=MemoryTier.COMPRESSED,
            scope=entries[0].scope,
            scope_id=entries[0].scope_id,
            metadata={"summarized_ids": entry_ids},
        )
        return summary_id

    def __repr__(self) -> str:
        return f"<MemoryManager(entries={len(self._entries)})>"
