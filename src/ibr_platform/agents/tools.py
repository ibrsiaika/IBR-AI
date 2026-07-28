"""
Tool Framework — Base classes for agent tools (PRD Section 32.6).

Tools are the mechanism by which agents invoke external functionality
(search, fetch, compute, store). Every tool has a typed signature,
declared permissions, and audit logging.

This module provides:
    - ToolBase: Abstract base class for all tools
    - ToolResult: Structured result from tool execution
    - ToolRegistry: Registry of available tools

References:
    - PRD Section 32.6 (Plugin and Tool System Design)
    - PRD Section 61 (MCP — Model Context Protocol)
    - ADR-0004 (Agent Framework — Custom layer on LangGraph)
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ToolResult:
    """Result of a tool execution.

    Attributes:
        success: Whether the execution succeeded.
        data: Result data (tool-specific).
        error: Error message if success is False.
        metadata: Additional metadata (latency, source, etc.).
    """

    success: bool = True
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ToolBase(abc.ABC):
    """Abstract base class for all agent tools (PRD Section 32.6).

    Every tool inherits from ToolBase and implements:
        - name property: The tool name (used for lookup)
        - execute() method: The tool's functionality

    Tools are registered in a ToolRegistry and invoked by agents via
    the tool name. All tool invocations are logged to the audit log.

    Usage:
        class SearchTool(ToolBase):
            @property
            def name(self) -> str:
                return "search"

            async def execute(self, query: str, **kwargs) -> ToolResult:
                # Perform search
                return ToolResult(success=True, data={"results": [...]})

        registry = ToolRegistry()
        registry.register(SearchTool())
        result = await registry.get("search").execute(query="test")
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """The tool name (used for registry lookup)."""
        ...

    @abc.abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with the given arguments.

        Args:
            **kwargs: Tool-specific arguments.

        Returns:
            ToolResult with success status and data.
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r})>"


class ToolRegistry:
    """Registry of available tools (PRD Section 32.6).

    Tools are registered by name and can be looked up for execution.
    The registry enforces that tool names are unique.

    Usage:
        registry = ToolRegistry()
        registry.register(SearchTool())
        registry.register(FetchTool())

        tool = registry.get("search")
        result = await tool.execute(query="test")

        # List all available tools
        for name in registry.list_tools():
            print(name)
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolBase] = {}

    def register(self, tool: ToolBase) -> None:
        """Register a tool.

        Args:
            tool: The tool instance to register.

        Raises:
            TypeError: If tool is not a ToolBase instance.
            ValueError: If a tool with the same name is already registered.
        """
        if not isinstance(tool, ToolBase):
            raise TypeError(f"tool must be a ToolBase instance, got {type(tool)}")
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolBase | None:
        """Get a tool by name.

        Args:
            name: The tool name.

        Returns:
            The ToolBase instance, or None if not found.
        """
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """List all registered tool names.

        Returns:
            List of tool names.
        """
        return list(self._tools.keys())

    def is_registered(self, name: str) -> bool:
        """Check if a tool is registered.

        Args:
            name: The tool name.

        Returns:
            True if the tool is registered, False otherwise.
        """
        return name in self._tools

    def __repr__(self) -> str:
        return f"<ToolRegistry(tools={len(self._tools)})>"
