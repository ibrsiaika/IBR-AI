"""
Tests for Section 35 — Memory System (12-tier implementation).

Verifies:
1. All 12 memory tiers are defined and functional
2. MemoryManager API (write, read, search, update, delete, summarize)
3. Scope isolation (project, user, organization)
4. Versioning (immutable entries, prior versions queryable)
5. Eviction policy (LRU-based)

Run: pytest tests/unit/test_memory_system.py -v
"""
from __future__ import annotations

import pytest

ALL_TIERS = [
    "WORKING",
    "SHORT_TERM",
    "LONG_TERM",
    "SEMANTIC",
    "EPISODIC",
    "PROCEDURAL",
    "PROJECT",
    "CONVERSATION",
    "KNOWLEDGE",
    "VECTOR",
    "GRAPH",
    "COMPRESSED",
]


class TestMemoryTier:
    """Test the MemoryTier enum (PRD Section 15.1)."""

    def test_tier_importable(self) -> None:
        """MemoryTier is importable."""
        from ibr_platform.platform.memory import MemoryTier
        assert MemoryTier is not None

    @pytest.mark.parametrize("tier_name", ALL_TIERS)
    def test_tier_defined(self, tier_name: str) -> None:
        """Each of the 12 tiers is defined."""
        from ibr_platform.platform.memory import MemoryTier
        assert hasattr(MemoryTier, tier_name), f"Tier {tier_name} not defined"

    def test_tier_count(self) -> None:
        """Exactly 12 tiers are defined."""
        from ibr_platform.platform.memory import MemoryTier
        tiers = list(MemoryTier)
        assert len(tiers) == 12, f"Expected 12 tiers, got {len(tiers)}"


class TestMemoryEntry:
    """Test the MemoryEntry dataclass."""

    def test_entry_importable(self) -> None:
        """MemoryEntry is importable."""
        from ibr_platform.platform.memory import MemoryEntry
        assert MemoryEntry is not None

    def test_entry_has_required_fields(self) -> None:
        """MemoryEntry has all required fields (PRD Section 15.3)."""
        from ibr_platform.platform.memory import MemoryEntry, MemoryTier

        entry = MemoryEntry(
            content="Test content",
            tier=MemoryTier.LONG_TERM,
            scope="project",
            scope_id="proj1",
        )
        assert entry.id is not None
        assert entry.content == "Test content"
        assert entry.tier == MemoryTier.LONG_TERM
        assert entry.scope == "project"
        assert entry.scope_id == "proj1"
        assert entry.version == 1
        assert entry.created_at is not None
        assert entry.updated_at is not None
        assert entry.access_count == 0
        assert entry.confidence == 0.0

    def test_entry_auto_generates_id(self) -> None:
        """MemoryEntry auto-generates unique ID."""
        from ibr_platform.platform.memory import MemoryEntry, MemoryTier

        e1 = MemoryEntry(content="A", tier=MemoryTier.WORKING, scope="project", scope_id="p1")
        e2 = MemoryEntry(content="B", tier=MemoryTier.WORKING, scope="project", scope_id="p1")
        assert e1.id != e2.id


class TestMemoryManager:
    """Test the MemoryManager (PRD Section 15.3 — Memory Operations API)."""

    def test_manager_importable(self) -> None:
        """MemoryManager is importable."""
        from ibr_platform.platform.memory import MemoryManager
        assert MemoryManager is not None

    def test_manager_instantiable(self) -> None:
        """MemoryManager can be instantiated."""
        from ibr_platform.platform.memory import MemoryManager
        mgr = MemoryManager()
        assert mgr is not None

    async def test_write_returns_id(self) -> None:
        """write() returns a memory entry ID."""
        from ibr_platform.platform.memory import MemoryManager, MemoryTier

        mgr = MemoryManager()
        entry_id = await mgr.write(
            content="Test memory",
            tier=MemoryTier.LONG_TERM,
            scope="project",
            scope_id="proj1",
        )
        assert entry_id is not None
        assert isinstance(entry_id, str)

    async def test_read_returns_entry(self) -> None:
        """read() returns the stored entry."""
        from ibr_platform.platform.memory import MemoryManager, MemoryTier

        mgr = MemoryManager()
        entry_id = await mgr.write(
            content="Read me",
            tier=MemoryTier.LONG_TERM,
            scope="project",
            scope_id="proj1",
        )
        entry = await mgr.read(entry_id)
        assert entry is not None
        assert entry.content == "Read me"

    async def test_read_unknown_id_returns_none(self) -> None:
        """read() with unknown ID returns None."""
        from ibr_platform.platform.memory import MemoryManager

        mgr = MemoryManager()
        result = await mgr.read("nonexistent-id")
        assert result is None

    async def test_search_returns_results(self) -> None:
        """search() returns matching entries."""
        from ibr_platform.platform.memory import MemoryManager, MemoryTier

        mgr = MemoryManager()
        await mgr.write(
            content="machine learning basics",
            tier=MemoryTier.LONG_TERM,
            scope="project",
            scope_id="proj1",
        )
        await mgr.write(
            content="database optimization",
            tier=MemoryTier.LONG_TERM,
            scope="project",
            scope_id="proj1",
        )
        results = await mgr.search("machine", scope="project", scope_id="proj1")
        assert len(results) >= 1
        assert any("machine" in r.content for r in results)

    async def test_delete_removes_entry(self) -> None:
        """delete() removes the entry."""
        from ibr_platform.platform.memory import MemoryManager, MemoryTier

        mgr = MemoryManager()
        entry_id = await mgr.write(
            content="Delete me",
            tier=MemoryTier.WORKING,
            scope="project",
            scope_id="proj1",
        )
        await mgr.delete(entry_id)
        assert await mgr.read(entry_id) is None


class TestScopeIsolation:
    """Test scope isolation (PRD Section 15.3)."""

    async def test_project_isolation(self) -> None:
        """Project A cannot read Project B's memory."""
        from ibr_platform.platform.memory import MemoryManager, MemoryTier

        mgr = MemoryManager()
        # Write to project A
        await mgr.write(
            content="Project A secret",
            tier=MemoryTier.LONG_TERM,
            scope="project",
            scope_id="projA",
        )
        # Search in project B — should not find it
        results = await mgr.search("secret", scope="project", scope_id="projB")
        assert len(results) == 0

    async def test_user_isolation(self) -> None:
        """User A cannot read User B's memory."""
        from ibr_platform.platform.memory import MemoryManager, MemoryTier

        mgr = MemoryManager()
        await mgr.write(
            content="User A data",
            tier=MemoryTier.CONVERSATION,
            scope="user",
            scope_id="userA",
        )
        results = await mgr.search("data", scope="user", scope_id="userB")
        assert len(results) == 0

    async def test_organization_isolation(self) -> None:
        """Org A cannot read Org B's memory."""
        from ibr_platform.platform.memory import MemoryManager, MemoryTier

        mgr = MemoryManager()
        await mgr.write(
            content="Org A knowledge",
            tier=MemoryTier.KNOWLEDGE,
            scope="organization",
            scope_id="orgA",
        )
        results = await mgr.search("knowledge", scope="organization", scope_id="orgB")
        assert len(results) == 0


class TestVersioning:
    """Test memory versioning (PRD Section 15.7)."""

    async def test_update_creates_new_version(self) -> None:
        """update() creates a new version (immutable entries)."""
        from ibr_platform.platform.memory import MemoryManager, MemoryTier

        mgr = MemoryManager()
        entry_id = await mgr.write(
            content="Original content",
            tier=MemoryTier.LONG_TERM,
            scope="project",
            scope_id="proj1",
        )
        # Update
        await mgr.update(entry_id, content="Updated content")
        entry = await mgr.read(entry_id)
        assert entry.content == "Updated content"
        assert entry.version == 2

    async def test_prior_version_queryable(self) -> None:
        """Prior versions are queryable (PRD Section 15.7)."""
        from ibr_platform.platform.memory import MemoryManager, MemoryTier

        mgr = MemoryManager()
        entry_id = await mgr.write(
            content="v1",
            tier=MemoryTier.LONG_TERM,
            scope="project",
            scope_id="proj1",
        )
        await mgr.update(entry_id, content="v2")
        await mgr.update(entry_id, content="v3")

        versions = await mgr.get_versions(entry_id)
        assert len(versions) == 3  # v1, v2, v3
        assert versions[0].content == "v1"
        assert versions[1].content == "v2"
        assert versions[2].content == "v3"


class TestEviction:
    """Test memory eviction policy (PRD Section 15.6)."""

    async def test_working_memory_evicted_on_complete(self) -> None:
        """Working memory is cleared when task completes."""
        from ibr_platform.platform.memory import MemoryManager, MemoryTier

        mgr = MemoryManager()
        await mgr.write(
            content="Task context",
            tier=MemoryTier.WORKING,
            scope="project",
            scope_id="proj1",
        )
        assert mgr.count(tier=MemoryTier.WORKING) == 1
        await mgr.clear_tier(MemoryTier.WORKING)
        assert mgr.count(tier=MemoryTier.WORKING) == 0

    async def test_short_term_ttl_eviction(self) -> None:
        """Short-term memory has TTL-based eviction."""
        from ibr_platform.platform.memory import MemoryManager, MemoryTier

        mgr = MemoryManager(short_term_ttl_seconds=0)  # Immediate expiry
        await mgr.write(
            content="Short-lived",
            tier=MemoryTier.SHORT_TERM,
            scope="project",
            scope_id="proj1",
        )
        # Trigger eviction
        await mgr.evict_expired()
        assert mgr.count(tier=MemoryTier.SHORT_TERM) == 0

    async def test_access_count_incremented(self) -> None:
        """Reading an entry increments its access count."""
        from ibr_platform.platform.memory import MemoryManager, MemoryTier

        mgr = MemoryManager()
        entry_id = await mgr.write(
            content="Access me",
            tier=MemoryTier.LONG_TERM,
            scope="project",
            scope_id="proj1",
        )
        entry = await mgr.read(entry_id)
        assert entry.access_count == 1
        entry = await mgr.read(entry_id)
        assert entry.access_count == 2


class TestMemoryStats:
    """Test memory statistics."""

    async def test_stats_returns_counts(self) -> None:
        """get_stats() returns per-tier counts."""
        from ibr_platform.platform.memory import MemoryManager, MemoryTier

        mgr = MemoryManager()
        await mgr.write(content="A", tier=MemoryTier.WORKING, scope="project", scope_id="p1")
        await mgr.write(content="B", tier=MemoryTier.LONG_TERM, scope="project", scope_id="p1")
        await mgr.write(content="C", tier=MemoryTier.LONG_TERM, scope="project", scope_id="p1")

        stats = mgr.get_stats()
        assert isinstance(stats, dict)
        assert stats.get(MemoryTier.WORKING) == 1
        assert stats.get(MemoryTier.LONG_TERM) == 2
