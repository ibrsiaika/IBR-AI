"""
Agents package — Specialist AI agents (PRD Section 33).

Contains 25+ agents organized by function group:
    - base: AgentBase ABC, Task, AgentResult, AgentRegistry
    - message: AgentMessage JSON envelope (PRD Section 11.2)
    - lifecycle: AgentLifecycle manager (PRD Section 11.3)
    - roster: 12-agent roster metadata (PRD Section 11.1)
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
from ibr_platform.agents.lifecycle import (
    AgentInstance,
    AgentLifecycle,
)
from ibr_platform.agents.message import AgentMessage
from ibr_platform.agents.roster import (
    AGENT_ROSTER,
    get_agent_info,
    list_agent_names,
    list_agents_by_group,
    list_agents_by_priority,
)

__all__ = [
    # Base
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
    # Message
    "AgentMessage",
    # Lifecycle
    "AgentInstance",
    "AgentLifecycle",
    # Roster
    "AGENT_ROSTER",
    "get_agent_info",
    "list_agent_names",
    "list_agents_by_group",
    "list_agents_by_priority",
]
