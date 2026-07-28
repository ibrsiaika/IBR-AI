# ADR-0005: RAG Architecture — Hybrid (Dense + Sparse + Graph)

**Date**: 2026-07-28
**Status**: Accepted
**PRD Reference**: PRD Section 31.3, Section 50 (Production RAG), Section 51 (Knowledge Graphs)

## Context

Naive vector RAG is insufficient for production (PRD Section 50.1). The platform needs retrieval that combines keyword precision (BM25), semantic understanding (dense), and multi-hop reasoning (graph). Production RAG requires overfetch-and-rerank for quality, and source tracking for citation.

## Decision

Implement hybrid retrieval combining BM25 (sparse), dense vector search, and knowledge graph traversal, with reciprocal rank fusion (RRF) and cross-encoder reranking.

## Alternatives

### 1. Hybrid: Dense + Sparse + Graph with RRF + Reranking (CHOSEN)

BM25 for keyword precision, dense for semantic, graph for multi-hop. RRF fuses BM25+dense; cross-encoder reranks top candidates. Validated by PRD Section 50 benchmarks (15-30% nDCG improvement).

### 2. Pure Dense (vector only)

Simple but misses keyword-precise queries (code identifiers, proper nouns). PRD Section 78 benchmark showed no improvement over BM25 with poor embeddings.

### 3. Pure Sparse (BM25 only)

Excellent for keyword queries but misses semantic similarity. Cannot find paraphrased content.

### 4. RAG-Fusion

Generates multiple query variants and fuses results. Adds latency but improves recall. Could be a future enhancement.


## Consequences

### Positive

- 15-30% nDCG improvement over dense-only (validated in PRD Section 50)
- Handles both keyword-precise and semantic-similarity queries
- Graph retrieval enables multi-hop reasoning (PRD Section 51)
- Cross-encoder reranking improves precision on top results

### Negative

- Three retrieval systems to maintain (BM25, vector, graph)
- Reranking adds 50-200ms latency per query
- RRF weight tuning required per use case

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
