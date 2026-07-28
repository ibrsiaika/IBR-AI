# ADR-0015: Container Runtime — containerd + gVisor (for Sandboxing)

**Date**: 2026-07-28
**Status**: Accepted
**PRD Reference**: PRD Section 31.3, Section 22 (Security — Sandboxed Execution), Section 65 (GPU Scheduling)

## Context

The platform runs agent code in sandboxed containers (PRD Section 22.1). The container runtime must be: CNCF-standard, lightweight, and support additional sandboxing for untrusted agent code. As of 2025, containerd is the de facto K8s runtime; gVisor provides kernel-level sandboxing on top.

## Decision

Use containerd as the primary container runtime, with gVisor for agent sandboxing (high-security workloads).

## Alternatives

### 1. containerd + gVisor for sandboxing (CHOSEN)

containerd is the CNCF standard (replaced Docker as K8s default). gVisor provides an additional kernel-level sandbox for agent execution (intercepts syscalls). Together: standard + secure.

### 2. containerd only (no gVisor)

Standard and simple but lacks the additional sandboxing layer for untrusted agent code. Acceptable for trusted workloads but not for agent execution.

### 3. CRI-O

CNCF project used by OpenShift. Functionally similar to containerd but smaller community. No significant advantage.

### 4. Docker Engine

No longer supported as K8s runtime (deprecated in K8s 1.24). Still fine for building images but not for running containers in K8s.

### 5. Kata Containers

VM-based container runtime — strongest isolation but heaviest overhead. Considered for highest-security workloads but overkill for general use.

### 6. gVisor only (not as runtime class)

gVisor is a runtime class, not a standalone runtime. Must be used with containerd or CRI-O.


## Consequences

### Positive

- containerd is the industry standard — broad support, well-documented
- gVisor provides kernel-level sandboxing for agent code (PRD Section 22)
- Both are open-source (Apache 2.0 and BSD)
- gVisor intercepts syscalls, preventing container escape attacks

### Negative

- gVisor adds 10-30% overhead on syscall-heavy workloads
- gVisor does not support all syscalls (some applications may fail)
- Two runtime classes to manage (default containerd, sandboxed gVisor)

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
