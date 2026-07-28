# ADR-0001: Technology Stack and Project Structure

**Date**: 2026-07-28
**Status**: Accepted
**PRD Reference**: Section 31 (Phase 1 — Deep Research), Section 32 (System Design)

## Context

The IBR Platform requires a technology stack and project structure that supports:
- CPU-first deployment (Tiny to Enterprise modes)
- 25+ specialist AI agents with async execution
- Multi-tier memory system (vector, graph, SQL, Redis)
- Training pipeline (PyTorch, DeepSpeed)
- REST and gRPC APIs
- Kubernetes deployment with Helm charts
- Comprehensive testing (unit, integration, E2E, performance, security)

The choices must align with PRD Section 21 (Technology Stack Evaluation) and
the 50 verified practical patterns documented in PRD Sections 57, 74, 107.

## Decision

### Language and Runtime
- **Primary language**: Python 3.11+ (for ML ecosystem, async support, type hints)
- **Secondary language**: Go (for high-concurrency services, future)
- **Frontend**: Next.js + React + TypeScript (for dashboard)

### Project Structure
- **src layout**: Code in `src/ibr_platform/` (prevents accidental imports)
- **Monorepo**: All components in one repository
- **Namespace packages**: `ibr_platform.platform`, `ibr_platform.agents`, etc.

### Core Dependencies
- **Async**: asyncio, aiohttp, httpx
- **Configuration**: Pydantic Settings (type-safe, env var support)
- **Logging**: structlog (structured JSON logs)
- **Observability**: Prometheus client, OpenTelemetry
- **CLI**: click, rich

### Optional Dependencies (extras)
- **ML**: torch, transformers, sentence-transformers, scikit-learn
- **Vector DB**: qdrant-client, pgvector
- **Graph DB**: neo4j
- **API**: FastAPI, uvicorn

### Code Quality
- **Linting**: ruff (fast, modern)
- **Type checking**: mypy (strict mode)
- **Security**: bandit, pip-audit
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Coverage target**: 80%+

## Alternatives Considered

### Language
- **Rust**: Faster, safer, but lacks ML ecosystem (PyTorch, transformers). Chosen
  for future high-performance components, not primary.
- **Go**: Excellent for services, but ML library support is weaker than Python.
  Chosen for future infrastructure services.
- **Node.js/TypeScript**: Good for APIs and dashboard, but ML ecosystem is immature.
  Chosen for dashboard only.

### Project Structure
- **Flat layout** (code at root): Simpler, but allows accidental imports of
  uninstalled packages during testing. Rejected.
- **Monorepo with workspaces**: More complex setup. The project is small enough
  that a single pyproject.toml suffices.

### Configuration
- **Plain YAML**: No type validation, no env var support. Rejected.
- **python-dotenv**: Limited to env vars, no nested config. Rejected.
- **Hydra/OmegaConf**: Powerful but adds complexity. Considered for future.

## Consequences

### Positive
- Python ecosystem provides access to all required ML libraries
- src layout prevents packaging bugs
- Pydantic Settings provides type-safe configuration with env var support
- Monorepo enables atomic commits across components
- ruff + mypy ensure code quality

### Negative
- Python's GIL limits CPU-bound parallelism (mitigated by async + multiprocessing)
- src layout requires `pip install -e .` for development (acceptable)
- Monorepo can become large; may need to split later if components diverge

### Mitigations
- Use asyncio for I/O-bound work (most agent operations)
- Use multiprocessing for CPU-bound work (training, embeddings)
- Document the development setup clearly in README.md
- Monitor repo size; split if a component exceeds 50K lines

## Compliance

This ADR complies with:
- PRD Section 9.5 (Maintainability & Portability): Python is deployable on any
  platform with Python 3.11+
- PRD Section 9.5 (CPU-first): All dependencies run on CPU; GPU is optional
- PRD Section 21 (Technology Stack): Aligns with the 14 technology decisions
- PRD Section 32.2 (Folder Structure): Adopts the specified structure with src layout

## References

- PRD Section 21: Technology Stack Evaluation
- PRD Section 32: System Design — Folder Structure
- PRD Section 33: Agent Framework
- Python Packaging Authority: https://packaging.python.org/
- Pydantic Settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- src layout: https://bskinn.github.io/My-How-Why-Pyproject-Src
