"""Tests for Section 51 — Knowledge Graph Construction."""
from __future__ import annotations


class TestKnowledgeGraph:
    """Test the KnowledgeGraph (PRD Section 51)."""

    def test_kg_importable(self) -> None:
        from ibr_platform.platform.knowledge_graph import KnowledgeGraph
        assert KnowledgeGraph is not None

    def test_kg_instantiable(self) -> None:
        from ibr_platform.platform.knowledge_graph import KnowledgeGraph
        kg = KnowledgeGraph()
        assert kg is not None

    def test_add_entity(self) -> None:
        from ibr_platform.platform.knowledge_graph import KnowledgeGraph
        kg = KnowledgeGraph()
        e = kg.add_entity(name="OpenAI", label="Organization")
        assert e.name == "OpenAI"
        assert e.label == "Organization"
        assert kg.entity_count == 1

    def test_add_relationship(self) -> None:
        from ibr_platform.platform.knowledge_graph import KnowledgeGraph
        kg = KnowledgeGraph()
        e1 = kg.add_entity(name="OpenAI", label="Organization")
        e2 = kg.add_entity(name="GPT-4", label="Model")
        rel = kg.add_relationship(e1.id, e2.id, "DEVELOPED")
        assert rel is not None
        assert rel.rel_type == "DEVELOPED"
        assert kg.relationship_count == 1

    def test_add_relationship_nonexistent_entity(self) -> None:
        from ibr_platform.platform.knowledge_graph import KnowledgeGraph
        kg = KnowledgeGraph()
        rel = kg.add_relationship("nonexistent1", "nonexistent2")
        assert rel is None

    def test_query_by_label(self) -> None:
        from ibr_platform.platform.knowledge_graph import KnowledgeGraph
        kg = KnowledgeGraph()
        kg.add_entity(name="OpenAI", label="Organization")
        kg.add_entity(name="GPT-4", label="Model")
        kg.add_entity(name="Google", label="Organization")
        orgs = kg.query_entities(label="Organization")
        assert len(orgs) == 2

    def test_query_by_name(self) -> None:
        from ibr_platform.platform.knowledge_graph import KnowledgeGraph
        kg = KnowledgeGraph()
        kg.add_entity(name="OpenAI", label="Organization")
        kg.add_entity(name="Google", label="Organization")
        results = kg.query_entities(name_contains="open")
        assert len(results) == 1
        assert results[0].name == "OpenAI"

    def test_traverse(self) -> None:
        from ibr_platform.platform.knowledge_graph import KnowledgeGraph
        kg = KnowledgeGraph()
        e1 = kg.add_entity(name="A")
        e2 = kg.add_entity(name="B")
        e3 = kg.add_entity(name="C")
        kg.add_relationship(e1.id, e2.id)
        kg.add_relationship(e2.id, e3.id)
        neighbors = kg.traverse(e1.id, max_hops=2)
        names = [e.name for e in neighbors]
        assert "B" in names
        assert "C" in names

    def test_pagerank(self) -> None:
        from ibr_platform.platform.knowledge_graph import KnowledgeGraph
        kg = KnowledgeGraph()
        e1 = kg.add_entity(name="A")
        e2 = kg.add_entity(name="B")
        e3 = kg.add_entity(name="C")
        kg.add_relationship(e1.id, e2.id)
        kg.add_relationship(e2.id, e3.id)
        kg.add_relationship(e3.id, e1.id)
        pr = kg.pagerank(iterations=50)
        assert len(pr) == 3
        # All entities should have positive PageRank
        for score in pr.values():
            assert score > 0

    def test_get_stats(self) -> None:
        from ibr_platform.platform.knowledge_graph import KnowledgeGraph
        kg = KnowledgeGraph()
        kg.add_entity(name="A", label="Person")
        kg.add_entity(name="B", label="Person")
        kg.add_entity(name="C", label="Concept")
        kg.add_relationship(kg._entities[list(kg._entities)[0]].id,
                           kg._entities[list(kg._entities)[1]].id)
        stats = kg.get_stats()
        assert stats["entity_count"] == 3
        assert stats["relationship_count"] == 1

    def test_entity_has_provenance(self) -> None:
        from ibr_platform.platform.knowledge_graph import KnowledgeGraph
        kg = KnowledgeGraph()
        e = kg.add_entity(name="Test", provenance="artifact_123", confidence=0.85)
        assert e.provenance == "artifact_123"
        assert e.confidence == 0.85
