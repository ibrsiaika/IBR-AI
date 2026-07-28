# ADR-0013: Backend Language — Python (Agents) + Go (Services)

**Date**: 2026-07-28
**Status**: Accepted
**PRD Reference**: PRD Section 31.3, Section 33 (Agent Framework), Section 20 (APIs)

## Context

The platform has two distinct backend needs: (1) ML/agent code that needs PyTorch, transformers, and the ML ecosystem (Python), and (2) high-concurrency infrastructure services (API gateway, message router, health checker) that benefit from Go's performance and concurrency model.

## Decision

Use Python for agent and ML code, Go for high-concurrency infrastructure services.

## Alternatives

### 1. Python (agents) + Go (services) (CHOSEN)

Python for ML ecosystem alignment, Go for high-concurrency services. Each language used where it excels. Industry pattern (e.g., Uber, Discord use this split).

### 2. Pure Python

Simpler (one language) but Python's GIL limits high-concurrency services. Asyncio helps for I/O-bound but not CPU-bound work.

### 3. Pure Go

Excellent performance and concurrency but lacks ML ecosystem. Would require CGO bindings to PyTorch — fragile and slow.

### 4. Rust

Best performance and safety but steep learning curve and smaller talent pool. Considered for future performance-critical components.

### 5. Java

Mature, good performance, but verbose and declining in ML/AI adoption.

### 6. Node.js/TypeScript

Good for APIs and shares language with frontend, but weak ML ecosystem.


## Consequences

### Positive

- Each language used where it excels (Python for ML, Go for services)
- Go services are fast, memory-efficient, and easy to deploy (single binary)
- Python agents have full access to ML ecosystem
- Industry-proven pattern (Uber, Discord, etc.)

### Negative

- Two languages to maintain (Python and Go)
- Inter-language communication adds complexity (gRPC recommended)
- Team needs both Python and Go skills

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
