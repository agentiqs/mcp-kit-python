"""Interface definitions for MCP targets."""

from abc import abstractmethod
from typing import Any

from mcp import Tool
from mcp.types import Content

from mcp_kit.mixins import ConfigurableMixin


class Target(ConfigurableMixin):
    """Abstract base class for MCP targets.

    A Target represents a destination for MCP tool calls. It defines the interface
    that all concrete target implementations must follow.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this target.

        :return: The target name
        """
        ...

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the target for use.

        This method should be called before any other operations.
        """
        ...

    @abstractmethod
    async def list_tools(self) -> list[Tool]:
        """List all available tools for this target.

        :return: List of available MCP tools
        """
        ...

    @abstractmethod
    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> list[Content]:
        """Call a specific tool with given arguments.

        :param name: Name of the tool to call
        :param arguments: Arguments to pass to the tool
        :return: List of content responses from the tool
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Clean up and close the target.

        This method should be called when the target is no longer needed.
        """
        ...
