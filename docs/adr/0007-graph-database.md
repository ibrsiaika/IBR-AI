# ADR-0007: Graph Database — Neo4j Enterprise

**Date**: 2026-07-28
**Status**: Accepted
**PRD Reference**: PRD Section 31.3, Section 32.4 (KG Schema), Section 51 (KG Construction)

## Context

The platform's knowledge graph (PRD Section 32.4) stores entities, relationships, events with provenance. It must support Cypher queries for multi-hop reasoning, scale to 1B+ entities, and provide enterprise clustering for high availability.

## Decision

Use Neo4j Enterprise as the primary graph database for the knowledge graph.

## Alternatives

### 1. Neo4j Enterprise (CHOSEN)

Mature Cypher query language, proven at billion-edge scale, enterprise clustering and RBAC. Reference implementation for LLM-driven KG construction (PRD Section 51).

### 2. Neo4j Community Edition

Free and open-source (GPLv3), but lacks clustering, RBAC, and advanced security features needed for Enterprise mode.

### 3. Nebula Graph

Open-source, distributed, good for very large scale. But smaller community and less mature than Neo4j.

### 4. TigerGraph

Enterprise-grade, good for analytics. But proprietary and expensive; overkill for the platform's needs.

### 5. ArangoDB

Multi-model (graph + document + key-value). Reduces infrastructure but lacks Cypher and has weaker graph query capabilities.

### 6. Amazon Neptune

Managed graph database. But vendor lock-in and not self-hostable.


## Consequences

### Positive

- Mature Cypher query language with broad adoption
- Enterprise features (clustering, RBAC, audit logging) for compliance
- Reference implementation for LLM-driven KG (Neo4j LLM Graph Builder)
- Strong Python driver and ecosystem

### Negative

- Enterprise Edition requires commercial license (budget required for Enterprise mode)
- Community Edition (GPLv3) may conflict with proprietary licensing
- Not as horizontally scalable as Nebula or TigerGraph

### Mitigations

The negative consequences are mitigated by:
- Comprehensive documentation of all technology choices (this ADR series)
- Phased rollout — each technology is tested in isolation before full adoption
- Exit strategy — the layered architecture (PRD Section 10) ensures any single
  technology can be replaced without cascading changes

## Compliance

This ADR complies with:
- PRD Section 9 (Non-Functional Requirements)
- PRD Section 21 (Technology Stack Evaluation)
- PRD Section 22 (Security & Safety Requirements)
- The 50 verified practical patterns (PRD Sections 57, 74, 107)

## References

- PRD PDF: `docs/IBR_Platform_PRD.pdf`
- Research note: `docs/research/section_31_research.md`
- ADR index: `docs/adr/README.md`
