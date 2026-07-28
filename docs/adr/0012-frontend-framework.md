# ADR-0012: Frontend Framework — Next.js 14 + React + TypeScript + Tailwind

**Date**: 2026-07-28
**Status**: Accepted
**PRD Reference**: PRD Section 31.3, Section 20 (APIs & Dashboard), Section 42 (Documentation)

## Context

The platform's dashboard (PRD Section 20.2) needs: real-time agent status, knowledge graph visualization, training job monitoring, and cost tracking. The framework must support SSR (for performance), strong typing (for maintainability), and rapid UI development.

## Decision

Use Next.js 14 (App Router) with React, TypeScript, and Tailwind CSS for the dashboard.

## Alternatives

### 1. Next.js 14 + React + TypeScript + Tailwind (CHOSEN)

Industry standard, large talent pool, SSR for performance, TypeScript for type safety, Tailwind for rapid styling. Most comprehensive ecosystem.

### 2. Vue 3 + Nuxt

Excellent DX, smaller bundle size. But smaller talent pool and ecosystem than React.

### 3. Svelte + SvelteKit

Best runtime performance, least boilerplate. But smallest ecosystem and fewer libraries.

### 4. Angular

Enterprise-grade with strong opinions. But steep learning curve and declining popularity.

### 5. Remix

Excellent web standards compliance. But smaller ecosystem than Next.js.


## Consequences

### Positive

- Largest talent pool — easiest to hire for
- SSR/SSG for performance and SEO
- TypeScript for type safety in large codebases
- Tailwind enables rapid, consistent styling
- Rich ecosystem of React component libraries (shadcn/ui, Radix)

### Negative

- React's ecosystem can be overwhelming (too many choices)
- Next.js 14 App Router is relatively new (some breaking changes from Pages Router)
- Node.js required for frontend (separate from Python backend)

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
