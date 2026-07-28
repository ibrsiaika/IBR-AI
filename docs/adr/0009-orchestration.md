# ADR-0009: Orchestration — Kubernetes + Ray + Volcano

**Date**: 2026-07-28
**Status**: Accepted
**PRD Reference**: PRD Section 31.3, Section 65 (GPU Cluster Scheduling), Section 32.3 (Runtime/Kernel/Scheduler)

## Context

The platform needs to orchestrate: microservices (API, dashboard, agents), distributed training jobs (requiring gang scheduling), and distributed inference (multi-replica vLLM). Native Kubernetes scheduling cannot handle gang scheduling, leading to deadlock when multiple distributed jobs compete for GPUs.

## Decision

Use Kubernetes for service orchestration, Ray for ML workload orchestration, and Volcano for gang scheduling of distributed training jobs.

## Alternatives

### 1. Kubernetes + Ray + Volcano (CHOSEN)

K8s for services, Ray for ML workloads (training + distributed inference), Volcano for gang scheduling. KubeRay integrates Ray with K8s. Validated by PRD Section 65.

### 2. Pure Kubernetes (no Ray)

Simpler but lacks Ray's actor model for distributed ML. Training jobs would need custom distributed orchestration.

### 3. Pure Ray (no K8s)

Ray handles ML workloads well but lacks K8s's service orchestration, networking, and ecosystem (Helm, Istio, etc.).

### 4. Nomad

HashiCorp's orchestrator. Simpler than K8s but smaller ecosystem and less community support.

### 5. Docker Swarm

Simple but limited features. Not suitable for production ML workloads.


## Consequences

### Positive

- K8s is the industry standard — broad ecosystem, all clouds support it
- Ray's actor model fits agent architecture perfectly
- Volcano eliminates gang scheduling deadlock for distributed training
- KubeRay integrates Ray clusters with K8s declaratively

### Negative

- Three systems to learn and operate (K8s, Ray, Volcano)
- K8s operational complexity (but unavoidable for Enterprise mode)
- Volcano adds a custom scheduler (potential compatibility issues)

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
