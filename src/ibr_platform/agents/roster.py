"""
Agent Roster — 12 Specialist Agents (PRD Section 11.1, Table 11.1).

This module defines the metadata for all 12 specialist agents in the IBR
Platform. Each agent has: name, role, function_group, tools, memory_access,
and priority.

The roster is a static dictionary that serves as the source of truth for
which agents exist and what they do. The actual agent implementations
(inherit from AgentBase) are registered separately via the AgentRegistry.

References:
    - PRD Section 11.1 (Agent Inventory, Table 11.1)
    - PRD Section 33 (Agent Framework — Phase 3)
"""

from __future__ import annotations

from typing import Any

# Agent Roster (PRD Section 11.1, Table 11.1)
# Each entry: name -> {role, function_group, tools, memory_access, priority}
AGENT_ROSTER: dict[str, dict[str, Any]] = {
    "Planner": {
        "name": "Planner",
        "role": "Decompose objectives into execution graphs",
        "function_group": "Orchestration",
        "tools": ["task_graph_builder", "cost_estimator"],
        "memory_access": "Read: project memory; Write: plan artifacts",
        "priority": "P0",
    },
    "WebResearch": {
        "name": "WebResearch",
        "role": "Search and read web sources",
        "function_group": "Research",
        "tools": ["search_api", "browser_automation", "html_parser", "pdf_parser"],
        "memory_access": "Read: working memory; Write: research artifacts",
        "priority": "P0",
    },
    "AcademicResearch": {
        "name": "AcademicResearch",
        "role": "Read papers from arXiv, PubMed, IEEE, ACM",
        "function_group": "Research",
        "tools": ["scholarly_apis", "citation_extractor"],
        "memory_access": "Read: working memory; Write: paper summaries",
        "priority": "P0",
    },
    "CodeResearch": {
        "name": "CodeResearch",
        "role": "Analyze Git repositories, documentation, issues",
        "function_group": "Research",
        "tools": ["git_client", "language_servers", "ast_parser"],
        "memory_access": "Read: working memory; Write: code summaries",
        "priority": "P0",
    },
    "Verification": {
        "name": "Verification",
        "role": "Cross-source fact-checking, confidence scoring",
        "function_group": "Quality",
        "tools": ["source_ranker", "contradiction_detector"],
        "memory_access": "Read: research artifacts; Write: evidence reports",
        "priority": "P0",
    },
    "Memory": {
        "name": "Memory",
        "role": "Store and retrieve knowledge across sessions",
        "function_group": "State",
        "tools": ["vector_db", "graph_db", "sql"],
        "memory_access": "Read/Write: all memory tiers",
        "priority": "P0",
    },
    "KnowledgeGraph": {
        "name": "KnowledgeGraph",
        "role": "Extract entities, relationships, events",
        "function_group": "State",
        "tools": ["ner", "relation_extraction", "event_extraction", "graph_db"],
        "memory_access": "Read: research artifacts; Write: graph entities/edges",
        "priority": "P0",
    },
    "Dataset": {
        "name": "Dataset",
        "role": "Generate training datasets",
        "function_group": "Data",
        "tools": ["data_assembler", "quality_scorer", "deduplicator"],
        "memory_access": "Read: knowledge graph, memory; Write: dataset artifacts",
        "priority": "P1",
    },
    "Training": {
        "name": "Training",
        "role": "Run training jobs (SFT, LoRA, QLoRA, GRPO)",
        "function_group": "ML",
        "tools": ["pytorch", "deepspeed", "lora", "distributed_scheduler"],
        "memory_access": "Read: datasets; Write: model artifacts",
        "priority": "P0",
    },
    "Evaluation": {
        "name": "Evaluation",
        "role": "Run benchmarks, compute metrics",
        "function_group": "ML",
        "tools": ["benchmark_harness", "statistical_tests"],
        "memory_access": "Read: model artifacts; Write: eval reports",
        "priority": "P0",
    },
    "SelfImprovement": {
        "name": "SelfImprovement",
        "role": "Triage failures, propose experiments",
        "function_group": "ML",
        "tools": ["failure_analyzer", "hypothesis_generator"],
        "memory_access": "Read: eval reports, audit logs; Write: experiment plans",
        "priority": "P1",
    },
    "Deployment": {
        "name": "Deployment",
        "role": "Promote models to production, canary, rollback",
        "function_group": "Operations",
        "tools": ["canary_controller", "ab_router", "rollback_engine"],
        "memory_access": "Read: model registry; Write: deployment records",
        "priority": "P0",
    },
}


def get_agent_info(name: str) -> dict[str, Any] | None:
    """Get metadata for a specific agent.

    Args:
        name: Agent name (e.g., "Planner").

    Returns:
        Agent metadata dict, or None if not found.
    """
    return AGENT_ROSTER.get(name)


def list_agent_names() -> list[str]:
    """List all agent names in the roster.

    Returns:
        List of agent names.
    """
    return list(AGENT_ROSTER.keys())


def list_agents_by_group(group: str) -> list[str]:
    """List agents in a specific function group.

    Args:
        group: Function group name (e.g., "Research", "ML").

    Returns:
        List of agent names in that group.
    """
    return [
        name
        for name, info in AGENT_ROSTER.items()
        if info.get("function_group") == group
    ]


def list_agents_by_priority(priority: str) -> list[str]:
    """List agents with a specific priority.

    Args:
        priority: Priority level ("P0", "P1", or "P2").

    Returns:
        List of agent names with that priority.
    """
    return [
        name
        for name, info in AGENT_ROSTER.items()
        if info.get("priority") == priority
    ]
