# IBR Platform

> **Intelligent Brain Runtime** — Autonomous Agentic AI Research & Self-Improving Foundation Model Platform

**Version**: 0.1.0
**Status**: Pre-Alpha (Section 32 — System Design implemented)
**License**: Proprietary — Private Property, Not For Sale

## ⚠️ Proprietary Notice

This software is the private property of **ibrsiaika**. It is NOT open source.
No license is granted to use, copy, modify, or distribute this software.
This software is NOT for sale. Unauthorized use, copying, or distribution
is strictly prohibited.

## Overview

The IBR Platform is an autonomous agentic AI research and self-improving
foundation model platform. It is designed to:

- Conduct autonomous internet research
- Read and understand PDFs, books, code, videos, APIs, and databases
- Plan multi-step reasoning with verifiable citations
- Create training datasets automatically
- Train and fine-tune specialized models
- Continuously learn from new information
- Run multiple AI agents collaboratively
- Build specialized expert models
- Operate safely with human oversight

The platform is **CPU-first** — every component runs on commodity CPU hardware,
with GPU acceleration as an optional performance layer. This enables deployment
from a laptop to a datacenter cluster.

## Documentation

The complete specification is in [`docs/IBR_Platform_PRD.pdf`](docs/IBR_Platform_PRD.pdf)
— a 224-page document with 107 sections across 6 parts:

- **Part I** (Sections 1-29): Product Requirements Document
- **Part II** (Sections 30-44): Phase-by-Phase Engineering Specifications
- **Part III** (Sections 45-59): Verified Research on Compression & Golden Tokens
- **Part IV** (Sections 60-75): Extended Research on Protocols & Infrastructure
- **Part V** (Sections 76-91): Empirical Tests & CS Formulas
- **Part VI** (Sections 92-107): Claude, Compact Models, Data Optimization

Additional documentation:
- [Architecture Guide](docs/architecture.md)
- [ADR-0001: Technology Stack](docs/adr/0001-technology-stack-and-project-structure.md)
- [Section 32 Research](docs/research/section_32_research.md)
- [Master Build Prompt](MASTER_BUILD_PROMPT.md) — Instructions for AI engineering agents

## Quick Start

### Prerequisites

- Python 3.11+
- pip
- git

### Installation

```bash
# Clone the repository
git clone https://github.com/ibrsiaika/IBR-AI.git
cd IBR-AI

# Install in development mode
pip install -e ".[dev]"

# Verify installation
python -c "import ibr_platform; print(ibr_platform.__version__)"
# Output: 0.1.0
```

### Run Tests

```bash
# Run all unit tests
make test-unit

# Run with coverage
make test-cov

# Run linting and type checking
make check
```

### Usage

```python
from ibr_platform.config import settings, DeploymentMode
from ibr_platform.agents import AgentBase, Task, AgentResult, HealthStatus

# Check configuration
print(settings.deployment_mode)  # DeploymentMode.TINY

# Create a custom agent
class MyAgent(AgentBase):
    async def initialize(self, config):
        self.config = config

    async def execute(self, task):
        return AgentResult(success=True, data={"result": "done"})

    async def health_check(self):
        return HealthStatus(status="healthy")

    async def shutdown(self):
        pass

agent = MyAgent(name="my-agent")
print(agent)  # <MyAgent(name='my-agent', status='pending')>
```

## Project Structure

```
IBR-AI/
├── src/ibr_platform/          # Python source (src layout)
│   ├── agents/                # 25+ specialist agents
│   │   └── base.py            # AgentBase ABC, Task, AgentResult
│   ├── config/                # Pydantic Settings configuration
│   ├── platform/              # Core platform (runtime, kernel, scheduler)
│   ├── api/                   # REST and gRPC APIs
│   ├── models/                # Model definitions
│   ├── data/                  # Dataset schemas
│   └── utils/                 # Shared utilities
├── tests/                     # Test suites (unit, integration, e2e, perf, security)
├── docs/                      # Documentation (PRD PDF, ADRs, guides)
├── infra/                     # Infrastructure (Helm, Terraform, K8s)
├── scripts/                   # Benchmark and build scripts
├── pyproject.toml             # Python project configuration
├── Makefile                   # Common commands
└── MASTER_BUILD_PROMPT.md     # AI build instructions (1319 lines)
```

## Development

```bash
# Install development dependencies
make dev-install

# Run all pre-commit checks
make pre-commit

# Format code
make format

# Clean build artifacts
make clean
```

## Deployment Modes

The platform supports four deployment modes (PRD Section 17):

| Mode | Target | RAM | Model | Use Case |
|------|--------|-----|-------|----------|
| Tiny | Laptop | 2 GB | 125M-1B | Demos, single-user |
| Compact | Workstation | 8 GB | 1B-3B | Small team |
| Professional | Server | 32 GB | 7B-13B | Department |
| Enterprise | Cluster | 128+ GB | 70B+ | Organization |

Configure via environment variable:
```bash
export IBR_DEPLOYMENT_MODE=enterprise
```

Or via YAML config:
```python
from ibr_platform.config import Settings
settings = Settings.from_yaml("configs/enterprise.yaml")
```

## Current Status

**Implemented**:
- ✅ Section 32: System Design — Folder Structure & Architecture
- ✅ AgentBase ABC with Task, AgentResult, HealthStatus, AgentRegistry
- ✅ Configuration management (Pydantic Settings)
- ✅ Project structure (src layout, monorepo)
- ✅ Test infrastructure (28 unit tests passing)
- ✅ Code quality tooling (ruff, mypy, bandit, pytest)
- ✅ Documentation (architecture guide, ADR-0001, research notes)

**Pending** (per MASTER_BUILD_PROMPT.md priority order):
- Section 31: Phase 1 — Deep Research (14 ADRs)
- Section 10: High-Level Architecture (layer implementations)
- Section 11: Multi-Agent Architecture (25+ agents)
- Section 22: Security & Safety Requirements
- Sections 33-107: All remaining sections

## Contact

- **Repository**: https://github.com/ibrsiaika/IBR-AI
- **Owner**: ibrsiaika

## Copyright

© 2026 ibrsiaika. All rights reserved.
This software is proprietary and confidential. Unauthorized use, copying,
distribution, or modification is strictly prohibited.
