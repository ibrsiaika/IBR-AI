# ADR-0008: Inference Server — vLLM

**Date**: 2026-07-28
**Status**: Accepted
**PRD Reference**: PRD Section 31.3, Section 47 (Golden Token Stack), Section 100 (Low-Resource Inference)

## Context

The platform's inference server must deliver high throughput (100+ tokens/sec), low latency (p99 <2.5s), and support for continuous batching, PagedAttention, and speculative decoding. The arXiv performance study (Nov 2025) confirms vLLM achieves 24x higher throughput than HuggingFace TGI.

## Decision

Use vLLM as the primary LLM inference server, with llama.cpp as fallback for CPU-only deployment.

## Alternatives

### 1. vLLM (CHOSEN)

PagedAttention (24x throughput vs TGI), continuous batching (23-39x vs static), speculative decoding support, broad model support. Industry standard as of 2025. Validated by arXiv 2511.17593.

### 2. HuggingFace TGI

Good integration with HF ecosystem, but 24x slower than vLLM under high concurrency per arXiv benchmark.

### 3. NVIDIA Triton Inference Server

Enterprise-grade, supports multiple frameworks. But complex configuration and not LLM-specific.

### 4. SGLang

Newer alternative with good performance, but smaller community and less model support than vLLM.

### 5. TensorRT-LLM

NVIDIA's optimized inference. Excellent performance on NVIDIA GPUs but vendor lock-in.

### 6. llama.cpp (CPU fallback)

Best for CPU-only deployment (Tiny/Compact modes). GGUF format with configurable quantization. Used as fallback when GPU is unavailable.


## Consequences

### Positive

- 24x throughput improvement over alternatives (validated)
- PagedAttention eliminates KV cache fragmentation
- Supports speculative decoding (2-3x latency reduction)
- Active development and broad community support

### Negative

- GPU required for best performance (CPU mode falls back to llama.cpp)
- Configuration complexity for advanced features (speculative decoding, tensor parallelism)
- Rapid releases may introduce breaking changes

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
