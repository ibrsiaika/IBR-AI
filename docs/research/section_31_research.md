# Section 31 Research — Phase 1: Deep Research (14 ADRs)

**Date**: 2026-07-28
**PRD Section**: 31 (Phase 1 — Deep Research)
**Researcher**: AI Engineering Agent

## Topic Summary

This research informs 14 Architecture Decision Records (ADRs) that document
the technology choices for the IBR Platform. Each ADR covers one major
technology decision from PRD Section 31.3 (Table 31.1), with alternatives,
rationale, and consequences.

## Sources

### General
1. PRD Section 21 — Technology Stack Evaluation
   - https://github.com/ibrsiaika/IBR-AI/blob/main/docs/IBR_Platform_PRD.pdf
2. PRD Section 31 — Phase 1 Deep Research
3. PRD Sections 45-107 — Verified research on specific technologies

### Training Framework (ADR-0003)
4. ML Engineer comparison of PyTorch, TensorFlow, JAX
   - Sep 2024 — https://www.reddit.com/r/MachineLearning/comments/...
5. PyTorch vs JAX: Which Framework to Choose in 2025
   - https://www.datacamp.com/blog/pytorch-vs-jax

### Message Broker (ADR-0010)
6. What's your go-to message queue in 2025?
   - https://www.reddit.com/r/devops/comments/...
7. Kafka vs. Pulsar: Which Message Broker Actually Wins?
   - Oct 2025 — https://www.confluent.io/blog/kafka-vs-pulsar

### Container Runtime (ADR-0015)
8. CRI-O vs containerd: Choosing and Managing Kubernetes
   - https://www.aquasec.com/blog/cri-o-vs-containerd/
9. Kubernetes Without Docker: Why Container Runtimes Are Changing
   - Apr 2025 — https://thenewstack.io/kubernetes-without-docker/

### Vector Database (ADR-0006)
10. Firecrawl, "Best Vector Databases in 2026"
    - May 2026 — https://www.firecrawl.dev/blog/best-vector-databases
11. PRD Section 69 — Vector Database Comparison (Extended)

### Inference Server (ADR-0008)
12. arXiv 2511.17593 — vLLM vs HuggingFace TGI Performance Study
    - Nov 2025 — https://arxiv.org/html/2511.17593v1

### Agent Framework (ADR-0004)
13. PRD Section 55 — Real-World Agentic AI Deployments
14. LangGraph documentation — https://langchain-ai.github.io/langgraph/

### Observability (ADR-0011)
15. PRD Section 68 — LLM Observability Tooling

## Key Findings

### 1. PyTorch Remains the ML Standard (2025-2026)
PyTorch continues to dominate ML research and production, with the broadest
ecosystem, best community support, and DeepSpeed for distributed training.
JAX is excellent for research (especially at Google DeepMind) but has a
steeper learning curve and smaller ecosystem. For the IBR Platform, PyTorch
is the clear choice — it aligns with the platform's ML dependencies
(transformers, sentence-transformers, scikit-learn) and DeepSpeed provides
the distributed training capabilities needed for Phase 9.

### 2. Kafka Wins for Durability and Scale
For the platform's message broker needs (audit logging, event streaming,
inter-service communication), Kafka is the proven choice at scale. Redis
Streams is simpler but lacks Kafka's durability guarantees and replay
capability. Pulsar offers some advantages (multi-tenancy, geo-replication)
but adds operational complexity. For audit logging (which must be durable
and replayable for compliance), Kafka's append-only log is ideal.

### 3. containerd is the Default Kubernetes Runtime
As of 2025, containerd is the de facto container runtime for Kubernetes,
having replaced Docker as the default. CRI-O is a viable alternative (used
by OpenShift) but containerd has broader adoption. For high-security
workloads, gVisor provides an additional sandboxing layer on top of
containerd. The IBR Platform uses containerd with gVisor for agent sandboxes.

### 4. pgvectorscale Challenges Qdrant (Revised from PRD)
The PRD Section 69 research revealed that pgvectorscale achieves 471 QPS
at 99% recall on 50M vectors — 11.4x better than Qdrant's 41 QPS. This
challenges the original Phase 1 decision (Qdrant). The revised decision
(ADR-0006) uses pgvectorscale for moderate scale (<100M vectors) and Qdrant
for very large scale (>100M vectors).

### 5. vLLM is the Inference Standard
The arXiv performance study (Nov 2025) confirms vLLM achieves 24x higher
throughput than HuggingFace TGI via PagedAttention and continuous batching.
This is the single highest-impact inference optimization available.

## How Findings Apply to the 14 ADRs

Each finding informs the corresponding ADR:
- ADR-0003 (Training Framework): PyTorch + DeepSpeed
- ADR-0010 (Message Broker): Apache Kafka
- ADR-0015 (Container Runtime): containerd + gVisor
- ADR-0006 (Vector Database): pgvectorscale (moderate) / Qdrant (large)
- ADR-0008 (Inference Server): vLLM

The remaining ADRs (0002, 0004, 0005, 0007, 0009, 0011, 0012, 0013, 0014)
are informed by the PRD's existing research (Sections 45-107).

## Deviations from PRD

**Deviation 1**: ADR-0006 (Vector Database) revises the PRD Section 31.3
decision from "Qdrant" to "pgvectorscale for moderate scale, Qdrant for
large scale" based on the Firecrawl benchmark (May 2026) documented in
PRD Section 69.

**Justification**: The Firecrawl benchmark provides empirical evidence
that pgvectorscale outperforms Qdrant at moderate scale. The revised
decision preserves Qdrant for very large scale where its HNSW
implementation excels.

## Next Steps

1. Write ADR-0002 through ADR-0015 (14 ADRs)
2. Write ADR index (docs/adr/README.md)
3. Run tests to verify all ADRs have required structure
4. Commit and push
