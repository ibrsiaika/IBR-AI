#!/usr/bin/env python3
"""Generate 14 ADRs (ADR-0002 through ADR-0015) for Section 31."""
from pathlib import Path

ADR_DIR = Path(__file__).resolve().parent.parent / "docs" / "adr"
ADR_DIR.mkdir(parents=True, exist_ok=True)

ADRS = [
    {
        "number": "0002",
        "slug": "model-architecture",
        "title": "Model Architecture — Transformer + Mamba Hybrid",
        "decision": "Adopt a hybrid architecture combining Transformer (for reasoning) with Mamba (for long-context efficiency).",
        "context": "The platform needs models that can handle both complex reasoning (where Transformer excels) and long contexts (where Mamba's linear-time attention is superior). Pure Transformer scales quadratically with sequence length, making 100K+ token contexts expensive. Pure Mamba lacks the reasoning capability of Transformer's attention mechanism.",
        "alternatives": [
            ("Pure Transformer", "Well-understood, broad ecosystem support, but O(n²) attention limits long-context efficiency. 100K token context requires significant memory."),
            ("Pure Mamba (State Space Model)", "Linear-time inference, excellent for long contexts, but lacks the attention mechanism that enables strong reasoning on complex tasks."),
            ("RWKV", "Linear-time RNN-like architecture with Transformer-quality performance. Promising but less mature than Transformer/Mamba hybrids."),
            ("Transformer + Mamba Hybrid (CHOSEN)", "Use Transformer layers for reasoning-heavy parts of the model and Mamba layers for long-context processing. Combines strengths of both. Used by Jamba (AI21 Labs) and similar 2024-2025 models."),
        ],
        "consequences_pos": [
            "Excellent quality-to-compute ratio — Transformer for quality, Mamba for efficiency",
            "Can handle 100K+ token contexts without quadratic memory blowup",
            "Aligns with 2024-2025 hybrid architecture trend (Jamba, etc.)",
        ],
        "consequences_neg": [
            "More complex than pure Transformer — two architectures to maintain",
            "Less community support than pure Transformer",
            "Hybrid layer placement requires experimentation",
        ],
        "prd_refs": "PRD Section 31.3 (Table 31.1), Section 49 (MoE Architecture), Section 95 (Phi-3)",
    },
    {
        "number": "0003",
        "slug": "training-framework",
        "title": "Training Framework — PyTorch + DeepSpeed",
        "decision": "Use PyTorch as the primary ML framework with DeepSpeed for distributed training.",
        "context": "The platform's training pipeline (Phase 9) requires distributed training of models from 1B to 70B+ parameters. The framework must support: SFT, LoRA, QLoRA, GRPO, distillation; distributed training across multiple GPUs; checkpointing and resumption; and reproducibility.",
        "alternatives": [
            ("PyTorch + DeepSpeed (CHOSEN)", "PyTorch has the broadest ML ecosystem (transformers, sentence-transformers, scikit-learn). DeepSpeed provides ZeRO Stage 1/2/3 for memory efficiency and pipeline parallelism for large models. Industry standard as of 2025."),
            ("JAX + Flax", "Excellent for research (Google DeepMind uses it for Gemma), functional programming model enables easy parallelism. But steeper learning curve and smaller ecosystem than PyTorch."),
            ("TensorFlow", "Mature, production-tested, but declining in ML research popularity. Keras API is friendly but TF 2.x has fragmented ecosystem."),
            ("MXNet", "Apache project with good performance, but minimal community support and declining adoption."),
        ],
        "consequences_pos": [
            "Broadest ecosystem — transformers, sentence-transformers, peft, trl, accelerate all support PyTorch",
            "DeepSpeed enables training 70B+ models on limited GPU memory via ZeRO",
            "Large talent pool — most ML engineers know PyTorch",
            "Excellent documentation and community support",
        ],
        "consequences_neg": [
            "Python GIL limits CPU-bound parallelism (mitigated by DataLoader workers)",
            "PyTorch 2.x compilation (torch.compile) is still maturing",
            "DeepSpeed adds configuration complexity",
        ],
        "prd_refs": "PRD Section 31.3, Section 39 (Model Training), Section 52 (GRPO)",
    },
    {
        "number": "0004",
        "slug": "agent-framework",
        "title": "Agent Framework — Custom Layer on LangGraph",
        "decision": "Build a custom agent framework on top of LangGraph primitives, adding IBR-specific contracts, security, and observability.",
        "context": "The platform needs 25+ specialist agents that communicate via structured JSON messages (PRD Section 11.2), with full observability, human approval gates, and sandboxed execution. Off-the-shelf frameworks (LangChain, CrewAI) lack the enterprise features required.",
        "alternatives": [
            ("Custom on LangGraph (CHOSEN)", "LangGraph provides graph-based agent orchestration with state management and checkpointing. Custom layer adds IBR JSON protocol, security, audit logging, and enterprise features. Best of both worlds."),
            ("LangChain", "Broadest ecosystem but lacks graph-based orchestration. Agent execution is linear, not graph-based. No built-in state management for long-running workflows."),
            ("CrewAI", "Simple role-based API, good for prototyping. Lacks enterprise features (RBAC, audit logging, multi-tenancy) and graph-based execution."),
            ("AutoGPT", "Pioneered autonomous agents but codebase is experimental. Not suitable for production enterprise deployment."),
            ("Pure Custom (no framework)", "Maximum control but reinvents the wheel. LangGraph's graph execution, state management, and checkpointing are valuable primitives not worth rebuilding."),
        ],
        "consequences_pos": [
            "Graph-based orchestration matches the platform's execution graph model",
            "LangGraph is maintained by LangChain team — active development",
            "Custom layer enables IBR-specific security and compliance",
            "Can leverage LangChain ecosystem (tools, integrations)",
        ],
        "consequences_neg": [
            "Custom layer adds development and maintenance overhead",
            "LangGraph API may change (relatively new project)",
            "Team must understand both LangGraph and the custom layer",
        ],
        "prd_refs": "PRD Section 31.3, Section 33 (Agent Framework), Section 55 (Real-World Agentic AI)",
    },
    {
        "number": "0005",
        "slug": "rag-architecture",
        "title": "RAG Architecture — Hybrid (Dense + Sparse + Graph)",
        "decision": "Implement hybrid retrieval combining BM25 (sparse), dense vector search, and knowledge graph traversal, with reciprocal rank fusion (RRF) and cross-encoder reranking.",
        "context": "Naive vector RAG is insufficient for production (PRD Section 50.1). The platform needs retrieval that combines keyword precision (BM25), semantic understanding (dense), and multi-hop reasoning (graph). Production RAG requires overfetch-and-rerank for quality, and source tracking for citation.",
        "alternatives": [
            ("Hybrid: Dense + Sparse + Graph with RRF + Reranking (CHOSEN)", "BM25 for keyword precision, dense for semantic, graph for multi-hop. RRF fuses BM25+dense; cross-encoder reranks top candidates. Validated by PRD Section 50 benchmarks (15-30% nDCG improvement)."),
            ("Pure Dense (vector only)", "Simple but misses keyword-precise queries (code identifiers, proper nouns). PRD Section 78 benchmark showed no improvement over BM25 with poor embeddings."),
            ("Pure Sparse (BM25 only)", "Excellent for keyword queries but misses semantic similarity. Cannot find paraphrased content."),
            ("RAG-Fusion", "Generates multiple query variants and fuses results. Adds latency but improves recall. Could be a future enhancement."),
        ],
        "consequences_pos": [
            "15-30% nDCG improvement over dense-only (validated in PRD Section 50)",
            "Handles both keyword-precise and semantic-similarity queries",
            "Graph retrieval enables multi-hop reasoning (PRD Section 51)",
            "Cross-encoder reranking improves precision on top results",
        ],
        "consequences_neg": [
            "Three retrieval systems to maintain (BM25, vector, graph)",
            "Reranking adds 50-200ms latency per query",
            "RRF weight tuning required per use case",
        ],
        "prd_refs": "PRD Section 31.3, Section 50 (Production RAG), Section 51 (Knowledge Graphs)",
    },
    {
        "number": "0006",
        "slug": "vector-database",
        "title": "Vector Database — pgvectorscale (Moderate) + Qdrant (Large Scale)",
        "decision": "Use pgvectorscale for moderate scale (<100M vectors) and Qdrant for very large scale (>100M vectors) or advanced filtering requirements.",
        "context": "The platform needs vector similarity search for retrieval, semantic caching, and entity resolution. The original PRD decision (Qdrant) is revised based on the Firecrawl benchmark (May 2026) showing pgvectorscale achieves 471 QPS at 99% recall on 50M vectors — 11.4x better than Qdrant's 41 QPS.",
        "alternatives": [
            ("pgvectorscale for moderate scale, Qdrant for large scale (CHOSEN)", "pgvectorscale runs on PostgreSQL (which the platform already uses), reducing operational complexity. 11.4x faster than Qdrant at 50M vectors. For >100M vectors or advanced filtering, Qdrant's HNSW is superior."),
            ("Qdrant (original PRD decision)", "Apache 2.0, Rust-based reliability, strong filtering. But 11.4x slower than pgvectorscale at moderate scale per Firecrawl benchmark."),
            ("Milvus / Zilliz", "Purpose-built for very large scale (1B+ vectors). Good for Enterprise mode but overkill for Tiny/Compact modes."),
            ("Pinecone", "Managed service, no ops required. But vendor lock-in and not self-hostable (conflicts with Enterprise data residency requirements)."),
            ("pgvector (not pgvectorscale)", "Original Postgres vector extension. Slower than pgvectorscale but sufficient for <1M vectors. Used in Tiny mode."),
        ],
        "consequences_pos": [
            "pgvectorscale reduces operational complexity (one less database to manage)",
            "11.4x performance improvement at moderate scale",
            "Qdrant preserved for large-scale and advanced filtering use cases",
            "Both are open-source (Apache 2.0)",
        ],
        "consequences_neg": [
            "Two vector databases to support (pgvectorscale and Qdrant)",
            "Migration path needed if scale exceeds pgvectorscale's sweet spot",
            "pgvectorscale is newer (less battle-tested than Qdrant)",
        ],
        "prd_refs": "PRD Section 31.3 (original), Section 69 (revised — Vector DB Comparison), Section 77 (Vector Search Benchmark)",
    },
    {
        "number": "0007",
        "slug": "graph-database",
        "title": "Graph Database — Neo4j Enterprise",
        "decision": "Use Neo4j Enterprise as the primary graph database for the knowledge graph.",
        "context": "The platform's knowledge graph (PRD Section 32.4) stores entities, relationships, events with provenance. It must support Cypher queries for multi-hop reasoning, scale to 1B+ entities, and provide enterprise clustering for high availability.",
        "alternatives": [
            ("Neo4j Enterprise (CHOSEN)", "Mature Cypher query language, proven at billion-edge scale, enterprise clustering and RBAC. Reference implementation for LLM-driven KG construction (PRD Section 51)."),
            ("Neo4j Community Edition", "Free and open-source (GPLv3), but lacks clustering, RBAC, and advanced security features needed for Enterprise mode."),
            ("Nebula Graph", "Open-source, distributed, good for very large scale. But smaller community and less mature than Neo4j."),
            ("TigerGraph", "Enterprise-grade, good for analytics. But proprietary and expensive; overkill for the platform's needs."),
            ("ArangoDB", "Multi-model (graph + document + key-value). Reduces infrastructure but lacks Cypher and has weaker graph query capabilities."),
            ("Amazon Neptune", "Managed graph database. But vendor lock-in and not self-hostable."),
        ],
        "consequences_pos": [
            "Mature Cypher query language with broad adoption",
            "Enterprise features (clustering, RBAC, audit logging) for compliance",
            "Reference implementation for LLM-driven KG (Neo4j LLM Graph Builder)",
            "Strong Python driver and ecosystem",
        ],
        "consequences_neg": [
            "Enterprise Edition requires commercial license (budget required for Enterprise mode)",
            "Community Edition (GPLv3) may conflict with proprietary licensing",
            "Not as horizontally scalable as Nebula or TigerGraph",
        ],
        "prd_refs": "PRD Section 31.3, Section 32.4 (KG Schema), Section 51 (KG Construction)",
    },
    {
        "number": "0008",
        "slug": "inference-server",
        "title": "Inference Server — vLLM",
        "decision": "Use vLLM as the primary LLM inference server, with llama.cpp as fallback for CPU-only deployment.",
        "context": "The platform's inference server must deliver high throughput (100+ tokens/sec), low latency (p99 <2.5s), and support for continuous batching, PagedAttention, and speculative decoding. The arXiv performance study (Nov 2025) confirms vLLM achieves 24x higher throughput than HuggingFace TGI.",
        "alternatives": [
            ("vLLM (CHOSEN)", "PagedAttention (24x throughput vs TGI), continuous batching (23-39x vs static), speculative decoding support, broad model support. Industry standard as of 2025. Validated by arXiv 2511.17593."),
            ("HuggingFace TGI", "Good integration with HF ecosystem, but 24x slower than vLLM under high concurrency per arXiv benchmark."),
            ("NVIDIA Triton Inference Server", "Enterprise-grade, supports multiple frameworks. But complex configuration and not LLM-specific."),
            ("SGLang", "Newer alternative with good performance, but smaller community and less model support than vLLM."),
            ("TensorRT-LLM", "NVIDIA's optimized inference. Excellent performance on NVIDIA GPUs but vendor lock-in."),
            ("llama.cpp (CPU fallback)", "Best for CPU-only deployment (Tiny/Compact modes). GGUF format with configurable quantization. Used as fallback when GPU is unavailable."),
        ],
        "consequences_pos": [
            "24x throughput improvement over alternatives (validated)",
            "PagedAttention eliminates KV cache fragmentation",
            "Supports speculative decoding (2-3x latency reduction)",
            "Active development and broad community support",
        ],
        "consequences_neg": [
            "GPU required for best performance (CPU mode falls back to llama.cpp)",
            "Configuration complexity for advanced features (speculative decoding, tensor parallelism)",
            "Rapid releases may introduce breaking changes",
        ],
        "prd_refs": "PRD Section 31.3, Section 47 (Golden Token Stack), Section 100 (Low-Resource Inference)",
    },
    {
        "number": "0009",
        "slug": "orchestration",
        "title": "Orchestration — Kubernetes + Ray + Volcano",
        "decision": "Use Kubernetes for service orchestration, Ray for ML workload orchestration, and Volcano for gang scheduling of distributed training jobs.",
        "context": "The platform needs to orchestrate: microservices (API, dashboard, agents), distributed training jobs (requiring gang scheduling), and distributed inference (multi-replica vLLM). Native Kubernetes scheduling cannot handle gang scheduling, leading to deadlock when multiple distributed jobs compete for GPUs.",
        "alternatives": [
            ("Kubernetes + Ray + Volcano (CHOSEN)", "K8s for services, Ray for ML workloads (training + distributed inference), Volcano for gang scheduling. KubeRay integrates Ray with K8s. Validated by PRD Section 65."),
            ("Pure Kubernetes (no Ray)", "Simpler but lacks Ray's actor model for distributed ML. Training jobs would need custom distributed orchestration."),
            ("Pure Ray (no K8s)", "Ray handles ML workloads well but lacks K8s's service orchestration, networking, and ecosystem (Helm, Istio, etc.)."),
            ("Nomad", "HashiCorp's orchestrator. Simpler than K8s but smaller ecosystem and less community support."),
            ("Docker Swarm", "Simple but limited features. Not suitable for production ML workloads."),
        ],
        "consequences_pos": [
            "K8s is the industry standard — broad ecosystem, all clouds support it",
            "Ray's actor model fits agent architecture perfectly",
            "Volcano eliminates gang scheduling deadlock for distributed training",
            "KubeRay integrates Ray clusters with K8s declaratively",
        ],
        "consequences_neg": [
            "Three systems to learn and operate (K8s, Ray, Volcano)",
            "K8s operational complexity (but unavoidable for Enterprise mode)",
            "Volcano adds a custom scheduler (potential compatibility issues)",
        ],
        "prd_refs": "PRD Section 31.3, Section 65 (GPU Cluster Scheduling), Section 32.3 (Runtime/Kernel/Scheduler)",
    },
    {
        "number": "0010",
        "slug": "message-broker",
        "title": "Message Broker — Apache Kafka",
        "decision": "Use Apache Kafka as the primary message broker for event streaming, audit logging, and inter-service communication.",
        "context": "The platform needs durable, replayable messaging for: audit logs (7-year retention for compliance), event streaming (agent task events), and inter-service communication. Redis Streams lacks durability guarantees; RabbitMQ lacks replay capability.",
        "alternatives": [
            ("Apache Kafka (CHOSEN)", "Durable, high-throughput, replayable (critical for audit). Proven at massive scale (LinkedIn, Netflix, Uber). Append-only log is ideal for compliance audit trails."),
            ("Redis Streams", "Simpler than Kafka, lower latency. But lacks Kafka's durability guarantees and replay capability. Not suitable for audit logging."),
            ("RabbitMQ", "Mature, good for request-response patterns. But not designed for event streaming or replay."),
            ("Apache Pulsar", "Offers multi-tenancy and geo-replication advantages over Kafka. But adds operational complexity and smaller community. Could be reconsidered for Enterprise mode."),
            ("NATS", "Lightweight, high-performance. But lacks Kafka's ecosystem and durability features."),
        ],
        "consequences_pos": [
            "Durable, replayable logs — essential for audit compliance",
            "Proven at massive scale (LinkedIn processes trillions of messages/day)",
            "Rich ecosystem (Kafka Connect, Kafka Streams, Schema Registry)",
            "Supports event sourcing pattern for the platform's audit log",
        ],
        "consequences_neg": [
            "Operational complexity (Kafka clusters require careful tuning)",
            "Higher latency than Redis Streams for simple pub/sub",
            "Overkill for Tiny mode (could use Redis Streams as fallback)",
        ],
        "prd_refs": "PRD Section 31.3, Section 22 (Security — Audit Logging), Section 24 (Observability)",
    },
    {
        "number": "0011",
        "slug": "observability-stack",
        "title": "Observability Stack — Prometheus + Grafana + Loki + Tempo + Phoenix",
        "decision": "Use the open-source observability stack (Prometheus, Grafana, Loki, Tempo) for general observability, plus Arize Phoenix for LLM-specific tracing and evaluation.",
        "context": "The platform needs three-pillar observability (metrics, logs, traces) plus LLM-specific observability (agent traces, evaluation). Traditional APM tools (Datadog, New Relic) cannot capture semantic quality of LLM outputs.",
        "alternatives": [
            ("Prometheus + Grafana + Loki + Tempo + Phoenix (CHOSEN)", "Open-source, integrated, no vendor lock-in. Phoenix adds LLM-specific agent tracing. Validated by PRD Section 68."),
            ("Datadog", "Comprehensive APM but expensive at scale and cannot capture LLM semantic quality. Vendor lock-in."),
            ("New Relic", "Similar to Datadog — good APM but not LLM-specific."),
            ("Splunk", "Powerful log analysis but expensive and not LLM-specific."),
            ("Elastic Stack (ELK)", "Good for logs but weaker on metrics and traces than Prometheus/Grafana."),
            ("LangSmith (instead of Phoenix)", "Excellent LangChain integration but not open-source. Phoenix is Apache 2.0 and can be self-hosted."),
        ],
        "consequences_pos": [
            "Fully open-source — no vendor lock-in or licensing costs",
            "Integrated stack — metrics, logs, traces in one platform",
            "Phoenix adds LLM-specific agent evaluation (PRD Section 68)",
            "Self-hostable for Enterprise data residency requirements",
        ],
        "consequences_neg": [
            "More components to operate than a single-vendor solution",
            "Requires Grafana dashboard development effort",
            "Phoenix is newer than established APM tools",
        ],
        "prd_refs": "PRD Section 31.3, Section 24 (Observability), Section 68 (LLM Observability Tooling)",
    },
    {
        "number": "0012",
        "slug": "frontend-framework",
        "title": "Frontend Framework — Next.js 14 + React + TypeScript + Tailwind",
        "decision": "Use Next.js 14 (App Router) with React, TypeScript, and Tailwind CSS for the dashboard.",
        "context": "The platform's dashboard (PRD Section 20.2) needs: real-time agent status, knowledge graph visualization, training job monitoring, and cost tracking. The framework must support SSR (for performance), strong typing (for maintainability), and rapid UI development.",
        "alternatives": [
            ("Next.js 14 + React + TypeScript + Tailwind (CHOSEN)", "Industry standard, large talent pool, SSR for performance, TypeScript for type safety, Tailwind for rapid styling. Most comprehensive ecosystem."),
            ("Vue 3 + Nuxt", "Excellent DX, smaller bundle size. But smaller talent pool and ecosystem than React."),
            ("Svelte + SvelteKit", "Best runtime performance, least boilerplate. But smallest ecosystem and fewer libraries."),
            ("Angular", "Enterprise-grade with strong opinions. But steep learning curve and declining popularity."),
            ("Remix", "Excellent web standards compliance. But smaller ecosystem than Next.js."),
        ],
        "consequences_pos": [
            "Largest talent pool — easiest to hire for",
            "SSR/SSG for performance and SEO",
            "TypeScript for type safety in large codebases",
            "Tailwind enables rapid, consistent styling",
            "Rich ecosystem of React component libraries (shadcn/ui, Radix)",
        ],
        "consequences_neg": [
            "React's ecosystem can be overwhelming (too many choices)",
            "Next.js 14 App Router is relatively new (some breaking changes from Pages Router)",
            "Node.js required for frontend (separate from Python backend)",
        ],
        "prd_refs": "PRD Section 31.3, Section 20 (APIs & Dashboard), Section 42 (Documentation)",
    },
    {
        "number": "0013",
        "slug": "backend-language",
        "title": "Backend Language — Python (Agents) + Go (Services)",
        "decision": "Use Python for agent and ML code, Go for high-concurrency infrastructure services.",
        "context": "The platform has two distinct backend needs: (1) ML/agent code that needs PyTorch, transformers, and the ML ecosystem (Python), and (2) high-concurrency infrastructure services (API gateway, message router, health checker) that benefit from Go's performance and concurrency model.",
        "alternatives": [
            ("Python (agents) + Go (services) (CHOSEN)", "Python for ML ecosystem alignment, Go for high-concurrency services. Each language used where it excels. Industry pattern (e.g., Uber, Discord use this split)."),
            ("Pure Python", "Simpler (one language) but Python's GIL limits high-concurrency services. Asyncio helps for I/O-bound but not CPU-bound work."),
            ("Pure Go", "Excellent performance and concurrency but lacks ML ecosystem. Would require CGO bindings to PyTorch — fragile and slow."),
            ("Rust", "Best performance and safety but steep learning curve and smaller talent pool. Considered for future performance-critical components."),
            ("Java", "Mature, good performance, but verbose and declining in ML/AI adoption."),
            ("Node.js/TypeScript", "Good for APIs and shares language with frontend, but weak ML ecosystem."),
        ],
        "consequences_pos": [
            "Each language used where it excels (Python for ML, Go for services)",
            "Go services are fast, memory-efficient, and easy to deploy (single binary)",
            "Python agents have full access to ML ecosystem",
            "Industry-proven pattern (Uber, Discord, etc.)",
        ],
        "consequences_neg": [
            "Two languages to maintain (Python and Go)",
            "Inter-language communication adds complexity (gRPC recommended)",
            "Team needs both Python and Go skills",
        ],
        "prd_refs": "PRD Section 31.3, Section 33 (Agent Framework), Section 20 (APIs)",
    },
    {
        "number": "0014",
        "slug": "secrets-management",
        "title": "Secrets Management — HashiCorp Vault",
        "decision": "Use HashiCorp Vault as the primary secrets management system, with cloud-native alternatives (AWS Secrets Manager, GCP Secret Manager) as optional backends.",
        "context": "The platform must manage: API keys, database passwords, model weights (for proprietary models), OAuth tokens, and encryption keys. Secrets must never be in source code, environment variables, or config files. The system must support audit logging, dynamic secrets, and multi-cloud deployment.",
        "alternatives": [
            ("HashiCorp Vault (CHOSEN)", "Cloud-agnostic, dynamic secrets, audit logging, broad adoption. Open-source (BSL) with Enterprise tier. Industry standard for secrets management."),
            ("AWS Secrets Manager", "Good if fully on AWS. But vendor lock-in and not usable for multi-cloud or on-premise."),
            ("GCP Secret Manager", "Good if fully on GCP. Same vendor lock-in concern as AWS."),
            ("Azure Key Vault", "Good if fully on Azure. Same vendor lock-in concern."),
            ("Doppler", "Modern, developer-friendly secrets manager. But newer and less feature-complete than Vault."),
            ("Sealed Secrets (Kubernetes)", "Good for K8s-native secrets but limited to K8s and lacks dynamic secrets."),
            ("Environment variables + .env files", "Simple but insecure for production. No audit logging, no rotation, no access control. FORBIDDEN per RULE #8."),
        ],
        "consequences_pos": [
            "Cloud-agnostic — works on AWS, GCP, Azure, and on-premise",
            "Dynamic secrets (generates short-lived credentials on demand)",
            "Comprehensive audit logging for compliance",
            "Broad adoption — large community and tooling ecosystem",
        ],
        "consequences_neg": [
            "Operational complexity (Vault cluster requires careful setup)",
            "Vault Enterprise (for replication) requires paid license",
            "Adds a dependency (Vault must be highly available)",
        ],
        "prd_refs": "PRD Section 31.3, Section 22 (Security), Section 13 (Compliance)",
    },
    {
        "number": "0015",
        "slug": "container-runtime",
        "title": "Container Runtime — containerd + gVisor (for Sandboxing)",
        "decision": "Use containerd as the primary container runtime, with gVisor for agent sandboxing (high-security workloads).",
        "context": "The platform runs agent code in sandboxed containers (PRD Section 22.1). The container runtime must be: CNCF-standard, lightweight, and support additional sandboxing for untrusted agent code. As of 2025, containerd is the de facto K8s runtime; gVisor provides kernel-level sandboxing on top.",
        "alternatives": [
            ("containerd + gVisor for sandboxing (CHOSEN)", "containerd is the CNCF standard (replaced Docker as K8s default). gVisor provides an additional kernel-level sandbox for agent execution (intercepts syscalls). Together: standard + secure."),
            ("containerd only (no gVisor)", "Standard and simple but lacks the additional sandboxing layer for untrusted agent code. Acceptable for trusted workloads but not for agent execution."),
            ("CRI-O", "CNCF project used by OpenShift. Functionally similar to containerd but smaller community. No significant advantage."),
            ("Docker Engine", "No longer supported as K8s runtime (deprecated in K8s 1.24). Still fine for building images but not for running containers in K8s."),
            ("Kata Containers", "VM-based container runtime — strongest isolation but heaviest overhead. Considered for highest-security workloads but overkill for general use."),
            ("gVisor only (not as runtime class)", "gVisor is a runtime class, not a standalone runtime. Must be used with containerd or CRI-O."),
        ],
        "consequences_pos": [
            "containerd is the industry standard — broad support, well-documented",
            "gVisor provides kernel-level sandboxing for agent code (PRD Section 22)",
            "Both are open-source (Apache 2.0 and BSD)",
            "gVisor intercepts syscalls, preventing container escape attacks",
        ],
        "consequences_neg": [
            "gVisor adds 10-30% overhead on syscall-heavy workloads",
            "gVisor does not support all syscalls (some applications may fail)",
            "Two runtime classes to manage (default containerd, sandboxed gVisor)",
        ],
        "prd_refs": "PRD Section 31.3, Section 22 (Security — Sandboxed Execution), Section 65 (GPU Scheduling)",
    },
]


def generate_adr(adr: dict) -> str:
    """Generate ADR markdown content."""
    alt_section = "\n".join(
        f"### {i}. {name}\n\n{desc}\n" for i, (name, desc) in enumerate(adr["alternatives"], 1)
    )
    pos_section = "\n".join(f"- {p}" for p in adr["consequences_pos"])
    neg_section = "\n".join(f"- {n}" for n in adr["consequences_neg"])

    return f"""# ADR-{adr["number"]}: {adr["title"]}

**Date**: 2026-07-28
**Status**: Accepted
**PRD Reference**: {adr["prd_refs"]}

## Context

{adr["context"]}

## Decision

{adr["decision"]}

## Alternatives

{alt_section}

## Consequences

### Positive

{pos_section}

### Negative

{neg_section}

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
"""


# Write all ADRs
for adr in ADRS:
    path = ADR_DIR / f'{adr["number"]}-{adr["slug"]}.md'
    path.write_text(generate_adr(adr))
    print(f"  ✓ {path.name}")

print(f"\nGenerated {len(ADRS)} ADRs in {ADR_DIR}")
