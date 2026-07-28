# ADR-0002: Model Architecture — Transformer + Mamba Hybrid

**Date**: 2026-07-28
**Status**: Accepted
**PRD Reference**: PRD Section 31.3 (Table 31.1), Section 49 (MoE Architecture), Section 95 (Phi-3)

## Context

The platform needs models that can handle both complex reasoning (where Transformer excels) and long contexts (where Mamba's linear-time attention is superior). Pure Transformer scales quadratically with sequence length, making 100K+ token contexts expensive. Pure Mamba lacks the reasoning capability of Transformer's attention mechanism.

## Decision

Adopt a hybrid architecture combining Transformer (for reasoning) with Mamba (for long-context efficiency).

## Alternatives

### 1. Pure Transformer

Well-understood, broad ecosystem support, but O(n²) attention limits long-context efficiency. 100K token context requires significant memory.

### 2. Pure Mamba (State Space Model)

Linear-time inference, excellent for long contexts, but lacks the attention mechanism that enables strong reasoning on complex tasks.

### 3. RWKV

Linear-time RNN-like architecture with Transformer-quality performance. Promising but less mature than Transformer/Mamba hybrids.

### 4. Transformer + Mamba Hybrid (CHOSEN)

Use Transformer layers for reasoning-heavy parts of the model and Mamba layers for long-context processing. Combines strengths of both. Used by Jamba (AI21 Labs) and similar 2024-2025 models.


## Consequences

### Positive

- Excellent quality-to-compute ratio — Transformer for quality, Mamba for efficiency
- Can handle 100K+ token contexts without quadratic memory blowup
- Aligns with 2024-2025 hybrid architecture trend (Jamba, etc.)

### Negative

- More complex than pure Transformer — two architectures to maintain
- Less community support than pure Transformer
- Hybrid layer placement requires experimentation

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
