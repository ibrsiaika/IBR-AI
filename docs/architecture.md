# IBR Platform — Architecture Guide

**Version**: 0.1.0
**Audience**: Engineers, Architects
**Last Updated**: 2026-07-28

## Overview

The IBR (Intelligent Brain Runtime) Platform is an autonomous agentic AI research
and self-improving foundation model platform. This document describes the
high-level architecture, component organization, and key design decisions.

For the complete specification, see `/docs/IBR_Platform_PRD.pdf` (224 pages,
107 sections, 6 parts).

## Architecture Layers

The platform follows a layered architecture (PRD Section 10) where each layer
has a single responsibility and depends only on layers below it:

```
┌─────────────────────────────────────────────┐
│  User Layer (CLI, Dashboard, SDK, APIs)     │
├─────────────────────────────────────────────┤
│  Orchestration (Task Orchestrator)          │
├─────────────────────────────────────────────┤
│  Planning (Planner Agent)                   │
├─────────────────────────────────────────────┤
│  Execution (25+ Specialist Agents)          │
├─────────────────────────────────────────────┤
│  Knowledge (KG + Vector DB + Memory)        │
├─────────────────────────────────────────────┤
│  Data (Dataset Generator)                   │
├─────────────────────────────────────────────┤
│  Training (Training Pipeline)               │
├─────────────────────────────────────────────┤
│  Evaluation (Benchmarks + RLHF)             │
├─────────────────────────────────────────────┤
│  Registry (Model Registry)                  │
├─────────────────────────────────────────────┤
│  Deployment (Canary, A/B, Rollback)         │
└─────────────────────────────────────────────┘
```

## Project Structure

```
ibr-platform/
├── src/ibr_platform/          # Python source (src layout)
│   ├── __init__.py            # Package metadata, version
│   ├── py.typed               # PEP 561 type marker
│   ├── platform/              # Core platform (runtime, kernel, scheduler)
│   ├── agents/                # 25+ specialist agents
│   │   ├── base.py            # AgentBase ABC, Task, AgentResult, Registry
│   │   ├── planner/           # Planner agent
│   │   ├── research/          # Web, academic, code research
│   │   ├── verification/      # Fact-checking, confidence scoring
│   │   ├── memory/            # Multi-tier memory management
│   │   ├── knowledge_graph/   # KG construction and query
│   │   ├── training/          # SFT, LoRA, QLoRA, GRPO
│   │   ├── evaluation/        # Benchmarks and metrics
│   │   ├── deployment/        # Canary, A/B, rollback
│   │   ├── security/          # Audit, policy enforcement
│   │   ├── coding/            # Code analysis and generation
│   │   └── reasoning/         # CoT, ToT, ReAct, Reflexion
│   ├── api/                   # REST and gRPC APIs
│   ├── config/                # Pydantic Settings configuration
│   ├── models/                # Model definitions
│   ├── data/                  # Dataset schemas
│   └── utils/                 # Shared utilities
├── tests/                     # Test suites
│   ├── unit/                  # Unit tests (fast, isolated)
│   ├── integration/           # Integration tests (with Docker)
│   ├── e2e/                   # End-to-end tests (full stack)
│   ├── perf/                  # Performance benchmarks
│   └── security/              # Security tests
├── docs/                      # Documentation
│   ├── IBR_Platform_PRD.pdf   # 224-page specification (source of truth)
│   ├── adr/                   # Architecture Decision Records
│   ├── research/              # Research notes per section
│   ├── guides/                # Developer/deployment guides
│   └── runbooks/              # Operational runbooks
├── infra/                     # Infrastructure
│   ├── helm/                  # Helm charts
│   ├── terraform/             # Terraform modules
│   └── k8s/                   # Kubernetes manifests
├── api/                       # API definitions
│   ├── openapi/               # OpenAPI 3.1 specs
│   └── sdk/                   # Client SDKs
├── dashboard/                 # Next.js web dashboard
├── scripts/                   # Build and ops scripts
├── configs/                   # Deployment mode configs
├── pyproject.toml             # Python project config
├── Makefile                   # Common commands
└── README.md                  # Project overview
```

## Agent Framework

All agents inherit from `AgentBase` (PRD Section 33.4), an abstract base class
with four lifecycle methods:

```python
from ibr_platform.agents import AgentBase, Task, AgentResult, HealthStatus

class MyAgent(AgentBase):
    async def initialize(self, config: dict) -> None:
        """Set up the agent."""

    async def execute(self, task: Task) -> AgentResult:
        """Perform the agent's work."""

    async def health_check(self) -> HealthStatus:
        """Check agent health."""

    async def shutdown(self) -> None:
        """Clean up resources."""
```

Agents communicate via structured JSON messages (PRD Section 11.2) containing:
task_id, parent_task_id, agent_source, agent_target, task, priority,
dependencies, confidence, evidence, status, memory_ids, logs, artifacts.

## Configuration

Configuration uses Pydantic Settings (PRD Section 32.3) with environment variable
support:

```python
from ibr_platform.config import settings, DeploymentMode

print(settings.deployment_mode)  # DeploymentMode.TINY
print(settings.ram_budget_mb)    # 2048
```

Configuration can be loaded from:
1. Environment variables (prefixed `IBR_`)
2. YAML config files (`configs/enterprise.yaml`)
3. Default values

## Deployment Modes

The platform supports four deployment modes (PRD Section 17):

| Mode | Hardware | RAM Budget | Model Size | Engine |
|------|----------|------------|------------|--------|
| Tiny | Laptop | 2 GB | 125M-1B | llama.cpp |
| Compact | Workstation | 8 GB | 1B-3B | llama.cpp/vLLM |
| Professional | Server | 32 GB | 7B-13B | vLLM |
| Enterprise | Cluster | 128+ GB | 70B+ | vLLM+TensorParallel |

## Testing

The test pyramid (PRD Section 41):

| Layer | Count | Runtime | Coverage |
|-------|-------|---------|----------|
| Unit | 5000+ | <60s | >80% |
| Integration | 500+ | <10min | All contracts |
| E2E | 100+ | <60min | All user stories |
| Performance | 50+ | <2hr | All NFR targets |
| Security | 30+ | <4hr | OWASP Top 10 |
| Load | 10+ | <8hr | 2x peak |
| Regression | 200+ | <30min | Bug fixes |

## Quality Gates

Before any commit is accepted:
- [ ] All tests pass (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Type checking passes (`make type-check`)
- [ ] Security scan passes (`make security-check`)
- [ ] Coverage ≥ 80% (`make test-cov`)
- [ ] No secrets in code
- [ ] Documentation updated

## References

- PRD PDF: `/docs/IBR_Platform_PRD.pdf`
- ADR-0001: Technology Stack and Project Structure
- Section 32 Research: `/docs/research/section_32_research.md`
- README: `/README.md`
