# Section 32 Research — System Design: Folder Structure & Architecture

**Date**: 2026-07-28
**PRD Section**: 32 (Phase 2 — System Design)
**Researcher**: AI Engineering Agent

## Topic Summary

This research informs the implementation of PRD Section 32, which specifies the
project's folder structure, runtime/kernel/scheduler design, knowledge graph schema,
model registry schema, and plugin/tool system. The goal is to create a Python
monorepo that is well-organized, testable, and deployable across the four deployment
modes (Tiny, Compact, Professional, Enterprise).

## Sources

1. Python Packaging Authority, "pyproject.toml specification"
   - https://packaging.python.org/en/latest/specifications/pyproject-toml/
   - Authoritative source for Python project configuration

2. Brian Skinn, "My How and Why: pyproject.toml & the 'src' Project Structure"
   - https://bskinn.github.io/My-How-Why-Pyproject-Src
   - Apr 2019 (updated through 2025)
   - Documents the 'src' layout convention and its benefits

3. uv monorepo documentation issue
   - https://github.com/astral-sh/uv/issues/10960
   - Documents best practices for Python monorepo organization with uv

4. AWS, "AI agent frameworks & building blocks"
   - https://aws.amazon.com/marketplace/build-learn/ai-agent-learning-series/agent-frameworks
   - 2025 — covers CrewAI, AutoGen, Strands Agents SDK patterns

5. Langflow, "The Complete Guide to Choosing an AI Agent Framework"
   - https://www.langflow.org/blog/the-complete-guide-to-choosing-an-ai-agent-framework
   - Oct 2025 — covers 2025 agent framework architecture patterns

## Key Findings

### 1. The 'src' Layout is Best Practice
The 'src' layout (code in `src/` rather than project root) prevents accidental
imports of uninstalled packages during testing. This is critical for a project
like IBR that has many internal packages — without the src layout, tests might
import the local `platform/` directory rather than the installed `ibr_platform`
package, masking packaging errors.

**Decision**: Adopt the src layout. Code goes in `src/ibr_platform/`, tests in
`tests/`, with `pyproject.toml` at the root.

### 2. Monorepo with Namespace Packages
For a project with multiple deployable components (platform, agents, api,
dashboard), a monorepo with namespace packages is preferred over multiple
repositories. This enables:
- Atomic commits across components
- Shared dependencies and configuration
- Easier local development (one checkout)
- Simpler CI/CD

**Decision**: Monorepo structure with Python namespace packages
(`ibr_platform.platform`, `ibr_platform.agents`, `ibr_platform.api`).

### 3. Agent Base Class Pattern
The 2025 agent frameworks (CrewAI, AutoGen, LangGraph, Strands SDK) converge on
a common pattern for agent base classes:
- `initialize(config)` — set up the agent with configuration
- `execute(task) -> result` — perform the agent's work
- `health_check() -> status` — verify the agent is healthy
- `shutdown()` — clean up resources

This matches the PRD Section 33.4 specification. The base class should be an
abstract base class (ABC) with abstract methods, preventing instantiation of
incomplete agents.

**Decision**: Implement `AgentBase` as a Python ABC with abstract methods
`initialize`, `execute`, `health_check`, `shutdown`. Add type hints throughout.

### 4. Configuration via Pydantic Settings
Modern Python projects use Pydantic Settings for configuration management —
it provides type validation, environment variable loading, and nested config
support. This is superior to plain YAML or .env files.

**Decision**: Use Pydantic Settings for all configuration. Configs are defined
as Python classes, loaded from environment variables and YAML files.

### 5. Test Structure Mirrors Source Structure
Tests should mirror the source structure: `tests/unit/platform/test_runtime.py`
tests `src/ibr_platform/platform/runtime.py`. This makes it easy to find tests
for any module.

**Decision**: Tests in `tests/unit/`, `tests/integration/`, `tests/e2e/`,
mirroring the source structure.

## How Findings Apply to Section 32

- The folder structure from PRD Section 32.2 is adopted, with the 'src' layout
  (code in `src/ibr_platform/` rather than root-level `platform/`)
- The `AgentBase` ABC is implemented in `src/ibr_platform/agents/base.py`
- Configuration uses Pydantic Settings in `src/ibr_platform/config/`
- Tests mirror the source structure

## Deviations from PRD

**Deviation 1**: PRD Section 32.2 specifies `/platform/`, `/agents/`, etc. at
the repo root. The research recommends 'src' layout (`src/ibr_platform/platform/`).
**Justification**: The 'src' layout prevents accidental imports of uninstalled
packages and is the modern Python best practice. The logical structure is
preserved; only the physical location changes.

**Deviation 2**: PRD does not specify configuration management approach.
**Justification**: Pydantic Settings is chosen based on 2025 best practices
for type-safe configuration with environment variable support.

## Next Steps

1. Create `pyproject.toml` with project metadata and dependencies
2. Create the `src/ibr_platform/` package structure
3. Implement `AgentBase` ABC
4. Implement configuration management (Pydantic Settings)
5. Write tests for structure validation
6. Create Makefile with common commands
7. Document in README.md and docs/architecture.md
