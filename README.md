# IBR Platform

> **Intelligent Brain Runtime** — Autonomous Agentic AI Research & Self-Improving Foundation Model Platform

**Version**: 0.1.0
**Status**: Pre-Alpha — Sections 32, 31, 10, 11, 22, 33, 35 implemented
**License**: Proprietary — Private Property, Not For Sale

## ⚠️ Proprietary Notice

This software is the private property of **ibrsiaika**. It is NOT open source.
No license is granted to use, copy, modify, or distribute this software.
This software is NOT for sale. Unauthorized use, copying, or distribution
is strictly prohibited.

## 📋 Project Bulletin (Updated 2026-07-28)

### Latest Research Findings (2025-2026)

| Topic | Key Finding | Source | Applied In |
|-------|-------------|--------|------------|
| **pgvectorscale** | 471 QPS at 99% recall on 50M vectors — 11.4x faster than Qdrant | Firecrawl (May 2026) | ADR-0006 |
| **vLLM PagedAttention** | 24x throughput vs HuggingFace TGI | arXiv 2511.17593 (Nov 2025) | ADR-0008 |
| **FlashAttention-3** | 1.5-2x speedup on H100 GPU — but SLOWER on CPU (0.31-0.66x) | Tri Dao (2024) + our benchmark | ADR-0008, Sec 80 |
| **Speculative Decoding** | 2-3x latency reduction (2.07x at 70% acceptance, 3.15x at 90%) | arXiv 2502.10424 (Feb 2025) | Sec 82 |
| **Semantic Caching** | 89% hit rate at threshold 0.95 | Our benchmark (Sec 79) | Sec 47 |
| **INT8 Quantization** | 4x compression with MSE 0.000075 (negligible loss) | Our benchmark (Sec 81) | Sec 46 |
| **DeepSeek-R1 GRPO** | 80% less VRAM than PPO; spontaneous reasoning emergence | arXiv 2501.12948 (Jan 2025) | Sec 52 |
| **Phi-3 Textbook Quality** | 3.8B model on good data matches 13B on web data | Microsoft (Apr 2024) | Sec 95 |
| **Claude Haiku 4.5** | Near-Sonnet quality at 1/3 cost, 2x speed | Anthropic (Oct 2025) | Sec 93 |
| **Constitutional AI** | RLAIF produces safer models than RLHF without human labels | Anthropic (Dec 2022) | Sec 94 |
| **Letta Memory** | Git-based versioning, automatic persistence, programmatic context mgmt | Letta (Jul-Dec 2025) | Sec 35 |
| **MCP Protocol** | Open standard for agent-tool integration (JSON-RPC 2.0) | Anthropic (Nov 2024) | Sec 61 |
| **Volcano Gang Scheduling** | Eliminates distributed training deadlock on K8s | Ray Docs, Volcano (2025) | ADR-0009 |
| **OWASP LLM Top 10 2025** | 10 critical risks for LLM applications | OWASP GenAI Security (2025) | Sec 54 |
| **MoE (DeepSeek-V3)** | 671B quality at 37B compute (sparse activation) | Friendli (Aug 2025) | Sec 49 |

### CPU-First Validation (Real Benchmarks)

| Model Size | CPU Tokens/sec | Verdict |
|------------|---------------|---------|
| 125M | 278.73 | ✅ Comfortable interactive |
| 350M | 73.34 | ✅ Interactive |
| 1B | 8.60 | ⚠️ Marginally interactive |
| 3B | 0.94 | ❌ Batch only |
| 7B | 0.06 | ❌ Infeasible on CPU |
| 13B | 0.004 | ❌ Requires GPU |

**Conclusion**: CPU-first is viable for 125M-1B models. 7B+ requires GPU.

### Golden Token Stack (23 Techniques)

The complete stack of techniques that reduce per-token cost by 90-99%:
- **Model**: Compact models, distillation, MoE, multi-model routing
- **Quantization**: INT8 (4x), INT4 (8x), GGUF
- **Inference**: PagedAttention (24x), speculative decoding (2-3x), FlashAttention (GPU only)
- **Caching**: Semantic (89% hit), prefix (30-60%), exact-match (100%)
- **Data**: Textbook quality, curriculum learning, deduplication
- **Token**: BPE (18x compression), stop-word removal, context compression

## 📚 Documentation

- [**PRD PDF**](docs/IBR_Platform_PRD.pdf) — 224-page comprehensive specification (107 sections, 6 parts)
- [Architecture Guide](docs/architecture.md) — Layered architecture and project structure
- [ADR Index](docs/adr/README.md) — 15 Architecture Decision Records
- [Master Build Prompt](MASTER_BUILD_PROMPT.md) — 1319-line AI build instructions
- Research notes: `docs/research/section_*_research.md`

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/ibrsiaika/IBR-AI.git
cd IBR-AI

# Install
pip install -e ".[dev]"

# Verify
python -c "import ibr_platform; print(ibr_platform.__version__)"

# Run tests
make test-unit
```

## 📦 What's Implemented

### Phase 0 — Foundation (Complete)
- ✅ **Section 32**: System Design — Folder Structure & Architecture
  - src layout (src/ibr_platform/), pyproject.toml, Makefile
  - AgentBase ABC, Task, AgentResult, HealthStatus, AgentRegistry
  - Pydantic Settings configuration (4 deployment modes)

- ✅ **Section 31**: Phase 1 — Deep Research (14 ADRs)
  - ADR-0002 through ADR-0015 (technology decisions)
  - Key decisions: PyTorch+DeepSpeed, vLLM, pgvectorscale+Qdrant, Neo4j,
    Kafka, containerd+gVisor, LangGraph, Vault, Phoenix

### Phase 1 — Core Platform (In Progress)
- ✅ **Section 10**: High-Level Architecture
  - 10-layer ArchitectureLayer enum (USER → DEPLOYMENT)
  - LayerBase ABC, can_depend() dependency rule checker
  - TaskOrchestrator (submit, get_result, cancel, health_check)

- ✅ **Section 11**: Multi-Agent Architecture
  - AgentMessage JSON envelope (14 fields, PRD 11.2)
  - AgentLifecycle (spawn, execute, terminate, health_check)
  - 12-agent roster (Planner, Research, Verification, Memory, etc.)

- ✅ **Section 22**: Security & Safety Requirements
  - RBAC (4 roles: admin/engineer/researcher/viewer)
  - Immutable audit log (SHA-256 hash-chained, tamper-evident)
  - Approval gate (two-person rule for critical actions)
  - Sandbox config (gVisor, no egress by default)

- ✅ **Section 33**: Agent Framework (8 P0 agents)
  - PlannerAgent, WebResearchAgent, VerificationAgent, MemoryAgent
  - KnowledgeGraphAgent, TrainingAgent, EvaluationAgent, DeploymentAgent
  - ToolBase ABC, ToolRegistry

- ✅ **Section 35**: Memory System (12-tier)
  - 12 MemoryTiers (WORKING through COMPRESSED)
  - MemoryManager API (write, read, search, update, delete, summarize)
  - Scope isolation (project, user, organization)
  - Versioning (immutable entries, get_versions)
  - TTL-based eviction, access tracking, per-tier stats

### Test Summary
- **337 tests** — all passing
- Lint: 0 errors (ruff)
- Type check: 0 errors (mypy strict, 29 source files)
- Security: 0 issues (bandit)

## 📂 Project Structure

```
IBR-AI/
├── src/ibr_platform/
│   ├── agents/               # 8 P0 agents + tool framework
│   │   ├── base.py           # AgentBase ABC, Task, AgentResult
│   │   ├── message.py        # AgentMessage (JSON envelope)
│   │   ├── lifecycle.py      # AgentLifecycle manager
│   │   ├── roster.py         # 12-agent roster
│   │   ├── tools.py          # ToolBase, ToolRegistry
│   │   ├── planner/          # PlannerAgent
│   │   ├── research/         # WebResearchAgent
│   │   ├── verification/     # VerificationAgent
│   │   ├── memory_agent/     # MemoryAgent
│   │   ├── knowledge_graph/  # KnowledgeGraphAgent
│   │   ├── training_agent/   # TrainingAgent
│   │   ├── evaluation_agent/ # EvaluationAgent
│   │   └── deployment_agent/ # DeploymentAgent
│   ├── platform/
│   │   ├── architecture.py   # 10-layer architecture
│   │   ├── orchestrator.py   # TaskOrchestrator
│   │   ├── memory.py         # 12-tier memory system
│   │   └── security/         # RBAC, audit, approval, sandbox
│   ├── config/               # Pydantic Settings
│   ├── api/                  # REST/gRPC APIs (pending)
│   └── utils/                # Shared utilities
├── tests/unit/               # 337 tests (all passing)
├── docs/                     # PRD PDF, ADRs, research notes
├── pyproject.toml            # Python project config
└── Makefile                  # 20+ commands
```

## 🔧 Development

```bash
make dev-install     # Install with all extras
make test-unit       # Run unit tests
make check           # Lint + type check + security scan
make pre-commit      # All pre-commit checks
make format          # Format code
```

## 📊 Deployment Modes

| Mode | Hardware | RAM | Model | Engine |
|------|----------|-----|-------|--------|
| Tiny | Laptop | 2 GB | 125M-1B | llama.cpp |
| Compact | Workstation | 8 GB | 1B-3B | llama.cpp/vLLM |
| Professional | Server | 32 GB | 7B-13B | vLLM |
| Enterprise | Cluster | 128+ GB | 70B+ | vLLM+TensorParallel |

## 🗺️ Roadmap (Per MASTER_BUILD_PROMPT.md)

**Completed**: Sections 32, 31, 10, 11, 22, 33, 35

**Next** (priority order):
- Section 34: Research Engine (crawlers, parsers, extractors)
- Section 50: Production RAG (hybrid search, reranking)
- Section 51: Knowledge Graph Construction
- Section 39: Model Training (SFT, LoRA, QLoRA, GRPO)
- Section 38: Dataset Generation (9 dataset types)
- Section 40: Self-Improvement Loop
- Section 20: APIs & Dashboard
- Section 17: CPU Optimization & Deployment Modes
- Sections 45-107: All verified research sections

## 📝 Copyright

© 2026 ibrsiaika. All rights reserved.
This software is proprietary and confidential. Unauthorized use, copying,
distribution, or modification is strictly prohibited.
