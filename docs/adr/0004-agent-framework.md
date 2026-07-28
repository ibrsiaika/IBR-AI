# ADR-0004: Agent Framework — Custom Layer on LangGraph

**Date**: 2026-07-28
**Status**: Accepted
**PRD Reference**: PRD Section 31.3, Section 33 (Agent Framework), Section 55 (Real-World Agentic AI)

## Context

The platform needs 25+ specialist agents that communicate via structured JSON messages (PRD Section 11.2), with full observability, human approval gates, and sandboxed execution. Off-the-shelf frameworks (LangChain, CrewAI) lack the enterprise features required.

## Decision

Build a custom agent framework on top of LangGraph primitives, adding IBR-specific contracts, security, and observability.

## Alternatives

### 1. Custom on LangGraph (CHOSEN)

LangGraph provides graph-based agent orchestration with state management and checkpointing. Custom layer adds IBR JSON protocol, security, audit logging, and enterprise features. Best of both worlds.

### 2. LangChain

Broadest ecosystem but lacks graph-based orchestration. Agent execution is linear, not graph-based. No built-in state management for long-running workflows.

### 3. CrewAI

Simple role-based API, good for prototyping. Lacks enterprise features (RBAC, audit logging, multi-tenancy) and graph-based execution.

### 4. AutoGPT

Pioneered autonomous agents but codebase is experimental. Not suitable for production enterprise deployment.

### 5. Pure Custom (no framework)

Maximum control but reinvents the wheel. LangGraph's graph execution, state management, and checkpointing are valuable primitives not worth rebuilding.


## Consequences

### Positive

- Graph-based orchestration matches the platform's execution graph model
- LangGraph is maintained by LangChain team — active development
- Custom layer enables IBR-specific security and compliance
- Can leverage LangChain ecosystem (tools, integrations)

### Negative

- Custom layer adds development and maintenance overhead
- LangGraph API may change (relatively new project)
- Team must understand both LangGraph and the custom layer

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
