# Architecture Decision Records (ADRs)

This directory contains all Architecture Decision Records for the IBR Platform.
Each ADR documents a significant technology or architectural decision, including
the context, decision, alternatives considered, and consequences.

## ADR Index

| Number | Title | Decision | Status |
|--------|-------|----------|--------|
| [0001](0001-technology-stack-and-project-structure.md) | Technology Stack & Project Structure | Python 3.11+, src layout, Pydantic Settings | Accepted |
| [0002](0002-model-architecture.md) | Model Architecture | Transformer + Mamba Hybrid | Accepted |
| [0003](0003-training-framework.md) | Training Framework | PyTorch + DeepSpeed | Accepted |
| [0004](0004-agent-framework.md) | Agent Framework | Custom layer on LangGraph | Accepted |
| [0005](0005-rag-architecture.md) | RAG Architecture | Hybrid (Dense + Sparse + Graph) with RRF + Reranking | Accepted |
| [0006](0006-vector-database.md) | Vector Database | pgvectorscale (moderate) + Qdrant (large scale) | Accepted |
| [0007](0007-graph-database.md) | Graph Database | Neo4j Enterprise | Accepted |
| [0008](0008-inference-server.md) | Inference Server | vLLM (with llama.cpp fallback) | Accepted |
| [0009](0009-orchestration.md) | Orchestration | Kubernetes + Ray + Volcano | Accepted |
| [0010](0010-message-broker.md) | Message Broker | Apache Kafka | Accepted |
| [0011](0011-observability-stack.md) | Observability Stack | Prometheus + Grafana + Loki + Tempo + Phoenix | Accepted |
| [0012](0012-frontend-framework.md) | Frontend Framework | Next.js 14 + React + TypeScript + Tailwind | Accepted |
| [0013](0013-backend-language.md) | Backend Language | Python (agents) + Go (services) | Accepted |
| [0014](0014-secrets-management.md) | Secrets Management | HashiCorp Vault | Accepted |
| [0015](0015-container-runtime.md) | Container Runtime | containerd + gVisor (sandboxing) | Accepted |

## Summary

The 15 ADRs (0001-0015) document the complete technology stack for the IBR Platform.
They implement PRD Section 31 (Phase 1 — Deep Research) which requires 14 Architecture
Decision Records for the major technology decisions.

### Decision Summary by Category

**Languages**: Python 3.11+ (agents, ML), Go (services), TypeScript (frontend)
**Frameworks**: PyTorch + DeepSpeed (training), LangGraph (agents), Next.js 14 (frontend)
**Data Stores**: pgvectorscale/Qdrant (vector), Neo4j (graph), PostgreSQL (SQL), Redis (cache)
**Infrastructure**: Kubernetes + Ray + Volcano (orchestration), Kafka (messaging), Vault (secrets)
**Observability**: Prometheus + Grafana + Loki + Tempo + Phoenix
**Security**: containerd + gVisor (sandboxing), 6-layer guardrail stack

### Key Deviations from Original PRD

1. **ADR-0006 (Vector Database)**: Revised from "Qdrant" to "pgvectorscale for moderate
   scale, Qdrant for large scale" based on Firecrawl benchmark (May 2026) showing
   pgvectorscale is 11.4x faster at 50M vectors.

2. **ADR-0008 (Inference Server)**: Added llama.cpp as CPU fallback, based on PRD
   Section 100 (Low-Resource Inference) research showing CPU-first deployment needs.

3. **ADR-0011 (Observability)**: Added Arize Phoenix for LLM-specific observability,
   based on PRD Section 68 research showing traditional APM tools cannot capture
   LLM semantic quality.

## ADR Process

### When to Write an ADR

Write an ADR when making a decision that:
- Affects the architecture or technology stack
- Is difficult to reverse
- Has significant trade-offs
- Will be referenced by future developers

### ADR Structure

Each ADR must include:
1. **Title**: ADR-XXXX: Decision Title
2. **Date**: When the decision was made
3. **Status**: Proposed, Accepted, Deprecated, or Superseded
4. **Context**: Why this decision is needed
5. **Decision**: What was decided
6. **Alternatives**: What else was considered (at least 2)
7. **Consequences**: Positive, negative, and mitigations
8. **Compliance**: How this complies with the PRD
9. **References**: Links to PRD sections and research notes

### File Naming

ADRs are numbered sequentially: `NNNN-slug.md` (e.g., `0006-vector-database.md`).
Once an ADR is committed, its number is never reused even if the ADR is deprecated.

## References

- PRD Section 31: Phase 1 — Deep Research
- PRD Section 21: Technology Stack Evaluation
- Research note: `docs/research/section_31_research.md`
- PRD PDF: `docs/IBR_Platform_PRD.pdf`
