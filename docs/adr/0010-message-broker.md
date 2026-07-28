# ADR-0010: Message Broker — Apache Kafka

**Date**: 2026-07-28
**Status**: Accepted
**PRD Reference**: PRD Section 31.3, Section 22 (Security — Audit Logging), Section 24 (Observability)

## Context

The platform needs durable, replayable messaging for: audit logs (7-year retention for compliance), event streaming (agent task events), and inter-service communication. Redis Streams lacks durability guarantees; RabbitMQ lacks replay capability.

## Decision

Use Apache Kafka as the primary message broker for event streaming, audit logging, and inter-service communication.

## Alternatives

### 1. Apache Kafka (CHOSEN)

Durable, high-throughput, replayable (critical for audit). Proven at massive scale (LinkedIn, Netflix, Uber). Append-only log is ideal for compliance audit trails.

### 2. Redis Streams

Simpler than Kafka, lower latency. But lacks Kafka's durability guarantees and replay capability. Not suitable for audit logging.

### 3. RabbitMQ

Mature, good for request-response patterns. But not designed for event streaming or replay.

### 4. Apache Pulsar

Offers multi-tenancy and geo-replication advantages over Kafka. But adds operational complexity and smaller community. Could be reconsidered for Enterprise mode.

### 5. NATS

Lightweight, high-performance. But lacks Kafka's ecosystem and durability features.


## Consequences

### Positive

- Durable, replayable logs — essential for audit compliance
- Proven at massive scale (LinkedIn processes trillions of messages/day)
- Rich ecosystem (Kafka Connect, Kafka Streams, Schema Registry)
- Supports event sourcing pattern for the platform's audit log

### Negative

- Operational complexity (Kafka clusters require careful tuning)
- Higher latency than Redis Streams for simple pub/sub
- Overkill for Tiny mode (could use Redis Streams as fallback)

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
