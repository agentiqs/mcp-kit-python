"""Interface definitions for response generators."""

from abc import abstractmethod
from typing import Any

from mcp import Tool
from mcp.types import Content

from mcp_kit.mixins import ConfigurableMixin


class ResponseGenerator(ConfigurableMixin):
    """Interface for generating response data for an MCP call_tool.

    Response generators create synthetic responses for MCP tool calls,
    which is useful for testing, mocking, or simulation scenarios.
    """

    @abstractmethod
    async def generate(
        self,
        target_name: str,
        tool: Tool,
        arguments: dict[str, Any] | None = None,
    ) -> list[Content]:
        """Generate an MCP call tool response.

        :param target_name: Name of the target that would handle the tool call
        :param tool: The MCP tool definition
        :param arguments: Arguments that would be passed to the tool
        :return: List of generated content responses
        """
