# ADR-0003: Training Framework — PyTorch + DeepSpeed

**Date**: 2026-07-28
**Status**: Accepted
**PRD Reference**: PRD Section 31.3, Section 39 (Model Training), Section 52 (GRPO)

## Context

The platform's training pipeline (Phase 9) requires distributed training of models from 1B to 70B+ parameters. The framework must support: SFT, LoRA, QLoRA, GRPO, distillation; distributed training across multiple GPUs; checkpointing and resumption; and reproducibility.

## Decision

Use PyTorch as the primary ML framework with DeepSpeed for distributed training.

## Alternatives

### 1. PyTorch + DeepSpeed (CHOSEN)

PyTorch has the broadest ML ecosystem (transformers, sentence-transformers, scikit-learn). DeepSpeed provides ZeRO Stage 1/2/3 for memory efficiency and pipeline parallelism for large models. Industry standard as of 2025.

### 2. JAX + Flax

Excellent for research (Google DeepMind uses it for Gemma), functional programming model enables easy parallelism. But steeper learning curve and smaller ecosystem than PyTorch.

### 3. TensorFlow

Mature, production-tested, but declining in ML research popularity. Keras API is friendly but TF 2.x has fragmented ecosystem.

### 4. MXNet

Apache project with good performance, but minimal community support and declining adoption.


## Consequences

### Positive

- Broadest ecosystem — transformers, sentence-transformers, peft, trl, accelerate all support PyTorch
- DeepSpeed enables training 70B+ models on limited GPU memory via ZeRO
- Large talent pool — most ML engineers know PyTorch
- Excellent documentation and community support

### Negative

- Python GIL limits CPU-bound parallelism (mitigated by DataLoader workers)
- PyTorch 2.x compilation (torch.compile) is still maturing
- DeepSpeed adds configuration complexity

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
