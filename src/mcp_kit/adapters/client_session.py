"""Client session adapter for MCP targets."""

import logging
from typing import Any

from mcp.types import CallToolResult, ListToolsResult, TextContent

from mcp_kit.targets.interfaces import Target

logger = logging.getLogger(__name__)


class ClientSessionAdapter:
    """Adapter class to convert the target MCP server to a ClientSession.

    This adapter provides a client session interface for interacting with
    MCP targets, wrapping tool calls and error handling.
    """

    def __init__(self, target: Target):
        """Initialize the client session adapter.

        :param target: The MCP target to adapt
        """
        self.target = target

    async def list_tools(self) -> ListToolsResult:
        """List all available tools from the target.

        :return: Result containing the list of available tools
        """
        return ListToolsResult(tools=await self.target.list_tools())

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> CallToolResult:
        """Call a tool on the target with error handling.

        :param name: Name of the tool to call
        :param arguments: Arguments to pass to the tool
        :return: Result containing the tool response or error information
        """
        try:
            return CallToolResult(
                content=await self.target.call_tool(name=name, arguments=arguments),
                isError=False,
            )
        except Exception as e:
            msg = f"Error calling tool {name} with arguments {arguments}: {e}"
            logger.exception(msg)
            return CallToolResult(
                content=[TextContent(type="text", text=msg)],
                isError=True,
            )
