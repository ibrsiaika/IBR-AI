# ADR-0006: Vector Database — pgvectorscale (Moderate) + Qdrant (Large Scale)

**Date**: 2026-07-28
**Status**: Accepted
**PRD Reference**: PRD Section 31.3 (original), Section 69 (revised — Vector DB Comparison), Section 77 (Vector Search Benchmark)

## Context

The platform needs vector similarity search for retrieval, semantic caching, and entity resolution. The original PRD decision (Qdrant) is revised based on the Firecrawl benchmark (May 2026) showing pgvectorscale achieves 471 QPS at 99% recall on 50M vectors — 11.4x better than Qdrant's 41 QPS.

## Decision

Use pgvectorscale for moderate scale (<100M vectors) and Qdrant for very large scale (>100M vectors) or advanced filtering requirements.

## Alternatives

### 1. pgvectorscale for moderate scale, Qdrant for large scale (CHOSEN)

pgvectorscale runs on PostgreSQL (which the platform already uses), reducing operational complexity. 11.4x faster than Qdrant at 50M vectors. For >100M vectors or advanced filtering, Qdrant's HNSW is superior.

### 2. Qdrant (original PRD decision)

Apache 2.0, Rust-based reliability, strong filtering. But 11.4x slower than pgvectorscale at moderate scale per Firecrawl benchmark.

### 3. Milvus / Zilliz

Purpose-built for very large scale (1B+ vectors). Good for Enterprise mode but overkill for Tiny/Compact modes.

### 4. Pinecone

Managed service, no ops required. But vendor lock-in and not self-hostable (conflicts with Enterprise data residency requirements).

### 5. pgvector (not pgvectorscale)

Original Postgres vector extension. Slower than pgvectorscale but sufficient for <1M vectors. Used in Tiny mode.


## Consequences

### Positive

- pgvectorscale reduces operational complexity (one less database to manage)
- 11.4x performance improvement at moderate scale
- Qdrant preserved for large-scale and advanced filtering use cases
- Both are open-source (Apache 2.0)

### Negative

- Two vector databases to support (pgvectorscale and Qdrant)
- Migration path needed if scale exceeds pgvectorscale's sweet spot
- pgvectorscale is newer (less battle-tested than Qdrant)

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
