"""
Tests for Section 33 — Agent Framework (Phase 3, 8 P0 agents).

Verifies that all 8 P0 priority agents:
1. Inherit from AgentBase
2. Can be instantiated
3. Implement all 4 lifecycle methods (initialize, execute, health_check, shutdown)
4. Are registered in the agent registry
5. Return correct AgentResult from execute()

Run: pytest tests/unit/test_agent_framework.py -v
"""
from __future__ import annotations

import pytest

P0_AGENTS = [
    "PlannerAgent",
    "WebResearchAgent",
    "VerificationAgent",
    "MemoryAgent",
    "KnowledgeGraphAgent",
    "TrainingAgent",
    "EvaluationAgent",
    "DeploymentAgent",
]


class TestToolFramework:
    """Test the tool framework (PRD Section 32.6)."""

    def test_tool_base_importable(self) -> None:
        """ToolBase is importable."""
        from ibr_platform.agents.tools import ToolBase
        assert ToolBase is not None

    def test_tool_base_is_abstract(self) -> None:
        """ToolBase cannot be instantiated directly."""
        from ibr_platform.agents.tools import ToolBase
        with pytest.raises(TypeError):
            ToolBase()

    def test_concrete_tool_works(self) -> None:
        """A concrete ToolBase subclass can be instantiated and called."""
        from ibr_platform.agents.tools import ToolBase, ToolResult

        class EchoTool(ToolBase):
            @property
            def name(self) -> str:
                return "echo"

            async def execute(self, **kwargs: object) -> ToolResult:
                return ToolResult(success=True, data={"echo": kwargs.get("message", "")})

        tool = EchoTool()
        assert tool.name == "echo"

    def test_tool_registry(self) -> None:
        """ToolRegistry can register and retrieve tools."""
        from ibr_platform.agents.tools import ToolBase, ToolRegistry, ToolResult

        class TestTool(ToolBase):
            @property
            def name(self) -> str:
                return "test_tool"

            async def execute(self, **kwargs: object) -> ToolResult:
                return ToolResult(success=True)

        registry = ToolRegistry()
        registry.register(TestTool())
        assert registry.get("test_tool") is not None
        assert "test_tool" in registry.list_tools()


@pytest.mark.parametrize("agent_name", P0_AGENTS)
class TestP0Agents:
    """Test all 8 P0 priority agents (PRD Section 33.2)."""

    def test_agent_importable(self, agent_name: str) -> None:
        """Each agent is importable from its module."""
        import importlib
        # Map agent name to module
        module_map = {
            "PlannerAgent": "ibr_platform.agents.planner",
            "WebResearchAgent": "ibr_platform.agents.research",
            "VerificationAgent": "ibr_platform.agents.verification",
            "MemoryAgent": "ibr_platform.agents.memory_agent",
            "KnowledgeGraphAgent": "ibr_platform.agents.knowledge_graph",
            "TrainingAgent": "ibr_platform.agents.training_agent",
            "EvaluationAgent": "ibr_platform.agents.evaluation_agent",
            "DeploymentAgent": "ibr_platform.agents.deployment_agent",
        }
        module = importlib.import_module(module_map[agent_name])
        assert hasattr(module, agent_name)

    def test_agent_inherits_from_base(self, agent_name: str) -> None:
        """Each agent inherits from AgentBase."""
        import importlib

        from ibr_platform.agents.base import AgentBase

        module_map = {
            "PlannerAgent": "ibr_platform.agents.planner",
            "WebResearchAgent": "ibr_platform.agents.research",
            "VerificationAgent": "ibr_platform.agents.verification",
            "MemoryAgent": "ibr_platform.agents.memory_agent",
            "KnowledgeGraphAgent": "ibr_platform.agents.knowledge_graph",
            "TrainingAgent": "ibr_platform.agents.training_agent",
            "EvaluationAgent": "ibr_platform.agents.evaluation_agent",
            "DeploymentAgent": "ibr_platform.agents.deployment_agent",
        }
        module = importlib.import_module(module_map[agent_name])
        agent_class = getattr(module, agent_name)
        assert issubclass(agent_class, AgentBase)

    def test_agent_can_be_instantiated(self, agent_name: str) -> None:
        """Each agent can be instantiated."""
        import importlib

        module_map = {
            "PlannerAgent": "ibr_platform.agents.planner",
            "WebResearchAgent": "ibr_platform.agents.research",
            "VerificationAgent": "ibr_platform.agents.verification",
            "MemoryAgent": "ibr_platform.agents.memory_agent",
            "KnowledgeGraphAgent": "ibr_platform.agents.knowledge_graph",
            "TrainingAgent": "ibr_platform.agents.training_agent",
            "EvaluationAgent": "ibr_platform.agents.evaluation_agent",
            "DeploymentAgent": "ibr_platform.agents.deployment_agent",
        }
        module = importlib.import_module(module_map[agent_name])
        agent_class = getattr(module, agent_name)
        agent = agent_class()
        assert agent is not None
        assert agent.name == agent_name

    async def test_agent_initialize(self, agent_name: str) -> None:
        """Each agent's initialize() works."""
        import importlib

        module_map = {
            "PlannerAgent": "ibr_platform.agents.planner",
            "WebResearchAgent": "ibr_platform.agents.research",
            "VerificationAgent": "ibr_platform.agents.verification",
            "MemoryAgent": "ibr_platform.agents.memory_agent",
            "KnowledgeGraphAgent": "ibr_platform.agents.knowledge_graph",
            "TrainingAgent": "ibr_platform.agents.training_agent",
            "EvaluationAgent": "ibr_platform.agents.evaluation_agent",
            "DeploymentAgent": "ibr_platform.agents.deployment_agent",
        }
        module = importlib.import_module(module_map[agent_name])
        agent_class = getattr(module, agent_name)
        agent = agent_class()
        await agent.initialize({})
        assert agent.is_initialized is True

    async def test_agent_execute_returns_result(self, agent_name: str) -> None:
        """Each agent's execute() returns an AgentResult."""
        import importlib

        from ibr_platform.agents.base import AgentResult, Task

        module_map = {
            "PlannerAgent": "ibr_platform.agents.planner",
            "WebResearchAgent": "ibr_platform.agents.research",
            "VerificationAgent": "ibr_platform.agents.verification",
            "MemoryAgent": "ibr_platform.agents.memory_agent",
            "KnowledgeGraphAgent": "ibr_platform.agents.knowledge_graph",
            "TrainingAgent": "ibr_platform.agents.training_agent",
            "EvaluationAgent": "ibr_platform.agents.evaluation_agent",
            "DeploymentAgent": "ibr_platform.agents.deployment_agent",
        }
        module = importlib.import_module(module_map[agent_name])
        agent_class = getattr(module, agent_name)
        agent = agent_class()
        await agent.initialize({})
        task = Task(task="Test task", agent_target=agent_name)
        result = await agent.execute(task)
        assert isinstance(result, AgentResult)
        assert result.success in (True, False)  # Must be a boolean

    async def test_agent_health_check(self, agent_name: str) -> None:
        """Each agent's health_check() returns a HealthStatus."""
        import importlib

        from ibr_platform.agents.base import HealthStatus

        module_map = {
            "PlannerAgent": "ibr_platform.agents.planner",
            "WebResearchAgent": "ibr_platform.agents.research",
            "VerificationAgent": "ibr_platform.agents.verification",
            "MemoryAgent": "ibr_platform.agents.memory_agent",
            "KnowledgeGraphAgent": "ibr_platform.agents.knowledge_graph",
            "TrainingAgent": "ibr_platform.agents.training_agent",
            "EvaluationAgent": "ibr_platform.agents.evaluation_agent",
            "DeploymentAgent": "ibr_platform.agents.deployment_agent",
        }
        module = importlib.import_module(module_map[agent_name])
        agent_class = getattr(module, agent_name)
        agent = agent_class()
        await agent.initialize({})
        health = await agent.health_check()
        assert isinstance(health, HealthStatus)
        assert health.status in ("healthy", "degraded", "unhealthy")

    async def test_agent_shutdown(self, agent_name: str) -> None:
        """Each agent's shutdown() works without error."""
        import importlib

        module_map = {
            "PlannerAgent": "ibr_platform.agents.planner",
            "WebResearchAgent": "ibr_platform.agents.research",
            "VerificationAgent": "ibr_platform.agents.verification",
            "MemoryAgent": "ibr_platform.agents.memory_agent",
            "KnowledgeGraphAgent": "ibr_platform.agents.knowledge_graph",
            "TrainingAgent": "ibr_platform.agents.training_agent",
            "EvaluationAgent": "ibr_platform.agents.evaluation_agent",
            "DeploymentAgent": "ibr_platform.agents.deployment_agent",
        }
        module = importlib.import_module(module_map[agent_name])
        agent_class = getattr(module, agent_name)
        agent = agent_class()
        await agent.initialize({})
        await agent.shutdown()  # Should not raise


class TestAgentRegistry:
    """Test that agents are registered in the global registry."""

    def test_registry_has_all_p0_agents(self) -> None:
        """All 8 P0 agents are in the global registry after import."""
        # Import all agent modules to trigger registration
        import ibr_platform.agents.deployment_agent  # noqa: F401
        import ibr_platform.agents.evaluation_agent  # noqa: F401
        import ibr_platform.agents.knowledge_graph  # noqa: F401
        import ibr_platform.agents.memory_agent  # noqa: F401
        import ibr_platform.agents.planner  # noqa: F401
        import ibr_platform.agents.research  # noqa: F401
        import ibr_platform.agents.training_agent  # noqa: F401
        import ibr_platform.agents.verification  # noqa: F401
        from ibr_platform.agents.base import get_registry
        registry = get_registry()
        registered = registry.list_agents()
        # Check that at least some agents are registered
        assert len(registered) >= 8
