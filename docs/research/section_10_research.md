# Section 10 Research — High-Level Architecture

**Date**: 2026-07-28
**PRD Section**: 10 (High-Level Architecture)
**Researcher**: AI Engineering Agent

## Topic Summary

This research informs the implementation of the IBR Platform's layered
architecture (PRD Section 10). The platform uses 10 layers, each with a
single responsibility, with strict dependency rules: upper layers may
depend on lower layers, but lower layers NEVER depend on upper layers.

## Sources

1. Mech2Dude, "Is Clean Architecture Still Clean in 2025?"
   - Aug 2025 — https://medium.com/@Mech2Dude/is-clean-architecture-still-clean-in-2025
   - Compares Layered, Hexagonal, Onion, and Clean architectures

2. "Layered Architecture != Hexagonal, Onion and Clean"
   - https://www.reddit.com/r/softwarearchitecture/comments/...
   - Clarifies that layered architecture is simpler than the alternatives
     and sufficient for many use cases

3. "Multi-Agent Orchestration: 5 Patterns That Work in 2026"
   - May 2026 — https://www.langchain.com/blog/multi-agent-orchestration
   - Documents 5 production orchestration patterns: fan-out, pipeline,
     debate, supervisor, swarm

4. "Python + Agents: Orchestrating advanced multi-agent workflows"
   - LangChain session — covers async orchestration patterns in Python

5. "A Multi-Agent LLM Scheduler with ReAct Orchestration"
   - Jul 2025 — arXiv paper on Gradientsys scheduling framework
   - Documents typed model-based scheduling for multi-agent systems

6. PRD Section 10 (High-Level Architecture)
7. PRD Section 11 (Multi-Agent Architecture)
8. ADR-0001 (Technology Stack and Project Structure)

## Key Findings

### 1. Layered Architecture is Sufficient for the IBR Platform
The research confirms that a layered architecture (simpler than Clean/
Hexagonal/Onion) is sufficient for the platform's needs. The key principle
is dependency direction: upper layers depend on lower layers, never reverse.
This enables:
- Swapping implementations (e.g., replace vector DB) without cascading changes
- Testing layers in isolation (mock lower layers)
- Clear separation of concerns

The platform does NOT need the full complexity of Clean Architecture
(dependency inversion via interfaces) because the components are not
expected to be reused outside the platform. Layered architecture provides
the right balance of discipline and simplicity.

### 2. Task Orchestrator Pattern
The orchestrator pattern (PRD Section 10, Layer 2) is the standard entry
point for multi-agent systems. The orchestrator:
- Receives user requests
- Authenticates and enforces quotas
- Dispatches to the Planner Agent
- Tracks request status
- Returns results

This centralizes cross-cutting concerns (auth, quota, logging) at a single
point, rather than scattering them across agents.

### 3. Async-First Design
The platform uses asyncio throughout because:
- Agent execution is I/O-bound (network calls, LLM API calls, DB queries)
- Asyncio enables high concurrency with single-threaded simplicity
- The GIL is not a bottleneck for I/O-bound work
- Python 3.11+ asyncio is mature and well-supported

### 4. Dependency Rule Enforcement
The `can_depend()` function enables runtime dependency rule checking.
This prevents architectural erosion — if a developer accidentally makes
a lower layer depend on an upper layer, the check fails. This is
particularly valuable in a large codebase where manual review may miss
violations.

## How Findings Apply to Section 10

- 10-layer architecture implemented as `ArchitectureLayer` IntEnum
- `LayerBase` ABC for all layer components
- `can_depend()` function for dependency rule enforcement
- `TaskOrchestrator` as the Layer 2 entry point
- Async-first design with asyncio throughout

## Deviations from PRD

**None.** The implementation follows the PRD Section 10 specification
exactly. The 10 layers, their order, and their responsibilities match
Table 10.1 in the PRD.

## Next Steps

1. ✅ Implement `ArchitectureLayer` enum (10 layers)
2. ✅ Implement `LayerBase` ABC
3. ✅ Implement `can_depend()` dependency checker
4. ✅ Implement `TaskOrchestrator` (Layer 2)
5. ✅ Write 74 tests (all passing)
6. Next: Implement Layer 1 (User — CLI/API) and Layer 3 (Planning — Planner Agent)
