# IBR Platform — Developer Guide

**Version**: 0.1.0
**Audience**: Contributing engineers
**Last Updated**: 2026-07-28

## Quick Start

```bash
# Clone
git clone https://github.com/ibrsiaika/IBR-AI.git
cd IBR-AI

# Install (development mode)
pip install -e ".[dev]"

# Run tests
make test-unit

# Run linting
make lint

# Run the API server
make dev
```

## Architecture

The platform uses a 10-layer architecture (PRD Section 10):
1. User (CLI, Dashboard, API)
2. Orchestration (TaskOrchestrator)
3. Planning (PlannerAgent)
4. Execution (25+ specialist agents)
5. Knowledge (KnowledgeGraph + VectorDB)
6. Data (DatasetGenerator)
7. Training (TrainingPipeline)
8. Evaluation (EvaluationAgent)
9. Registry (ModelRegistry)
10. Deployment (DeploymentAgent)

Dependency rule: upper layers depend on lower layers, never reverse.

## Key Modules

| Module | Location | Description |
|--------|----------|-------------|
| AgentBase | `agents/base.py` | Abstract base class for all agents |
| AgentMessage | `agents/message.py` | JSON communication envelope |
| TaskOrchestrator | `platform/orchestrator.py` | Entry point for requests |
| MemoryManager | `platform/memory.py` | 12-tier memory system |
| KnowledgeGraph | `platform/knowledge_graph/` | Entity/relationship graph |
| ResearchPipeline | `platform/research/` | 5 free data sources |
| HybridSearch | `platform/rag/` | BM25 + Dense + RRF |
| TrainingPipeline | `platform/training/` | SFT, LoRA, QLoRA, GRPO |
| DatasetGenerator | `platform/dataset/` | 9 dataset types |
| SelfImprovementLoop | `platform/improvement/` | Failure → Hypothesis → Experiment |
| Quantizer | `platform/compression/` | INT8/INT4 quantization |
| GuardrailStack | `platform/safety/` | 6-layer safety stack |
| ComplianceChecker | `platform/compliance/` | GDPR, SOC2, HIPAA, EU AI Act |
| DeploymentManager | `platform/deployment/` | 4 deployment modes |
| API Server | `api/server/` | FastAPI REST endpoints |
| CS Formulas | `utils/formulas.py` | 14 mathematical formulas |

## Testing

```bash
# Run all unit tests (536+ tests)
make test-unit

# Run with coverage
make test-cov

# Run specific module
pytest tests/unit/test_memory_system.py -v
```

## Code Quality

```bash
make check  # lint + type check + security scan
make format # auto-format code
```

## Deployment Modes

| Mode | Hardware | Model | Engine |
|------|----------|-------|--------|
| Tiny | Laptop | 125M-1B | llama.cpp |
| Compact | Workstation | 1B-3B | llama.cpp |
| Professional | Server | 7B-13B | vLLM |
| Enterprise | Cluster | 70B+ | vLLM+TP |

## FREE Data Sources

All data sources are FREE — no paid APIs:
- DuckDuckGo (web search)
- arXiv (academic papers)
- Wikipedia (encyclopedia)
- GitHub (code repositories)
- PubMed (biomedical literature)
