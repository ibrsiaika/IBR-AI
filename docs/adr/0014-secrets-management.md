# ADR-0014: Secrets Management — HashiCorp Vault

**Date**: 2026-07-28
**Status**: Accepted
**PRD Reference**: PRD Section 31.3, Section 22 (Security), Section 13 (Compliance)

## Context

The platform must manage: API keys, database passwords, model weights (for proprietary models), OAuth tokens, and encryption keys. Secrets must never be in source code, environment variables, or config files. The system must support audit logging, dynamic secrets, and multi-cloud deployment.

## Decision

Use HashiCorp Vault as the primary secrets management system, with cloud-native alternatives (AWS Secrets Manager, GCP Secret Manager) as optional backends.

## Alternatives

### 1. HashiCorp Vault (CHOSEN)

Cloud-agnostic, dynamic secrets, audit logging, broad adoption. Open-source (BSL) with Enterprise tier. Industry standard for secrets management.

### 2. AWS Secrets Manager

Good if fully on AWS. But vendor lock-in and not usable for multi-cloud or on-premise.

### 3. GCP Secret Manager

Good if fully on GCP. Same vendor lock-in concern as AWS.

### 4. Azure Key Vault

Good if fully on Azure. Same vendor lock-in concern.

### 5. Doppler

Modern, developer-friendly secrets manager. But newer and less feature-complete than Vault.

### 6. Sealed Secrets (Kubernetes)

Good for K8s-native secrets but limited to K8s and lacks dynamic secrets.

### 7. Environment variables + .env files

Simple but insecure for production. No audit logging, no rotation, no access control. FORBIDDEN per RULE #8.


## Consequences

### Positive

- Cloud-agnostic — works on AWS, GCP, Azure, and on-premise
- Dynamic secrets (generates short-lived credentials on demand)
- Comprehensive audit logging for compliance
- Broad adoption — large community and tooling ecosystem

### Negative

- Operational complexity (Vault cluster requires careful setup)
- Vault Enterprise (for replication) requires paid license
- Adds a dependency (Vault must be highly available)

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
