# ADR-0011: Observability Stack — Prometheus + Grafana + Loki + Tempo + Phoenix

**Date**: 2026-07-28
**Status**: Accepted
**PRD Reference**: PRD Section 31.3, Section 24 (Observability), Section 68 (LLM Observability Tooling)

## Context

The platform needs three-pillar observability (metrics, logs, traces) plus LLM-specific observability (agent traces, evaluation). Traditional APM tools (Datadog, New Relic) cannot capture semantic quality of LLM outputs.

## Decision

Use the open-source observability stack (Prometheus, Grafana, Loki, Tempo) for general observability, plus Arize Phoenix for LLM-specific tracing and evaluation.

## Alternatives

### 1. Prometheus + Grafana + Loki + Tempo + Phoenix (CHOSEN)

Open-source, integrated, no vendor lock-in. Phoenix adds LLM-specific agent tracing. Validated by PRD Section 68.

### 2. Datadog

Comprehensive APM but expensive at scale and cannot capture LLM semantic quality. Vendor lock-in.

### 3. New Relic

Similar to Datadog — good APM but not LLM-specific.

### 4. Splunk

Powerful log analysis but expensive and not LLM-specific.

### 5. Elastic Stack (ELK)

Good for logs but weaker on metrics and traces than Prometheus/Grafana.

### 6. LangSmith (instead of Phoenix)

Excellent LangChain integration but not open-source. Phoenix is Apache 2.0 and can be self-hosted.


## Consequences

### Positive

- Fully open-source — no vendor lock-in or licensing costs
- Integrated stack — metrics, logs, traces in one platform
- Phoenix adds LLM-specific agent evaluation (PRD Section 68)
- Self-hostable for Enterprise data residency requirements

### Negative

- More components to operate than a single-vendor solution
- Requires Grafana dashboard development effort
- Phoenix is newer than established APM tools

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
