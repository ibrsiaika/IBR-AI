"""
Tests for Section 11 — Multi-Agent Architecture.

Verifies the agent communication protocol (JSON envelope), agent lifecycle
management, and the 12-agent roster defined in PRD Section 11.

Run: pytest tests/unit/test_multi_agent.py -v
"""
from __future__ import annotations

import pytest


class TestAgentMessage:
    """Test the AgentMessage JSON envelope (PRD Section 11.2)."""

    def test_agent_message_importable(self) -> None:
        """AgentMessage is importable."""
        from ibr_platform.agents.message import AgentMessage
        assert AgentMessage is not None

    def test_agent_message_has_all_fields(self) -> None:
        """AgentMessage has all fields from PRD Section 11.2."""
        from ibr_platform.agents.message import AgentMessage
        msg = AgentMessage(
            task="Test task",
            agent_source="Planner",
            agent_target="Research",
        )
        # Required fields from PRD 11.2
        assert hasattr(msg, "task_id")
        assert hasattr(msg, "parent_task_id")
        assert hasattr(msg, "agent_source")
        assert hasattr(msg, "agent_target")
        assert hasattr(msg, "task")
        assert hasattr(msg, "priority")
        assert hasattr(msg, "dependencies")
        assert hasattr(msg, "confidence")
        assert hasattr(msg, "evidence")
        assert hasattr(msg, "status")
        assert hasattr(msg, "memory_ids")
        assert hasattr(msg, "logs")
        assert hasattr(msg, "artifacts")
        assert hasattr(msg, "timestamp")

    def test_agent_message_auto_generates_id(self) -> None:
        """AgentMessage auto-generates a unique task_id."""
        from ibr_platform.agents.message import AgentMessage
        msg1 = AgentMessage(task="A", agent_source="X", agent_target="Y")
        msg2 = AgentMessage(task="B", agent_source="X", agent_target="Y")
        assert msg1.task_id != msg2.task_id
        assert len(msg1.task_id) > 0

    def test_agent_message_default_status_pending(self) -> None:
        """Default status is 'pending'."""
        from ibr_platform.agents.message import AgentMessage, MessageStatus
        msg = AgentMessage(task="Test", agent_source="X", agent_target="Y")
        assert msg.status == MessageStatus.PENDING

    def test_agent_message_to_dict(self) -> None:
        """AgentMessage can be serialized to dict (for JSON)."""
        from ibr_platform.agents.message import AgentMessage
        msg = AgentMessage(task="Test", agent_source="Planner", agent_target="Research")
        d = msg.to_dict()
        assert isinstance(d, dict)
        assert d["task"] == "Test"
        assert d["agent_source"] == "Planner"
        assert d["agent_target"] == "Research"

    def test_agent_message_to_json(self) -> None:
        """AgentMessage can be serialized to JSON string."""
        import json

        from ibr_platform.agents.message import AgentMessage
        msg = AgentMessage(task="Test", agent_source="X", agent_target="Y")
        json_str = msg.to_json()
        parsed = json.loads(json_str)
        assert parsed["task"] == "Test"

    def test_agent_message_from_dict(self) -> None:
        """AgentMessage can be deserialized from dict."""
        from ibr_platform.agents.message import AgentMessage, MessageStatus
        d = {
            "task": "Test from dict",
            "agent_source": "Planner",
            "agent_target": "Research",
            "priority": "P1_HIGH",
            "status": "complete",
        }
        msg = AgentMessage.from_dict(d)
        assert msg.task == "Test from dict"
        assert msg.agent_source == "Planner"
        assert msg.status == MessageStatus.COMPLETE


class TestAgentLifecycle:
    """Test the agent lifecycle management (PRD Section 11.3)."""

    def test_lifecycle_importable(self) -> None:
        """AgentLifecycle is importable."""
        from ibr_platform.agents.lifecycle import AgentLifecycle
        assert AgentLifecycle is not None

    def test_lifecycle_can_be_instantiated(self) -> None:
        """AgentLifecycle can be instantiated."""
        from ibr_platform.agents.lifecycle import AgentLifecycle
        lifecycle = AgentLifecycle()
        assert lifecycle is not None

    def test_lifecycle_has_spawn_method(self) -> None:
        """AgentLifecycle has a spawn method."""
        from ibr_platform.agents.lifecycle import AgentLifecycle
        lc = AgentLifecycle()
        assert hasattr(lc, "spawn")

    def test_lifecycle_has_terminate_method(self) -> None:
        """AgentLifecycle has a terminate method."""
        from ibr_platform.agents.lifecycle import AgentLifecycle
        lc = AgentLifecycle()
        assert hasattr(lc, "terminate")

    def test_lifecycle_has_health_check_method(self) -> None:
        """AgentLifecycle has a health_check method."""
        from ibr_platform.agents.lifecycle import AgentLifecycle
        lc = AgentLifecycle()
        assert hasattr(lc, "health_check")

    async def test_lifecycle_spawn_returns_agent_id(self) -> None:
        """Spawning an agent returns a unique agent ID."""
        from ibr_platform.agents.base import AgentBase, AgentResult, HealthStatus
        from ibr_platform.agents.lifecycle import AgentLifecycle

        class DummyAgent(AgentBase):
            async def initialize(self, config):
                pass
            async def execute(self, task):
                return AgentResult(success=True)
            async def health_check(self):
                return HealthStatus(status="healthy")
            async def shutdown(self):
                pass

        lc = AgentLifecycle()
        agent_id = await lc.spawn("dummy", DummyAgent, config={})
        assert agent_id is not None
        assert isinstance(agent_id, str)

    async def test_lifecycle_terminate_removes_agent(self) -> None:
        """Terminating an agent removes it from the lifecycle."""
        from ibr_platform.agents.base import AgentBase, AgentResult, HealthStatus
        from ibr_platform.agents.lifecycle import AgentLifecycle

        class DummyAgent(AgentBase):
            async def initialize(self, config):
                pass
            async def execute(self, task):
                return AgentResult(success=True)
            async def health_check(self):
                return HealthStatus(status="healthy")
            async def shutdown(self):
                pass

        lc = AgentLifecycle()
        agent_id = await lc.spawn("dummy", DummyAgent, config={})
        await lc.terminate(agent_id)
        assert agent_id not in lc.active_agents

    async def test_lifecycle_list_active(self) -> None:
        """list_active returns all active agent IDs."""
        from ibr_platform.agents.base import AgentBase, AgentResult, HealthStatus
        from ibr_platform.agents.lifecycle import AgentLifecycle

        class DummyAgent(AgentBase):
            async def initialize(self, config):
                pass
            async def execute(self, task):
                return AgentResult(success=True)
            async def health_check(self):
                return HealthStatus(status="healthy")
            async def shutdown(self):
                pass

        lc = AgentLifecycle()
        id1 = await lc.spawn("a1", DummyAgent, config={})
        id2 = await lc.spawn("a2", DummyAgent, config={})
        active = lc.list_active()
        assert id1 in active
        assert id2 in active
        assert len(active) == 2


class TestAgentRoster:
    """Test the 12-agent roster (PRD Section 11.1, Table 11.1)."""

    EXPECTED_AGENTS = [
        "Planner",
        "WebResearch",
        "AcademicResearch",
        "CodeResearch",
        "Verification",
        "Memory",
        "KnowledgeGraph",
        "Dataset",
        "Training",
        "Evaluation",
        "SelfImprovement",
        "Deployment",
    ]

    def test_agent_roster_importable(self) -> None:
        """The agent roster is importable."""
        from ibr_platform.agents.roster import AGENT_ROSTER
        assert AGENT_ROSTER is not None

    @pytest.mark.parametrize("agent_name", EXPECTED_AGENTS)
    def test_agent_in_roster(self, agent_name: str) -> None:
        """Each expected agent is in the roster."""
        from ibr_platform.agents.roster import AGENT_ROSTER
        assert agent_name in AGENT_ROSTER, f"Agent '{agent_name}' not in roster"

    def test_roster_has_12_agents(self) -> None:
        """The roster has at least 12 agents."""
        from ibr_platform.agents.roster import AGENT_ROSTER
        assert len(AGENT_ROSTER) >= 12

    @pytest.mark.parametrize("agent_name", EXPECTED_AGENTS)
    def test_agent_has_metadata(self, agent_name: str) -> None:
        """Each agent has metadata (role, function_group, tools, memory_access)."""
        from ibr_platform.agents.roster import AGENT_ROSTER
        info = AGENT_ROSTER[agent_name]
        assert "role" in info
        assert "function_group" in info
        assert "tools" in info
        assert "memory_access" in info

    @pytest.mark.parametrize("agent_name", EXPECTED_AGENTS)
    def test_agent_has_priority(self, agent_name: str) -> None:
        """Each agent has a priority level (P0-P2)."""
        from ibr_platform.agents.roster import AGENT_ROSTER
        info = AGENT_ROSTER[agent_name]
        assert "priority" in info
        assert info["priority"] in ["P0", "P1", "P2"]
