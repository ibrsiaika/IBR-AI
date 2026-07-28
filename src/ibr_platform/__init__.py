"""
IBR (Intelligent Brain Runtime) Platform.

An autonomous agentic AI research and self-improving foundation model platform.
Built CPU-first, deployable from laptop to datacenter cluster.

This package contains:
    - platform: Core platform (runtime, kernel, scheduler, config)
    - agents: Specialist AI agents (25+ agents per PRD Section 33)
    - api: REST and gRPC API definitions
    - config: Configuration management via Pydantic Settings
    - models: Model definitions and training configs
    - data: Dataset schemas and processing pipelines
    - utils: Shared utilities

See: /docs/IBR_Platform_PRD.pdf for the complete specification (224 pages, 107 sections).
"""

__version__ = "0.1.0"
__author__ = "ibrsiaika"
__email__ = "ibrsiaika@users.noreply.github.com"

# Proprietary — private property, not for sale, no license granted.
__license__ = "Proprietary"

__all__ = ["__version__", "__author__", "__email__", "__license__"]
