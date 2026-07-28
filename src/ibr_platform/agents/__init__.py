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

# Import and register all P0 agents (PRD Section 33.2)
from ibr_platform.agents.deployment_agent import DeploymentAgent
from ibr_platform.agents.evaluation_agent import EvaluationAgent
from ibr_platform.agents.knowledge_graph import KnowledgeGraphAgent
from ibr_platform.agents.lifecycle import (
    AgentInstance,
    AgentLifecycle,
)
from ibr_platform.agents.memory_agent import MemoryAgent
from ibr_platform.agents.message import AgentMessage
from ibr_platform.agents.planner import PlannerAgent
from ibr_platform.agents.research import WebResearchAgent
from ibr_platform.agents.roster import (
    AGENT_ROSTER,
    get_agent_info,
    list_agent_names,
    list_agents_by_group,
    list_agents_by_priority,
)
from ibr_platform.agents.training_agent import TrainingAgent
from ibr_platform.agents.verification import VerificationAgent

# Register agents in the global registry

_registry = get_registry()
if "PlannerAgent" not in _registry.list_agents():
    _registry.register("PlannerAgent", PlannerAgent)
if "WebResearchAgent" not in _registry.list_agents():
    _registry.register("WebResearchAgent", WebResearchAgent)
if "VerificationAgent" not in _registry.list_agents():
    _registry.register("VerificationAgent", VerificationAgent)
if "MemoryAgent" not in _registry.list_agents():
    _registry.register("MemoryAgent", MemoryAgent)
if "KnowledgeGraphAgent" not in _registry.list_agents():
    _registry.register("KnowledgeGraphAgent", KnowledgeGraphAgent)
if "TrainingAgent" not in _registry.list_agents():
    _registry.register("TrainingAgent", TrainingAgent)
if "EvaluationAgent" not in _registry.list_agents():
    _registry.register("EvaluationAgent", EvaluationAgent)
if "DeploymentAgent" not in _registry.list_agents():
    _registry.register("DeploymentAgent", DeploymentAgent)

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
