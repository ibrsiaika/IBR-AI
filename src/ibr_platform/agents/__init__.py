"""
Agents package — Specialist AI agents (PRD Section 33).

Contains 25+ agents organized by function group:
    - base: AgentBase ABC, Task, AgentResult, AgentRegistry
    - planner: Planner agent (decompose objectives into execution graphs)
    - research: Web, academic, code research agents
    - verification: Cross-source fact-checking and confidence scoring
    - memory: Memory agent (multi-tier storage and retrieval)
    - knowledge_graph: KG agent (entity/relationship extraction)
    - training: Training agent (SFT, LoRA, QLoRA, GRPO)
    - evaluation: Evaluation agent (benchmarks, metrics)
    - deployment: Deployment agent (canary, A/B, rollback)
    - security: Security agent (audit, policy enforcement)
    - coding: Coding agent (read, modify, test code)
    - reasoning: Reasoning agent (CoT, ToT, ReAct, Reflexion)
"""

from ibr_platform.agents.base import (
    AgentBase,
    AgentExecutionError,
    AgentInitializationError,
    AgentRegistry,
    AgentResult,
    AgentStatus,
    HealthStatus,
    MessageStatus,
    Priority,
    Task,
    get_registry,
    register_agent,
)

__all__ = [
    "AgentBase",
    "AgentExecutionError",
    "AgentInitializationError",
    "AgentRegistry",
    "AgentResult",
    "AgentStatus",
    "HealthStatus",
    "MessageStatus",
    "Priority",
    "Task",
    "get_registry",
    "register_agent",
]
