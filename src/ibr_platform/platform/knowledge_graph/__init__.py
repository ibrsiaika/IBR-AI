"""
Knowledge Graph — Construction & Query (PRD Section 51).

FREE implementation using in-memory graph (no Neo4j required for dev).
In production, uses Neo4j Community Edition (free, GPLv3) or no DB.

Implements:
    - Entity: Nodes with labels, properties, provenance
    - Relationship: Edges with type, properties, provenance
    - KnowledgeGraph: Add/query/traverse entities and relationships
    - PageRank: Compute entity centrality (PRD Section 84.7)

References:
    - PRD Section 32.4 (Knowledge Graph Schema)
    - PRD Section 51 (Knowledge Graph Construction)
    - PRD Section 84.7 (PageRank formula)
    - PRD Section 88.3 (PageRank benchmark)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class Entity:
    """A knowledge graph entity (PRD Section 32.4, Table 32.2).

    Attributes:
        id: Unique entity ID.
        label: Entity type (Person, Organization, Concept, etc.).
        name: Entity name.
        properties: Additional properties.
        provenance: Source artifact ID where this entity was extracted.
        confidence: Extraction confidence (0.0-1.0).
        created_at: When the entity was created.
    """

    name: str = ""
    label: str = "Concept"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    properties: dict[str, Any] = field(default_factory=dict)
    provenance: str = ""
    confidence: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class Relationship:
    """A knowledge graph relationship (PRD Section 32.4).

    Attributes:
        id: Unique relationship ID.
        source_id: Source entity ID.
        target_id: Target entity ID.
        rel_type: Relationship type (AUTHORED, CITES, DEFINES, etc.).
        properties: Additional properties.
        provenance: Source artifact ID.
        confidence: Extraction confidence.
        created_at: When the relationship was created.
    """

    source_id: str = ""
    target_id: str = ""
    rel_type: str = "RELATED_TO"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    properties: dict[str, Any] = field(default_factory=dict)
    provenance: str = ""
    confidence: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class KnowledgeGraph:
    """In-memory knowledge graph (FREE, no Neo4j required for development).

    Stores entities and relationships in memory. Supports:
        - add_entity, add_relationship
        - get_entity, get_relationship
        - query_entities (by label, name)
        - traverse (BFS from entity, N hops)
        - pagerank (compute centrality, PRD Section 84.7)
        - get_stats (entity/edge counts)

    In production, this uses Neo4j Community Edition (free, GPLv3).

    Usage:
        kg = KnowledgeGraph()
        e1 = kg.add_entity(name="OpenAI", label="Organization")
        e2 = kg.add_entity(name="GPT-4", label="Model")
        kg.add_relationship(e1.id, e2.id, "DEVELOPED")
        neighbors = kg.traverse(e1.id, max_hops=1)
    """

    def __init__(self) -> None:
        self._entities: dict[str, Entity] = {}
        self._relationships: dict[str, Relationship] = {}
        self._adjacency: dict[str, list[str]] = {}  # entity_id -> [target_ids]

    @property
    def entity_count(self) -> int:
        return len(self._entities)

    @property
    def relationship_count(self) -> int:
        return len(self._relationships)

    def add_entity(
        self,
        name: str,
        label: str = "Concept",
        properties: dict[str, Any] | None = None,
        provenance: str = "",
        confidence: float = 0.0,
    ) -> Entity:
        """Add an entity to the graph.

        Args:
            name: Entity name.
            label: Entity label/type.
            properties: Additional properties.
            provenance: Source artifact ID.
            confidence: Extraction confidence.

        Returns:
            The created Entity.
        """
        entity = Entity(
            name=name,
            label=label,
            properties=properties or {},
            provenance=provenance,
            confidence=confidence,
        )
        self._entities[entity.id] = entity
        self._adjacency.setdefault(entity.id, [])
        return entity

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str = "RELATED_TO",
        properties: dict[str, Any] | None = None,
        provenance: str = "",
        confidence: float = 0.0,
    ) -> Relationship | None:
        """Add a relationship between two entities.

        Args:
            source_id: Source entity ID.
            target_id: Target entity ID.
            rel_type: Relationship type.
            properties: Additional properties.
            provenance: Source artifact ID.
            confidence: Extraction confidence.

        Returns:
            The created Relationship, or None if entities don't exist.
        """
        if source_id not in self._entities or target_id not in self._entities:
            return None

        rel = Relationship(
            source_id=source_id,
            target_id=target_id,
            rel_type=rel_type,
            properties=properties or {},
            provenance=provenance,
            confidence=confidence,
        )
        self._relationships[rel.id] = rel
        self._adjacency.setdefault(source_id, []).append(target_id)
        return rel

    def get_entity(self, entity_id: str) -> Entity | None:
        """Get an entity by ID."""
        return self._entities.get(entity_id)

    def query_entities(
        self,
        label: str | None = None,
        name_contains: str | None = None,
    ) -> list[Entity]:
        """Query entities by label or name.

        Args:
            label: Filter by label (None = all labels).
            name_contains: Filter by name substring (None = all names).

        Returns:
            List of matching entities.
        """
        results = list(self._entities.values())
        if label is not None:
            results = [e for e in results if e.label == label]
        if name_contains is not None:
            lower = name_contains.lower()
            results = [e for e in results if lower in e.name.lower()]
        return results

    def traverse(
        self,
        start_id: str,
        max_hops: int = 2,
    ) -> list[Entity]:
        """BFS traversal from a starting entity.

        Args:
            start_id: Starting entity ID.
            max_hops: Maximum traversal depth.

        Returns:
            List of reachable entities (excluding the start entity).
        """
        if start_id not in self._entities:
            return []

        visited: set[str] = {start_id}
        current: list[str] = [start_id]
        results: list[Entity] = []

        for _ in range(max_hops):
            next_level: list[str] = []
            for eid in current:
                for target_id in self._adjacency.get(eid, []):
                    if target_id not in visited:
                        visited.add(target_id)
                        entity = self._entities.get(target_id)
                        if entity:
                            results.append(entity)
                        next_level.append(target_id)
            current = next_level
            if not current:
                break

        return results

    def pagerank(
        self,
        damping: float = 0.85,
        iterations: int = 100,
    ) -> dict[str, float]:
        """Compute PageRank for all entities (PRD Section 84.7).

        Formula: PR(p) = (1-d)/N + d * sum PR(q)/out_degree(q)

        Args:
            damping: Damping factor (default 0.85).
            iterations: Number of iterations.

        Returns:
            Dictionary mapping entity_id -> PageRank score.
        """
        n = len(self._entities)
        if n == 0:
            return {}

        entity_ids = list(self._entities.keys())
        pr: dict[str, float] = dict.fromkeys(entity_ids, 1.0 / n)

        # Build in-degree map (who points to each entity)
        in_links: dict[str, list[str]] = {eid: [] for eid in entity_ids}
        out_degree: dict[str, int] = dict.fromkeys(entity_ids, 0)

        for rel in self._relationships.values():
            in_links[rel.target_id].append(rel.source_id)
            out_degree[rel.source_id] = out_degree.get(rel.source_id, 0) + 1

        for _ in range(iterations):
            new_pr: dict[str, float] = {}
            for eid in entity_ids:
                rank = (1 - damping) / n
                for source_id in in_links[eid]:
                    deg = out_degree.get(source_id, 0)
                    if deg > 0:
                        rank += damping * pr[source_id] / deg
                new_pr[eid] = rank
            pr = new_pr

        return pr

    def get_stats(self) -> dict[str, int]:
        """Get graph statistics.

        Returns:
            Dictionary with entity_count, relationship_count, label_counts.
        """
        label_counts: dict[str, int] = {}
        for entity in self._entities.values():
            label_counts[entity.label] = label_counts.get(entity.label, 0) + 1

        return {
            "entity_count": len(self._entities),
            "relationship_count": len(self._relationships),
            **{f"label_{k}": v for k, v in label_counts.items()},
        }

    def __repr__(self) -> str:
        return f"<KnowledgeGraph(entities={len(self._entities)}, edges={len(self._relationships)})>"
